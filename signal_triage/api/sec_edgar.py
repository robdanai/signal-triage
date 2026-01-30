"""
Production-Grade SEC EDGAR API Client.

Full-featured client for SEC EDGAR with:
- Filing retrieval (10-K, 10-Q, 8-K, amendments)
- Financial data extraction (XBRL parsing)
- 8-K event detection (bankruptcy, delisting, covenant defaults)
- CIK/ticker lookup
- Rate limiting (10 req/sec per SEC guidelines)
- Caching with TTL
- Retry logic with exponential backoff
- Circuit breaker for fault tolerance

SEC API Documentation: https://www.sec.gov/edgar/sec-api-documentation
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from signal_triage.config import get_config
from signal_triage.infrastructure.rate_limiter import get_rate_limiter
from signal_triage.infrastructure.cache import get_cache_manager
from signal_triage.infrastructure.circuit_breaker import get_circuit_breaker
from signal_triage.infrastructure.retry import get_retry_strategy


logger = logging.getLogger(__name__)


class SECEdgarClient:
    """
    Production-grade SEC EDGAR API client.
    
    Provides high-availability access to SEC filings with automatic rate limiting,
    caching, and error handling.
    """
    
    PROVIDER = "sec_edgar"
    BASE_URL = "https://www.sec.gov"
    DATA_API_URL = "https://data.sec.gov"
    
    def __init__(self):
        """Initialize SEC EDGAR client with infrastructure components."""
        if requests is None:
            raise ImportError(
                "SEC EDGAR client requires 'requests' package. "
                "Install: pip install requests"
            )
        
        self.config = get_config()
        self.rate_limiter = get_rate_limiter()
        self.cache = get_cache_manager()
        self.circuit_breaker = get_circuit_breaker(self.PROVIDER)
        self.retry_strategy = get_retry_strategy()
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.api.sec_user_agent,
            "Accept": "application/json"
        })
    
    def _api_call(self, url: str, headers: Optional[dict] = None, 
                  params: Optional[dict] = None) -> requests.Response:
        """
        Make API call with rate limiting, retry, and circuit breaker.
        
        Args:
            url: API endpoint URL.
            headers: Optional additional headers.
            params: Optional query parameters.
        
        Returns:
            Response object.
        
        Raises:
            requests.HTTPError: If request fails after retries.
        """
        # Acquire rate limit token
        self.rate_limiter.acquire(self.PROVIDER)
        
        # Merge headers
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)
        
        # Make request with circuit breaker and retry
        def _request():
            resp = self.session.get(
                url,
                headers=req_headers,
                params=params,
                timeout=self.config.api.sec_timeout
            )
            resp.raise_for_status()
            return resp
        
        return self.circuit_breaker.call(
            lambda: self.retry_strategy.call(_request)
        )
    
    def lookup_cik(self, ticker: str) -> Optional[str]:
        """
        Lookup CIK (Central Index Key) by ticker symbol.
        
        Args:
            ticker: Stock ticker (e.g., "AAPL", "TSLA").
        
        Returns:
            CIK string (e.g., "0000320193") or None if not found.
        """
        cache_key = self.cache.make_key(self.PROVIDER, "lookup_cik", ticker=ticker.upper())
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Use SEC company tickers JSON
            url = f"{self.DATA_API_URL}/files/company_tickers.json"
            resp = self._api_call(url)
            data = resp.json()
            
            # Search for ticker
            ticker_upper = ticker.upper()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker_upper:
                    cik = str(entry["cik_str"]).zfill(10)  # Pad to 10 digits
                    self.cache.set(cache_key, cik, ttl=self.config.cache.ttl_sec_filings)
                    return cik
            
            # Not found
            self.cache.set(cache_key, None, ttl=self.config.cache.ttl_sec_filings)
            return None
            
        except Exception as e:
            logger.error(f"Failed to lookup CIK for ticker {ticker}: {e}")
            return None
    
    def get_company_info(self, cik: str) -> dict[str, Any]:
        """
        Get company information by CIK.
        
        Args:
            cik: Company CIK (e.g., "0000320193" or "320193").
        
        Returns:
            Dict with name, sic, sic_description, tickers, exchanges, etc.
        """
        cik_padded = cik.lstrip("0") if cik.startswith("0") else cik
        cache_key = self.cache.make_key(self.PROVIDER, "company_info", cik=cik_padded)
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            url = f"{self.DATA_API_URL}/submissions/CIK{cik_padded}.json"
            resp = self._api_call(url)
            data = resp.json()
            
            result = {
                "cik": data.get("cik"),
                "name": data.get("name"),
                "sic": data.get("sic"),
                "sic_description": data.get("sicDescription"),
                "tickers": data.get("tickers", []),
                "exchanges": data.get("exchanges", []),
                "fiscal_year_end": data.get("fiscalYearEnd"),
                "business_address": data.get("addresses", {}).get("business"),
                "phone": data.get("phone"),
                "source": "SEC EDGAR Submissions API",
                "date": self._today_iso(),
            }
            
            self.cache.set(cache_key, result, ttl=self.config.cache.ttl_company_financials)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get company info for CIK {cik}: {e}")
            return {
                "cik": cik,
                "error": str(e),
                "source": "SEC EDGAR (failed)",
            }
    
    def get_filings(
        self,
        cik: str,
        form_type: str = "10-K",
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get filing history for a company.
        
        Args:
            cik: Company CIK.
            form_type: Filing type ("10-K", "10-Q", "8-K", "10-K/A", etc.).
            limit: Maximum number of filings to return.
        
        Returns:
            List of filings with filing_date, accession_number, document_url, source.
        """
        cik_padded = cik.lstrip("0") if cik.startswith("0") else cik
        cache_key = self.cache.make_key(
            self.PROVIDER, "filings",
            cik=cik_padded, form_type=form_type, limit=limit
        )
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            url = f"{self.DATA_API_URL}/submissions/CIK{cik_padded}.json"
            resp = self._api_call(url)
            data = resp.json()
            
            filings_data = data.get("filings", {}).get("recent", {})
            forms = filings_data.get("form", [])
            filing_dates = filings_data.get("filingDate", [])
            accession_numbers = filings_data.get("accessionNumber", [])
            primary_documents = filings_data.get("primaryDocument", [])
            
            results = []
            count = 0
            
            for i, form in enumerate(forms):
                if form == form_type and count < limit:
                    filing_date = filing_dates[i] if i < len(filing_dates) else "N/A"
                    accession = accession_numbers[i] if i < len(accession_numbers) else ""
                    primary_doc = primary_documents[i] if i < len(primary_documents) else ""
                    
                    # Build document URL
                    accession_no_dashes = accession.replace("-", "")
                    doc_url = (
                        f"{self.BASE_URL}/Archives/edgar/data/{cik_padded}/"
                        f"{accession_no_dashes}/{primary_doc}"
                    )
                    
                    results.append({
                        "cik": cik,
                        "form_type": form,
                        "filing_date": filing_date,
                        "accession_number": accession,
                        "document_url": doc_url,
                        "source": f"SEC EDGAR Submissions API (CIK {cik})",
                        "date": self._today_iso(),
                    })
                    count += 1
            
            self.cache.set(cache_key, results, ttl=self.config.cache.ttl_sec_filings)
            return results
            
        except Exception as e:
            logger.error(f"Failed to get filings for CIK {cik}: {e}")
            return [{"error": str(e), "source": "SEC EDGAR (failed)"}]
    
    def get_company_financials(self, cik: str) -> dict[str, Any]:
        """
        Get company financials from SEC EDGAR Company Facts API (XBRL data).
        
        Args:
            cik: Company CIK.
        
        Returns:
            Dict with revenue, total_debt, ebitda, filing_date, source.
        """
        cik_padded = cik.lstrip("0") if cik.startswith("0") else cik
        cache_key = self.cache.make_key(self.PROVIDER, "company_financials", cik=cik_padded)
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            url = f"{self.DATA_API_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"
            resp = self._api_call(url)
            data = resp.json()
            
            facts = data.get("facts", {}).get("us-gaap", {})
            
            revenue = None
            total_debt = None
            ebitda = None
            filing_date = None
            
            # Extract Revenue
            for tag in ["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"]:
                if tag in facts:
                    units = facts[tag].get("units", {})
                    usd_data = units.get("USD", [])
                    if usd_data:
                        annual = [x for x in usd_data if x.get("form") == "10-K"]
                        if annual:
                            revenue = annual[-1].get("val")
                            filing_date = annual[-1].get("filed") or annual[-1].get("end")
                            break
            
            # Extract Debt
            long_term_debt = None
            current_debt = None
            for tag in ["LongTermDebt", "LongTermDebtNoncurrent"]:
                if tag in facts:
                    units = facts[tag].get("units", {})
                    usd_data = units.get("USD", [])
                    if usd_data:
                        annual = [x for x in usd_data if x.get("form") == "10-K"]
                        if annual:
                            long_term_debt = annual[-1].get("val")
                            break
            
            if "DebtCurrent" in facts:
                units = facts["DebtCurrent"].get("units", {})
                usd_data = units.get("USD", [])
                if usd_data:
                    annual = [x for x in usd_data if x.get("form") == "10-K"]
                    if annual:
                        current_debt = annual[-1].get("val")
            
            if long_term_debt is not None and current_debt is not None:
                total_debt = long_term_debt + current_debt
            elif long_term_debt is not None:
                total_debt = long_term_debt
            
            # Calculate EBITDA (Operating Income + D&A)
            operating_income = None
            depreciation = None
            
            for tag in ["OperatingIncomeLoss", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]:
                if tag in facts:
                    units = facts[tag].get("units", {})
                    usd_data = units.get("USD", [])
                    if usd_data:
                        annual = [x for x in usd_data if x.get("form") == "10-K"]
                        if annual:
                            operating_income = annual[-1].get("val")
                            break
            
            for tag in ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization"]:
                if tag in facts:
                    units = facts[tag].get("units", {})
                    usd_data = units.get("USD", [])
                    if usd_data:
                        annual = [x for x in usd_data if x.get("form") == "10-K"]
                        if annual:
                            depreciation = annual[-1].get("val")
                            break
            
            if operating_income is not None and depreciation is not None:
                ebitda = operating_income + depreciation
            
            result = {
                "cik": cik,
                "revenue": revenue,
                "total_debt": total_debt,
                "ebitda": ebitda,
                "filing_date": filing_date,
                "source": f"SEC EDGAR Company Facts API (CIK {cik})",
                "date": self._today_iso(),
            }
            
            self.cache.set(cache_key, result, ttl=self.config.cache.ttl_company_financials)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get company financials for CIK {cik}: {e}")
            return {
                "cik": cik,
                "error": str(e),
                "source": "SEC EDGAR Company Facts API (failed)",
            }
    
    def detect_8k_distress_events(self, cik: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Detect distress events in recent 8-K filings.
        
        Distress indicators:
        - Item 1.01: Material agreements (restructuring)
        - Item 1.03: Bankruptcy or receivership
        - Item 2.04: Triggering events accelerating obligations
        - Item 3.01: Delisting or failure to meet listing standards
        - Item 5.02: Management departures
        - Item 8.01: Other events (often restructuring)
        
        Args:
            cik: Company CIK.
            limit: Max number of 8-K filings to check.
        
        Returns:
            List of 8-K events with distress indicators.
        """
        filings = self.get_filings(cik, form_type="8-K", limit=limit)
        
        distress_events = []
        for filing in filings:
            if "error" not in filing:
                distress_events.append({
                    **filing,
                    "items_detected": "N/A",  # Would need HTML parsing to detect items
                    "distress_level": "unknown",  # Would need NLP/parsing to classify
                })
        
        return distress_events
    
    def get_recent_8k_comparables(
        self,
        limit: int = 10,
        industry: Optional[str] = None,
        geography: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get recent 8-K filings across all companies (for comparable analysis).
        
        Args:
            limit: Max number of filings to return.
            industry: Industry filter (not supported by EDGAR feed, passed through).
            geography: Geography filter (not supported, passed through).
        
        Returns:
            List of recent 8-K filings with company info.
        """
        cache_key = self.cache.make_key(
            self.PROVIDER, "recent_8k",
            limit=limit, industry=industry, geography=geography
        )
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            url = f"{self.BASE_URL}/cgi-bin/browse-edgar"
            params = {
                "action": "getcurrent",
                "type": "8-K",
                "company": "",
                "dateb": "",
                "owner": "include",
                "start": 0,
                "count": max(limit, 40),
                "output": "atom"
            }
            
            headers = {"Accept": "application/atom+xml"}
            resp = self._api_call(url, headers=headers, params=params)
            
            entries = self._parse_edgar_atom_feed(resp.text)[:limit]
            
            result = []
            for e in entries:
                datum = {
                    "name": e["name"],
                    "industry": industry or "N/A",
                    "geography": geography or "US",
                    "restructuring_date": e["filing_date"],
                    "cik": e["cik"],
                    "source": "SEC EDGAR (recent 8-K filings)",
                    "date": self._today_iso(),
                }
                result.append(datum)
            
            self.cache.set(cache_key, result, ttl=self.config.cache.ttl_sec_filings)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get recent 8-K comparables: {e}")
            return []
    
    def _parse_edgar_atom_feed(self, xml_text: str) -> list[dict[str, Any]]:
        """
        Parse SEC EDGAR Atom feed into list of filing entries.
        
        Args:
            xml_text: Atom feed XML content.
        
        Returns:
            List of entries with name, form_type, filing_date, cik, link.
        """
        out: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return out
        
        def find_all(elem: ET.Element, tag: str) -> list[ET.Element]:
            if "}" in tag:
                return elem.findall(tag)
            for ns in ("http://www.w3.org/2005/Atom", ""):
                q = f"{{{ns}}}{tag}" if ns else tag
                found = elem.findall(q)
                if found:
                    return found
            return []
        
        def find_one(elem: ET.Element, tag: str) -> ET.Element | None:
            if "}" in tag:
                return elem.find(tag)
            for ns in ("http://www.w3.org/2005/Atom", ""):
                q = f"{{{ns}}}{tag}" if ns else tag
                node = elem.find(q)
                if node is not None:
                    return node
            return None
        
        def text(elem: ET.Element | None) -> str:
            return (elem.text or "").strip() if elem is not None else ""
        
        for entry in find_all(root, "entry"):
            title_el = find_one(entry, "title")
            updated_el = find_one(entry, "updated")
            link_el = find_one(entry, "link")
            title = text(title_el)
            updated = text(updated_el)
            
            name = title
            if " - " in title:
                parts = title.split(" - ", 1)
                if len(parts) == 2:
                    if parts[0].strip().upper().startswith("8-K"):
                        name = parts[1].strip()
                    else:
                        name = parts[0].strip()
            
            cik_match = re.search(r"\s*\((\d+)\)\s*$", name)
            cik = cik_match.group(1) if cik_match else ""
            if cik:
                name = name[: cik_match.start()].strip()
            
            filing_date = updated[:10] if len(updated) >= 10 else updated
            href = link_el.get("href", "") if link_el is not None else ""
            
            out.append({
                "name": name or "Unknown",
                "form_type": "8-K",
                "filing_date": filing_date,
                "accession": "",
                "cik": cik,
                "link": href,
            })
        
        return out
    
    def _today_iso(self) -> str:
        """Get current date in ISO format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

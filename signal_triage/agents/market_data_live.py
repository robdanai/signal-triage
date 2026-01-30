"""
Live Market Data Integration — Free and Commercial APIs.

Provides live market data for Benchmarker using free APIs (SEC EDGAR, FRED) and
commercial APIs (9fin, Bloomberg) when credentials are available.

Institutional Restructuring Desk: Real-time market validation replaces stubs with
actual precedent recovery rates, exit multiples, yield spreads, and macro indicators.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set to DEBUG for verbose output

# Add handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# User-Agent for SEC EDGAR (required)
SEC_USER_AGENT = "SignalTriage/1.0 (distressed debt analysis; contact via SEC.gov)"
DEFAULT_TIMEOUT = 30

# Simple in-memory cache for rate-limited APIs
_API_CACHE: dict[str, tuple[Any, datetime]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes default cache

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
RETRY_INITIAL_DELAY = 1.0  # Initial delay in seconds


def _cache_get(key: str, ttl_seconds: int = _CACHE_TTL_SECONDS) -> Any | None:
    """Get cached value if still valid."""
    if key in _API_CACHE:
        value, cached_at = _API_CACHE[key]
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age < ttl_seconds:
            return value
    return None


def _cache_set(key: str, value: Any) -> None:
    """Set cached value with current timestamp."""
    _API_CACHE[key] = (value, datetime.now(timezone.utc))


def _retry_with_backoff(func, max_retries: int = MAX_RETRIES, initial_delay: float = RETRY_INITIAL_DELAY):
    """
    Retry function with exponential backoff.

    Args:
        func: Function to retry (should raise exception on failure)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)

    Returns:
        Result from func() on success

    Raises:
        Last exception if all retries fail
    """
    import time
    
    last_exception = None
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s delay: {e}")
                time.sleep(delay)
                delay *= RETRY_BACKOFF_FACTOR
            else:
                logger.error(f"All {max_retries} retries failed: {e}")
    
    raise last_exception  # type: ignore[misc]


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ===== SEC EDGAR (Free) =====

def edgar_get_company_financials(
    cik: str,
    form_type: str = "10-K",
) -> dict[str, Any]:
    """
    Fetch company financials from SEC EDGAR (XBRL or HTML parsing).

    Args:
        cik: Company CIK (e.g. "0001652044" for Sonder).
        form_type: Filing type ("10-K", "10-Q", "8-K").

    Returns:
        Dict with revenue, total_debt, ebitda (if extractable), filing_date, source.

    Note: SEC EDGAR provides XBRL datasets (company-facts.json) which contain
    structured financial data. This is a free, no-API-key source.
    """
    if requests is None:
        return {"error": "requests not installed", "source": "SEC EDGAR (failed)"}

    # SEC Company Facts API: https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
    cik_padded = cik.lstrip("0") if cik.startswith("0") else cik
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    headers = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e), "source": "SEC EDGAR Company Facts API"}

    # Extract facts: Revenue, Debt, EBITDA (if available)
    # XBRL tags: us-gaap:Revenues, us-gaap:LongTermDebt, us-gaap:DebtCurrent, etc.
    facts = data.get("facts", {}).get("us-gaap", {})

    revenue = None
    total_debt = None
    ebitda = None
    filing_date = None

    # Revenue (or SalesRevenueNet)
    for tag in ["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"]:
        if tag in facts:
            units = facts[tag].get("units", {})
            usd_data = units.get("USD", [])
            if usd_data:
                # Get most recent 10-K entry
                annual = [x for x in usd_data if x.get("form") == "10-K"]
                if annual:
                    revenue = annual[-1].get("val")
                    filing_date = annual[-1].get("filed") or annual[-1].get("end")
                    break

    # Debt: LongTermDebt + DebtCurrent
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

    # Try to calculate EBITDA from OperatingIncomeLoss + DepreciationDepletionAndAmortization
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

    return {
        "cik": cik,
        "revenue": revenue,
        "total_debt": total_debt,
        "ebitda": ebitda,
        "filing_date": filing_date,
        "source": f"SEC EDGAR Company Facts API (CIK {cik})",
        "date": _today_iso(),
    }


def edgar_get_recent_distressed_filings(
    limit: int = 20,
    form_types: list[str] = ["8-K", "10-Q", "10-K"],
) -> list[dict[str, Any]]:
    """
    Fetch recent SEC filings that may indicate distress (8-K, 10-Q, 10-K).

    Args:
        limit: Max number of filings to return.
        form_types: List of form types to fetch (8-K for events, 10-K/10-Q for financials).

    Returns:
        List of filings with name, form_type, filing_date, cik, source.
    """
    if requests is None:
        return []

    results = []
    for form in form_types[:3]:  # Limit to 3 form types to avoid rate limiting
        url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcurrent&type={form}&company=&dateb=&owner=include"
            f"&start=0&count={limit}&output=atom"
        )
        headers = {"User-Agent": SEC_USER_AGENT, "Accept": "application/atom+xml"}
        try:
            resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            # Parse using existing _parse_edgar_atom_feed from market_data_client
            from signal_triage.agents.market_data_client import _parse_edgar_atom_feed
            entries = _parse_edgar_atom_feed(resp.text)[:limit]
            for e in entries:
                e["industry"] = "N/A"  # EDGAR doesn't provide SIC/industry in feed
                e["geography"] = "US"
                e["source"] = f"SEC EDGAR (recent {form} filings)"
                e["date"] = _today_iso()
            results.extend(entries)
        except Exception:
            continue

    return results[:limit]


def edgar_detect_8k_distress_events(
    cik: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch 8-K filings for a specific company and detect distress events.

    Distress indicators in 8-K:
    - Item 1.01: Entry into Material Definitive Agreement (restructuring agreements)
    - Item 1.03: Bankruptcy or Receivership
    - Item 2.04: Triggering Events That Accelerate Obligations
    - Item 3.01: Notice of Delisting or Failure to Satisfy Listing Standards
    - Item 5.02: Departure of Directors or Officers (management turnover)
    - Item 8.01: Other Events (often used for restructuring announcements)

    Args:
        cik: Company CIK (e.g. "0001652044").
        limit: Max number of 8-K filings to check.

    Returns:
        List of 8-K events with distress indicators, filing_date, items, source.
    """
    if requests is None:
        return []

    # SEC submissions API: https://data.sec.gov/submissions/CIK{cik}.json
    cik_padded = cik.lstrip("0") if cik.startswith("0") else cik
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    headers = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"error": str(e), "source": "SEC EDGAR Submissions API"}]

    # Extract recent 8-K filings
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_documents = filings.get("primaryDocument", [])

    distress_events = []
    count = 0

    for i, form in enumerate(forms):
        if form == "8-K" and count < limit:
            filing_date = filing_dates[i] if i < len(filing_dates) else "N/A"
            accession = accession_numbers[i] if i < len(accession_numbers) else ""
            primary_doc = primary_documents[i] if i < len(primary_documents) else ""

            # Build URL to filing document
            accession_no_dashes = accession.replace("-", "")
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/"
                f"{accession_no_dashes}/{primary_doc}"
            )

            distress_events.append({
                "cik": cik,
                "form_type": "8-K",
                "filing_date": filing_date,
                "accession_number": accession,
                "document_url": doc_url,
                "items_detected": "N/A",  # Would need to parse HTML/text to detect items
                "source": f"SEC EDGAR Submissions API (CIK {cik})",
                "date": _today_iso(),
            })
            count += 1

    return distress_events


def edgar_get_filing_history(
    cik: str,
    form_type: str = "10-K",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Get filing history for a company (10-K, 10-Q, 8-K, amendments).

    Args:
        cik: Company CIK.
        form_type: Filing type ("10-K", "10-Q", "8-K", "10-K/A" for amendments).
        limit: Max number of filings to return.

    Returns:
        List of filings with filing_date, accession_number, document_url, source.
    """
    if requests is None:
        return []

    cik_padded = cik.lstrip("0") if cik.startswith("0") else cik
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    headers = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"error": str(e), "source": "SEC EDGAR Submissions API"}]

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_documents = filings.get("primaryDocument", [])

    results = []
    count = 0

    for i, form in enumerate(forms):
        if form == form_type and count < limit:
            filing_date = filing_dates[i] if i < len(filing_dates) else "N/A"
            accession = accession_numbers[i] if i < len(accession_numbers) else ""
            primary_doc = primary_documents[i] if i < len(primary_documents) else ""

            accession_no_dashes = accession.replace("-", "")
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/"
                f"{accession_no_dashes}/{primary_doc}"
            )

            results.append({
                "cik": cik,
                "form_type": form,
                "filing_date": filing_date,
                "accession_number": accession,
                "document_url": doc_url,
                "source": f"SEC EDGAR Submissions API (CIK {cik})",
                "date": _today_iso(),
            })
            count += 1

    return results


# ===== FRED (Federal Reserve Economic Data) — Free =====

def fred_get_treasury_yield(maturity: str = "10Y") -> dict[str, Any]:
    """
    Fetch US Treasury yield from FRED (Federal Reserve Economic Data).

    Args:
        maturity: "10Y" (10-year), "2Y", "5Y", "30Y".

    Returns:
        Dict with yield_pct, maturity, date, source.

    FRED API is free with API key (register at https://fred.stlouisfed.org/docs/api/api_key.html).
    If FRED_API_KEY env var is not set, returns stub.
    """
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "yield_pct": None,
            "maturity": maturity,
            "source": "FRED (no API key; register at https://fred.stlouisfed.org/docs/api/api_key.html)",
            "date": _today_iso(),
        }

    # FRED series IDs for Treasury yields
    series_map = {
        "2Y": "DGS2",
        "5Y": "DGS5",
        "10Y": "DGS10",
        "30Y": "DGS30",
    }
    series_id = series_map.get(maturity, "DGS10")

    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",  # Most recent first
        "limit": 1,
    }

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        obs = data.get("observations", [])
        if obs:
            latest = obs[0]
            yield_val = latest.get("value")
            obs_date = latest.get("date")
            if yield_val and yield_val != ".":
                return {
                    "yield_pct": float(yield_val),
                    "maturity": maturity,
                    "date": obs_date,
                    "source": f"FRED (Federal Reserve Economic Data, series {series_id})",
                }
    except Exception:
        pass

    return {
        "yield_pct": None,
        "maturity": maturity,
        "source": "FRED (API call failed)",
        "date": _today_iso(),
    }


def calculate_yield_spread(
    target_yield: float,
    treasury_maturity: str = "10Y",
) -> dict[str, Any]:
    """
    Calculate yield spread over Treasury (OAS approximation).

    Args:
        target_yield: Debt yield (e.g. 12.5% for distressed bond).
        treasury_maturity: "10Y", "2Y", "5Y", "30Y".

    Returns:
        Dict with spread_bps, target_yield, treasury_yield, source.
    """
    treasury = fred_get_treasury_yield(treasury_maturity)
    treasury_yield = treasury.get("yield_pct")

    if treasury_yield is None:
        return {
            "spread_bps": None,
            "target_yield": target_yield,
            "treasury_yield": None,
            "source": "Spread calculation failed (no Treasury yield available)",
        }

    spread_bps = (target_yield - treasury_yield) * 100  # Convert to basis points
    return {
        "spread_bps": round(spread_bps, 1),
        "target_yield": target_yield,
        "treasury_yield": treasury_yield,
        "maturity": treasury_maturity,
        "source": f"Spread over {treasury_maturity} Treasury ({treasury.get('source')})",
        "date": treasury.get("date"),
    }


# ===== Alpha Vantage (Free/Commercial) =====

def alphavantage_get_stock_price(
    symbol: str,
    market: str = "US",
) -> dict[str, Any]:
    """
    Fetch current stock price from Alpha Vantage (free tier: 25 calls/day).

    Args:
        symbol: Stock ticker (e.g. "AAPL", "GME").
        market: Market ("US", "UK", etc.).

    Returns:
        Dict with price, symbol, currency, source, date.

    Setup: Register for free API key at https://www.alphavantage.co/support/#api-key
    Set ALPHAVANTAGE_API_KEY environment variable.
    """
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "symbol": symbol,
            "price": None,
            "currency": "USD",
            "source": "Alpha Vantage (no API key; register at https://www.alphavantage.co/support/#api-key)",
            "date": _today_iso(),
        }

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        quote = data.get("Global Quote", {})
        price = quote.get("05. price")
        trading_day = quote.get("07. latest trading day")
        
        if price:
            return {
                "symbol": symbol,
                "price": float(price),
                "currency": "USD",
                "trading_day": trading_day,
                "source": f"Alpha Vantage (Global Quote for {symbol})",
                "date": _today_iso(),
            }
    except Exception as e:
        return {
            "symbol": symbol,
            "price": None,
            "error": str(e),
            "source": "Alpha Vantage (API call failed)",
            "date": _today_iso(),
        }

    return {
        "symbol": symbol,
        "price": None,
        "source": "Alpha Vantage (no data available)",
        "date": _today_iso(),
    }


def alphavantage_get_bond_yield(
    maturity: str = "10year",
) -> dict[str, Any]:
    """
    Fetch Treasury yield from Alpha Vantage (free alternative to FRED).

    Args:
        maturity: "3month", "2year", "5year", "10year", "30year".

    Returns:
        Dict with yield_pct, maturity, source, date.

    Note: Alpha Vantage provides Treasury yields via TREASURY_YIELD function.
    """
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "yield_pct": None,
            "maturity": maturity,
            "source": "Alpha Vantage (no API key)",
            "date": _today_iso(),
        }

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TREASURY_YIELD",
        "interval": "daily",
        "maturity": maturity,
        "apikey": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        time_series = data.get("data", [])
        if time_series:
            latest = time_series[0]
            yield_val = latest.get("value")
            obs_date = latest.get("date")
            
            if yield_val:
                return {
                    "yield_pct": float(yield_val),
                    "maturity": maturity,
                    "date": obs_date,
                    "source": f"Alpha Vantage (Treasury Yield {maturity})",
                }
    except Exception:
        pass

    return {
        "yield_pct": None,
        "maturity": maturity,
        "source": "Alpha Vantage (API call failed)",
        "date": _today_iso(),
    }


# ===== Yahoo Finance (Free, No API Key) =====

def yahoo_get_stock_quote(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch stock quote from Yahoo Finance (free, no API key required).

    Uses Yahoo Finance's public API (undocumented but widely used).

    Args:
        symbol: Stock ticker (e.g. "AAPL", "TSLA").

    Returns:
        Dict with price, volume, market_cap, pe_ratio, 52w high/low, source, date.

    Note: Yahoo Finance API is free but unofficial. Use responsibly.
    """
    if requests is None:
        return {"symbol": symbol, "price": None, "source": "Yahoo Finance (requests not installed)"}

    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "price,summaryDetail,defaultKeyStatistics"}
    headers = {"User-Agent": SEC_USER_AGENT}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        result = data.get("quoteSummary", {}).get("result", [])
        if not result:
            return {"symbol": symbol, "price": None, "source": "Yahoo Finance (no data)"}
        
        price_data = result[0].get("price", {})
        summary = result[0].get("summaryDetail", {})
        key_stats = result[0].get("defaultKeyStatistics", {})
        
        return {
            "symbol": symbol,
            "price": price_data.get("regularMarketPrice", {}).get("raw"),
            "currency": price_data.get("currency"),
            "volume": summary.get("volume", {}).get("raw"),
            "market_cap": price_data.get("marketCap", {}).get("raw"),
            "pe_ratio": summary.get("trailingPE", {}).get("raw"),
            "forward_pe": summary.get("forwardPE", {}).get("raw"),
            "week_52_high": summary.get("fiftyTwoWeekHigh", {}).get("raw"),
            "week_52_low": summary.get("fiftyTwoWeekLow", {}).get("raw"),
            "beta": key_stats.get("beta", {}).get("raw"),
            "shares_outstanding": key_stats.get("sharesOutstanding", {}).get("raw"),
            "source": f"Yahoo Finance (quote for {symbol})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"symbol": symbol, "price": None, "error": str(e), "source": "Yahoo Finance (failed)"}


def yahoo_get_company_financials(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch company financials from Yahoo Finance (free).

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with revenue, total_debt, ebitda, cash, source, date.
    """
    if requests is None:
        return {"symbol": symbol, "error": "requests not installed", "source": "Yahoo Finance (failed)"}

    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "financialData,defaultKeyStatistics,incomeStatementHistory"}
    headers = {"User-Agent": SEC_USER_AGENT}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        result = data.get("quoteSummary", {}).get("result", [])
        if not result:
            return {"symbol": symbol, "error": "No data", "source": "Yahoo Finance (no data)"}
        
        financial = result[0].get("financialData", {})
        
        return {
            "symbol": symbol,
            "revenue": financial.get("totalRevenue", {}).get("raw"),
            "total_debt": financial.get("totalDebt", {}).get("raw"),
            "ebitda": financial.get("ebitda", {}).get("raw"),
            "cash": financial.get("totalCash", {}).get("raw"),
            "free_cash_flow": financial.get("freeCashflow", {}).get("raw"),
            "gross_profit": financial.get("grossProfits", {}).get("raw"),
            "source": f"Yahoo Finance (financials for {symbol})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "source": "Yahoo Finance (failed)"}


# ===== Financial Modeling Prep (Free Tier) =====

def fmp_get_company_profile(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch company profile from Financial Modeling Prep (free tier: 250 calls/day).

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with company info, industry, sector, description, source, date.

    Setup: Register for free API key at https://site.financialmodelingprep.com/developer/docs
    Env var: FMP_API_KEY
    """
    api_key = os.environ.get("FMP_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "symbol": symbol,
            "error": "FMP_API_KEY not set",
            "source": "Financial Modeling Prep (no API key; register at https://site.financialmodelingprep.com/developer/docs)",
        }

    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
    params = {"apikey": api_key}

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            return {"symbol": symbol, "error": "No data", "source": "FMP (no data)"}
        
        profile = data[0]
        return {
            "symbol": symbol,
            "company_name": profile.get("companyName"),
            "industry": profile.get("industry"),
            "sector": profile.get("sector"),
            "description": profile.get("description"),
            "ceo": profile.get("ceo"),
            "website": profile.get("website"),
            "market_cap": profile.get("mktCap"),
            "price": profile.get("price"),
            "beta": profile.get("beta"),
            "source": f"Financial Modeling Prep (profile for {symbol})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "source": "FMP (failed)"}


def fmp_get_financial_ratios(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch financial ratios from Financial Modeling Prep (free tier).

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with debt ratios, liquidity ratios, profitability ratios, source, date.
    """
    api_key = os.environ.get("FMP_API_KEY", "").strip()
    if not api_key or requests is None:
        return {"symbol": symbol, "error": "FMP_API_KEY not set", "source": "FMP (no API key)"}

    url = f"https://financialmodelingprep.com/api/v3/ratios/{symbol}"
    params = {"apikey": api_key, "limit": 1}

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            return {"symbol": symbol, "error": "No data", "source": "FMP (no data)"}
        
        ratios = data[0]
        return {
            "symbol": symbol,
            "date": ratios.get("date"),
            "current_ratio": ratios.get("currentRatio"),
            "quick_ratio": ratios.get("quickRatio"),
            "debt_equity_ratio": ratios.get("debtEquityRatio"),
            "debt_ratio": ratios.get("debtRatio"),
            "interest_coverage": ratios.get("interestCoverage"),
            "return_on_equity": ratios.get("returnOnEquity"),
            "return_on_assets": ratios.get("returnOnAssets"),
            "gross_profit_margin": ratios.get("grossProfitMargin"),
            "operating_profit_margin": ratios.get("operatingProfitMargin"),
            "net_profit_margin": ratios.get("netProfitMargin"),
            "source": f"Financial Modeling Prep (ratios for {symbol})",
            "date_fetched": _today_iso(),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "source": "FMP (failed)"}


# ===== Finnhub (Free Tier) =====

def finnhub_get_company_news(
    symbol: str,
    days: int = 7,
) -> list[dict[str, Any]]:
    """
    Fetch company news from Finnhub (free tier: 60 calls/minute).

    Args:
        symbol: Stock ticker.
        days: Number of days to look back.

    Returns:
        List of news articles with headline, summary, url, datetime, sentiment, source.

    Setup: Register for free API key at https://finnhub.io/register
    Env var: FINNHUB_API_KEY
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not api_key or requests is None:
        return []

    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d"),
        "token": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for article in data[:20]:  # Limit to 20 most recent
            results.append({
                "headline": article.get("headline"),
                "summary": article.get("summary"),
                "url": article.get("url"),
                "datetime": article.get("datetime"),
                "source_name": article.get("source"),
                "source": f"Finnhub (company news for {symbol})",
                "date": _today_iso(),
            })
        return results
    except Exception:
        return []


def finnhub_get_sentiment(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch news sentiment from Finnhub (free tier).

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with sentiment score, buzz, source, date.
    """
    api_key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not api_key or requests is None:
        return {"symbol": symbol, "sentiment": None, "source": "Finnhub (no API key)"}

    url = "https://finnhub.io/api/v1/news-sentiment"
    params = {"symbol": symbol, "token": api_key}

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "symbol": symbol,
            "sentiment_score": data.get("sentiment", {}).get("score"),
            "buzz_score": data.get("buzz", {}).get("articlesInLastWeek"),
            "positive_mentions": data.get("sentiment", {}).get("positive"),
            "negative_mentions": data.get("sentiment", {}).get("negative"),
            "source": f"Finnhub (sentiment for {symbol})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"symbol": symbol, "sentiment": None, "error": str(e), "source": "Finnhub (failed)"}


# ===== Polygon.io (Free Tier) =====

def polygon_get_stock_quote(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch stock quote from Polygon.io (free tier: 5 calls/minute).

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with price, volume, open, high, low, close, source, date.

    Setup: Register for free API key at https://polygon.io/
    Env var: POLYGON_API_KEY
    """
    api_key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not api_key or requests is None:
        return {"symbol": symbol, "price": None, "source": "Polygon.io (no API key)"}

    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
    params = {"apiKey": api_key}

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        results = data.get("results", [])
        if not results:
            return {"symbol": symbol, "price": None, "source": "Polygon.io (no data)"}
        
        quote = results[0]
        return {
            "symbol": symbol,
            "open": quote.get("o"),
            "high": quote.get("h"),
            "low": quote.get("l"),
            "close": quote.get("c"),
            "price": quote.get("c"),  # Alias for close
            "volume": quote.get("v"),
            "vwap": quote.get("vw"),
            "timestamp": quote.get("t"),
            "source": f"Polygon.io (quote for {symbol})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"symbol": symbol, "price": None, "error": str(e), "source": "Polygon.io (failed)"}


# ===== PACER (US Bankruptcy Courts - Free) =====

def pacer_search_bankruptcy_cases(
    company_name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Search for bankruptcy cases on PACER (Public Access to Court Electronic Records).

    Note: PACER requires account registration (free for limited use, $0.10/page after).
    This function provides stub interface; full implementation requires PACER credentials.

    Args:
        company_name: Company name to search.
        limit: Max number of cases to return.

    Returns:
        List of bankruptcy cases with case_number, district, filing_date, status, source.

    Setup: Register at https://pacer.uscourts.gov/
    Note: PACER API access is limited; consider using SEC EDGAR for public company bankruptcies.
    """
    # TODO: Implement PACER integration
    # PACER requires authentication and has usage fees ($0.10/page after cap)
    # For now, recommend using SEC EDGAR 8-K filings for public company bankruptcies
    
    _ = company_name, limit
    
    return [
        {
            "company": company_name,
            "case_number": None,
            "district": None,
            "filing_date": None,
            "status": None,
            "source": (
                "PACER search requires registration at https://pacer.uscourts.gov/. "
                "For public companies, use SEC EDGAR 8-K filings (Item 1.03) as free alternative."
            ),
            "date": _today_iso(),
        }
    ]


# ===== World Bank API (Free) =====

def worldbank_get_gdp_growth(
    country_code: str = "US",
    years: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch GDP growth rate from World Bank (free, no API key required).

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "CN").
        years: Number of years to fetch.

    Returns:
        List of GDP growth rates by year with value, year, country, source.

    API: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
    """
    if requests is None:
        return []

    # World Bank API: GDP growth (annual %)
    indicator = "NY.GDP.MKTP.KD.ZG"
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
    params = {"format": "json", "per_page": years}

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if len(data) < 2:
            return []
        
        results = []
        for entry in data[1]:  # First element is metadata, second is data
            if entry.get("value") is not None:
                results.append({
                    "country": entry.get("country", {}).get("value"),
                    "country_code": country_code,
                    "year": entry.get("date"),
                    "gdp_growth_pct": entry.get("value"),
                    "source": f"World Bank (GDP growth for {country_code})",
                    "date": _today_iso(),
                })
        return results
    except Exception:
        return []


# ===== Bureau of Labor Statistics (BLS) - Free =====

def bls_get_unemployment_rate(
) -> dict[str, Any]:
    """
    Fetch US unemployment rate from Bureau of Labor Statistics (free, no API key required).

    Returns:
        Dict with unemployment_rate, date, source.

    API: https://www.bls.gov/developers/
    Note: BLS offers free API but rate-limited. This uses public data endpoint.
    """
    if requests is None:
        return {"unemployment_rate": None, "source": "BLS (requests not installed)"}

    # BLS public data series: Unemployment Rate (seasonally adjusted)
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000"

    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        series_data = data.get("Results", {}).get("series", [])
        if not series_data:
            return {"unemployment_rate": None, "source": "BLS (no data)"}
        
        latest = series_data[0].get("data", [])[0]
        return {
            "unemployment_rate": float(latest.get("value")),
            "year": latest.get("year"),
            "period": latest.get("periodName"),
            "source": "Bureau of Labor Statistics (US unemployment rate)",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"unemployment_rate": None, "error": str(e), "source": "BLS (failed)"}


# ===== Smart Fallback Mechanism =====

def get_stock_quote_with_fallback(
    symbol: str,
) -> dict[str, Any]:
    """
    Get stock quote with intelligent fallback across multiple free sources.

    Tries in order:
    1. Yahoo Finance (free, no key)
    2. Alpha Vantage (free, 25/day with key)
    3. Polygon.io (free, 5/min with key)
    4. IEX Cloud (paid, with key)

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with price, volume, source, date (from first successful source).

    This ensures resilience: if one API is down or rate-limited, automatically falls back.
    """
    # Check cache first (5 minute TTL)
    cache_key = f"stock_quote:{symbol}"
    cached = _cache_get(cache_key, ttl_seconds=300)
    if cached:
        logger.debug(f"Cache hit for stock quote: {symbol}")
        return cached

    logger.info(f"Fetching stock quote for {symbol} (no cache)")
    
    sources = [
        ("Yahoo Finance", lambda: yahoo_get_stock_quote(symbol)),
        ("Alpha Vantage", lambda: alphavantage_get_stock_price(symbol)),
        ("Polygon.io", lambda: polygon_get_stock_quote(symbol)),
        ("IEX Cloud", lambda: iexcloud_get_stock_quote(symbol)),
    ]

    for source_name, fetch_func in sources:
        try:
            logger.debug(f"Trying {source_name} for {symbol}")
            result = fetch_func()
            if result.get("price") is not None:
                logger.info(f"✅ Successfully fetched {symbol} from {source_name}: ${result['price']}")
                result["fallback_note"] = f"Retrieved from {source_name}"
                _cache_set(cache_key, result)
                return result
            else:
                logger.warning(f"⚠️ {source_name} returned no price for {symbol}")
        except Exception as e:
            logger.warning(f"❌ {source_name} failed for {symbol}: {e}")
            continue

    # All sources failed
    logger.error(f"🚨 All sources failed for stock quote: {symbol}")
    return {
        "symbol": symbol,
        "price": None,
        "source": "All sources failed (Yahoo, Alpha Vantage, Polygon, IEX Cloud)",
        "date": _today_iso(),
    }


def get_company_financials_with_fallback(
    symbol: str,
    cik: str | None = None,
) -> dict[str, Any]:
    """
    Get company financials with intelligent fallback.

    Tries in order:
    1. SEC EDGAR (free, no key, most reliable for US public companies)
    2. Yahoo Finance (free, no key)
    3. IEX Cloud (paid, with key)
    4. Financial Modeling Prep (free, 250/day with key)

    Args:
        symbol: Stock ticker.
        cik: Optional CIK (for SEC EDGAR, more reliable if known).

    Returns:
        Dict with revenue, total_debt, ebitda, source, date.
    """
    # Check cache first (1 hour TTL for financials)
    cache_key = f"financials:{symbol}:{cik}"
    cached = _cache_get(cache_key, ttl_seconds=3600)
    if cached:
        return cached

    sources = []
    
    # If CIK is provided, try SEC EDGAR first (most reliable)
    if cik:
        sources.append(("SEC EDGAR", lambda: edgar_get_company_financials(cik)))
    
    sources.extend([
        ("Yahoo Finance", lambda: yahoo_get_company_financials(symbol)),
        ("IEX Cloud", lambda: iexcloud_get_company_financials(symbol)),
        ("FMP", lambda: fmp_get_company_profile(symbol)),
    ])

    for source_name, fetch_func in sources:
        try:
            result = fetch_func()
            # Check if we got meaningful data (at least revenue or debt)
            if result.get("revenue") is not None or result.get("total_debt") is not None:
                result["fallback_note"] = f"Retrieved from {source_name}"
                _cache_set(cache_key, result)
                return result
        except Exception:
            continue

    return {
        "symbol": symbol,
        "cik": cik,
        "revenue": None,
        "total_debt": None,
        "ebitda": None,
        "source": "All sources failed (SEC EDGAR, Yahoo, IEX Cloud, FMP)",
        "date": _today_iso(),
    }


# ===== OpenFIGI (Free) =====

def openfigi_lookup_security(
    identifier: str,
    id_type: str = "TICKER",
) -> dict[str, Any]:
    """
    Lookup security identifier using OpenFIGI (free, no API key required for basic use).

    Resolves ticker to FIGI, CUSIP, ISIN, etc.

    Args:
        identifier: Ticker, CUSIP, ISIN, or other identifier.
        id_type: Type of identifier ("TICKER", "ID_CUSIP", "ID_ISIN", etc.).

    Returns:
        Dict with figi, cusip, isin, ticker, name, security_type, source.

    API: https://www.openfigi.com/api
    """
    if requests is None:
        return {"identifier": identifier, "figi": None, "source": "OpenFIGI (requests not installed)"}

    url = "https://api.openfigi.com/v3/mapping"
    headers = {"Content-Type": "application/json"}
    payload = [{"idType": id_type, "idValue": identifier}]

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if not data or "error" in data[0]:
            return {"identifier": identifier, "figi": None, "source": "OpenFIGI (no match)"}
        
        match = data[0].get("data", [])[0]
        return {
            "identifier": identifier,
            "figi": match.get("figi"),
            "cusip": match.get("cusip"),
            "isin": match.get("isin"),
            "ticker": match.get("ticker"),
            "name": match.get("name"),
            "security_type": match.get("securityType"),
            "exchange_code": match.get("exchCode"),
            "source": f"OpenFIGI (lookup for {identifier})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {"identifier": identifier, "figi": None, "error": str(e), "source": "OpenFIGI (failed)"}


# ===== IEX Cloud (Commercial) =====

def iexcloud_get_stock_quote(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch stock quote from IEX Cloud (commercial, pay-as-you-go pricing).

    Args:
        symbol: Stock ticker (e.g. "AAPL").

    Returns:
        Dict with price, symbol, volume, market_cap, source, date.

    Setup: Register at https://iexcloud.io/ and get API token.
    Set IEXCLOUD_API_TOKEN environment variable.
    """
    api_token = os.environ.get("IEXCLOUD_API_TOKEN", "").strip()
    if not api_token or requests is None:
        return {
            "symbol": symbol,
            "price": None,
            "source": "IEX Cloud (no API token; register at https://iexcloud.io/)",
            "date": _today_iso(),
        }

    # IEX Cloud API v1 (stable endpoint)
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
    params = {"token": api_token}

    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "symbol": data.get("symbol", symbol),
            "price": data.get("latestPrice"),
            "volume": data.get("latestVolume"),
            "market_cap": data.get("marketCap"),
            "pe_ratio": data.get("peRatio"),
            "week_52_high": data.get("week52High"),
            "week_52_low": data.get("week52Low"),
            "ytd_change": data.get("ytdChange"),
            "source": f"IEX Cloud (quote for {symbol})",
            "date": _today_iso(),
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "price": None,
            "error": str(e),
            "source": "IEX Cloud (API call failed)",
            "date": _today_iso(),
        }


def iexcloud_get_company_financials(
    symbol: str,
) -> dict[str, Any]:
    """
    Fetch company financials from IEX Cloud (income statement, balance sheet).

    Args:
        symbol: Stock ticker.

    Returns:
        Dict with revenue, total_debt, ebitda, filing_date, source.
    """
    api_token = os.environ.get("IEXCLOUD_API_TOKEN", "").strip()
    if not api_token or requests is None:
        return {
            "symbol": symbol,
            "error": "IEX Cloud API token not set",
            "source": "IEX Cloud (failed)",
        }

    # Get income statement (for revenue, EBITDA)
    income_url = f"https://cloud.iexapis.com/stable/stock/{symbol}/income"
    balance_url = f"https://cloud.iexapis.com/stable/stock/{symbol}/balance-sheet"
    params = {"token": api_token, "last": 1}  # Get most recent filing

    revenue = None
    ebitda = None
    total_debt = None
    filing_date = None

    try:
        # Income statement
        resp = requests.get(income_url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        income_data = resp.json()
        
        if income_data and "income" in income_data:
            latest = income_data["income"][0]
            revenue = latest.get("totalRevenue")
            ebitda = latest.get("ebitda")
            filing_date = latest.get("fiscalDate")

        # Balance sheet
        resp = requests.get(balance_url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        balance_data = resp.json()
        
        if balance_data and "balancesheet" in balance_data:
            latest = balance_data["balancesheet"][0]
            total_debt = latest.get("totalDebt") or latest.get("longTermDebt")

    except Exception as e:
        return {
            "symbol": symbol,
            "error": str(e),
            "source": "IEX Cloud (API call failed)",
        }

    return {
        "symbol": symbol,
        "revenue": revenue,
        "total_debt": total_debt,
        "ebitda": ebitda,
        "filing_date": filing_date,
        "source": f"IEX Cloud (financials for {symbol})",
        "date": _today_iso(),
    }


# ===== CDS Spreads (Multiple Sources) =====

def get_cds_spread(
    ticker: str,
    maturity: str = "5Y",
) -> dict[str, Any]:
    """
    Fetch CDS (Credit Default Swap) spread for a company.

    CDS spreads indicate credit risk: higher spread = higher default probability.

    Args:
        ticker: Company ticker or name.
        maturity: CDS maturity ("1Y", "5Y", "10Y").

    Returns:
        Dict with cds_spread_bps, ticker, maturity, source, date.

    Data Sources (in order of preference):
    1. Bloomberg (CDSW function) - requires Terminal or API
    2. Markit/IHS Markit (now part of S&P) - requires subscription
    3. ICE Data Services - requires subscription
    4. Stub when no source available

    Implementation: Currently returns stub; requires commercial data subscription.
    """
    # TODO: Implement Bloomberg, Markit, or ICE Data Services integration
    # Bloomberg Terminal: use blpapi to query CDS spreads (CDSW function)
    # Markit: https://ihsmarkit.com/products/markit-cds.html
    # ICE: https://www.ice.com/

    _ = ticker, maturity

    return {
        "ticker": ticker,
        "cds_spread_bps": None,
        "maturity": maturity,
        "source": (
            "CDS spreads require Bloomberg Terminal (blpapi), Markit/IHS Markit subscription, "
            "or ICE Data Services. Not available via free APIs."
        ),
        "date": _today_iso(),
    }


def calculate_credit_spread(
    bond_yield: float,
    treasury_maturity: str = "10Y",
) -> dict[str, Any]:
    """
    Calculate credit spread (OAS approximation) for a bond over Treasury.

    Args:
        bond_yield: Yield on corporate/distressed bond (%).
        treasury_maturity: Comparable Treasury maturity.

    Returns:
        Dict with spread_bps, bond_yield, treasury_yield, source, date.
    """
    # Use FRED Treasury yield (primary) or Alpha Vantage (fallback)
    treasury = fred_get_treasury_yield(treasury_maturity)
    treasury_yield = treasury.get("yield_pct")

    if treasury_yield is None:
        # Fallback to Alpha Vantage
        maturity_map = {"2Y": "2year", "5Y": "5year", "10Y": "10year", "30Y": "30year"}
        av_maturity = maturity_map.get(treasury_maturity, "10year")
        treasury = alphavantage_get_bond_yield(av_maturity)
        treasury_yield = treasury.get("yield_pct")

    if treasury_yield is None:
        return {
            "spread_bps": None,
            "bond_yield": bond_yield,
            "treasury_yield": None,
            "source": "Credit spread calculation failed (no Treasury yield available)",
        }

    spread_bps = (bond_yield - treasury_yield) * 100
    return {
        "spread_bps": round(spread_bps, 1),
        "bond_yield": bond_yield,
        "treasury_yield": treasury_yield,
        "maturity": treasury_maturity,
        "source": f"Credit spread over {treasury_maturity} Treasury (calculated)",
        "date": _today_iso(),
    }


# ===== 9fin (Commercial) =====

def ninefin_get_recovery_rates_live(
    industry: str | None = None,
    tranche_type: str | None = None,
    year: int | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch live recovery rates from 9fin API (when credentials available).

    Requires: NINEFIN_API_KEY environment variable.

    Args:
        industry: Industry filter (e.g. "Retail", "Energy").
        tranche_type: Debt type (e.g. "1st Lien", "Unsecured", "2nd Lien").
        year: Year filter for recovery data.

    Returns:
        List of recovery rate entries with source and date.

    Implementation: When 9fin API endpoint and schema are available, call API here.
    For now, returns empty list when NINEFIN_API_KEY is not set (caller falls back to stub).
    """
    api_key = os.environ.get("NINEFIN_API_KEY", "").strip()
    if not api_key or requests is None:
        return []

    # TODO: 9fin API endpoint (requires commercial subscription)
    # Example (hypothetical):
    # url = "https://api.9fin.com/v1/recovery-rates"
    # headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    # params = {"industry": industry, "tranche_type": tranche_type, "year": year}
    # resp = requests.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
    # data = resp.json()
    # return data.get("results", [])

    # For now, return empty (benchmarker will use stub)
    _ = industry, tranche_type, year
    return []


def ninefin_get_precedent_transactions(
    industry: str | None = None,
    geography: str | None = None,
    year: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch precedent restructuring transactions from 9fin database.

    9fin provides comprehensive restructuring deal data including:
    - Pre/post-restructuring capital structure
    - Recovery rates by tranche
    - Exit multiples (EV/EBITDA)
    - Timeline and key milestones

    Args:
        industry: Industry filter.
        geography: Geography filter.
        year: Year filter for transactions.
        limit: Max number of transactions to return.

    Returns:
        List of precedent transactions with company, date, structure, recovery_rates, source.

    Setup: Requires NINEFIN_API_KEY from 9fin subscription.
    """
    api_key = os.environ.get("NINEFIN_API_KEY", "").strip()
    if not api_key or requests is None:
        return []

    # TODO: Implement 9fin precedent transactions API
    # url = "https://api.9fin.com/v1/precedents"
    # headers = {"Authorization": f"Bearer {api_key}"}
    # params = {"industry": industry, "geography": geography, "year": year, "limit": limit}

    _ = industry, geography, year, limit
    return []


# ===== Reorg Research (Commercial) =====

def reorg_get_distressed_companies(
    industry: str | None = None,
    geography: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch list of distressed companies from Reorg Research.

    Reorg provides real-time restructuring intelligence:
    - Companies in distress or bankruptcy
    - Proposed restructuring plans
    - Creditor committee information
    - Court filings and updates

    Args:
        industry: Industry filter.
        geography: Geography filter.
        limit: Max number of companies to return.

    Returns:
        List of distressed companies with name, status, restructuring_plan, source, date.

    Setup: Requires REORG_API_KEY from Reorg Research subscription.
    API: https://reorg.com/
    """
    api_key = os.environ.get("REORG_API_KEY", "").strip()
    if not api_key or requests is None:
        return []

    # TODO: Implement Reorg Research API
    # Reorg typically provides data via web platform; API access may vary
    # Contact Reorg for API documentation

    _ = industry, geography, limit
    return []


def reorg_get_bankruptcy_filings(
    company_name: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch recent Chapter 11 bankruptcy filings from Reorg Research.

    Args:
        company_name: Optional company name filter.
        limit: Max number of filings to return.

    Returns:
        List of bankruptcy filings with company, filing_date, case_number, district, source.
    """
    api_key = os.environ.get("REORG_API_KEY", "").strip()
    if not api_key or requests is None:
        return []

    # TODO: Implement Reorg bankruptcy filings API
    _ = company_name, limit
    return []


# ===== Debtwire (Commercial) =====

def debtwire_get_distressed_deals(
    industry: str | None = None,
    deal_type: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch distressed debt deals from Debtwire.

    Debtwire provides:
    - Distressed M&A transactions
    - Out-of-court restructurings
    - Debt exchanges and amendments
    - Market intelligence and news

    Args:
        industry: Industry filter.
        deal_type: Deal type ("M&A", "Restructuring", "Debt Exchange", etc.).
        limit: Max number of deals to return.

    Returns:
        List of deals with company, deal_type, date, value, terms, source.

    Setup: Requires DEBTWIRE_API_KEY from Debtwire subscription.
    API: https://www.debtwire.com/
    """
    api_key = os.environ.get("DEBTWIRE_API_KEY", "").strip()
    if not api_key or requests is None:
        return []

    # TODO: Implement Debtwire API
    # Debtwire data is typically accessed via web platform
    # API access requires enterprise subscription; contact Debtwire for details

    _ = industry, deal_type, limit
    return []


# ===== Internal Precedent Database (Local Storage) =====

def build_internal_precedent_database(
    data_sources: list[str] = ["edgar", "ninefin", "reorg", "debtwire"],
) -> dict[str, Any]:
    """
    Build internal precedent transaction database from multiple sources.

    Aggregates data from:
    - SEC EDGAR (8-K distress events, Chapter 11 filings)
    - 9fin (recovery rates, exit multiples)
    - Reorg Research (restructuring intelligence)
    - Debtwire (distressed deals)
    - Manual entries (user-provided precedents)

    Database schema (SQLite or JSON file):
    - company_name, industry, geography
    - restructuring_date, exit_date
    - pre_restructuring_debt, post_restructuring_debt
    - recovery_rates (dict by tranche)
    - exit_multiple, exit_enterprise_value
    - source, date_added

    Args:
        data_sources: List of sources to pull from.

    Returns:
        Dict with status, num_records, sources_used, database_path.

    Implementation: Create SQLite database in signal_triage/data/precedents.db
    """
    # TODO: Implement database builder
    # 1. Create SQLite schema
    # 2. Fetch data from each source
    # 3. Normalize and insert into database
    # 4. Add deduplication logic
    # 5. Provide query interface for benchmarker.py

    _ = data_sources

    return {
        "status": "not_implemented",
        "num_records": 0,
        "sources_used": [],
        "database_path": None,
        "source": "Internal precedent database builder (implementation TODO)",
        "date": _today_iso(),
    }


def query_internal_precedent_database(
    industry: str | None = None,
    tranche_type: str | None = None,
    year_range: tuple[int, int] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Query internal precedent database for matching transactions.

    Args:
        industry: Industry filter.
        tranche_type: Debt tranche type.
        year_range: (start_year, end_year) tuple.
        limit: Max results.

    Returns:
        List of precedent transactions from internal database.
    """
    # TODO: Implement query interface
    # Connect to SQLite database and execute query with filters

    _ = industry, tranche_type, year_range, limit

    return []


# ===== Bloomberg (Commercial) =====

def bloomberg_get_peer_multiples(
    ticker: str,
    industry: str | None = None,
) -> dict[str, Any]:
    """
    Fetch peer EV/EBITDA multiples from Bloomberg (when Bloomberg Terminal or API available).

    Requires: Bloomberg Terminal or BLOOMBERG_API_KEY.

    Args:
        ticker: Target company ticker.
        industry: Industry for peer selection.

    Returns:
        Dict with peers (list), median_ev_ebitda, source, date.

    Implementation: When Bloomberg API access is available, call API here.
    Returns stub when no credentials.
    """
    # Bloomberg Terminal: use blpapi (Python package for Terminal)
    # Bloomberg API: use REST API with credentials

    # Check for Bloomberg Terminal (blpapi)
    try:
        import blpapi  # type: ignore[import]
        # TODO: implement Bloomberg Terminal blpapi call to get peer multiples
        # Example: HistoricalDataRequest for "EV_TO_T12M_EBITDA" field
        _ = blpapi, ticker, industry
    except ImportError:
        pass

    # Check for Bloomberg API key (REST API)
    api_key = os.environ.get("BLOOMBERG_API_KEY", "").strip()
    if api_key and requests:
        # TODO: implement Bloomberg REST API call when available
        _ = api_key, ticker, industry
        pass

    # Stub
    return {
        "ticker": ticker,
        "peers": [],
        "median_ev_ebitda": None,
        "source": "Bloomberg (no Terminal or API access; install blpapi or set BLOOMBERG_API_KEY)",
        "date": _today_iso(),
    }


# ===== Credit Ratings (S&P, Moody's, Fitch) =====

def get_sp_credit_rating(
    ticker: str,
) -> dict[str, Any]:
    """
    Fetch S&P credit rating for a company.

    Ratings scale: AAA (highest) → D (default)
    Investment grade: BBB- and above
    High yield (junk): BB+ and below

    Args:
        ticker: Company ticker or CUSIP.

    Returns:
        Dict with rating, outlook, watch_status, rating_date, source.

    Data Source: S&P Capital IQ (requires subscription)
    API: https://www.spglobal.com/ratings/en/

    Setup: Requires S&P_CAPITAL_IQ_API_KEY environment variable.
    """
    api_key = os.environ.get("SP_CAPITAL_IQ_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "ticker": ticker,
            "rating": None,
            "outlook": None,
            "watch_status": None,
            "source": "S&P (no API key; requires S&P Capital IQ subscription)",
            "date": _today_iso(),
        }

    # TODO: Implement S&P Capital IQ API call when subscription available
    # Example endpoint (hypothetical): https://api.capitaliq.com/v1/ratings
    # Headers: {"Authorization": f"Bearer {api_key}"}
    # Params: {"ticker": ticker}

    _ = api_key, ticker

    return {
        "ticker": ticker,
        "rating": None,
        "outlook": None,
        "watch_status": None,
        "source": "S&P Capital IQ (implementation TODO; subscription required)",
        "date": _today_iso(),
    }


def get_moodys_credit_rating(
    ticker: str,
) -> dict[str, Any]:
    """
    Fetch Moody's credit rating for a company.

    Ratings scale: Aaa (highest) → C (default)
    Investment grade: Baa3 and above
    High yield (speculative): Ba1 and below

    Args:
        ticker: Company ticker or CUSIP.

    Returns:
        Dict with rating, outlook, watch_status, rating_date, source.

    Data Source: Moody's Analytics (requires subscription)
    API: https://www.moodysanalytics.com/

    Setup: Requires MOODYS_API_KEY environment variable.
    """
    api_key = os.environ.get("MOODYS_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "ticker": ticker,
            "rating": None,
            "outlook": None,
            "watch_status": None,
            "source": "Moody's (no API key; requires Moody's Analytics subscription)",
            "date": _today_iso(),
        }

    # TODO: Implement Moody's Analytics API call when subscription available
    _ = api_key, ticker

    return {
        "ticker": ticker,
        "rating": None,
        "outlook": None,
        "watch_status": None,
        "source": "Moody's Analytics (implementation TODO; subscription required)",
        "date": _today_iso(),
    }


def get_fitch_credit_rating(
    ticker: str,
) -> dict[str, Any]:
    """
    Fetch Fitch credit rating for a company.

    Ratings scale: AAA (highest) → D (default)
    Investment grade: BBB- and above
    High yield: BB+ and below

    Args:
        ticker: Company ticker or CUSIP.

    Returns:
        Dict with rating, outlook, watch_status, rating_date, source.

    Data Source: Fitch Solutions (requires subscription)
    API: https://www.fitchratings.com/

    Setup: Requires FITCH_API_KEY environment variable.
    """
    api_key = os.environ.get("FITCH_API_KEY", "").strip()
    if not api_key or requests is None:
        return {
            "ticker": ticker,
            "rating": None,
            "outlook": None,
            "watch_status": None,
            "source": "Fitch (no API key; requires Fitch Solutions subscription)",
            "date": _today_iso(),
        }

    # TODO: Implement Fitch Solutions API call when subscription available
    _ = api_key, ticker

    return {
        "ticker": ticker,
        "rating": None,
        "outlook": None,
        "watch_status": None,
        "source": "Fitch Solutions (implementation TODO; subscription required)",
        "date": _today_iso(),
    }


def get_aggregate_credit_ratings(
    ticker: str,
) -> dict[str, Any]:
    """
    Fetch credit ratings from all three major agencies (S&P, Moody's, Fitch).

    Args:
        ticker: Company ticker or CUSIP.

    Returns:
        Dict with sp_rating, moodys_rating, fitch_rating, consensus_level, source.

    Consensus level: "Investment Grade", "High Yield", "Distressed", or "Mixed".
    """
    sp = get_sp_credit_rating(ticker)
    moodys = get_moodys_credit_rating(ticker)
    fitch = get_fitch_credit_rating(ticker)

    # Determine consensus level (simplified logic)
    ratings = [
        sp.get("rating"),
        moodys.get("rating"),
        fitch.get("rating"),
    ]
    ratings = [r for r in ratings if r]  # Filter out None

    consensus = "N/A"
    if ratings:
        # Simplified: check if any rating contains "CCC", "D", etc. (distressed)
        distressed_indicators = ["CCC", "CC", "C", "D", "Ca", "Caa"]
        if any(ind in str(r) for r in ratings for ind in distressed_indicators):
            consensus = "Distressed"
        # Check for investment grade (BBB-/Baa3 and above)
        elif any("AAA" in str(r) or "AA" in str(r) or "A" in str(r) or "BBB" in str(r) or "Baa" in str(r) for r in ratings):
            consensus = "Investment Grade"
        else:
            consensus = "High Yield"

    return {
        "ticker": ticker,
        "sp_rating": sp.get("rating"),
        "sp_outlook": sp.get("outlook"),
        "moodys_rating": moodys.get("rating"),
        "moodys_outlook": moodys.get("outlook"),
        "fitch_rating": fitch.get("rating"),
        "fitch_outlook": fitch.get("outlook"),
        "consensus_level": consensus,
        "source": "Aggregate from S&P, Moody's, Fitch",
        "date": _today_iso(),
    }


def detect_rating_changes(
    ticker: str,
    lookback_days: int = 90,
) -> list[dict[str, Any]]:
    """
    Detect recent rating changes, outlook changes, or watch list additions.

    Early warning indicators:
    - Downgrade (e.g., BBB → BB+): increased default risk
    - Outlook change (Stable → Negative): potential future downgrade
    - Watch list (Creditwatch Negative, Under Review): imminent rating action

    Args:
        ticker: Company ticker.
        lookback_days: How far back to check for rating changes.

    Returns:
        List of rating events with date, agency, action, old_rating, new_rating, source.

    Implementation: Requires historical ratings data from S&P/Moody's/Fitch APIs.
    Currently returns stub.
    """
    _ = ticker, lookback_days

    return [
        {
            "ticker": ticker,
            "date": None,
            "agency": None,
            "action": None,
            "old_rating": None,
            "new_rating": None,
            "source": "Rating change detection requires S&P/Moody's/Fitch API subscriptions (implementation TODO)",
        }
    ]


def get_industry_sector_benchmarks(
    industry: str,
) -> dict[str, Any]:
    """
    Get industry-level credit metrics and benchmarks.

    Useful for peer comparison and relative credit quality assessment.

    Args:
        industry: Industry name or GICS code (e.g., "Retail", "Energy").

    Returns:
        Dict with median_rating, default_rate, recovery_rate, sector_outlook, source.

    Data Sources:
    - S&P Industry Surveys
    - Moody's Industry Reports
    - Fitch Sector Reports

    Implementation: Requires agency API subscriptions; currently returns stub.
    """
    _ = industry

    return {
        "industry": industry,
        "median_rating": None,
        "default_rate": None,
        "recovery_rate": None,
        "sector_outlook": None,
        "source": "Industry benchmarks require S&P/Moody's/Fitch sector data (implementation TODO)",
        "date": _today_iso(),
    }


# ===== API Configuration =====

def get_available_apis() -> dict[str, bool]:
    """
    Check which market data APIs are available based on env vars and installed packages.

    Returns:
        Dict with {api_name: is_available}.
    """
    apis = {
        # Free APIs (No API Key Required)
        "sec_edgar": requests is not None,
        "yahoo_finance": requests is not None,
        "worldbank": requests is not None,
        "bls": requests is not None,
        "openfigi": requests is not None,
        
        # Free APIs (API Key Required)
        "fred": bool(os.environ.get("FRED_API_KEY", "").strip()) and requests is not None,
        "alphavantage": bool(os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()) and requests is not None,
        "fmp": bool(os.environ.get("FMP_API_KEY", "").strip()) and requests is not None,
        "finnhub": bool(os.environ.get("FINNHUB_API_KEY", "").strip()) and requests is not None,
        "polygon": bool(os.environ.get("POLYGON_API_KEY", "").strip()) and requests is not None,
        
        # Commercial - Market Data
        "iexcloud": bool(os.environ.get("IEXCLOUD_API_TOKEN", "").strip()) and requests is not None,
        "bloomberg_terminal": False,
        "bloomberg_api": bool(os.environ.get("BLOOMBERG_API_KEY", "").strip()) and requests is not None,
        
        # Commercial - Restructuring Intelligence
        "ninefin": bool(os.environ.get("NINEFIN_API_KEY", "").strip()) and requests is not None,
        "reorg": bool(os.environ.get("REORG_API_KEY", "").strip()) and requests is not None,
        "debtwire": bool(os.environ.get("DEBTWIRE_API_KEY", "").strip()) and requests is not None,
        
        # Commercial - Credit Ratings
        "sp_capital_iq": bool(os.environ.get("SP_CAPITAL_IQ_API_KEY", "").strip()) and requests is not None,
        "moodys": bool(os.environ.get("MOODYS_API_KEY", "").strip()) and requests is not None,
        "fitch": bool(os.environ.get("FITCH_API_KEY", "").strip()) and requests is not None,
    }

    # Check for Bloomberg Terminal (blpapi package)
    try:
        import blpapi  # type: ignore[import]
        apis["bloomberg_terminal"] = True
        _ = blpapi
    except ImportError:
        pass

    return apis


def check_api_health() -> dict[str, dict[str, Any]]:
    """
    Check health/availability of all APIs by making test calls.

    Returns:
        Dict with {api_name: {available: bool, latency_ms: float, error: str}}.

    Warning: This makes actual API calls and counts against rate limits.
    Use sparingly (e.g., on startup or diagnostics).
    """
    import time
    
    health = {}
    
    # Test SEC EDGAR (free, no key)
    try:
        start = time.time()
        edgar_get_company_financials("0001652044")  # Sonder
        latency = (time.time() - start) * 1000
        health["sec_edgar"] = {"available": True, "latency_ms": round(latency, 2), "error": None}
    except Exception as e:
        health["sec_edgar"] = {"available": False, "latency_ms": None, "error": str(e)}
    
    # Test Yahoo Finance (free, no key)
    try:
        start = time.time()
        result = yahoo_get_stock_quote("AAPL")
        latency = (time.time() - start) * 1000
        available = result.get("price") is not None
        health["yahoo_finance"] = {
            "available": available,
            "latency_ms": round(latency, 2),
            "error": None if available else "No price data"
        }
    except Exception as e:
        health["yahoo_finance"] = {"available": False, "latency_ms": None, "error": str(e)}
    
    # Test FRED (if key available)
    if os.environ.get("FRED_API_KEY", "").strip():
        try:
            start = time.time()
            result = fred_get_treasury_yield("10Y")
            latency = (time.time() - start) * 1000
            available = result.get("yield_pct") is not None
            health["fred"] = {
                "available": available,
                "latency_ms": round(latency, 2),
                "error": None if available else "No yield data"
            }
        except Exception as e:
            health["fred"] = {"available": False, "latency_ms": None, "error": str(e)}
    
    # Add warnings for unofficial APIs
    health["_warnings"] = {
        "yahoo_finance": "Unofficial API - may break without notice. Use as fallback only.",
        "rate_limits": {
            "alphavantage": "25 calls/day (free tier)",
            "polygon": "5 calls/minute (free tier)",
            "fmp": "250 calls/day (free tier)",
            "finnhub": "60 calls/minute (free tier)",
        }
    }
    
    return health


def get_recommended_setup() -> str:
    """
    Return setup instructions for live market data based on what's available.

    Returns:
        String with setup instructions and recommendations.
    """
    apis = get_available_apis()

    if not requests:
        return "Install requests: pip install requests (required for all market data APIs)."

    instructions = ["=== MARKET DATA API SETUP STATUS ===\n"]

    # Free APIs (No API Key Required)
    instructions.append("--- FREE APIs (No API Key Required) ---")
    if apis["sec_edgar"]:
        instructions.append("✅ SEC EDGAR: Available (10-K/10-Q/8-K filings, company financials, distress events)")
    else:
        instructions.append("❌ SEC EDGAR: Install requests (pip install requests)")

    if apis["yahoo_finance"]:
        instructions.append("✅ Yahoo Finance: Available (stock quotes, company financials)")
    else:
        instructions.append("❌ Yahoo Finance: Install requests (pip install requests)")

    if apis["worldbank"]:
        instructions.append("✅ World Bank: Available (GDP growth, economic indicators)")
    else:
        instructions.append("❌ World Bank: Install requests (pip install requests)")

    if apis["bls"]:
        instructions.append("✅ BLS: Available (US unemployment rate, labor statistics)")
    else:
        instructions.append("❌ BLS: Install requests (pip install requests)")

    if apis["openfigi"]:
        instructions.append("✅ OpenFIGI: Available (security identifier lookup: FIGI/CUSIP/ISIN)")
    else:
        instructions.append("❌ OpenFIGI: Install requests (pip install requests)")

    # Free APIs (API Key Required)
    instructions.append("\n--- FREE APIs (API Key Required) ---")
    if apis["fred"]:
        instructions.append("✅ FRED: Available (Treasury yields, macro data)")
    else:
        instructions.append(
            "⚠️ FRED: Register for free API key at https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "   Set FRED_API_KEY environment variable"
        )

    if apis["alphavantage"]:
        instructions.append("✅ Alpha Vantage: Available (stock prices, bond yields)")
    else:
        instructions.append(
            "⚠️ Alpha Vantage: Register for free API key at https://www.alphavantage.co/support/#api-key\n"
            "   Set ALPHAVANTAGE_API_KEY environment variable (25 calls/day free)"
        )

    if apis["fmp"]:
        instructions.append("✅ Financial Modeling Prep: Available (company profiles, financial ratios)")
    else:
        instructions.append(
            "⚠️ Financial Modeling Prep: Register for free API key at https://site.financialmodelingprep.com/developer/docs\n"
            "   Set FMP_API_KEY environment variable (250 calls/day free)"
        )

    if apis["finnhub"]:
        instructions.append("✅ Finnhub: Available (company news, sentiment analysis)")
    else:
        instructions.append(
            "⚠️ Finnhub: Register for free API key at https://finnhub.io/register\n"
            "   Set FINNHUB_API_KEY environment variable (60 calls/minute free)"
        )

    if apis["polygon"]:
        instructions.append("✅ Polygon.io: Available (stock quotes, aggregates)")
    else:
        instructions.append(
            "⚠️ Polygon.io: Register for free API key at https://polygon.io/\n"
            "   Set POLYGON_API_KEY environment variable (5 calls/minute free)"
        )

    # Commercial - Market Data
    instructions.append("\n--- COMMERCIAL APIs: Market Data ---")
    if apis["iexcloud"]:
        instructions.append("✅ IEX Cloud: Available (stock quotes, company financials)")
    else:
        instructions.append(
            "⚠️ IEX Cloud: Register at https://iexcloud.io/ (pay-as-you-go pricing)\n"
            "   Set IEXCLOUD_API_TOKEN environment variable"
        )

    if apis["bloomberg_terminal"]:
        instructions.append("✅ Bloomberg Terminal: Available (peer multiples, CDS spreads)")
    elif apis["bloomberg_api"]:
        instructions.append("✅ Bloomberg API: API key detected (peer multiples, CDS spreads)")
    else:
        instructions.append(
            "⚠️ Bloomberg: Requires Bloomberg Terminal (install blpapi) or API access\n"
            "   Set BLOOMBERG_API_KEY environment variable if using API"
        )

    # Commercial - Restructuring Intelligence
    instructions.append("\n--- COMMERCIAL APIs: Restructuring Intelligence ---")
    if apis["ninefin"]:
        instructions.append("✅ 9fin: Available (recovery rates, exit multiples, precedent transactions)")
    else:
        instructions.append(
            "⚠️ 9fin: Requires commercial subscription (https://www.9fin.com/)\n"
            "   Set NINEFIN_API_KEY environment variable"
        )

    if apis["reorg"]:
        instructions.append("✅ Reorg Research: Available (distressed companies, bankruptcy filings)")
    else:
        instructions.append(
            "⚠️ Reorg Research: Requires subscription (https://reorg.com/)\n"
            "   Set REORG_API_KEY environment variable"
        )

    if apis["debtwire"]:
        instructions.append("✅ Debtwire: Available (distressed M&A, debt exchanges)")
    else:
        instructions.append(
            "⚠️ Debtwire: Requires enterprise subscription (https://www.debtwire.com/)\n"
            "   Set DEBTWIRE_API_KEY environment variable"
        )

    # Commercial - Credit Ratings
    instructions.append("\n--- COMMERCIAL APIs: Credit Ratings ---")
    if apis["sp_capital_iq"]:
        instructions.append("✅ S&P Capital IQ: Available (credit ratings, industry benchmarks)")
    else:
        instructions.append(
            "⚠️ S&P Capital IQ: Requires subscription (https://www.spglobal.com/marketintelligence/)\n"
            "   Set SP_CAPITAL_IQ_API_KEY environment variable"
        )

    if apis["moodys"]:
        instructions.append("✅ Moody's Analytics: Available (credit ratings, default rates)")
    else:
        instructions.append(
            "⚠️ Moody's Analytics: Requires subscription (https://www.moodysanalytics.com/)\n"
            "   Set MOODYS_API_KEY environment variable"
        )

    if apis["fitch"]:
        instructions.append("✅ Fitch Solutions: Available (credit ratings, sector reports)")
    else:
        instructions.append(
            "⚠️ Fitch Solutions: Requires subscription (https://www.fitchratings.com/)\n"
            "   Set FITCH_API_KEY environment variable"
        )

    # Summary
    available_count = sum(apis.values())
    total_count = len(apis)
    instructions.append(f"\n=== SUMMARY: {available_count}/{total_count} APIs Available ===")
    
    # Count free APIs (no key required)
    free_no_key = sum([
        apis["sec_edgar"], 
        apis["yahoo_finance"], 
        apis["worldbank"], 
        apis["bls"], 
        apis["openfigi"]
    ])
    
    # Count free APIs (key required)
    free_with_key = sum([
        apis["fred"], 
        apis["alphavantage"], 
        apis["fmp"], 
        apis["finnhub"], 
        apis["polygon"]
    ])
    
    instructions.append(f"\n📊 Free APIs: {free_no_key}/5 (no key) + {free_with_key}/5 (key required) = {free_no_key + free_with_key}/10 total")
    
    if free_no_key >= 3:
        instructions.append("✅ Basic setup complete (SEC EDGAR, Yahoo Finance, World Bank, BLS, OpenFIGI)")
        instructions.append("   You can use live data for company financials, stock prices, and economic indicators")
    else:
        instructions.append("❌ Install requests (pip install requests) to enable all free APIs")
    
    if free_with_key >= 2:
        instructions.append("✅ Enhanced setup complete (FRED + Alpha Vantage/FMP/Finnhub/Polygon)")
        instructions.append("   You have Treasury yields, sentiment analysis, and news coverage")
    else:
        instructions.append("⚠️ Recommended: Register for FRED + FMP (both free) for comprehensive market data")

    return "\n".join(instructions)

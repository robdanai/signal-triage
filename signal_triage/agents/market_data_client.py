"""
Market data API clients for the Benchmarker agent (Legacy Compatibility Layer).

This module provides backward-compatible functions that delegate to the new
production-grade API clients in signal_triage.api package.

For new code, import directly from signal_triage.api:
    from signal_triage.api import SECEdgarClient, MarketPricingClient

Provides live data with citation (source, date) on every datum.
- SEC EDGAR: recent 8-K filings for comparables (no API key required; User-Agent required).
- 9fin / other: stub interface for recovery benchmarks and exit multiples (env API key when available).
"""

from __future__ import annotations

import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# Import new production-grade clients
try:
    from signal_triage.api import SECEdgarClient, MarketPricingClient
    _NEW_CLIENTS_AVAILABLE = True
except ImportError:
    _NEW_CLIENTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# SEC requires a descriptive User-Agent with contact info
# Set SEC_USER_AGENT environment variable with your email
# See: https://www.sec.gov/os/webmaster-faq
SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "SignalTriage/1.0 (+https://github.com/yourusername/Signal-Triage; sample@example.com)"
)
DEFAULT_TIMEOUT = 30


def _citation(datum: dict[str, Any], source_name: str, date_iso: str) -> dict[str, Any]:
    """Add citation (source, date) to a datum. Mutates and returns datum."""
    datum["source"] = f"Source: {source_name}."
    datum["date"] = date_iso
    return datum


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# --- SEC EDGAR ---


def _parse_edgar_atom_feed(xml_text: str) -> list[dict[str, Any]]:
    """
    Parse SEC EDGAR browse-edgar Atom feed into list of filing entries.

    Each entry has: name (company), form_type, filing_date, accession (if in link), cik.
    """
    out: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out

    # Handle default ns
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

    # Entries: <entry> with <title>, <updated>, <link>, etc.
    for entry in find_all(root, "entry"):
        title_el = find_one(entry, "title")
        updated_el = find_one(entry, "updated")
        link_el = find_one(entry, "link")
        title = text(title_el)
        updated = text(updated_el)
        # Title often looks like "8-K - Company Name (0001234567)" or "Company Name - 8-K"
        name = title
        if " - " in title:
            parts = title.split(" - ", 1)
            if len(parts) == 2:
                # Prefer company name (part that doesn't start with form type)
                if parts[0].strip().upper().startswith("8-K"):
                    name = parts[1].strip()
                else:
                    name = parts[0].strip()
        # Strip (CIK) suffix
        cik_match = re.search(r"\s*\((\d+)\)\s*$", name)
        cik = cik_match.group(1) if cik_match else ""
        if cik:
            name = name[: cik_match.start()].strip()
        # Filing date from updated (ISO format)
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


def edgar_get_recent_8k_comparables(
    *,
    limit: int = 10,
    industry: str | None = None,
    geography: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch recent 8-K filings from SEC EDGAR Atom feed and return as comparables.

    Each item has: name, industry, geography, restructuring_date, source, date.
    industry/geography are passed through (EDGAR feed does not filter by them).
    
    NOTE: This function now delegates to the production-grade SECEdgarClient
    with rate limiting, caching, and error handling.
    """
    if _NEW_CLIENTS_AVAILABLE:
        try:
            client = SECEdgarClient()
            return client.get_recent_8k_comparables(
                limit=limit,
                industry=industry,
                geography=geography
            )
        except Exception as e:
            logger.warning(f"Production client failed, falling back to legacy: {e}")
    
    # Legacy fallback (no rate limiting, caching, or circuit breaker)
    if requests is None:
        raise ImportError(
            "Live EDGAR market data requires 'requests'. Install with: pip install requests"
        )
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        "?action=getcurrent&type=8-K&company=&dateb=&owner=include"
        f"&start=0&count={max(limit, 40)}&output=atom"
    )
    headers = {"User-Agent": SEC_USER_AGENT, "Accept": "application/atom+xml"}
    resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers=headers)
    resp.raise_for_status()
    entries = _parse_edgar_atom_feed(resp.text)[:limit]
    fetched_date = _today_iso()
    result: list[dict[str, Any]] = []
    for e in entries:
        datum = {
            "name": e["name"],
            "industry": industry or "N/A",
            "geography": geography or "US",
            "restructuring_date": e["filing_date"],
        }
        _citation(datum, "SEC EDGAR (recent 8-K filings)", fetched_date)
        result.append(datum)
    return result


# --- 9fin / other (stub: env API key when available) ---


def ninefin_get_recovery_benchmarks(
    tranche_type: str | None = None,
    industry: str | None = None,
    year: int | None = None,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch recovery benchmarks from 9fin (or other provider) when API key is set.

    Returns empty list when NINEFIN_API_KEY is not set; otherwise would call live API.
    Every entry includes source and date when data is returned.
    """
    api_key = os.environ.get("NINEFIN_API_KEY", "").strip()
    if not api_key:
        return []
    # TODO: implement live 9fin API call when endpoint and schema are available.
    # For now, return empty so benchmarker falls back to stub.
    _ = tranche_type, industry, year, limit, api_key
    return []


def ninefin_get_exit_multiples(
    industry: str | None = None,
    geography: str | None = None,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch exit multiples from 9fin (or other provider) when API key is set.

    Returns empty list when NINEFIN_API_KEY is not set.
    """
    api_key = os.environ.get("NINEFIN_API_KEY", "").strip()
    if not api_key:
        return []
    # TODO: implement live 9fin API call when endpoint and schema are available.
    _ = industry, geography, limit, api_key
    return []


def get_benchmarker_live_config() -> tuple[bool, str]:
    """
    Read env/config for Benchmarker live data.

    Returns:
        (use_live, data_source) where use_live is True when BENCHMARKER_USE_LIVE
        is set to 1/true/yes, and data_source is BENCHMARKER_DATA_SOURCE or 'stub'.
    """
    use_live = os.environ.get("BENCHMARKER_USE_LIVE", "").strip().lower() in (
        "1", "true", "yes"
    )
    data_source = os.environ.get("BENCHMARKER_DATA_SOURCE", "stub").strip().lower()
    if not data_source:
        data_source = "stub"
    return use_live, data_source


# === Live Data Integration (NEW) ===

def get_live_treasury_yield(maturity: str = "10Y") -> dict[str, Any]:
    """
    Fetch live US Treasury yield from FRED (free API with key).

    Requires: FRED_API_KEY environment variable (register at fred.stlouisfed.org).

    Returns:
        Dict with yield_pct, maturity, date, source.
    
    NOTE: This function now delegates to the production-grade MarketPricingClient.
    """
    if _NEW_CLIENTS_AVAILABLE:
        try:
            client = MarketPricingClient()
            return client.get_treasury_yield(maturity)
        except Exception as e:
            logger.warning(f"Production client failed, falling back to legacy: {e}")
    
    # Legacy fallback
    try:
        from signal_triage.agents.market_data_live import fred_get_treasury_yield
        return fred_get_treasury_yield(maturity)
    except ImportError:
        return {
            "yield_pct": None,
            "maturity": maturity,
            "source": "FRED (market_data_live module not found)",
            "date": None,
        }
    except Exception as e:
        return {
            "yield_pct": None,
            "maturity": maturity,
            "source": f"FRED (error: {e})",
            "date": None,
        }


def get_live_company_financials(cik: str) -> dict[str, Any]:
    """
    Fetch company financials from SEC EDGAR (free, no API key required).

    Args:
        cik: Company CIK (e.g. "0001652044").

    Returns:
        Dict with revenue, total_debt, ebitda, filing_date, source.
    
    NOTE: This function now delegates to the production-grade SECEdgarClient.
    """
    if _NEW_CLIENTS_AVAILABLE:
        try:
            client = SECEdgarClient()
            return client.get_company_financials(cik)
        except Exception as e:
            logger.warning(f"Production client failed, falling back to legacy: {e}")
    
    # Legacy fallback
    try:
        from signal_triage.agents.market_data_live import edgar_get_company_financials
        return edgar_get_company_financials(cik)
    except ImportError:
        return {
            "cik": cik,
            "error": "market_data_live module not found",
            "source": "SEC EDGAR (failed)",
        }
    except Exception as e:
        return {
            "cik": cik,
            "error": str(e),
            "source": "SEC EDGAR (failed)",
        }

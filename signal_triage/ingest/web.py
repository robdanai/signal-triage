"""
Web/URL ingestion (Phase 5).

Ingests from URLs and SEC EDGAR filings. Caches content when cache_dir is set;
tracks source and date for provenance. Returns DocumentChunk list compatible with
Librarian and pipeline.
"""

import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from signal_triage.ingest.reader import DocumentChunk

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# SEC requires a descriptive User-Agent (see https://www.sec.gov/os/webmaster-faq)
SEC_USER_AGENT = "SignalTriage/1.0 (distressed debt analysis; contact via SEC.gov)"

# Default request timeout (seconds)
DEFAULT_TIMEOUT = 30


def _html_to_text(html: str) -> str:
    """Strip HTML tags and normalize whitespace for plain-text analysis."""
    if not html or not html.strip():
        return ""
    # Remove script/style
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    # Replace tags with space
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _cache_path(cache_dir: Path, key: str, ext: str = ".txt") -> Path:
    """Return path for a cache file from a key (e.g. URL hash or accession)."""
    name = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32] + ext
    return cache_dir / name


def _read_cached(cache_dir: Path, key: str) -> str | None:
    """Return cached content if present and valid."""
    p = _cache_path(cache_dir, key)
    if p.exists():
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
    return None


def _write_cache(cache_dir: Path, key: str, content: str) -> None:
    """Write content to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    _cache_path(cache_dir, key).write_text(content, encoding="utf-8", errors="replace")


def ingest_url(
    url: str,
    *,
    cache_dir: Path | None = None,
) -> list[DocumentChunk]:
    """
    Ingest document from URL: fetch content, optionally cache, return chunks with provenance.

    Args:
        url: HTTP(S) URL to fetch.
        cache_dir: If set, cache raw response here and use on repeat requests.

    Returns:
        List of DocumentChunk with section_label set to source descriptor (url, fetched_date).
    """
    if requests is None:
        raise ImportError("Phase 5 URL ingestion requires 'requests'. Install with: pip install requests")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL must be http or https: {url}")

    cache_key = f"url:{url}"
    if cache_dir is not None:
        cached = _read_cached(Path(cache_dir), cache_key)
        if cached is not None:
            fetched_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            source_name = parsed.netloc or url
            section_label = f"url={url} | fetched_date={fetched_date} | source_name={source_name}"
            return [
                DocumentChunk(
                    content=cached,
                    page_number=None,
                    section_label=section_label,
                    start_char=0,
                    end_char=len(cached),
                )
            ]

    resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": SEC_USER_AGENT})
    resp.raise_for_status()
    content_type = (resp.headers.get("Content-Type") or "").lower()
    raw = resp.text

    if "html" in content_type or url.lower().endswith(".htm") or url.lower().endswith(".html"):
        text = _html_to_text(raw)
    else:
        text = raw

    fetched_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    source_name = parsed.netloc or url
    section_label = f"url={url} | fetched_date={fetched_date} | source_name={source_name}"

    if cache_dir is not None:
        _write_cache(Path(cache_dir), cache_key, text)

    return [
        DocumentChunk(
            content=text,
            page_number=None,
            section_label=section_label,
            start_char=0,
            end_char=len(text),
        )
    ]


def _normalize_accession(accession_number: str, cik: str | None = None) -> tuple[str, str]:
    """
    Parse SEC accession number (and optional CIK) into CIK and path segment.

    accession_number may be "ACC" (e.g. 0001234567-21-000789) or "CIK/ACC" (e.g. 1652044/0001193125-25-261546).
    When only ACC is given, pass cik= (SEC URL requires CIK; it cannot be derived from accession for all filings).

    Returns:
        (cik_for_url, accession_no_dashes) for building SEC URLs.
    """
    acc = accession_number.strip()
    if cik is None and "/" in acc:
        cik_part, acc = acc.split("/", 1)
        cik = (cik_part or "").strip()
        acc = acc.strip()
    if not cik:
        # Fallback: first segment of accession as CIK (works only when accession encodes CIK)
        part0 = acc.split("-")[0] if "-" in acc else acc[:10]
        try:
            cik = str(int(part0))
        except ValueError:
            cik = part0.lstrip("0") or "0"
    no_dashes = acc.replace("-", "")
    return cik, no_dashes


def ingest_edgar_filing(
    accession_number: str,
    *,
    cik: str | None = None,
    cache_dir: Path | None = None,
) -> list[DocumentChunk]:
    """
    Ingest SEC EDGAR filing by accession number: fetch filing text, optionally cache,
    return chunks with accession_number and filing_date in provenance.

    Uses SEC EDGAR Archives (index.json + primary document). Requires User-Agent.
    SEC rate limit: 10 requests/second; this function makes 2 requests per filing.
    SEC URLs require CIK; pass cik= or use "CIK/accession" (e.g. 1652044/0001193125-25-261546).

    Args:
        accession_number: SEC accession number (e.g. 0001234567-21-000789) or "CIK/accession".
        cik: Optional CIK when accession_number does not include it (required for many filings).
        cache_dir: If set, cache fetched text here.

    Returns:
        List of DocumentChunk with section_label including accession_number, filing_date, source='EDGAR'.
    """
    if requests is None:
        raise ImportError("Phase 5 EDGAR ingestion requires 'requests'. Install with: pip install requests")

    cik_str, acc_path = _normalize_accession(accession_number, cik=cik)
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_str}/{acc_path}"
    cache_key = f"edgar:{cik_str}/{acc_path}"

    if cache_dir is not None:
        cached = _read_cached(Path(cache_dir), cache_key)
        if cached is not None:
            section_label = f"accession_number={accession_number} | source=EDGAR"
            return [
                DocumentChunk(
                    content=cached,
                    page_number=None,
                    section_label=section_label,
                    start_char=0,
                    end_char=len(cached),
                )
            ]

    headers = {"User-Agent": SEC_USER_AGENT, "Accept": "application/json"}
    index_url = f"{base_url}/index.json"
    idx_resp = requests.get(index_url, timeout=DEFAULT_TIMEOUT, headers=headers)
    if idx_resp.status_code == 404:
        raise ValueError(
            f"EDGAR filing not found: {accession_number}. "
            "Provide CIK (e.g. ingest_edgar_filing(accession, cik='1652044')) or use 'CIK/accession'."
        )
    idx_resp.raise_for_status()
    index_data = idx_resp.json()

    filing_date = ""
    directory = index_data.get("directory") if isinstance(index_data, dict) else None
    if isinstance(directory, dict):
        filing_date = (
            directory.get("filingDate") or directory.get("lastUpdate") or ""
        )
        if isinstance(filing_date, str):
            filing_date = filing_date.strip()
        else:
            filing_date = ""

    items: list[dict[str, Any]] = []
    if isinstance(directory, dict):
        items = directory.get("item") or []
    if not items and isinstance(index_data, dict) and isinstance(index_data.get("item"), list):
        items = index_data["item"]

    doc_name = None
    for it in items:
        if not isinstance(it, dict):
            continue
        name = (it.get("name") or "").strip()
        if name in ("index.htm", "index.html", "index.json"):
            continue
        if name.endswith(".htm") or name.endswith(".html") or name.endswith(".txt"):
            doc_name = name
            break
    if not doc_name and items:
        doc_name = items[0].get("name") if isinstance(items[0], dict) else None
    if not doc_name:
        raise ValueError(f"No document found in EDGAR filing index: {accession_number}")

    doc_url = f"{base_url}/{doc_name}"
    doc_resp = requests.get(doc_url, timeout=DEFAULT_TIMEOUT, headers=headers)
    doc_resp.raise_for_status()
    raw = doc_resp.text

    if doc_name.lower().endswith((".htm", ".html")):
        text = _html_to_text(raw)
    else:
        text = raw

    section_label = f"accession_number={accession_number} | filing_date={filing_date} | source=EDGAR"

    if cache_dir is not None:
        _write_cache(Path(cache_dir), cache_key, text)

    return [
        DocumentChunk(
            content=text,
            page_number=None,
            section_label=section_label,
            start_char=0,
            end_char=len(text),
        )
    ]

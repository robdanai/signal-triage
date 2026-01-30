"""
One-command production pipeline: Ingest → Librarian → Quant → Benchmarker → Auditor → Comparator → Reporter.

Runs subagents in order per ORCHESTRATION.md. Every step is versioned and reproducible;
output is a single, auditable analyst report. Config versions captured for audit trail.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from signal_triage.ingest.reader import read_document, full_text
from signal_triage.ingest.web import ingest_url, ingest_edgar_filing
from signal_triage.document_intel.extractor import extract_baskets_and_covenants, extract_baskets_and_covenants_enhanced
from signal_triage.document_intel import ENHANCED_PARSER_AVAILABLE
from signal_triage.signals_io import scan_document_and_write_signals, write_signals_from_chunks, read_signals
from signal_triage.analyzer import analyze_text
from signal_triage.recovery_engine import run_waterfall_from_signals, tornado_drivers
from signal_triage.agents.benchmarker import run_benchmarker
from signal_triage.agents.auditor import run_auditor
from signal_triage.agents.comparator import run_comparator
from signal_triage.reports.document_report import build_document_report, build_auditable_report
from signal_triage.agents.batch_portfolio import run_batch_portfolio
from signal_triage.agents.auditor import run_auditor as _run_auditor, build_audit_trail
from signal_triage.signals_loader import get_signals_config_version


def _is_url(s: str) -> bool:
    """True if s looks like an http(s) URL."""
    return isinstance(s, str) and (
        s.strip().lower().startswith("http://") or s.strip().lower().startswith("https://")
    )


# SEC accession: e.g. 0001234567-21-000789 or 1652044/0001193125-25-261546
_EDGAR_ACCESSION_RE = re.compile(
    r"^\s*(\d{1,10}/)?\d{10}-\d{2}-\d{6}\s*$"
)


def _is_edgar_accession(s: str) -> bool:
    """True if s looks like an SEC EDGAR accession number (with optional CIK/ prefix)."""
    return isinstance(s, str) and _EDGAR_ACCESSION_RE.match(s.strip()) is not None


def _config_versions() -> dict[str, Any]:
    """Author: Capture versioned configs for audit trail."""
    versions: dict[str, Any] = {}
    v = get_signals_config_version()
    if v is not None:
        versions["signals_config"] = v
    try:
        from signal_triage.settings_loader import load_settings
        s = load_settings()
        versions["settings"] = s.get("version") or s.get("schema_version")
    except Exception:
        pass
    return versions


def _extract_with_parser(chunks: list[Any], use_enhanced: bool = True) -> Any:
    """
    Extract baskets and covenants using standard or enhanced parser.
    
    Args:
        chunks: Document chunks to extract from.
        use_enhanced: If True and available, use enhanced forensic parser.
    
    Returns:
        ExtractionResult or EnhancedExtractionResult
    """
    if use_enhanced and ENHANCED_PARSER_AVAILABLE:
        try:
            return extract_baskets_and_covenants_enhanced(chunks=chunks)
        except Exception:
            # Fall back to standard parser if enhanced fails
            return extract_baskets_and_covenants(chunks=chunks)
    return extract_baskets_and_covenants(chunks=chunks)


def run_pipeline(
    file_path: str | Path,
    *,
    signals_path: str | Path = "signals.json",
    industry: str | None = None,
    geography: str | None = None,
    require_audit_gate: bool = True,
    include_tornado: bool = False,
    cache_dir: str | Path | None = None,
    use_enhanced_parser: bool = True,  # NEW: Use enhanced forensic parser by default
    # Forensic analysis parameters (optional)
    covenant_params: dict[str, Any] | None = None,  # For covenant headroom: {reported_ebitda, addbacks, total_debt, leverage_covenant, ...}
    ch11_params: dict[str, Any] | None = None,  # For Ch. 11 feasibility: {going_concern_ev, tangible_asset_pct, secured_debt, total_debt, ...}
) -> dict[str, Any]:
    """
    Run the full pipeline for a single document: Ingest → Librarian → Quant → Benchmarker
    → Auditor → Reporter. Returns a single auditable report per document.

    Args:
        file_path: Path to .txt or .pdf, or a URL (http(s)), or SEC EDGAR accession (e.g. 0001234567-21-000789).
        signals_path: Where to write/read signals.json (Librarian handoff to Quant).
        industry: Optional industry filter for Benchmarker.
        geography: Optional geography filter for Benchmarker.
        require_audit_gate: If True, Reporter does not publish when Auditor fails.
        include_tornado: If True and quant run succeeds, add tornado_drivers to quant summary.
        cache_dir: Optional directory for caching URL/EDGAR fetches (ignored for local files).

    Returns:
        Dict with report_format "auditable_report", document, librarian_summary,
        quant_summary, benchmarker_summary, auditor_summary, audit_trail, published.
    """
    config_versions = _config_versions()
    source_label: str
    chunks: list[Any]
    text: str

    input_str = str(file_path).strip() if isinstance(file_path, str) else None
    cache_path = Path(cache_dir) if cache_dir else None

    if input_str and _is_url(input_str):
        # Phase 5: Web ingestion from URL
        try:
            chunks = ingest_url(input_str, cache_dir=cache_path)
            text = full_text(chunks)
            source_label = input_str
            document_sources = [input_str]
        except Exception as e:
            return {
                "report_format": "auditable_report",
                "error": str(e),
                "document": build_document_report({}, source_path=input_str, text_length=0),
                "published": False,
            }
        try:
            extraction = extract_baskets_and_covenants(chunks=chunks)
            librarian_result = extraction.to_dict()
            write_signals_from_chunks(chunks, signals_path=signals_path, source_file=source_label)
        except Exception as e:
            librarian_result = {"error": str(e), "baskets": [], "collateral_leakage_flags": []}
    elif input_str and _is_edgar_accession(input_str):
        # Phase 5: EDGAR ingestion by accession
        try:
            chunks = ingest_edgar_filing(input_str, cache_dir=cache_path)
            text = full_text(chunks)
            source_label = input_str
            document_sources = [input_str]
        except Exception as e:
            return {
                "report_format": "auditable_report",
                "error": str(e),
                "document": build_document_report({}, source_path=f"EDGAR:{input_str}", text_length=0),
                "published": False,
            }
        try:
            extraction = _extract_with_parser(chunks=chunks, use_enhanced=use_enhanced_parser)
            librarian_result = extraction.to_dict()
            write_signals_from_chunks(chunks, signals_path=signals_path, source_file=source_label)
        except Exception as e:
            librarian_result = {"error": str(e), "baskets": [], "collateral_leakage_flags": []}
    else:
        # Local file path
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return {
                "report_format": "auditable_report",
                "error": f"File not found or not a file: {path}",
                "published": False,
            }
        document_sources = [str(path.resolve())]
        source_label = str(path)

        # 1. Author: Ingest with provenance (DocumentChunk)
        try:
            chunks = read_document(path)
            text = full_text(chunks)
        except Exception as e:
            return {
                "report_format": "auditable_report",
                "error": str(e),
                "document": build_document_report({}, source_path=str(path), text_length=0),
                "published": False,
            }

        # 2. Librarian: Extract baskets/covenants, write signals (LME/collateral leakage flags, section/page)
        # Uses enhanced forensic parser by default (table extraction, EBITDA normalization, LME risk scoring)
        try:
            extraction = _extract_with_parser(chunks=chunks, use_enhanced=use_enhanced_parser)
            librarian_result = extraction.to_dict()
            scan_document_and_write_signals(path, signals_path=signals_path)
        except Exception as e:
            librarian_result = {"error": str(e), "baskets": [], "collateral_leakage_flags": []}

    # 3. Quant: Waterfall from signals (LME-adjusted EV), situational summary
    quant_result = None
    try:
        quant_result = run_waterfall_from_signals(signals_path)
    except FileNotFoundError:
        pass
    except Exception as e:
        quant_result = {"error": str(e)}

    if include_tornado and quant_result and "recoveries" in quant_result and "error" not in quant_result:
        tranches = [{"name": r["name"], "claim": r["claim"]} for r in quant_result["recoveries"]]
        base_ev = quant_result.get("ev_used", 0) + quant_result.get("ev_remaining", 0)
        coll = float(quant_result.get("collateral_leakage_ev_adjustment", 0) or 0)
        quant_result["tornado_drivers"] = tornado_drivers(tranches, base_ev, collateral_adjustment=coll)

    # 4. Benchmarker: Market multiples, precedent recovery, Critical Variance flags
    benchmarker_result = {}
    if quant_result and "recoveries" in quant_result:
        model_recoveries = [
            {"name": r["name"], "recovery_pct": r["recovery_pct"]}
            for r in quant_result["recoveries"]
        ]
        benchmarker_result = run_benchmarker(
            industry=industry,
            geography=geography,
            model_recoveries=model_recoveries,
        )
    else:
        benchmarker_result = run_benchmarker(industry=industry, geography=geography)

    # 5. Auditor: Stress-test, Critical Variance reconciliation, audit trail, gate
    auditor_result = {
        "passed": True,
        "audit_trail": _build_audit_trail_for_pipeline(config_versions, document_sources, benchmarker_result),
    }
    if quant_result and "recoveries" in quant_result:
        auditor_result = _run_auditor(
            quant_result,
            benchmarker_result,
            config_versions,
            document_sources,
            require_gate=require_audit_gate,
        )

    # 6. Comparator: (single doc — no prior/current; skip or empty)
    comparator_result = None

    # 6.5. Forensic Analysis (optional): Covenant headroom, Ch. 11 feasibility, priming risk
    covenant_forensics_result = None
    ch11_feasibility_result = None
    priming_risk_result = librarian_result.get("priming_risk") if isinstance(librarian_result, dict) else None
    
    if covenant_params:
        try:
            from signal_triage.covenant_forensics import calculate_headroom
            covenant_forensics_result = calculate_headroom(**covenant_params)
        except Exception as e:
            covenant_forensics_result = {"error": str(e)}
    
    if ch11_params:
        try:
            from signal_triage.chapter11_modeling import assess_feasibility, calculate_liquidation_value
            # Calculate liquidation value if not provided
            if "liquidation_value" not in ch11_params:
                gc_ev = ch11_params.get("going_concern_ev")
                tangible_pct = ch11_params.get("tangible_asset_pct", 0.5)
                liq_result = calculate_liquidation_value(gc_ev, tangible_pct, orderly=True)
                ch11_params["liquidation_value"] = liq_result["liquidation_value"]
            ch11_feasibility_result = assess_feasibility(**ch11_params)
        except Exception as e:
            ch11_feasibility_result = {"error": str(e)}
    
    # 7. Reporter: Build auditable report; respect Auditor gate
    analysis = analyze_text(text)
    doc_report = build_document_report(analysis, source_path=source_label, text_length=len(text))
    report = build_auditable_report(
        doc_report,
        librarian_result=librarian_result if "error" not in str(librarian_result.get("error", "")) else None,
        quant_result=quant_result,
        benchmarker_result=benchmarker_result,
        auditor_result=auditor_result,
        comparator_result=comparator_result,
        covenant_forensics_result=covenant_forensics_result,
        ch11_feasibility_result=ch11_feasibility_result,
        priming_risk_result=priming_risk_result,
        require_audit_gate=require_audit_gate,
    )
    report["config_versions"] = config_versions
    report["document_sources"] = document_sources
    return report


def build_run_manifest(
    config_versions: dict[str, Any],
    document_sources: list[str],
    *,
    pipeline_mode: str = "single",
    input_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Build a run manifest for reproducibility: config_versions, document_sources, timestamp.
    Optional pipeline_mode and input_path allow a repro script to re-run the same pipeline.
    """
    manifest: dict[str, Any] = {
        "config_versions": dict(config_versions),
        "document_sources": list(document_sources),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "pipeline_mode": pipeline_mode,
    }
    if input_path is not None:
        s = str(input_path)
        if _is_url(s) or _is_edgar_accession(s):
            manifest["input_path"] = s
        else:
            manifest["input_path"] = str(Path(input_path).resolve())
    if report_path is not None:
        manifest["report_path"] = str(Path(report_path).resolve())
    return manifest


def write_run_manifest(
    report_path: str | Path,
    report: dict[str, Any],
    *,
    pipeline_mode: str = "single",
    input_path: str | Path | None = None,
) -> Path:
    """
    Write run_manifest.json next to the report file. Uses config_versions and
    document_sources from report; pipeline_mode and input_path are for repro.
    Returns the path to the written manifest file.
    """
    report_path = Path(report_path).resolve()
    config_versions = report.get("config_versions") or {}
    document_sources = report.get("document_sources")
    if document_sources is None and report.get("report_format") == "auditable_report":
        doc = report.get("document", {}) or {}
        prov = doc.get("provenance") or {}
        src = prov.get("source_path")
        document_sources = [src] if src else []
    else:
        document_sources = document_sources or []
    manifest = build_run_manifest(
        config_versions,
        document_sources,
        pipeline_mode=pipeline_mode,
        input_path=input_path,
        report_path=report_path,
    )
    manifest_path = report_path.parent / "run_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


def _build_audit_trail_for_pipeline(
    config_versions: dict[str, Any],
    document_sources: list[str],
    benchmarker_result: dict[str, Any],
) -> dict[str, Any]:
    """Build audit trail with market_data_dates from Benchmarker."""
    market_dates = None
    df = benchmarker_result.get("data_freshness")
    if isinstance(df, dict):
        market_dates = df.get("last_updated_iso")
    return build_audit_trail(config_versions, document_sources, market_data_dates=market_dates)


def run_pipeline_batch(
    folder_path: str | Path,
    *,
    recursive: bool = False,
    signals_path: str | Path = "signals.json",
    industry: str | None = None,
    geography: str | None = None,
    require_audit_gate: bool = True,
    include_tornado: bool = False,
) -> dict[str, Any]:
    """
    Run the full pipeline for all .txt and .pdf in folder. Per-document reports
    plus portfolio summary; Comparator runs when 2+ documents (prior vs current).
    Returns a single auditable report with results, portfolio, and comparisons.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return {
            "report_format": "pipeline_batch",
            "error": f"Not a directory: {folder}",
            "results": [],
            "portfolio": {},
            "published": False,
        }
    BATCH_SUFFIXES = (".txt", ".pdf")
    files = []
    if recursive:
        for ext in BATCH_SUFFIXES:
            files.extend(folder.rglob(f"*{ext}"))
    else:
        for p in folder.iterdir():
            if p.is_file() and (p.suffix or "").lower() in BATCH_SUFFIXES:
                files.append(p)
    files = sorted(set(files), key=lambda p: (p.name.lower(), str(p)))
    if not files:
        return {
            "report_format": "pipeline_batch",
            "results": [],
            "portfolio": {"summary": "No .txt or .pdf files found."},
            "published": True,
        }

    config_versions = _config_versions()
    results: list[dict[str, Any]] = []
    document_sources: list[str] = []

    for fp in files:
        doc_report = run_pipeline(
            fp,
            signals_path=Path(signals_path).parent / f"signals_{fp.stem}.json" if len(files) > 1 else signals_path,
            industry=industry,
            geography=geography,
            require_audit_gate=require_audit_gate,
            include_tornado=include_tornado,
        )
        results.append(doc_report)
        doc_path = doc_report.get("document", {}).get("file") or doc_report.get("document", {}).get("provenance", {}).get("source_path") or str(fp)
        document_sources.append(doc_path)

    # Portfolio summary from document reports
    doc_list = [r.get("document", r) for r in results if "document" in r and r.get("document")]
    portfolio = run_batch_portfolio(
        doc_list,
        id_key="file",
        score_key="score",
        top_n=10,
    ) if doc_list else {"ranked": [], "top_risks": [], "summary": "No documents processed."}

    # Comparator: prior vs current when 2+ results (use first two or consecutive pairs)
    comparator_result = None
    if len(results) >= 2:
        # Use document reports for comparison (score, tier, signals)
        snapshots = [
            r.get("document", r) for r in results[:10]
            if r.get("document") and r.get("document", {}).get("score") is not None
        ]
        if len(snapshots) >= 2:
            comparator_result = run_comparator(
                snapshots,
                id_key="file",
                score_key="score",
                tier_key="tier_label",
            )

    # Single auditable output: results, portfolio, comparator, config_versions
    published = all(r.get("published", True) for r in results)
    return {
        "report_format": "pipeline_batch",
        "config_versions": config_versions,
        "document_sources": document_sources,
        "results": results,
        "portfolio": portfolio,
        "comparator": comparator_result,
        "published": published,
    }

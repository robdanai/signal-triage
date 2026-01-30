"""
Formal "report per document" structure: score, tier, top signals, evidence, provenance.
Used by batch mode and portfolio summary. All outputs (single doc, batch results,
portfolio top_risks/ranked) use this same shape for alignment.
"""

from typing import Any, TypedDict


# --- Canonical report schema (report per document) ---
# Core fields every document report must have. Pass-through keys (score_breakdown,
# lme_signals, covenant_signals, analyst_checklist, etc.) may be included for
# downstream use.


class Provenance(TypedDict, total=False):
    """Source and size metadata for the analyzed document."""
    source_path: str
    text_length: int


class TopSignal(TypedDict, total=False):
    """Single top signal with type and evidence snippet."""
    type: str
    evidence: str


class DocumentReportCore(TypedDict, total=False):
    """
    Canonical "report per document" output. Batch mode and portfolio summary
    emit this format (portfolio top_risks/ranked use the same fields).
    """
    score: float
    tier: str
    tier_label: str
    top_signals: list[dict[str, Any]]  # list of {type, evidence}
    evidence_snippets: list[str]
    provenance: dict[str, Any]  # {source_path, text_length}
    file: str  # alias for provenance.source_path
    # Pass-through for portfolio and downstream
    score_breakdown: dict[str, Any]
    lme_signals: list[dict[str, Any]]
    covenant_signals: list[dict[str, Any]]
    analyst_checklist: list[str]
    tier_thresholds: list[dict[str, Any]] | None


# Canonical field names for report-per-document (for validation/emission).
DOCUMENT_REPORT_FIELDS = (
    "score",
    "tier",
    "tier_label",
    "top_signals",
    "evidence_snippets",
    "provenance",
)


def build_document_report(
    analyzer_result: dict[str, Any],
    source_path: str | None = None,
    text_length: int = 0,
) -> dict[str, Any]:
    """
    Build a standardized document report from analyzer output.

    Args:
        analyzer_result: Output from analyze_text() (score, tier, signals, etc.).
        source_path: File or document path for provenance.
        text_length: Character count for provenance.

    Returns:
        Dict with: score, tier, tier_label, top_signals, evidence_snippets,
        provenance, and pass-through keys (file, score_breakdown, lme_signals,
        covenant_signals, analyst_checklist, etc.) for portfolio and downstream use.
    """
    breakdown = analyzer_result.get("score_breakdown") or {}
    signals_with_meta = breakdown.get("signals") or []
    # Top signals: up to 10, with type and evidence (for report display)
    top_signals = [
        {"type": s.get("type", ""), "evidence": (s.get("evidence") or "")[:200]}
        for s in signals_with_meta[:10]
    ]
    # Evidence snippets: distinct non-empty evidence strings
    evidence_snippets = []
    seen = set()
    for s in signals_with_meta:
        ev = (s.get("evidence") or "").strip()
        if ev and ev not in seen:
            seen.add(ev)
            evidence_snippets.append(ev[:300])
    provenance = {
        "source_path": source_path,
        "text_length": text_length,
    }

    report: dict[str, Any] = {
        "score": analyzer_result.get("score"),
        "tier": analyzer_result.get("tier"),
        "tier_label": analyzer_result.get("tier_label", ""),
        "top_signals": top_signals,
        "evidence_snippets": evidence_snippets,
        "provenance": provenance,
        # Pass-through for batch_portfolio and JSON output
        "file": source_path,
        "score_breakdown": breakdown,
        "lme_signals": analyzer_result.get("lme_signals") or [],
        "covenant_signals": analyzer_result.get("covenant_signals") or [],
        "analyst_checklist": analyzer_result.get("analyst_checklist") or [],
        "tier_thresholds": analyzer_result.get("tier_thresholds"),
    }
    return report


def build_auditable_report(
    document_report: dict[str, Any],
    *,
    librarian_result: dict[str, Any] | None = None,
    quant_result: dict[str, Any] | None = None,
    benchmarker_result: dict[str, Any] | None = None,
    auditor_result: dict[str, Any] | None = None,
    comparator_result: dict[str, Any] | None = None,
    covenant_forensics_result: dict[str, Any] | None = None,
    ch11_feasibility_result: dict[str, Any] | None = None,
    priming_risk_result: dict[str, Any] | None = None,
    require_audit_gate: bool = True,
) -> dict[str, Any]:
    """
    Reporter: Formal "report per document" that aggregates Librarian, Quant,
    Benchmarker, Comparator, and Forensic modules (covenant, Ch. 11, priming).
    Do not publish final report if Auditor has flagged when require_audit_gate is True.

    Args:
        document_report: From build_document_report (score, tier, signals, provenance).
        librarian_result: ExtractionResult.to_dict() or signals payload (baskets, collateral_leakage_flags).
        quant_result: run_waterfall / run_waterfall_from_signals (recoveries, fulcrum, situational_summary, apr_violations).
        benchmarker_result: run_benchmarker (market_multiple, recovery_variance, precedents).
        auditor_result: run_auditor (passed, audit_trail, for_reporter).
        comparator_result: run_comparator / compare_two (deltas, summary).
        covenant_forensics_result: calculate_headroom (normalized_ebitda, leverage_analysis, overall_critical_distress).
        ch11_feasibility_result: assess_feasibility (feasibility, collateral_coverage, adequate_protection).
        priming_risk_result: analyze_priming_risk (priming_risk_level, majority_can_prime, risk_note).
        require_audit_gate: If True, set published=False when auditor passed is False.

    Returns:
        Dict with report_format: "auditable_report", document: document_report,
        librarian_summary, quant_summary, benchmarker_summary, auditor_summary,
        comparator_summary (when present), forensics_summary (NEW), audit_trail,
        published (bool), and analyst_note.
    """
    published = True
    analyst_note_parts = []
    if quant_result and quant_result.get("situational_summary"):
        analyst_note_parts.append(quant_result["situational_summary"])
    if auditor_result is not None:
        if require_audit_gate and not auditor_result.get("passed", True):
            published = False
        msg = auditor_result.get("for_reporter")
        if msg:
            analyst_note_parts.append(msg)
    analyst_note = " ".join(analyst_note_parts) if analyst_note_parts else None

    out: dict[str, Any] = {
        "report_format": "auditable_report",
        "document": document_report,
        "librarian_summary": None,
        "quant_summary": None,
        "benchmarker_summary": None,
        "auditor_summary": None,
        "comparator_summary": None,
        "forensics_summary": None,  # NEW: covenant, Ch. 11, priming
        "audit_trail": None,
        "published": published,
        "analyst_note": analyst_note,
    }
    if librarian_result is not None:
        baskets = librarian_result.get("baskets") or librarian_result.get("trap_doors") or []
        leakage = librarian_result.get("collateral_leakage_flags") or []
        out["librarian_summary"] = {
            "basket_count": len(baskets),
            "collateral_leakage_flags_count": len(leakage),
            "collateral_leakage_flags": leakage[:10],
        }
    if quant_result is not None:
        apr_violations = quant_result.get("apr_violations", [])
        out["quant_summary"] = {
            "fulcrum_security": quant_result.get("fulcrum_security"),
            "ev_used": quant_result.get("ev_used"),
            "ev_remaining": quant_result.get("ev_remaining"),
            "situational_summary": quant_result.get("situational_summary"),
            "recoveries": quant_result.get("recoveries"),
            "apr_violations": apr_violations,
            "apr_violations_count": len(apr_violations),
        }
    if benchmarker_result is not None:
        out["benchmarker_summary"] = {
            "market_multiple": benchmarker_result.get("market_multiple"),
            "recovery_variance": benchmarker_result.get("recovery_variance"),
            "critical_variance_flagged": any(
                v.get("critical_variance") for v in (benchmarker_result.get("recovery_variance") or [])
            ),
        }
    if auditor_result is not None:
        out["auditor_summary"] = {
            "passed": auditor_result.get("passed"),
            "stress_test": auditor_result.get("stress_test"),
            "critical_variance": auditor_result.get("critical_variance"),
            "for_reporter": auditor_result.get("for_reporter"),
        }
        out["audit_trail"] = auditor_result.get("audit_trail")
    if comparator_result is not None:
        out["comparator_summary"] = {
            "comparisons": comparator_result.get("comparisons"),
            "narrative": comparator_result.get("narrative"),
            "summary": comparator_result.get("summary"),
        }
    
    # NEW: Forensics Summary (covenant headroom, Ch. 11 feasibility, priming risk)
    forensics_summary = {}
    if covenant_forensics_result is not None:
        forensics_summary["covenant_headroom"] = {
            "normalized_ebitda": covenant_forensics_result.get("normalized_ebitda_analysis", {}).get("normalized_ebitda"),
            "leverage_headroom_pct": covenant_forensics_result.get("leverage_analysis", {}).get("headroom_pct"),
            "critical_distress": covenant_forensics_result.get("overall_critical_distress"),
            "actual_leverage": covenant_forensics_result.get("leverage_analysis", {}).get("actual_leverage"),
            "covenant_leverage": covenant_forensics_result.get("leverage_analysis", {}).get("covenant_leverage"),
        }
    if ch11_feasibility_result is not None:
        forensics_summary["ch11_feasibility"] = {
            "feasibility": ch11_feasibility_result.get("feasibility"),
            "going_concern_ev": ch11_feasibility_result.get("going_concern_ev"),
            "liquidation_value": ch11_feasibility_result.get("liquidation_value"),
            "collateral_coverage_gc_pct": ch11_feasibility_result.get("collateral_coverage_gc_pct"),
            "adequate_protection_monthly": ch11_feasibility_result.get("adequate_protection_monthly"),
            "feasibility_note": ch11_feasibility_result.get("feasibility_note"),
        }
    if priming_risk_result is not None:
        forensics_summary["priming_risk"] = {
            "priming_risk_level": priming_risk_result.get("priming_risk_level"),
            "incremental_basket_present": priming_risk_result.get("incremental_basket_present"),
            "majority_can_prime": priming_risk_result.get("majority_can_prime"),
            "consent_threshold": priming_risk_result.get("consent_threshold"),
            "risk_note": priming_risk_result.get("risk_note"),
        }
    
    if forensics_summary:
        out["forensics_summary"] = forensics_summary
    
    return out


def build_error_report(
    source_path: str | None = None,
    error_message: str = "",
    *,
    id_key: str = "file",
) -> dict[str, Any]:
    """
    Build a document report for a failed document (same shape as build_document_report).
    Used by batch mode so every result row is a formal report (score=None, error set).
    """
    provenance: dict[str, Any] = {
        "source_path": source_path,
        "text_length": 0,
    }
    report: dict[str, Any] = {
        "score": None,
        "tier": None,
        "tier_label": "",
        "top_signals": [],
        "evidence_snippets": [],
        "provenance": provenance,
        id_key: source_path,
        "score_breakdown": {"components": [], "signals": []},
        "lme_signals": [],
        "covenant_signals": [],
        "analyst_checklist": [],
        "tier_thresholds": None,
    }
    if error_message:
        report["error"] = error_message
    return report

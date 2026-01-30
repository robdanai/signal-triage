"""
Summary & Risk Narrative agent: short restructuring-style overview and tier for analyst-facing output.
"""

from typing import Any


def run_summary_narrative(analysis_result: dict[str, Any]) -> dict[str, Any]:
    """
    Produce a concise summary and risk narrative from an analysis result.

    Consumes the output of analyze_text() and returns a short restructuring-style
    overview with tier, score, top risk highlights, and analyst priorities.

    Args:
        analysis_result: Dict from analyzer.analyze_text() containing at least
            score, tier, tier_label, and optionally score_breakdown, signals,
            analyst_checklist, lme_signals, covenant_signals.

    Returns:
        Dict with:
        - summary: Short narrative paragraph (restructuring-style overview).
        - tier: Tier name (e.g. low, medium, high).
        - tier_label: Human-readable tier label.
        - score: Distress score (0–100).
        - risk_highlights: List of top risk/signal descriptions (up to 5).
        - analyst_priority: First few checklist items for follow-up (up to 5).
        - raw: Optional reference to top signal types present.
    """
    score = analysis_result.get("score")
    if score is None:
        try:
            score = float(analysis_result.get("base_score", 0)) + float(
                analysis_result.get("length_factor", 0)
            )
        except (TypeError, ValueError):
            score = 0.0
    else:
        score = float(score)

    tier = analysis_result.get("tier", "unknown")
    tier_label = analysis_result.get("tier_label", "")

    # Collect signal types and evidence for risk highlights
    all_signal_entries: list[dict[str, Any]] = []
    for key in ("lme_signals", "covenant_signals"):
        sigs = analysis_result.get(key, [])
        if isinstance(sigs, list):
            for s in sigs:
                if isinstance(s, dict):
                    all_signal_entries.append(s)
    breakdown = analysis_result.get("score_breakdown", {}) or {}
    breakdown_sigs = breakdown.get("signals", []) if isinstance(breakdown, dict) else []
    for s in breakdown_sigs:
        if isinstance(s, dict) and s not in all_signal_entries:
            all_signal_entries.append(s)

    # Build risk_highlights: short descriptions from signal type + evidence snippet
    risk_highlights: list[str] = []
    seen_types: set[str] = set()
    for s in all_signal_entries[:10]:
        stype = (s.get("type") or "signal").replace("_", " ")
        if stype in seen_types:
            continue
        seen_types.add(stype)
        evidence = (s.get("evidence") or "").strip()
        if evidence:
            snippet = evidence[:80] + ("..." if len(evidence) > 80 else "")
            risk_highlights.append(f"{stype}: {snippet}")
        else:
            risk_highlights.append(stype)
        if len(risk_highlights) >= 5:
            break

    # Analyst priority: first N checklist items
    analyst_checklist = analysis_result.get("analyst_checklist", [])
    if not isinstance(analyst_checklist, list):
        analyst_checklist = []
    analyst_priority = list(analyst_checklist[:5])

    # Build short narrative (restructuring-style)
    parts = [
        f"Document indicates {tier_label or tier} distress (score {score:.1f})."
    ]
    if risk_highlights:
        # In summary sentence use only short labels (signal types), not full evidence
        short_labels = [h.split(":", 1)[0].strip() for h in risk_highlights[:3]]
        parts.append(
            "Key concerns: " + "; ".join(short_labels) + "."
        )
    else:
        parts.append("No structured distress signals identified in this run.")
    if analyst_priority:
        parts.append(
            "Analyst priority: " + analyst_priority[0] + "."
        )
    summary = " ".join(parts)

    return {
        "summary": summary,
        "tier": tier,
        "tier_label": tier_label,
        "score": round(score, 2),
        "risk_highlights": risk_highlights,
        "analyst_priority": analyst_priority,
        "raw": {
            "signal_types": list(seen_types),
        },
    }

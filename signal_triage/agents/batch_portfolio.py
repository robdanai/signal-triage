"""
Batch Portfolio agent: rank multiple businesses by distress and produce a top-risk list.
Output format aligned with report-per-document: score, tier, top_signals,
evidence_snippets, provenance (plus rank and id).
"""

from typing import Any


def run_batch_portfolio(
    business_results: list[dict[str, Any]],
    *,
    top_n: int = 10,
    id_key: str = "file",
    score_key: str = "score",
) -> dict[str, Any]:
    """
    Rank businesses by distress score and produce a top-risk list and summary.
    Each item in ranked/top_risks uses the same shape as a document report
    (score, tier, tier_label, top_signals, evidence_snippets, provenance) plus rank and id.

    Args:
        business_results: List of per-document reports (from build_document_report).
            Each must have an identifier (see id_key) and numeric score (see score_key).
        top_n: Number of top-risk items in top_risks. Default 10.
        id_key: Key for document identifier (e.g. "file" for path, "id" for names). Default "id".
        score_key: Key for distress score (default "score").

    Returns:
        Dict with:
        - ranked: full report-per-document items sorted by score descending, with rank.
        - top_risks: top N items in same format as document report (score, tier,
          top_signals, evidence_snippets, provenance) plus rank and id.
        - summary: short narrative (portfolio size, top risks by id and score).
    """
    if not business_results:
        return {
            "ranked": [],
            "top_risks": [],
            "summary": "Portfolio is empty; no businesses to rank.",
        }

    # Sort by score descending (highest distress first)
    def sort_key(item: dict[str, Any]) -> float:
        s = item.get(score_key)
        if s is None:
            return -1.0
        try:
            return float(s)
        except (TypeError, ValueError):
            return -1.0

    ranked = sorted(
        [dict(r) for r in business_results],
        key=sort_key,
        reverse=True,
    )

    # Attach rank (1-based)
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i

    # Build top_risks: same format as document report (score, tier, top_signals,
    # evidence_snippets, provenance) plus rank and id for alignment with report-per-document.
    top_risks = []
    for item in ranked[:top_n]:
        entry: dict[str, Any] = {
            "rank": item["rank"],
            "id": item.get(id_key, ""),
            "score": item.get(score_key),
            "tier": item.get("tier"),
            "tier_label": item.get("tier_label", ""),
            "top_signals": (item.get("top_signals") or [])[:5],
            "evidence_snippets": (item.get("evidence_snippets") or [])[:5],
            "provenance": item.get("provenance") or {},
        }
        # Optional: top_signal_types from lme/covenant for quick scan
        signal_types: list[str] = []
        for key in ("lme_signals", "covenant_signals"):
            sigs = item.get(key, [])
            if isinstance(sigs, list):
                for s in sigs[:3]:
                    if isinstance(s, dict) and "type" in s:
                        signal_types.append(s["type"])
        if signal_types:
            entry["top_signal_types"] = signal_types
        top_risks.append(entry)

    # Build summary narrative
    n = len(ranked)
    parts = [f"Portfolio of {n} business(es)."]
    if top_risks:
        risk_bits = [
            f"{r['id']} (score {r['score']})"
            for r in top_risks[:5]
        ]
        parts.append("Top risks: " + "; ".join(risk_bits) + ".")
    summary = " ".join(parts)

    return {
        "ranked": ranked,
        "top_risks": top_risks,
        "summary": summary,
    }

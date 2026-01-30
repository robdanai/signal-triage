"""
Comparator agent: highlight changes across time or peers.

Compares analysis results to surface:
- Score and tier deltas (prior vs current, or vs baseline)
- New / removed signal types
- Short narrative of material changes for analyst use.
"""

from __future__ import annotations

from typing import Any


def _signal_types(signals: list[dict[str, Any]]) -> set[str]:
    """Extract distinct signal types from a list of signal dicts."""
    out: set[str] = set()
    for s in signals:
        if isinstance(s, dict) and "type" in s:
            out.add(str(s["type"]))
    return out


def _all_signals(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect lme_signals and covenant_signals (and any other *_signals) from analyzer output."""
    out: list[dict[str, Any]] = []
    for key, val in item.items():
        if key.endswith("_signals") and isinstance(val, list):
            for s in val:
                if isinstance(s, dict):
                    out.append(s)
    return out


def compare_two(
    prior: dict[str, Any],
    current: dict[str, Any],
    *,
    prior_id: str = "prior",
    current_id: str = "current",
    score_key: str = "score",
    tier_key: str = "tier",
) -> dict[str, Any]:
    """
    Compare two analysis results (e.g. prior vs current filing).

    Args:
        prior: Earlier analysis result (score, tier, *_signals).
        current: Later analysis result.
        prior_id: Label for prior (e.g. "2023-10-K").
        current_id: Label for current (e.g. "2024-10-K").
        score_key: Key for numeric score. Default "score".
        tier_key: Key for tier label. Default "tier".

    Returns:
        Dict with:
        - prior_id, current_id
        - score_delta: current - prior (positive = more distress)
        - tier_prior, tier_current
        - tier_changed: bool
        - new_signal_types: list of signal types in current but not prior
        - removed_signal_types: list of signal types in prior but not current
        - summary: short narrative of changes
    """
    score_prior = prior.get(score_key)
    score_current = current.get(score_key)
    try:
        p = float(score_prior) if score_prior is not None else 0.0
    except (TypeError, ValueError):
        p = 0.0
    try:
        c = float(score_current) if score_current is not None else 0.0
    except (TypeError, ValueError):
        c = 0.0
    score_delta = round(c - p, 2)

    tier_prior = prior.get(tier_key) or ""
    tier_current = current.get(tier_key) or ""
    tier_changed = tier_prior != tier_current

    types_prior = _signal_types(_all_signals(prior))
    types_current = _signal_types(_all_signals(current))
    new_signal_types = sorted(types_current - types_prior)
    removed_signal_types = sorted(types_prior - types_current)

    # Build summary narrative
    parts: list[str] = []
    parts.append(f"Comparison: {prior_id} → {current_id}.")
    if score_delta != 0:
        direction = "higher" if score_delta > 0 else "lower"
        parts.append(f"Score {direction} by {abs(score_delta):.2f} (now {c:.2f}).")
    if tier_changed:
        parts.append(f"Tier changed from '{tier_prior}' to '{tier_current}'.")
    if new_signal_types:
        parts.append(f"New signal types: {', '.join(new_signal_types)}.")
    if removed_signal_types:
        parts.append(f"Removed signal types: {', '.join(removed_signal_types)}.")
    summary = " ".join(parts) if parts else f"No material change between {prior_id} and {current_id}."

    return {
        "prior_id": prior_id,
        "current_id": current_id,
        "score_delta": score_delta,
        "score_prior": p,
        "score_current": c,
        "tier_prior": tier_prior,
        "tier_current": tier_current,
        "tier_changed": tier_changed,
        "new_signal_types": new_signal_types,
        "removed_signal_types": removed_signal_types,
        "summary": summary,
    }


def run_comparator(
    snapshots: list[dict[str, Any]],
    *,
    baseline_index: int | None = None,
    id_key: str = "id",
    as_of_key: str = "as_of",
    score_key: str = "score",
    tier_key: str = "tier",
) -> dict[str, Any]:
    """
    Run Comparator over multiple snapshots (time or peers).

    - If len(snapshots) == 2: treat as prior vs current (time comparison).
    - If baseline_index is set: compare each snapshot to the baseline.
    - Otherwise: compare each consecutive pair and optionally rank by score.

    Args:
        snapshots: List of analysis results. Each may have id, as_of, score, tier, *_signals.
        baseline_index: If set, compare every other snapshot to snapshots[baseline_index].
        id_key: Key for snapshot identifier (e.g. "id", "source_path").
        as_of_key: Optional key for date/label (e.g. "as_of", "filing_date").
        score_key: Key for distress score.
        tier_key: Key for tier label.

    Returns:
        Dict with:
        - mode: "pair" | "baseline" | "multi"
        - comparisons: list of compare_two-style results
        - narrative: short overall summary
    """
    if not snapshots:
        return {
            "mode": "none",
            "comparisons": [],
            "narrative": "No snapshots provided; nothing to compare.",
        }

    if len(snapshots) == 1:
        s = snapshots[0]
        sid = s.get(id_key) or s.get("source_path") or "single"
        return {
            "mode": "single",
            "comparisons": [],
            "narrative": f"Single snapshot '{sid}'; add prior or peer snapshots to compare.",
        }

    comparisons: list[dict[str, Any]] = []
    mode = "multi"

    if len(snapshots) == 2 and baseline_index is None:
        mode = "pair"
        prior = snapshots[0]
        current = snapshots[1]
        prior_id = str(prior.get(id_key) or prior.get(as_of_key) or "prior")
        current_id = str(current.get(id_key) or current.get(as_of_key) or "current")
        comparisons.append(
            compare_two(
                prior,
                current,
                prior_id=prior_id,
                current_id=current_id,
                score_key=score_key,
                tier_key=tier_key,
            )
        )
    elif baseline_index is not None and 0 <= baseline_index < len(snapshots):
        mode = "baseline"
        baseline = snapshots[baseline_index]
        base_id = str(
            baseline.get(id_key) or baseline.get(as_of_key) or f"baseline_{baseline_index}"
        )
        for i, snap in enumerate(snapshots):
            if i == baseline_index:
                continue
            snap_id = str(snap.get(id_key) or snap.get(as_of_key) or f"snapshot_{i}")
            comparisons.append(
                compare_two(
                    baseline,
                    snap,
                    prior_id=base_id,
                    current_id=snap_id,
                    score_key=score_key,
                    tier_key=tier_key,
                )
            )
    else:
        # Consecutive pairs: 0→1, 1→2, ...
        for i in range(len(snapshots) - 1):
            prior = snapshots[i]
            current = snapshots[i + 1]
            prior_id = str(prior.get(id_key) or prior.get(as_of_key) or f"t{i}")
            current_id = str(current.get(id_key) or current.get(as_of_key) or f"t{i+1}")
            comparisons.append(
                compare_two(
                    prior,
                    current,
                    prior_id=prior_id,
                    current_id=current_id,
                    score_key=score_key,
                    tier_key=tier_key,
                )
            )

    # Overall narrative
    if not comparisons:
        narrative = "No comparisons produced."
    elif len(comparisons) == 1:
        narrative = comparisons[0].get("summary", "")
    else:
        parts = [c.get("summary", "") for c in comparisons]
        narrative = " | ".join(parts)

    return {
        "mode": mode,
        "comparisons": comparisons,
        "narrative": narrative,
    }

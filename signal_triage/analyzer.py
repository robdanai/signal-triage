"""
Core analysis logic for calculating distress scores from text.
"""

import re

from signal_triage.checklist import generate_checklist
from signal_triage.settings_loader import load_settings, get_tier_for_score
from signal_triage.signals_loader import load_signal_rules, load_signal_weights


# Negation cues that, appearing shortly before a phrase in the same sentence,
# indicate the filing is denying the condition ("no Event of Default has
# occurred", "alleviated substantial doubt"). Without this, boilerplate
# compliance language scores as distress.
_NEGATION_CUES = re.compile(
    r"\b(no|not|none|without|neither|nor|absence of|alleviat\w*|"
    r"no longer|did not|does not|has not|have not|was not|were not)\b"
)
_NEGATION_WINDOW = 40  # characters before the phrase
_SENTENCE_BREAK = re.compile(r"[.;!?]\s")


def _phrase_pattern(phrase: str) -> re.Pattern:
    """Word-boundary, case-insensitive pattern so 'mac' does not match 'machine'."""
    return re.compile(r"(?<!\w)" + re.escape(phrase.lower()) + r"(?!\w)")


def _is_negated(text_lower: str, pos: int) -> bool:
    window = text_lower[max(0, pos - _NEGATION_WINDOW):pos]
    # Only look within the current sentence.
    breaks = list(_SENTENCE_BREAK.finditer(window))
    if breaks:
        window = window[breaks[-1].end():]
    return bool(_NEGATION_CUES.search(window))


def _find_affirmative_matches(text_lower: str, phrases: list[str]) -> list[tuple[int, int, str]]:
    """All non-negated (start, end, phrase) matches for a rule's phrases."""
    hits = []
    for phrase in phrases:
        if not phrase or not phrase.strip():
            continue
        for m in _phrase_pattern(phrase).finditer(text_lower):
            if not _is_negated(text_lower, m.start()):
                hits.append((m.start(), m.end(), phrase))
    hits.sort()
    return hits


def _snippet(text: str, start: int, end: int, pad: int = 60) -> str:
    snippet = text[max(0, start - pad):min(len(text), end + pad)].strip()
    return snippet if len(snippet) <= 200 else snippet[:197] + "..."


def _detect_signals_from_config(text: str, signal_rules: list[dict]) -> list[dict]:
    """
    Detect signals from config-driven rules (phrases per signal type).

    - Matching is case-insensitive on word boundaries.
    - Negated mentions ("no event of default") are ignored.
    - Rules are evaluated highest-weight first; a text span already claimed by a
      higher-weight rule does not also trigger a lower-weight rule, so one
      phrase (e.g. "covenant breach", listed under two rules) is counted once.

    Returns at most one signal per rule id, with the first unclaimed match as
    evidence and the total number of affirmative mentions as ``hits``.
    """
    if not text or not text.strip() or not signal_rules:
        return []
    text_lower = text.lower()
    claimed: list[tuple[int, int]] = []
    out = []
    ordered = sorted(signal_rules, key=lambda r: -float(r.get("weight") or 0))
    for rule in ordered:
        sid = rule.get("id") or ""
        hits = _find_affirmative_matches(text_lower, rule.get("phrases") or [])
        unclaimed = [
            h for h in hits
            if not any(h[0] < c_end and c_start < h[1] for c_start, c_end in claimed)
        ]
        if not unclaimed:
            continue
        start, end, phrase = unclaimed[0]
        claimed.extend((h[0], h[1]) for h in unclaimed)
        out.append({
            "type": sid,
            "evidence": _snippet(text, start, end),
            "matched_phrase": phrase,
            "hits": len(unclaimed),
            "char_offset": start,
        })
    # Preserve document order for display.
    out.sort(key=lambda s: s["char_offset"])
    return out


def _signal_weights(settings: dict) -> dict:
    # Weights: config (signals_config.json) overrides settings (settings.json)
    weights = dict(settings.get("signal_weights", {}))
    config_weights = load_signal_weights()
    if config_weights:
        weights.update(config_weights)
    return weights


def _score_signals(all_signals: list[dict], settings: dict) -> dict:
    """
    Combine detected signals into a 0-100 distress score.

    Each signal contributes an independent probability-like severity
    p = min(weight / weight_scale, max_signal_severity) * confidence, combined
    as 100 * (1 - prod(1 - p)). This is bounded, has diminishing returns (ten
    weak signals do not outrank one going-concern opinion by sheer volume) and
    is independent of document length.

    Severity floors (settings.severity_floors) then guarantee a minimum score
    for signals that are dispositive on their own, e.g. a going-concern doubt.
    """
    scoring = settings.get("scoring", {})
    weight_scale = float(scoring.get("weight_scale", 50.0))
    max_sev = float(scoring.get("max_signal_severity", 0.9))
    floors = settings.get("severity_floors", {})
    default_conf = float(settings.get("default_signal_confidence", 0.85))
    weights = _signal_weights(settings)

    survival = 1.0
    scored = []
    for s in all_signals:
        stype = s.get("type", "unknown")
        weight = weights.get(stype, 10)
        conf = float(s.get("confidence", default_conf))
        p = min(weight / weight_scale, max_sev) * conf
        survival *= 1.0 - p
        scored.append({
            "type": stype,
            "evidence": (s.get("evidence") or "")[:200],
            "matched_phrase": s.get("matched_phrase"),
            "hits": s.get("hits", 1),
            "weight": weight,
            "confidence": conf,
            "severity": round(p, 4),
        })
    signal_score = round(100.0 * (1.0 - survival), 2)

    floor_score, floor_source = 0.0, None
    for sig in scored:
        f = float(floors.get(sig["type"], 0))
        if f > floor_score:
            floor_score, floor_source = f, sig["type"]
    score = round(min(max(signal_score, floor_score), 100.0), 2)

    components = [{
        "name": "credit_signals",
        "weight": 100.0,
        "contribution": signal_score,
        "confidence": max((s["confidence"] for s in scored), default=default_conf),
    }]
    if floor_source and floor_score > signal_score:
        components.append({
            "name": f"severity_floor:{floor_source}",
            "weight": 0.0,
            "contribution": round(floor_score - signal_score, 2),
            "confidence": 1.0,
        })
    return {
        "score": score,
        "signal_score": signal_score,
        "floor_applied": floor_source if floor_score > signal_score else None,
        "breakdown": {"components": components, "signals": scored},
    }


def analyze_text(text: str) -> dict:
    """
    Analyze text content and return score details.

    The score is driven entirely by config-defined credit signals
    (signals_config.json); see _score_signals for the formula.

    Args:
        text: The text content to analyze

    Returns:
        A dict with score and explanation details. ``keywords_found``,
        ``keyword_count`` and ``base_score`` describe the matched credit
        phrases; ``length_factor`` is retained for backward compatibility and
        is always 0 (document length no longer affects the score).
    """
    settings = load_settings()
    if not text or not text.strip():
        tier_name, tier_label = get_tier_for_score(0.0, settings)
        return {
            "score": 0.0,
            "keywords_found": [],
            "keyword_count": 0,
            "base_score": 0.0,
            "length_factor": 0.0,
            "floor_applied": None,
            "lme_signals": [],
            "covenant_signals": [],
            "analyst_checklist": [],
            "score_breakdown": {"components": [], "signals": []},
            "tier": tier_name,
            "tier_label": tier_label,
            "tier_thresholds": settings.get("tiers", []),
        }

    signal_rules = load_signal_rules()
    all_signals = _detect_signals_from_config(text, signal_rules) if signal_rules else []
    scored = _score_signals(all_signals, settings)
    score = scored["score"]

    # Backward compatibility: covenant_signals = covenant-related types
    covenant_types = {"covenant_risk", "liquidity_covenant"}
    covenant_signals = [s for s in all_signals if s.get("type") in covenant_types]
    analyst_checklist = generate_checklist(all_signals)
    tier_name, tier_label = get_tier_for_score(score, settings)

    lme_types = {"dropdown", "sprime_leakage", "uptiering"}
    lme_signals = [s for s in all_signals if s.get("type") in lme_types]
    keywords_found = [s["matched_phrase"] for s in all_signals if s.get("matched_phrase")]
    return {
        "score": score,
        "keywords_found": keywords_found,
        "keyword_count": len(keywords_found),
        "base_score": scored["signal_score"],
        "length_factor": 0.0,
        "floor_applied": scored["floor_applied"],
        "lme_signals": lme_signals,
        "covenant_signals": covenant_signals,
        "analyst_checklist": analyst_checklist,
        "score_breakdown": scored["breakdown"],
        "tier": tier_name,
        "tier_label": tier_label,
        "tier_thresholds": settings.get("tiers", []),
    }


def calculate_distress_score(text: str) -> float:
    """
    Calculate a distress score from text content.

    Args:
        text: The text content to analyze

    Returns:
        A float representing the distress score (0.0 to 100.0)
    """
    return analyze_text(text)["score"]

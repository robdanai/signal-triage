"""
Signal Extractor agent: produces structured signals with evidence snippets and confidence.

Tailored to restructuring/distress:
- LME (dropdown, sprime_leakage, uptiering)
- Covenant/waiver and default language
- Going concern, liquidity shortfall, debt maturity wall, auditor emphasis
"""

from __future__ import annotations

from typing import Any

from signal_triage.lme_parser import detect_lme
from signal_triage.settings_loader import load_settings


# Covenant/waiver and default phrases (aligned with analyzer)
COVENANT_PHRASES = [
    "covenant breach", "covenant default", "waiver", "material adverse",
    "mac", "material adverse change", "cure period", "event of default",
]
DEFAULT_PHRASES = [
    "event of default", "default under", "cross-default", "acceleration",
]

# Phase 3 rule-based signals (restructuring/distress)
GOING_CONCERN_PHRASES = [
    "going concern", "substantial doubt", "ability to continue",
    "doubt about our ability", "may be unable to continue",
]
LIQUIDITY_PHRASES = [
    "liquidity shortfall", "insufficient liquidity", "liquidity constraint",
    "may not have sufficient", "cash flow shortfall", "breach of covenant",
]
MATURITY_PHRASES = [
    "debt maturity", "maturity wall", "refinancing risk", "near-term maturities",
    "maturities due", "upcoming maturity", "refinancing of our debt",
]
AUDITOR_EMPHASIS_PHRASES = [
    "emphasis of matter", "going concern", "material uncertainty",
    "significant doubt", "auditor emphasis",
]


def _snippet(text: str, pos: int, phrase: str, context: int = 20) -> str:
    """Extract a short evidence snippet around the match."""
    start = max(0, pos - context)
    end = min(len(text), pos + len(phrase) + context)
    return text[start:end].strip()


def _detect_phrase_signals(
    text: str,
    signal_type: str,
    phrases: list[str],
    context: int = 20,
) -> list[dict[str, Any]]:
    """Detect signals by phrase match; return list of {type, evidence, label, span}."""
    if not text or not text.strip():
        return []
    text_lower = text.lower()
    out = []
    for phrase in phrases:
        pos = text_lower.find(phrase)
        if pos == -1:
            continue
        snippet_val = _snippet(text, pos, phrase, context)
        if len(snippet_val) > 200:
            snippet_val = snippet_val[:197] + "..."
        out.append({
            "type": signal_type,
            "label": phrase,
            "evidence": snippet_val,
            "span": (pos, pos + len(phrase)),
        })
    return out


def _detect_covenant_signals(text: str) -> list[dict[str, Any]]:
    """Detect covenant/waiver language; return one covenant_risk signal with evidence."""
    signals = _detect_phrase_signals(text, "covenant_risk", COVENANT_PHRASES)
    # Deduplicate: one covenant_risk per doc (first match)
    return signals[:1] if signals else []


def _detect_default_signals(text: str) -> list[dict[str, Any]]:
    """Detect default/acceleration language."""
    return _detect_phrase_signals(text, "potential_default", DEFAULT_PHRASES)[:1]


def _detect_going_concern_signals(text: str) -> list[dict[str, Any]]:
    """Detect going concern language."""
    return _detect_phrase_signals(text, "going_concern", GOING_CONCERN_PHRASES)


def _detect_liquidity_signals(text: str) -> list[dict[str, Any]]:
    """Detect liquidity shortfall / covenant breach language."""
    return _detect_phrase_signals(text, "liquidity_shortfall", LIQUIDITY_PHRASES)


def _detect_maturity_signals(text: str) -> list[dict[str, Any]]:
    """Detect debt maturity wall / refinancing risk."""
    return _detect_phrase_signals(text, "debt_maturity_wall", MATURITY_PHRASES)


def _detect_auditor_emphasis_signals(text: str) -> list[dict[str, Any]]:
    """Detect auditor emphasis of matter."""
    return _detect_phrase_signals(text, "auditor_emphasis", AUDITOR_EMPHASIS_PHRASES)


def _add_confidence_and_weight(
    signals: list[dict[str, Any]],
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Add confidence and weight to each signal from settings."""
    default_conf = settings.get("default_signal_confidence", 0.85)
    weights = settings.get("signal_weights", {})
    out = []
    for s in signals:
        stype = s.get("type", "unknown")
        weight = weights.get(stype, 10)
        out.append({
            **s,
            "confidence": default_conf,
            "weight": weight,
        })
    return out


def extract_signals(
    text: str,
    settings: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Extract all rule-based distress signals from text with evidence snippets and confidence.

    Args:
        text: Raw document text to analyze.
        settings: Optional pre-loaded settings (tiers, signal_weights, default_signal_confidence).
                  If None, load_settings() is used.

    Returns:
        List of signals; each has type, evidence, confidence, weight, and optionally label, span.
    """
    if settings is None:
        settings = load_settings()

    if not text or not text.strip():
        return []

    # LME (already returns type, label, evidence, span)
    lme_signals = detect_lme(text)

    # Covenant and default (same semantics as analyzer)
    covenant_signals = _detect_covenant_signals(text)
    default_signals = _detect_default_signals(text)

    # Phase 3: going concern, liquidity, maturity wall, auditor emphasis
    going_concern = _detect_going_concern_signals(text)
    liquidity = _detect_liquidity_signals(text)
    maturity = _detect_maturity_signals(text)
    auditor = _detect_auditor_emphasis_signals(text)

    # Normalize LME items to same shape (add label if missing)
    all_raw = []
    for s in lme_signals:
        all_raw.append({
            "type": s["type"],
            "label": s.get("label", s["type"]),
            "evidence": (s.get("evidence") or "")[:200],
            "span": s.get("span"),
        })
    for s in covenant_signals + default_signals + going_concern + liquidity + maturity + auditor:
        all_raw.append({
            "type": s["type"],
            "label": s.get("label", s["type"]),
            "evidence": (s.get("evidence") or "")[:200],
            "span": s.get("span"),
        })

    return _add_confidence_and_weight(all_raw, settings)


def run_signal_extractor(
    text: str,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run the Signal Extractor agent and return a structured result for downstream use.

    Args:
        text: Raw document text.
        settings: Optional settings dict; if None, load_settings() is used.

    Returns:
        Dict with key "signals": list of {type, evidence, confidence, weight, ...}.
    """
    signals = extract_signals(text, settings=settings)
    return {"signals": signals}

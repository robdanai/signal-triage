"""
Core analysis logic for calculating distress scores from text.
"""

from signal_triage.checklist import generate_checklist
from signal_triage.settings_loader import load_settings, get_tier_for_score
from signal_triage.signals_loader import load_signal_rules, load_signal_weights


def _detect_signals_from_config(text: str, signal_rules: list[dict]) -> list[dict]:
    """
    Detect signals from config-driven rules (phrases per signal type).
    Returns at most one signal per rule id; first phrase match wins.
    """
    if not text or not text.strip() or not signal_rules:
        return []
    text_lower = text.lower()
    out = []
    for rule in signal_rules:
        sid = rule.get("id") or ""
        phrases = rule.get("phrases") or []
        for phrase in phrases:
            if phrase in text_lower:
                pos = text_lower.find(phrase)
                start = max(0, pos - 20)
                end = min(len(text), pos + len(phrase) + 20)
                snippet = text[start:end].strip()
                if len(snippet) > 120:
                    snippet = snippet[:117] + "..."
                out.append({"type": sid, "evidence": snippet})
                break  # one signal per rule type
    return out


def _build_score_breakdown(
    base_score: float,
    length_factor: float,
    all_signals: list[dict],
    settings: dict,
) -> dict:
    """Build structured score breakdown: components and signals with weights and confidence."""
    components = [
        {
            "name": "keyword_distress",
            "weight": 50.0,
            "contribution": base_score,
            "confidence": min(0.5 + 0.1 * (base_score / 10) if base_score else 0.5, 0.95),
        },
        {
            "name": "length_factor",
            "weight": 50.0,
            "contribution": length_factor,
            "confidence": 0.6,
        },
    ]
    # Weights: config (signals_config.json) overrides settings (settings.json)
    signal_weights = dict(settings.get("signal_weights", {}))
    config_weights = load_signal_weights()
    if config_weights:
        signal_weights.update(config_weights)
    default_conf = settings.get("default_signal_confidence", 0.85)
    signals_with_meta = []
    for s in all_signals:
        stype = s.get("type", "unknown")
        weight = signal_weights.get(stype, 10)
        signals_with_meta.append({
            "type": stype,
            "evidence": (s.get("evidence") or "")[:200],
            "weight": weight,
            "confidence": default_conf,
        })
    return {
        "components": components,
        "signals": signals_with_meta,
    }


def analyze_text(text: str) -> dict:
    """
    Analyze text content and return score details.

    Args:
        text: The text content to analyze

    Returns:
        A dict with score and explanation details
    """
    if not text or not text.strip():
        settings = load_settings()
        tier_name, tier_label = get_tier_for_score(0.0, settings)
        return {
            "score": 0.0,
            "keywords_found": [],
            "keyword_count": 0,
            "base_score": 0.0,
            "length_factor": 0.0,
            "lme_signals": [],
            "covenant_signals": [],
            "analyst_checklist": [],
            "score_breakdown": {"components": [], "signals": []},
            "tier": tier_name,
            "tier_label": tier_label,
            "tier_thresholds": settings.get("tiers", []),
        }

    # Simple placeholder algorithm
    # In a real implementation, this would analyze the text for distress indicators
    text_lower = text.lower()

    # Count potential distress keywords (simple example)
    distress_keywords = [
        "help", "urgent", "emergency", "distress", "crisis",
        "worried", "anxious", "scared", "afraid", "panic",
    ]

    keywords_found = [kw for kw in distress_keywords if kw in text_lower]
    keyword_count = len(keywords_found)

    # Calculate score based on keyword frequency and text length
    # This is a placeholder - replace with actual analysis logic
    base_score = min(keyword_count * 10, 50)  # Max 50 from keywords
    length_factor = min(len(text) / 100, 50)  # Max 50 from length

    score = base_score + length_factor

    # Normalize to 0-100 range
    score = min(score, 100.0)

    signal_rules = load_signal_rules()
    config_signals = _detect_signals_from_config(text, signal_rules) if signal_rules else []
    all_signals = config_signals
    # Backward compatibility: covenant_signals = covenant-related types
    covenant_types = {"covenant_risk", "liquidity_covenant"}
    covenant_signals = [s for s in all_signals if s.get("type") in covenant_types]
    analyst_checklist = generate_checklist(all_signals)

    settings = load_settings()
    score_breakdown = _build_score_breakdown(
        base_score, length_factor, all_signals, settings
    )
    tier_name, tier_label = get_tier_for_score(score, settings)

    lme_types = {"dropdown", "sprime_leakage", "uptiering"}
    lme_signals = [s for s in all_signals if s.get("type") in lme_types]
    return {
        "score": score,
        "keywords_found": keywords_found,
        "keyword_count": keyword_count,
        "base_score": base_score,
        "length_factor": length_factor,
        "lme_signals": lme_signals,
        "covenant_signals": covenant_signals,
        "analyst_checklist": analyst_checklist,
        "score_breakdown": score_breakdown,
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

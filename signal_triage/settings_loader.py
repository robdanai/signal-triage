"""
Load tier thresholds and signal weights from a settings file.
Falls back to package default if no file is found.
Signal weights are merged with signals_config.json when present.
Validates schema_version for reproducibility; warns on unsupported version.
"""

import json
import warnings
from pathlib import Path
from typing import Any

from signal_triage.config_schema import SUPPORTED_SETTINGS_VERSIONS
from signal_triage.signals_loader import load_signal_weights

# Default tiers and weights (used when settings.json is missing)
DEFAULT_TIERS = [
    {"name": "low", "label": "Low distress", "min": 0, "max": 25},
    {"name": "medium", "label": "Medium distress", "min": 25, "max": 60},
    {"name": "high", "label": "High distress", "min": 60, "max": 100},
]
DEFAULT_SIGNAL_WEIGHTS = {
    "covenant_risk": 15,
    "potential_default": 20,
    "dropdown": 8,
    "sprime_leakage": 10,
    "uptiering": 12,
    "going_concern": 18,
    "liquidity_shortfall": 16,
    "refinancing_risk": 14,
    "debt_maturity_wall": 14,
    "auditor_emphasis": 18,
}
DEFAULT_SIGNAL_CONFIDENCE = 0.85


# Score aggregation parameters (see analyzer._score_signals)
DEFAULT_SCORING = {"weight_scale": 50.0, "max_signal_severity": 0.9}
# Minimum score when a dispositive signal is present (e.g. going-concern doubt -> high tier)
DEFAULT_SEVERITY_FLOORS = {"going_concern": 60.0}


def _load_scoring(data: dict[str, Any]) -> dict[str, float]:
    scoring = dict(DEFAULT_SCORING)
    raw = data.get("scoring")
    if isinstance(raw, dict):
        for key in scoring:
            val = raw.get(key)
            if isinstance(val, (int, float)) and val > 0:
                scoring[key] = float(val)
    scoring["max_signal_severity"] = min(scoring["max_signal_severity"], 1.0)
    return scoring


def _load_severity_floors(data: dict[str, Any]) -> dict[str, float]:
    raw = data.get("severity_floors")
    if not isinstance(raw, dict):
        return dict(DEFAULT_SEVERITY_FLOORS)
    return {
        str(k): float(v) for k, v in raw.items()
        if isinstance(v, (int, float)) and 0 <= v <= 100
    }


def _package_settings_path() -> Path:
    """Path to settings.json bundled with the package."""
    return Path(__file__).resolve().parent / "settings.json"


def _find_settings_path() -> Path | None:
    """Look for settings.json in cwd then package dir."""
    cwd = Path.cwd() / "settings.json"
    if cwd.exists() and cwd.is_file():
        return cwd
    pkg = _package_settings_path()
    if pkg.exists() and pkg.is_file():
        return pkg
    return None


def load_settings() -> dict[str, Any]:
    """
    Load settings from settings.json (cwd or package).
    Returns dict with keys: tiers, signal_weights, default_signal_confidence,
    scoring, severity_floors.
    """
    path = _find_settings_path()
    if path is None:
        return {
            "version": None,
            "tiers": DEFAULT_TIERS,
            "signal_weights": DEFAULT_SIGNAL_WEIGHTS,
            "default_signal_confidence": DEFAULT_SIGNAL_CONFIDENCE,
            "scoring": dict(DEFAULT_SCORING),
            "severity_floors": dict(DEFAULT_SEVERITY_FLOORS),
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {
            "version": None,
            "tiers": DEFAULT_TIERS,
            "signal_weights": DEFAULT_SIGNAL_WEIGHTS,
            "default_signal_confidence": DEFAULT_SIGNAL_CONFIDENCE,
            "scoring": dict(DEFAULT_SCORING),
            "severity_floors": dict(DEFAULT_SEVERITY_FLOORS),
        }
    # Validate schema_version for reproducibility (accept legacy "version")
    schema_version = data.get("schema_version") or data.get("version")
    if schema_version is not None and str(schema_version) not in SUPPORTED_SETTINGS_VERSIONS:
        warnings.warn(
            f"settings.json schema_version={schema_version!r} is not in supported "
            f"{SUPPORTED_SETTINGS_VERSIONS}; results may not be reproducible.",
            UserWarning,
            stacklevel=2,
        )
    tiers = data.get("tiers")
    if not tiers or not isinstance(tiers, list):
        tiers = DEFAULT_TIERS
    signal_weights = data.get("signal_weights")
    if not isinstance(signal_weights, dict):
        signal_weights = DEFAULT_SIGNAL_WEIGHTS.copy()
    else:
        # Merge with defaults so new signal types get a default weight
        merged = dict(DEFAULT_SIGNAL_WEIGHTS)
        merged.update(signal_weights)
        signal_weights = merged
    # Override with weights from signals_config.json when present (transparent weighting model)
    config_weights = load_signal_weights()
    if config_weights:
        signal_weights = dict(signal_weights)
        signal_weights.update(config_weights)
    confidence = data.get("default_signal_confidence", DEFAULT_SIGNAL_CONFIDENCE)
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        confidence = DEFAULT_SIGNAL_CONFIDENCE
    version = data.get("schema_version") or data.get("version")
    return {
        "version": str(version) if version is not None else None,
        "tiers": tiers,
        "signal_weights": signal_weights,
        "default_signal_confidence": confidence,
        "scoring": _load_scoring(data),
        "severity_floors": _load_severity_floors(data),
    }


def get_tier_for_score(score: float, settings: dict[str, Any] | None = None) -> tuple[str, str]:
    """
    Return (tier_name, tier_label) for a given score using configured thresholds.

    Args:
        score: Distress score 0–100.
        settings: Optional pre-loaded settings; if None, load_settings() is called.

    Returns:
        (tier_name, tier_label), e.g. ("medium", "Medium distress").
    """
    if settings is None:
        settings = load_settings()
    tiers = settings.get("tiers", DEFAULT_TIERS)
    for t in tiers:
        min_val = t.get("min", 0)
        max_val = t.get("max", 100)
        if min_val <= score < max_val:
            return (str(t.get("name", "unknown")), str(t.get("label", "Unknown")))
    # Fallback: last tier if score >= last max
    if tiers:
        last = tiers[-1]
        return (str(last.get("name", "high")), str(last.get("label", "High distress")))
    return ("unknown", "Unknown")

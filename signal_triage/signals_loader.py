"""
Load signal rules and weights from signals_config.json.
Used for transparent, config-driven rule-based signal detection and scoring.
Validates schema_version for reproducibility; warns on unsupported version.
"""

import json
import warnings
from pathlib import Path
from typing import Any

from signal_triage.config_schema import (
    DEFAULT_SIGNALS_CONFIG_SCHEMA_VERSION,
    SUPPORTED_SIGNALS_CONFIG_VERSIONS,
)

# Defaults used when no config file is found
DEFAULT_SIGNAL_CONFIDENCE = 0.85


def _package_config_path() -> Path:
    """Path to signals_config.json bundled with the package."""
    return Path(__file__).resolve().parent / "signals_config.json"


def _find_config_path() -> Path | None:
    """Look for signals_config.json in cwd then package dir."""
    cwd = Path.cwd() / "signals_config.json"
    if cwd.exists() and cwd.is_file():
        return cwd
    pkg = _package_config_path()
    if pkg.exists() and pkg.is_file():
        return pkg
    return None


def load_signal_rules() -> list[dict[str, Any]]:
    """
    Load signal rules (id, name, description, weight, phrases) from signals_config.json.

    Returns:
        List of signal rule dicts. Each has: id, name, description, weight, phrases.
        Empty list if config missing or invalid.
    """
    path = _find_config_path()
    if path is None:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    # Validate schema_version for reproducibility (accept legacy "version")
    schema_version = data.get("schema_version") or data.get("version")
    if schema_version is not None and str(schema_version) not in SUPPORTED_SIGNALS_CONFIG_VERSIONS:
        warnings.warn(
            f"signals_config.json schema_version={schema_version!r} is not in supported "
            f"{SUPPORTED_SIGNALS_CONFIG_VERSIONS}; results may not be reproducible.",
            UserWarning,
            stacklevel=2,
        )
    signals = data.get("signals")
    if not isinstance(signals, list):
        return []
    rules = []
    for s in signals:
        if not isinstance(s, dict):
            continue
        sid = s.get("id")
        if not sid or not isinstance(sid, str):
            continue
        raw_phrases = s.get("phrases")
        if not isinstance(raw_phrases, list):
            raw_phrases = []
        phrases = [p for p in raw_phrases if isinstance(p, str) and p.strip()]
        weight = s.get("weight")
        if not isinstance(weight, (int, float)):
            weight = 10
        rules.append({
            "id": sid.strip(),
            "name": str(s.get("name", sid)),
            "description": str(s.get("description", "")),
            "weight": float(weight),
            "phrases": phrases,
        })
    return rules


def load_signal_weights() -> dict[str, float]:
    """
    Load signal id -> weight map from signals_config.json.

    Returns:
        Dict mapping signal id to weight. Empty if config missing or invalid.
    """
    rules = load_signal_rules()
    return {r["id"]: r["weight"] for r in rules}


def get_default_signal_confidence() -> float:
    """Return default_signal_confidence from config, or package default."""
    path = _find_config_path()
    if path is None:
        return DEFAULT_SIGNAL_CONFIDENCE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SIGNAL_CONFIDENCE
    conf = data.get("default_signal_confidence")
    if isinstance(conf, (int, float)) and 0 <= conf <= 1:
        return float(conf)
    return DEFAULT_SIGNAL_CONFIDENCE


def get_signals_config_version() -> str | None:
    """
    Return the version string from signals_config.json for reproducibility and audit.

    Returns:
        Version string (e.g. "1.0") or None if config missing or no version key.
    """
    path = _find_config_path()
    if path is None:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    v = data.get("version")
    return str(v) if v is not None else None

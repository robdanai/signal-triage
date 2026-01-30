"""
Versioned config semantics for reproducibility.

Defines supported schema versions for:
- signals_config.json (signal rules and weights)
- signals.json (Librarian handoff: trap doors, LME, capital structure)
- settings.json (tiers and merged signal weights)

When loading configs, code validates schema_version and warns or errors on
unsupported versions. Bump versions when making breaking schema changes.
"""

# --- Supported schema versions (exact string match) ---

SUPPORTED_SIGNALS_CONFIG_VERSIONS = ("1.0",)
"""Supported schema_version values for signals_config.json."""

SUPPORTED_SIGNALS_JSON_VERSIONS = ("1.0",)
"""Supported schema_version values for signals.json (Librarian handoff)."""

SUPPORTED_SETTINGS_VERSIONS = ("1.0",)
"""Supported schema_version values for settings.json."""

# --- Default versions (written when creating/updating configs) ---

DEFAULT_SIGNALS_CONFIG_SCHEMA_VERSION = "1.0"
DEFAULT_SIGNALS_JSON_SCHEMA_VERSION = "1.0"
DEFAULT_SETTINGS_SCHEMA_VERSION = "1.0"

# --- Config names (optional human-readable identifiers) ---

SIGNALS_CONFIG_NAME = "distress_signals"
SIGNALS_JSON_CONFIG_NAME = "librarian_handoff"
SETTINGS_CONFIG_NAME = "tiers_and_weights"

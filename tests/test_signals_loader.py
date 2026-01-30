"""Tests for signal_triage.signals_loader (signal rules + weights config)."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.signals_loader import (
    load_signal_rules,
    load_signal_weights,
    get_default_signal_confidence,
)


class TestSignalsLoader(unittest.TestCase):
    def test_load_signal_rules_returns_list(self):
        """load_signal_rules returns a list (from package or cwd config)."""
        rules = load_signal_rules()
        self.assertIsInstance(rules, list)

    def test_load_signal_rules_structure(self):
        """Each rule has id, name, weight, phrases (when config is present)."""
        rules = load_signal_rules()
        if not rules:
            self.skipTest("signals_config.json not found")
        for r in rules:
            self.assertIn("id", r)
            self.assertIn("name", r)
            self.assertIn("weight", r)
            self.assertIn("phrases", r)
            self.assertIsInstance(r["phrases"], list)

    def test_load_signal_rules_distress_types(self):
        """Config includes restructuring/distress signal types when present."""
        rules = load_signal_rules()
        if not rules:
            self.skipTest("signals_config.json not found")
        ids = {r["id"] for r in rules}
        self.assertIn("going_concern", ids)
        self.assertIn("liquidity_covenant", ids)
        self.assertIn("debt_maturity_refinancing", ids)
        self.assertIn("auditor_emphasis", ids)

    def test_load_signal_weights_returns_dict(self):
        """load_signal_weights returns a dict id -> weight."""
        weights = load_signal_weights()
        self.assertIsInstance(weights, dict)

    def test_load_signal_weights_values_numeric(self):
        """Weights are numeric when config is present."""
        weights = load_signal_weights()
        for sid, w in weights.items():
            self.assertIsInstance(sid, str)
            self.assertIsInstance(w, (int, float))

    def test_get_default_signal_confidence_in_range(self):
        """get_default_signal_confidence returns a value in [0, 1]."""
        conf = get_default_signal_confidence()
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)


if __name__ == "__main__":
    unittest.main()

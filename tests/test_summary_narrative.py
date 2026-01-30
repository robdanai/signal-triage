"""Tests for signal_triage.agents.summary_narrative."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.agents.summary_narrative import run_summary_narrative


class TestSummaryNarrative(unittest.TestCase):
    def test_minimal_analysis_result(self):
        """Minimal analysis result produces summary with tier and score."""
        result = {
            "score": 35.0,
            "tier": "medium",
            "tier_label": "Medium distress",
        }
        out = run_summary_narrative(result)
        self.assertIn("summary", out)
        self.assertIn("Medium distress", out["summary"])
        self.assertEqual(out["tier"], "medium")
        self.assertEqual(out["tier_label"], "Medium distress")
        self.assertEqual(out["score"], 35.0)
        self.assertIsInstance(out["risk_highlights"], list)
        self.assertIsInstance(out["analyst_priority"], list)
        self.assertIn("raw", out)
        self.assertIn("signal_types", out["raw"])

    def test_score_from_components_when_missing(self):
        """When score is missing, it is derived from base_score + length_factor."""
        result = {
            "base_score": 20.0,
            "length_factor": 30.0,
            "tier": "medium",
            "tier_label": "Medium distress",
        }
        out = run_summary_narrative(result)
        self.assertEqual(out["score"], 50.0)

    def test_risk_highlights_from_signals(self):
        """Signals with evidence produce risk_highlights."""
        result = {
            "score": 65.0,
            "tier": "high",
            "tier_label": "High distress",
            "lme_signals": [
                {"type": "covenant_risk", "evidence": "covenant breach and waiver requested"},
            ],
            "covenant_signals": [
                {"type": "potential_default", "evidence": "event of default under the facility"},
            ],
        }
        out = run_summary_narrative(result)
        self.assertGreater(len(out["risk_highlights"]), 0)
        self.assertIn("covenant", out["summary"].lower() or "".join(out["risk_highlights"]).lower())

    def test_analyst_priority_from_checklist(self):
        """analyst_checklist in result becomes analyst_priority (up to 5)."""
        result = {
            "score": 50.0,
            "tier": "medium",
            "tier_label": "Medium distress",
            "analyst_checklist": [
                "Confirm event of default and any grace/cure period",
                "Check cross-defaults and cross-acceleration",
                "Review lender group and required consents",
            ],
        }
        out = run_summary_narrative(result)
        self.assertEqual(len(out["analyst_priority"]), 3)
        self.assertIn("event of default", out["analyst_priority"][0])
        self.assertIn("Analyst priority", out["summary"])

    def test_empty_signals_produces_sensible_narrative(self):
        """No signals produces narrative stating no structured distress signals."""
        result = {
            "score": 10.0,
            "tier": "low",
            "tier_label": "Low distress",
            "lme_signals": [],
            "covenant_signals": [],
            "analyst_checklist": [],
        }
        out = run_summary_narrative(result)
        self.assertIn("Low distress", out["summary"])
        self.assertEqual(out["risk_highlights"], [])
        self.assertEqual(out["analyst_priority"], [])


if __name__ == "__main__":
    unittest.main()

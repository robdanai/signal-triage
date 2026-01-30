"""Tests for signal_triage.agents.batch_portfolio."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.agents.batch_portfolio import run_batch_portfolio


class TestBatchPortfolio(unittest.TestCase):
    def test_empty_portfolio(self):
        """Empty business_results returns empty ranked and top_risks with summary."""
        result = run_batch_portfolio([])
        self.assertEqual(result["ranked"], [])
        self.assertEqual(result["top_risks"], [])
        self.assertIn("empty", result["summary"].lower())

    def test_single_business(self):
        """Single business is rank 1 and appears in top_risks."""
        results = [{"id": "Corp A", "score": 45.0}]
        out = run_batch_portfolio(results)
        self.assertEqual(len(out["ranked"]), 1)
        self.assertEqual(out["ranked"][0]["rank"], 1)
        self.assertEqual(out["ranked"][0]["id"], "Corp A")
        self.assertEqual(out["ranked"][0]["score"], 45.0)
        self.assertEqual(len(out["top_risks"]), 1)
        self.assertEqual(out["top_risks"][0]["id"], "Corp A")
        self.assertIn("Corp A", out["summary"])

    def test_ranking_descending_by_score(self):
        """Businesses are ranked by score descending (highest risk first)."""
        results = [
            {"id": "Low", "score": 10.0},
            {"id": "High", "score": 80.0},
            {"id": "Mid", "score": 50.0},
        ]
        out = run_batch_portfolio(results)
        ids_ordered = [r["id"] for r in out["ranked"]]
        self.assertEqual(ids_ordered, ["High", "Mid", "Low"])
        self.assertEqual(out["ranked"][0]["rank"], 1)
        self.assertEqual(out["ranked"][1]["rank"], 2)
        self.assertEqual(out["ranked"][2]["rank"], 3)

    def test_top_n_limits_top_risks(self):
        """top_risks contains at most top_n entries."""
        results = [
            {"id": f"Biz_{i}", "score": float(100 - i)}
            for i in range(15)
        ]
        out = run_batch_portfolio(results, top_n=5)
        self.assertEqual(len(out["ranked"]), 15)
        self.assertEqual(len(out["top_risks"]), 5)
        self.assertEqual(out["top_risks"][0]["id"], "Biz_0")
        self.assertEqual(out["top_risks"][4]["id"], "Biz_4")

    def test_custom_id_and_score_keys(self):
        """Custom id_key and score_key are respected."""
        results = [
            {"name": "Company X", "distress_score": 70.0},
            {"name": "Company Y", "distress_score": 30.0},
        ]
        out = run_batch_portfolio(
            results,
            id_key="name",
            score_key="distress_score",
        )
        self.assertEqual(out["ranked"][0]["name"], "Company X")
        self.assertEqual(out["ranked"][0]["distress_score"], 70.0)
        self.assertEqual(out["top_risks"][0]["id"], "Company X")
        self.assertEqual(out["top_risks"][0]["score"], 70.0)

    def test_signals_included_in_top_risks_when_present(self):
        """When analyzer-style signals are present, top_signal_types appear in top_risks."""
        results = [
            {
                "id": "Risky Co",
                "score": 60.0,
                "lme_signals": [{"type": "uptier_risk"}, {"type": "dropdown_risk"}],
                "covenant_signals": [{"type": "covenant_risk"}],
            },
        ]
        out = run_batch_portfolio(results, top_n=10)
        self.assertEqual(len(out["top_risks"]), 1)
        self.assertIn("top_signal_types", out["top_risks"][0])
        types = out["top_risks"][0]["top_signal_types"]
        self.assertIn("uptier_risk", types)
        self.assertIn("covenant_risk", types)

    def test_tier_label_and_top_signals_in_top_risks_when_present(self):
        """Document-report format: tier_label and top_signals are included in top_risks."""
        results = [
            {
                "id": "/path/to/a.pdf",
                "score": 70.0,
                "tier_label": "High distress",
                "top_signals": [
                    {"type": "going_concern", "evidence": "substantial doubt..."},
                    {"type": "covenant_risk", "evidence": "breach..."},
                ],
            },
        ]
        out = run_batch_portfolio(results, id_key="id", top_n=10)
        self.assertEqual(out["top_risks"][0]["tier_label"], "High distress")
        self.assertEqual(len(out["top_risks"][0]["top_signals"]), 2)
        self.assertEqual(out["top_risks"][0]["top_signals"][0]["type"], "going_concern")


if __name__ == "__main__":
    unittest.main()

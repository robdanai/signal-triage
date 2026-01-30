"""Tests for basket_stacking module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from decimal import Decimal
from signal_triage.basket_stacking import detect_basket_stacks, analyze_basket_interactions


class TestDetectBasketStacks(unittest.TestCase):
    def test_no_baskets(self):
        """Empty baskets: no stacking."""
        result = detect_basket_stacks([])
        self.assertFalse(result["stacks_detected"])
        self.assertEqual(result["max_stack_length"], 0)

    def test_single_basket_no_stacking(self):
        """Single basket: no stacking."""
        baskets = [{"category": "asset_sale", "dollar_limit": "$100M"}]
        result = detect_basket_stacks(baskets)
        self.assertFalse(result["stacks_detected"])

    def test_two_step_stack_asset_sale_to_investment(self):
        """Asset sale → investment basket: 2-step stack (medium)."""
        baskets = [
            {"category": "asset_sale", "dollar_limit": "$100M"},
            {"category": "investment_basket", "dollar_limit": "$50M"},
        ]
        result = detect_basket_stacks(baskets)
        self.assertTrue(result["stacks_detected"])
        self.assertEqual(result["max_stack_length"], 2)
        self.assertEqual(result["stacking_severity"], "medium")
        paths = result["stacking_paths"]
        self.assertGreater(len(paths), 0)
        # Check that asset_sale → investment_basket is in paths
        path_displays = [p["path_display"] for p in paths]
        self.assertIn("asset_sale → investment_basket", path_displays)

    def test_three_step_stack_asset_sale_to_investment_to_unrestricted(self):
        """Asset sale → investment → unrestricted sub: 3-step stack (high)."""
        baskets = [
            {"category": "asset_sale", "dollar_limit": "$100M"},
            {"category": "investment_basket", "dollar_limit": "$50M"},
            {"category": "transfer_to_unrestricted_sub", "dollar_limit": None},
        ]
        result = detect_basket_stacks(baskets)
        self.assertTrue(result["stacks_detected"])
        self.assertEqual(result["max_stack_length"], 3)
        self.assertEqual(result["stacking_severity"], "high")
        # Check for the 3-step path
        three_step = [p for p in result["stacking_paths"] if p["stack_length"] == 3]
        self.assertGreater(len(three_step), 0)
        self.assertIn("transfer_to_unrestricted_sub", three_step[0]["path"])

    def test_leakage_estimate(self):
        """Max leakage estimate = first limit in longest path."""
        baskets = [
            {"category": "asset_sale", "dollar_limit": "$100M"},
            {"category": "investment_basket", "dollar_limit": "$50M"},
        ]
        result = detect_basket_stacks(baskets)
        # Longest path is asset_sale → investment_basket with limit $100M (first step)
        self.assertEqual(result["max_leakage_estimate"], Decimal("100.00"))


class TestAnalyzeBasketInteractions(unittest.TestCase):
    def test_aggregate_leakage_capacity(self):
        """Aggregate leakage = sum of all dollar limits."""
        baskets = [
            {"category": "asset_sale", "dollar_limit": "$100M"},
            {"category": "investment_basket", "dollar_limit": "$50M"},
            {"category": "incremental_facility", "dollar_limit": "$200M"},
        ]
        result = analyze_basket_interactions(baskets)
        # Aggregate = 100 + 50 + 200 = 350
        self.assertEqual(result["aggregate_leakage_capacity"], Decimal("350.00"))

    def test_high_risk_paths_three_plus_steps(self):
        """Paths with 3+ steps are flagged as high risk."""
        baskets = [
            {"category": "asset_sale", "dollar_limit": "$100M"},
            {"category": "investment_basket", "dollar_limit": "$50M"},
            {"category": "transfer_to_unrestricted_sub", "dollar_limit": None},
        ]
        result = analyze_basket_interactions(baskets)
        self.assertGreater(result["high_risk_path_count"], 0)
        high_risk = result["high_risk_paths"]
        self.assertTrue(all(p["stack_length"] >= 3 for p in high_risk))

    def test_forensic_note(self):
        """Forensic note includes stack count, max length, severity."""
        baskets = [
            {"category": "asset_sale", "dollar_limit": "$100M"},
            {"category": "investment_basket", "dollar_limit": "$50M"},
        ]
        result = analyze_basket_interactions(baskets)
        note = result["forensic_note"]
        self.assertIn("Basket stacking detected", note)
        self.assertIn("path(s)", note)
        self.assertIn("Aggregate leakage capacity", note)


if __name__ == "__main__":
    unittest.main()

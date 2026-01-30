"""Tests for covenant_forensics module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from decimal import Decimal
from signal_triage.covenant_forensics import (
    normalize_ebitda,
    calculate_leverage_headroom,
    calculate_fccr_headroom,
    calculate_headroom,
)


class TestNormalizeEBITDA(unittest.TestCase):
    def test_no_addbacks(self):
        result = normalize_ebitda(100, {})
        self.assertEqual(result["reported_ebitda"], Decimal("100.00"))
        self.assertEqual(result["normalized_ebitda"], Decimal("100.00"))
        self.assertEqual(result["haircut_applied"], Decimal("0.00"))

    def test_conservative_addbacks_minimal_haircut(self):
        """One-time charges are 80% credible; 20% haircut."""
        result = normalize_ebitda(100, {"one_time_charges": 10})
        self.assertEqual(result["reported_ebitda"], Decimal("100.00"))
        self.assertEqual(result["total_addbacks"], Decimal("10.00"))
        # Haircut = 10 * (1 - 0.8) = 2
        self.assertEqual(result["haircut_applied"], Decimal("2.00"))
        self.assertEqual(result["normalized_ebitda"], Decimal("98.00"))

    def test_aggressive_addbacks_large_haircut(self):
        """Run-rate synergies are 30% credible; 70% haircut."""
        result = normalize_ebitda(100, {"run_rate_synergies": 20})
        self.assertEqual(result["aggressive_addbacks"], Decimal("20.00"))
        # Haircut = 20 * (1 - 0.3) = 14
        self.assertEqual(result["haircut_applied"], Decimal("14.00"))
        self.assertEqual(result["normalized_ebitda"], Decimal("86.00"))

    def test_mixed_addbacks(self):
        """Mix of conservative and aggressive add-backs."""
        result = normalize_ebitda(
            100,
            {
                "one_time_charges": 5,  # 20% haircut = 1
                "run_rate_synergies": 10,  # 70% haircut = 7
                "anticipated_savings": 10,  # 80% haircut = 8
            },
        )
        self.assertEqual(result["total_addbacks"], Decimal("25.00"))
        self.assertEqual(result["aggressive_addbacks"], Decimal("20.00"))
        # Total haircut = 1 + 7 + 8 = 16
        self.assertEqual(result["haircut_applied"], Decimal("16.00"))
        self.assertEqual(result["normalized_ebitda"], Decimal("84.00"))

    def test_no_haircut_mode(self):
        """When aggressiveness_haircut=False, no haircut applied."""
        result = normalize_ebitda(
            100, {"run_rate_synergies": 20}, aggressiveness_haircut=False
        )
        self.assertEqual(result["haircut_applied"], Decimal("0.00"))
        self.assertEqual(result["normalized_ebitda"], Decimal("100.00"))


class TestLeverageHeadroom(unittest.TestCase):
    def test_healthy_headroom(self):
        """Leverage 5.0x vs covenant 6.0x: 16.7% headroom (healthy)."""
        result = calculate_leverage_headroom(
            normalized_ebitda=100, total_debt=500, leverage_covenant=6.0
        )
        self.assertEqual(result["actual_leverage"], Decimal("5.00"))
        self.assertEqual(result["covenant_leverage"], Decimal("6.00"))
        self.assertEqual(result["headroom_pct"], Decimal("16.67"))
        self.assertFalse(result["critical_distress"])

    def test_critical_headroom(self):
        """Leverage 5.5x vs covenant 6.0x: 8.3% headroom (critical)."""
        result = calculate_leverage_headroom(
            normalized_ebitda=100, total_debt=550, leverage_covenant=6.0
        )
        self.assertEqual(result["actual_leverage"], Decimal("5.50"))
        self.assertEqual(result["headroom_pct"], Decimal("8.33"))
        self.assertTrue(result["critical_distress"])

    def test_breach(self):
        """Leverage 6.5x vs covenant 6.0x: negative headroom (breach)."""
        result = calculate_leverage_headroom(
            normalized_ebitda=100, total_debt=650, leverage_covenant=6.0
        )
        self.assertEqual(result["actual_leverage"], Decimal("6.50"))
        self.assertLess(result["headroom_pct"], Decimal("0"))
        self.assertTrue(result["critical_distress"])

    def test_zero_ebitda(self):
        """EBITDA zero or negative: always critical."""
        result = calculate_leverage_headroom(
            normalized_ebitda=0, total_debt=100, leverage_covenant=6.0
        )
        self.assertEqual(result["actual_leverage"], "N/A (EBITDA <= 0)")
        self.assertTrue(result["critical_distress"])


class TestFCCRHeadroom(unittest.TestCase):
    def test_healthy_fccr(self):
        """FCCR 1.5x vs covenant 1.1x: 36.4% headroom (healthy)."""
        result = calculate_fccr_headroom(
            normalized_ebitda=100,
            cash_interest=50,
            capex=25,
            fccr_covenant=1.1,
        )
        # FCCR = (100 - 25) / 50 = 1.5x
        self.assertEqual(result["actual_fccr"], Decimal("1.50"))
        self.assertEqual(result["covenant_fccr"], Decimal("1.10"))
        self.assertEqual(result["headroom_pct"], Decimal("36.36"))
        self.assertFalse(result["critical_distress"])

    def test_critical_fccr(self):
        """FCCR 1.15x vs covenant 1.1x: 4.5% headroom (critical)."""
        result = calculate_fccr_headroom(
            normalized_ebitda=100,
            cash_interest=50,
            capex=42.5,  # (100 - 42.5) / 50 = 1.15x
            fccr_covenant=1.1,
        )
        self.assertEqual(result["actual_fccr"], Decimal("1.15"))
        self.assertEqual(result["headroom_pct"], Decimal("4.55"))
        self.assertTrue(result["critical_distress"])

    def test_fccr_breach(self):
        """FCCR 0.9x vs covenant 1.1x: negative headroom (breach)."""
        result = calculate_fccr_headroom(
            normalized_ebitda=100,
            cash_interest=50,
            capex=55,  # (100 - 55) / 50 = 0.9x
            fccr_covenant=1.1,
        )
        self.assertEqual(result["actual_fccr"], Decimal("0.90"))
        self.assertLess(result["headroom_pct"], Decimal("0"))
        self.assertTrue(result["critical_distress"])


class TestFullHeadroomCalculation(unittest.TestCase):
    def test_healthy_company(self):
        """Conservative add-backs, healthy leverage and FCCR."""
        result = calculate_headroom(
            reported_ebitda=100,
            addbacks={"one_time_charges": 5},
            total_debt=500,
            leverage_covenant=6.0,
            cash_interest=50,
            capex=20,
            fccr_covenant=1.1,
        )
        # Normalized EBITDA = 100 - (5 * 0.2) = 99
        norm = result["normalized_ebitda_analysis"]
        self.assertEqual(norm["normalized_ebitda"], Decimal("99.00"))

        # Leverage = 500 / 99 = 5.05x; headroom = (6.0 - 5.05) / 6.0 = 15.8%
        lev = result["leverage_analysis"]
        self.assertGreater(lev["headroom_pct"], Decimal("15"))
        self.assertFalse(lev["critical_distress"])

        # FCCR = (99 - 20) / 50 = 1.58x; headroom = (1.58 - 1.1) / 1.1 = 43.6%
        fccr = result["fccr_analysis"]
        self.assertGreater(fccr["headroom_pct"], Decimal("30"))
        self.assertFalse(fccr["critical_distress"])

        self.assertFalse(result["overall_critical_distress"])

    def test_critical_distress_aggressive_addbacks(self):
        """Aggressive add-backs strip EBITDA; leverage headroom critical."""
        result = calculate_headroom(
            reported_ebitda=100,
            addbacks={
                "run_rate_synergies": 20,  # 70% haircut = 14
                "anticipated_savings": 10,  # 80% haircut = 8
            },
            total_debt=520,
            leverage_covenant=6.0,
        )
        # Normalized EBITDA = 100 - 14 - 8 = 78
        norm = result["normalized_ebitda_analysis"]
        self.assertEqual(norm["normalized_ebitda"], Decimal("78.00"))
        self.assertEqual(norm["aggressive_addbacks"], Decimal("30.00"))

        # Leverage = 520 / 78 = 6.67x; headroom = (6.0 - 6.67) / 6.0 = -11.1% (breach)
        lev = result["leverage_analysis"]
        self.assertLess(lev["headroom_pct"], Decimal("0"))
        self.assertTrue(lev["critical_distress"])

        self.assertTrue(result["overall_critical_distress"])

    def test_fccr_critical_leverage_healthy(self):
        """Leverage healthy but FCCR critical: overall critical."""
        result = calculate_headroom(
            reported_ebitda=100,
            addbacks={},
            total_debt=400,  # Leverage 4.0x vs 6.0x: healthy
            leverage_covenant=6.0,
            cash_interest=50,
            capex=43,  # FCCR = (100 - 43) / 50 = 1.14x vs 1.1x: 3.6% headroom (critical)
            fccr_covenant=1.1,
        )
        lev = result["leverage_analysis"]
        self.assertFalse(lev["critical_distress"])

        fccr = result["fccr_analysis"]
        self.assertTrue(fccr["critical_distress"])

        # Overall critical if ANY covenant critical
        self.assertTrue(result["overall_critical_distress"])


if __name__ == "__main__":
    unittest.main()

"""
Tests for Monte Carlo simulation engine.
"""

import unittest
from decimal import Decimal

from signal_triage.monte_carlo import (
    run_monte_carlo,
    MonteCarloParams,
    export_monte_carlo_summary,
    generate_risk_heatmap_data,
)


class TestMonteCarlo(unittest.TestCase):
    """Test Monte Carlo simulation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tranches = [
            {"name": "Senior Secured", "claim": 100, "tier": 1},
            {"name": "Mezzanine", "claim": 75, "tier": 2},
            {"name": "Unsecured", "claim": 50, "tier": 3},
        ]

    def test_monte_carlo_basic(self):
        """Test basic Monte Carlo simulation runs without errors."""
        params = MonteCarloParams(
            n_simulations=100,  # Small number for testing
            ev_mean=150.0,
            ev_std=30.0,
            seed=42,  # For reproducibility
        )

        result = run_monte_carlo(self.tranches, params)

        # Check result structure
        self.assertEqual(len(result.scenarios), 100)
        self.assertEqual(len(result.tranche_statistics), 3)
        self.assertIsInstance(result.fulcrum_probabilities, dict)

    def test_monte_carlo_statistics(self):
        """Test that statistics are calculated correctly."""
        params = MonteCarloParams(
            n_simulations=1000,
            ev_mean=150.0,
            ev_std=20.0,
            leakage_probability=0.0,  # No leakage for simplicity
            seed=42,
        )

        result = run_monte_carlo(self.tranches, params)

        # Check first tranche (Senior) statistics
        senior_stats = result.tranche_statistics[0]
        self.assertEqual(senior_stats["tranche"], "Senior Secured")

        # Senior should have high recovery in most scenarios
        self.assertGreater(senior_stats["mean_recovery"], 80.0)

        # Check that percentiles are in order
        self.assertLessEqual(senior_stats["p10_recovery"], senior_stats["median_recovery"])
        self.assertLessEqual(senior_stats["median_recovery"], senior_stats["p90_recovery"])

        # Par probability should be a valid probability
        self.assertGreaterEqual(senior_stats["par_probability"], 0.0)
        self.assertLessEqual(senior_stats["par_probability"], 1.0)

    def test_monte_carlo_with_leakage(self):
        """Test Monte Carlo with collateral leakage."""
        params = MonteCarloParams(
            n_simulations=1000,
            ev_mean=150.0,
            ev_std=20.0,
            leakage_probability=0.5,  # 50% chance of leakage
            leakage_mean_pct=0.2,  # 20% average leakage
            seed=42,
        )

        result = run_monte_carlo(self.tranches, params)

        # Check that some scenarios have leakage
        leakage_count = sum(1 for s in result.scenarios if s["leakage_occurred"])
        self.assertGreater(leakage_count, 0)

        # Recoveries should be lower with leakage
        senior_stats = result.tranche_statistics[0]
        self.assertLess(senior_stats["mean_recovery"], 100.0)

    def test_monte_carlo_fulcrum_probabilities(self):
        """Test that fulcrum probabilities sum to ~1.0."""
        params = MonteCarloParams(
            n_simulations=1000,
            ev_mean=150.0,
            ev_std=30.0,
            seed=42,
        )

        result = run_monte_carlo(self.tranches, params)

        # Sum of fulcrum probabilities should be close to 1.0
        total_prob = sum(result.fulcrum_probabilities.values())
        self.assertAlmostEqual(total_prob, 1.0, delta=0.01)

        # All probabilities should be valid
        for prob in result.fulcrum_probabilities.values():
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)

    def test_export_monte_carlo_summary(self):
        """Test export of Monte Carlo results."""
        params = MonteCarloParams(n_simulations=100, seed=42)
        result = run_monte_carlo(self.tranches, params)

        summary = export_monte_carlo_summary(result)

        # Check summary structure
        self.assertIn("n_simulations", summary)
        self.assertIn("params", summary)
        self.assertIn("tranche_statistics", summary)
        self.assertIn("fulcrum_probabilities", summary)

        self.assertEqual(summary["n_simulations"], 100)
        self.assertEqual(len(summary["tranche_statistics"]), 3)

    def test_generate_risk_heatmap_data(self):
        """Test risk heatmap data generation."""
        heatmap_data = generate_risk_heatmap_data(
            self.tranches,
            ev_range=(100, 200),
            leakage_range=(0, 0.3),
            n_points=5,  # Small grid for testing
        )

        # Should have data points for each tranche at each grid point
        # 5x5 grid = 25 points per tranche, 3 tranches = 75 total
        self.assertEqual(len(heatmap_data), 5 * 5 * 3)

        # Check structure of first data point
        first_point = heatmap_data[0]
        self.assertIn("ev", first_point)
        self.assertIn("leakage_pct", first_point)
        self.assertIn("tranche", first_point)
        self.assertIn("recovery_pct", first_point)

        # Check that recovery_pct is valid
        for point in heatmap_data:
            self.assertGreaterEqual(point["recovery_pct"], 0.0)
            self.assertLessEqual(point["recovery_pct"], 100.0)

    def test_monte_carlo_with_ebitda_multiple(self):
        """Test Monte Carlo using EBITDA multiple instead of direct EV."""
        params = MonteCarloParams(
            n_simulations=100,
            multiple_mean=8.0,
            multiple_std=2.0,
            seed=42,
        )

        result = run_monte_carlo(
            self.tranches,
            params,
            use_ebitda_multiple=True,
            base_ebitda=20.0,
        )

        # Check that scenarios have multiple field
        first_scenario = result.scenarios[0]
        self.assertIn("multiple", first_scenario)
        self.assertIn("ebitda", first_scenario)

        # EV should be ebitda * multiple
        self.assertAlmostEqual(
            first_scenario["ev"],
            first_scenario["ebitda"] * first_scenario["multiple"],
            delta=0.01
        )

    def test_monte_carlo_edge_cases(self):
        """Test Monte Carlo with edge cases."""
        # Very low EV mean
        params_low = MonteCarloParams(
            n_simulations=100,
            ev_mean=10.0,
            ev_std=5.0,
            seed=42,
        )

        result_low = run_monte_carlo(self.tranches, params_low)
        self.assertEqual(len(result_low.scenarios), 100)

        # Very high leakage
        params_high_leak = MonteCarloParams(
            n_simulations=100,
            ev_mean=150.0,
            leakage_probability=1.0,  # Always leaks
            leakage_mean_pct=0.4,  # 40% leakage
            seed=42,
        )

        result_high_leak = run_monte_carlo(self.tranches, params_high_leak)

        # All scenarios should have leakage
        leakage_count = sum(1 for s in result_high_leak.scenarios if s["leakage_occurred"])
        self.assertEqual(leakage_count, 100)

    def test_monte_carlo_reproducibility(self):
        """Test that same seed produces same results."""
        params1 = MonteCarloParams(n_simulations=100, seed=12345)
        params2 = MonteCarloParams(n_simulations=100, seed=12345)

        result1 = run_monte_carlo(self.tranches, params1)
        result2 = run_monte_carlo(self.tranches, params2)

        # First scenario should be identical
        self.assertAlmostEqual(
            result1.scenarios[0]["ev"],
            result2.scenarios[0]["ev"],
            delta=0.001
        )


if __name__ == "__main__":
    unittest.main()

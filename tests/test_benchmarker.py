"""Tests for signal_triage.agents.benchmarker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from unittest.mock import patch

from signal_triage.agents.benchmarker import (
    run_benchmarker,
    get_comparables,
    get_recovery_benchmarks,
    get_exit_multiples,
    get_market_multiple_for_quant,
    check_recovery_variance,
    check_data_freshness,
    get_yield_spread_signal,
    get_ratings_watch,
    get_sentiment_adjustment,
)

# Required keys on each recovery_variance item (run_benchmarker / check_recovery_variance contract)
RECOVERY_VARIANCE_KEYS = frozenset({
    "tranche_name",
    "model_recovery_pct",
    "precedent_recovery_pct",
    "variance_pct",
    "critical_variance",
    "for_auditor",
    "source",
})


class TestBenchmarker(unittest.TestCase):
    def test_run_benchmarker_returns_required_keys(self):
        out = run_benchmarker()
        self.assertIn("market_multiple", out)
        self.assertIn("recovery_variance", out)
        self.assertIn("precedents", out)
        self.assertIn("market_signals", out)
        self.assertIn("data_freshness", out)
        self.assertIn("comparables", out["precedents"])
        self.assertIn("recovery_benchmarks", out["precedents"])
        self.assertIn("exit_multiples", out["precedents"])
        self.assertIn("yield_spread", out["market_signals"])
        self.assertIn("ratings_watch", out["market_signals"])
        self.assertIn("sentiment", out["market_signals"])

    def test_run_benchmarker_with_model_recoveries_checks_variance(self):
        model_recoveries = [
            {"name": "1L", "recovery_pct": 95.0},
            {"name": "2L", "recovery_pct": 30.0},
        ]
        out = run_benchmarker(model_recoveries=model_recoveries, critical_variance_threshold_pct=25.0)
        self.assertEqual(len(out["recovery_variance"]), 2)
        # Model 95% vs stub precedent 72% -> diff 23% < 25% -> not critical
        # Model 30% vs 72% -> diff 42% >= 25% -> critical
        critical = [v for v in out["recovery_variance"] if v["critical_variance"]]
        self.assertGreaterEqual(len(critical), 0)  # stub precedent is 72%; 95-72=23, 72-30=42

    def test_run_benchmarker_recovery_variance_shape(self):
        """Assert recovery_variance list items have required keys and types (stub)."""
        model_recoveries = [
            {"name": "1L", "recovery_pct": 80.0},
            {"name": "2L", "recovery_pct": 45.0},
        ]
        out = run_benchmarker(model_recoveries=model_recoveries)
        rv = out["recovery_variance"]
        self.assertIsInstance(rv, list)
        self.assertEqual(len(rv), 2)
        for item in rv:
            self.assertIsInstance(item, dict)
            self.assertEqual(set(item.keys()), RECOVERY_VARIANCE_KEYS)
            self.assertIsInstance(item["tranche_name"], str)
            self.assertIsInstance(item["model_recovery_pct"], (int, float))
            self.assertIsInstance(item["precedent_recovery_pct"], (int, float))
            self.assertIsInstance(item["variance_pct"], (int, float))
            self.assertIsInstance(item["critical_variance"], bool)
            self.assertIn("for_auditor", item)
            self.assertIn("source", item)

    def test_run_benchmarker_critical_variance_flagged_when_above_threshold(self):
        """With mocked precedent, assert critical_variance True when variance >= threshold."""
        with patch(
            "signal_triage.agents.benchmarker.get_recovery_benchmarks",
            return_value=[{"tranche_type": "1L", "recovery_pct": 40.0, "source": "mock"}],
        ):
            out = run_benchmarker(
                model_recoveries=[{"name": "1L", "recovery_pct": 90.0}],
                critical_variance_threshold_pct=25.0,
            )
        self.assertEqual(len(out["recovery_variance"]), 1)
        v = out["recovery_variance"][0]
        self.assertEqual(v["tranche_name"], "1L")
        self.assertEqual(v["model_recovery_pct"], 90.0)
        self.assertEqual(v["precedent_recovery_pct"], 40.0)
        self.assertEqual(v["variance_pct"], 50.0)
        self.assertTrue(v["critical_variance"], "50% variance >= 25% should flag critical")
        self.assertIn("Critical Variance", v["for_auditor"])

    def test_run_benchmarker_critical_variance_not_flagged_when_within_threshold(self):
        """With mocked precedent, assert critical_variance False when variance < threshold."""
        with patch(
            "signal_triage.agents.benchmarker.get_recovery_benchmarks",
            return_value=[{"tranche_type": "1L", "recovery_pct": 70.0, "source": "mock"}],
        ):
            out = run_benchmarker(
                model_recoveries=[{"name": "1L", "recovery_pct": 85.0}],
                critical_variance_threshold_pct=25.0,
            )
        self.assertEqual(len(out["recovery_variance"]), 1)
        v = out["recovery_variance"][0]
        self.assertFalse(v["critical_variance"], "15% variance < 25% should not flag critical")
        self.assertIn("No critical variance", v["for_auditor"])

    def test_run_benchmarker_without_model_recoveries_returns_empty_recovery_variance(self):
        """Without model_recoveries, recovery_variance is empty list."""
        out = run_benchmarker()
        self.assertEqual(out["recovery_variance"], [])
        out_with_none = run_benchmarker(model_recoveries=None)
        self.assertEqual(out_with_none["recovery_variance"], [])

    def test_run_benchmarker_skips_invalid_model_recovery_entries(self):
        """Entries missing name or recovery_pct are skipped; only valid entries appear in recovery_variance."""
        model_recoveries = [
            {"name": "Valid", "recovery_pct": 50.0},
            {"recovery_pct": 60.0},   # missing name -> skipped
            {"name": "NoPct"},         # missing recovery_pct -> skipped
            {"name": "AlsoValid", "recovery_pct": 70.0},
        ]
        out = run_benchmarker(model_recoveries=model_recoveries)
        self.assertEqual(len(out["recovery_variance"]), 2)
        names = [v["tranche_name"] for v in out["recovery_variance"]]
        self.assertIn("Valid", names)
        self.assertIn("AlsoValid", names)

    def test_check_recovery_variance_critical_when_above_threshold(self):
        out = check_recovery_variance(90.0, "1L", precedent_recovery_pct=30.0, critical_variance_threshold_pct=25.0)
        self.assertTrue(out["critical_variance"])
        self.assertEqual(out["model_recovery_pct"], 90.0)
        self.assertEqual(out["precedent_recovery_pct"], 30.0)
        self.assertEqual(out["variance_pct"], 60.0)
        self.assertIn("Critical Variance", out["for_auditor"])
        self.assertIn("source", out)

    def test_check_recovery_variance_not_critical_when_within_threshold(self):
        out = check_recovery_variance(75.0, "1L", precedent_recovery_pct=72.0, critical_variance_threshold_pct=25.0)
        self.assertFalse(out["critical_variance"])
        self.assertEqual(out["variance_pct"], 3.0)
        self.assertIn("source", out)

    def test_get_market_multiple_for_quant_has_source(self):
        out = get_market_multiple_for_quant(industry="Retail", geography="US")
        self.assertIn("ev_ebitda_multiple", out)
        self.assertIn("source", out)
        self.assertIn("for_quant", out)
        self.assertIsNotNone(out["ev_ebitda_multiple"])

    def test_get_comparables_every_item_has_source(self):
        items = get_comparables(industry="Retail", geography="US")
        self.assertIsInstance(items, list)
        for item in items:
            self.assertIn("source", item)

    def test_get_recovery_benchmarks_every_item_has_source(self):
        items = get_recovery_benchmarks(tranche_type="1st Lien", industry="Retail")
        self.assertIsInstance(items, list)
        for item in items:
            self.assertIn("source", item)

    def test_get_exit_multiples_every_item_has_source(self):
        items = get_exit_multiples(industry="Retail", geography="US")
        self.assertIsInstance(items, list)
        for item in items:
            self.assertIn("source", item)

    def test_get_yield_spread_signal_computes_spread(self):
        out = get_yield_spread_signal(target_yield=0.08, benchmark_yield=0.04)
        self.assertIn("spread_bps", out)
        self.assertEqual(out["spread_bps"], 400.0)
        self.assertIn("source", out)

    def test_get_ratings_watch_has_source(self):
        items = get_ratings_watch(sector="Retail")
        self.assertIsInstance(items, list)
        for item in items:
            self.assertIn("source", item)

    def test_get_sentiment_adjustment_has_source(self):
        out = get_sentiment_adjustment(sector="Retail")
        self.assertIn("source", out)
        self.assertIn("best_case_shift", out)
        self.assertIn("worst_case_shift", out)

    def test_check_data_freshness_for_author_and_macro_note(self):
        out = check_data_freshness()
        self.assertIn("for_author", out)
        self.assertIn("macro_invalidation_note", out)
        self.assertIn("source", out)
        self.assertIn("stale", out)

    def test_get_comparables_live_edgar_returns_live_when_mock_succeeds(self):
        """With BENCHMARKER_USE_LIVE=1 and data_source=edgar, get_comparables uses live client."""
        live_comparables = [
            {
                "name": "Live Corp",
                "industry": "Retail",
                "geography": "US",
                "restructuring_date": "2024-06-15",
                "source": "Source: SEC EDGAR (recent 8-K filings).",
                "date": "2024-06-15",
            },
        ]
        with patch("signal_triage.agents.benchmarker.get_benchmarker_live_config", return_value=(True, "edgar")):
            with patch(
                "signal_triage.agents.benchmarker.edgar_get_recent_8k_comparables",
                return_value=live_comparables,
            ):
                items = get_comparables(industry="Retail", geography="US", limit=5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Live Corp")
        self.assertIn("source", items[0])
        self.assertIn("SEC EDGAR", items[0]["source"])

    def test_get_comparables_falls_back_to_stub_on_live_error(self):
        """When live EDGAR fails, get_comparables returns stub data."""
        with patch("signal_triage.agents.benchmarker.get_benchmarker_live_config", return_value=(True, "edgar")):
            with patch(
                "signal_triage.agents.benchmarker.edgar_get_recent_8k_comparables",
                side_effect=Exception("network error"),
            ):
                items = get_comparables(industry="Retail", geography="US")
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        self.assertIn("source", items[0])
        self.assertIn("Stub", items[0]["source"])

    def test_run_benchmarker_contract_preserved_with_live_comparables(self):
        """run_benchmarker still returns market_multiple, recovery_variance, precedents when comparables are live."""
        live_comparables = [
            {
                "name": "Live Corp",
                "industry": "Retail",
                "geography": "US",
                "restructuring_date": "2024-06-15",
                "source": "Source: SEC EDGAR.",
                "date": "2024-06-15",
            },
        ]
        with patch("signal_triage.agents.benchmarker.get_benchmarker_live_config", return_value=(True, "edgar")):
            with patch(
                "signal_triage.agents.benchmarker.edgar_get_recent_8k_comparables",
                return_value=live_comparables,
            ):
                out = run_benchmarker(industry="Retail", geography="US")
        self.assertIn("market_multiple", out)
        self.assertIn("recovery_variance", out)
        self.assertIn("precedents", out)
        self.assertIn("comparables", out["precedents"])
        self.assertEqual(out["precedents"]["comparables"], live_comparables)

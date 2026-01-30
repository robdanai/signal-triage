"""Tests for signal_triage.recovery_engine."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from decimal import Decimal

from signal_triage.recovery_engine import (
    run_waterfall,
    run_waterfall_from_signals,
    ev_sensitivity,
    tornado_drivers,
    _detect_apr_violations,
)


class TestRecoveryEngine(unittest.TestCase):
    def test_empty_tranches(self):
        out = run_waterfall([], 100.0)
        self.assertEqual(out["recoveries"], [])
        self.assertIsNone(out["fulcrum_security"])
        self.assertIsInstance(out["ev_used"], Decimal)
        self.assertIsInstance(out["ev_remaining"], Decimal)
        self.assertEqual(out["ev_used"], Decimal("0"))
        self.assertEqual(out["ev_remaining"], Decimal("100"))

    def test_zero_ev(self):
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 50}]
        out = run_waterfall(tranches, 0)
        self.assertEqual(out["ev_used"], 0.0)
        self.assertEqual(out["ev_remaining"], 0.0)
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 0.0)
        self.assertEqual(out["recoveries"][1]["recovery_pct"], 0.0)
        self.assertEqual(out["fulcrum_security"], "Senior")

    def test_ev_covers_all(self):
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 50}]
        out = run_waterfall(tranches, 200)
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 100.0)
        self.assertEqual(out["recoveries"][1]["recovery_pct"], 100.0)
        self.assertIsNone(out["fulcrum_security"])  # no partial tranche

    def test_fulcrum_partial_recovery(self):
        tranches = [
            {"name": "Senior", "claim": 100},
            {"name": "Mezz", "claim": 100},
            {"name": "Unsecured", "claim": 100},
        ]
        out = run_waterfall(tranches, 150)  # Senior 100%, Mezz 50%, Unsecured 0%
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 100.0)
        self.assertEqual(out["recoveries"][1]["recovery_pct"], 50.0)
        self.assertEqual(out["recoveries"][2]["recovery_pct"], 0.0)
        self.assertEqual(out["fulcrum_security"], "Mezz")

    def test_negative_ev_treated_as_zero(self):
        tranches = [{"name": "Senior", "claim": 50}]
        out = run_waterfall(tranches, -10)
        self.assertEqual(out["ev_used"], 0.0)
        self.assertEqual(out["ev_remaining"], 0.0)
        self.assertEqual(out["recoveries"][0]["recovered"], 0.0)

    def test_recoveries_have_required_keys(self):
        tranches = [{"name": "A", "claim": 50}]
        out = run_waterfall(tranches, 25)
        for r in out["recoveries"]:
            self.assertIn("name", r)
            self.assertIn("claim", r)
            self.assertIn("recovered", r)
            self.assertIn("recovery_pct", r)
            self.assertIsInstance(r["claim"], Decimal)
            self.assertIsInstance(r["recovered"], Decimal)
            self.assertIsInstance(r["recovery_pct"], Decimal)

    def test_run_waterfall_from_signals(self):
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 50}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"capital_structure": {"tranches": tranches, "default_ev": 120}}, f)
            path = f.name
        try:
            out = run_waterfall_from_signals(path)
            self.assertIsNotNone(out)
            self.assertEqual(out["fulcrum_security"], "Unsecured")
            self.assertEqual(out["recoveries"][0]["recovery_pct"], 100.0)
            self.assertEqual(out["recoveries"][1]["recovery_pct"], 40.0)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_run_waterfall_from_signals_ev_override(self):
        tranches = [{"name": "Senior", "claim": 100}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"capital_structure": {"tranches": tranches, "default_ev": 200}}, f)
            path = f.name
        try:
            out = run_waterfall_from_signals(path, ev_override=50)
            self.assertIsNotNone(out)
            self.assertEqual(out["recoveries"][0]["recovered"], 50.0)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_run_waterfall_from_signals_missing_capital_structure_returns_none(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"trap_doors": [], "lme_signals": []}, f)
            path = f.name
        try:
            self.assertIsNone(run_waterfall_from_signals(path))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_ev_sensitivity(self):
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 100}]
        results = ev_sensitivity(tranches, ev_base=150, ev_step=50.0, steps=2)
        self.assertEqual(len(results), 5)
        self.assertIsInstance(results[2]["ev"], Decimal)
        self.assertEqual(results[2]["ev"], Decimal("150"))
        self.assertEqual(results[2]["result"]["fulcrum_security"], "Unsecured")

    def test_exact_math_millions_ev_used_plus_remaining_equals_ev(self):
        """Credit Integrity: ev_used + ev_remaining must equal EV (exact arithmetic)."""
        tranches = [
            {"name": "1L", "claim": 1_000_000.10},
            {"name": "2L", "claim": 2_000_000.20},
            {"name": "Unsecured", "claim": 3_000_000.30},
        ]
        ev = 6_000_000.60
        out = run_waterfall(tranches, ev)
        self.assertAlmostEqual(out["ev_used"] + out["ev_remaining"], ev, places=2)
        total_recovered = sum(r["recovered"] for r in out["recoveries"])
        self.assertAlmostEqual(total_recovered, out["ev_used"], places=2)

    def test_pari_passu_pro_rata_recovery(self):
        """Credit Integrity: same-tier tranches get pro-rata recovery (Pari Passu)."""
        tranches = [
            {"name": "1L", "claim": 400, "tier": 0},
            {"name": "2L_PariPassu", "claim": 100, "tier": 0},
            {"name": "Unsecured", "claim": 200, "tier": 1},
        ]
        out = run_waterfall(tranches, 400)  # EV=400: 1L+2L share pro-rata 80% each
        self.assertEqual(out["recoveries"][0]["recovered"], 320.0)  # 80% of 400
        self.assertEqual(out["recoveries"][1]["recovered"], 80.0)   # 80% of 100
        self.assertEqual(out["recoveries"][2]["recovered"], 0.0)
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 80.0)
        self.assertEqual(out["recoveries"][1]["recovery_pct"], 80.0)

    # --- Edge cases: empty tranches, single tranche, LME adjustment boundary ---

    def test_empty_tranches_from_signals_returns_none(self):
        """run_waterfall_from_signals returns None when capital_structure has empty tranches."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "capital_structure": {"tranches": [], "default_ev": 100},
            }, f)
            path = f.name
        try:
            self.assertIsNone(run_waterfall_from_signals(path))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_single_tranche_ev_below_claim(self):
        """Single tranche with EV < claim: partial recovery, fulcrum is that tranche."""
        tranches = [{"name": "Senior", "claim": 100}]
        out = run_waterfall(tranches, 40)
        self.assertEqual(len(out["recoveries"]), 1)
        self.assertEqual(out["recoveries"][0]["recovered"], 40.0)
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 40.0)
        self.assertEqual(out["fulcrum_security"], "Senior")
        self.assertEqual(out["ev_used"], 40.0)
        self.assertEqual(out["ev_remaining"], 0.0)

    def test_single_tranche_ev_equals_claim(self):
        """Single tranche with EV = claim: 100% recovery, no fulcrum."""
        tranches = [{"name": "Senior", "claim": 100}]
        out = run_waterfall(tranches, 100)
        self.assertEqual(out["recoveries"][0]["recovered"], 100.0)
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 100.0)
        self.assertIsNone(out["fulcrum_security"])
        self.assertEqual(out["ev_used"], 100.0)
        self.assertEqual(out["ev_remaining"], 0.0)

    def test_single_tranche_ev_above_claim(self):
        """Single tranche with EV > claim: 100% recovery, ev_remaining = EV - claim."""
        tranches = [{"name": "Senior", "claim": 100}]
        out = run_waterfall(tranches, 150)
        self.assertEqual(out["recoveries"][0]["recovered"], 100.0)
        self.assertEqual(out["recoveries"][0]["recovery_pct"], 100.0)
        self.assertIsNone(out["fulcrum_security"])
        self.assertEqual(out["ev_used"], 100.0)
        self.assertEqual(out["ev_remaining"], 50.0)

    def test_lme_adjustment_zero_ev_unchanged(self):
        """LME adjustment 0: EV unchanged, no collateral_leakage_ev_adjustment in result."""
        tranches = [{"name": "Senior", "claim": 100}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "capital_structure": {"tranches": tranches, "default_ev": 80},
            }, f)
            path = f.name
        try:
            out = run_waterfall_from_signals(path, collateral_leakage_ev_adjustment=0)
            self.assertIsNotNone(out)
            self.assertEqual(out["ev_used"], 80.0)
            self.assertEqual(out["ev_remaining"], 0.0)
            self.assertNotIn("collateral_leakage_ev_adjustment", out)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_lme_adjustment_reduces_ev(self):
        """LME adjustment > 0 and < EV: EV reduced by adjustment before waterfall."""
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 50}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "capital_structure": {"tranches": tranches, "default_ev": 120},
            }, f)
            path = f.name
        try:
            out = run_waterfall_from_signals(path, collateral_leakage_ev_adjustment=20)
            self.assertIsNotNone(out)
            # Effective EV = 120 - 20 = 100; Senior gets 100%, Unsecured 0%
            self.assertEqual(out["ev_used"], 100.0)
            self.assertEqual(out["recoveries"][0]["recovery_pct"], 100.0)
            self.assertEqual(out["recoveries"][1]["recovery_pct"], 0.0)
            self.assertEqual(out["collateral_leakage_ev_adjustment"], 20.0)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_lme_adjustment_equals_ev_ev_becomes_zero(self):
        """LME adjustment = EV: effective EV becomes 0, all recoveries 0."""
        tranches = [{"name": "Senior", "claim": 100}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "capital_structure": {"tranches": tranches, "default_ev": 50},
            }, f)
            path = f.name
        try:
            out = run_waterfall_from_signals(path, collateral_leakage_ev_adjustment=50)
            self.assertIsNotNone(out)
            self.assertEqual(out["ev_used"], 0.0)
            self.assertEqual(out["ev_remaining"], 0.0)
            self.assertEqual(out["recoveries"][0]["recovered"], 0.0)
            self.assertEqual(out["recoveries"][0]["recovery_pct"], 0.0)
            self.assertEqual(out["fulcrum_security"], "Senior")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_lme_adjustment_exceeds_ev_clamped_to_zero(self):
        """LME adjustment > EV: effective EV clamped to 0 (no negative EV)."""
        tranches = [{"name": "Senior", "claim": 100}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "capital_structure": {"tranches": tranches, "default_ev": 30},
            }, f)
            path = f.name
        try:
            out = run_waterfall_from_signals(path, collateral_leakage_ev_adjustment=100)
            self.assertIsNotNone(out)
            self.assertEqual(out["ev_used"], 0.0)
            self.assertEqual(out["ev_remaining"], 0.0)
            self.assertEqual(out["recoveries"][0]["recovered"], 0.0)
        finally:
            Path(path).unlink(missing_ok=True)

    # --- Tornado drivers (Quant: tornado-ready output) ---

    def test_tornado_drivers_ev_shape(self):
        """tornado_drivers returns EV and collateral_adjustment drivers with low/base/high and recovery_by_tranche."""
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 100}]
        out = tornado_drivers(tranches, base_ev=150, collateral_adjustment=0, ev_step=50.0)
        self.assertEqual(len(out), 2)
        ev_d = next(d for d in out if d["driver"] == "EV")
        self.assertEqual(ev_d["low"], 100.0)
        self.assertEqual(ev_d["base"], 150.0)
        self.assertEqual(ev_d["high"], 200.0)
        self.assertEqual(len(ev_d["recovery_by_tranche"]), 2)
        for t in ev_d["recovery_by_tranche"]:
            self.assertIn("name", t)
            self.assertIn("low", t)
            self.assertIn("base", t)
            self.assertIn("high", t)

    def test_tornado_drivers_ev_recovery_values(self):
        """EV driver: low EV gives lower recovery for junior tranches, high EV gives higher."""
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 100}]
        out = tornado_drivers(tranches, base_ev=150, ev_step=50.0)
        ev_d = next(d for d in out if d["driver"] == "EV")
        senior = next(t for t in ev_d["recovery_by_tranche"] if t["name"] == "Senior")
        unsec = next(t for t in ev_d["recovery_by_tranche"] if t["name"] == "Unsecured")
        self.assertEqual(senior["low"], 100.0)
        self.assertEqual(senior["base"], 100.0)
        self.assertEqual(senior["high"], 100.0)
        self.assertLess(unsec["low"], unsec["base"])
        self.assertLess(unsec["base"], unsec["high"])
        self.assertEqual(unsec["base"], 50.0)

    def test_tornado_drivers_collateral_adjustment(self):
        """Collateral adjustment driver: higher adjustment reduces effective EV and recoveries."""
        tranches = [{"name": "Senior", "claim": 100}, {"name": "Unsecured", "claim": 100}]
        out = tornado_drivers(tranches, base_ev=200, collateral_adjustment=50, ev_step=50.0)
        coll_d = next(d for d in out if d["driver"] == "collateral_adjustment")
        self.assertEqual(coll_d["low"], 0.0)
        self.assertEqual(coll_d["base"], 50.0)
        self.assertEqual(coll_d["high"], 100.0)
        unsec = next(t for t in coll_d["recovery_by_tranche"] if t["name"] == "Unsecured")
        self.assertGreater(unsec["low"], unsec["base"])
        self.assertGreater(unsec["base"], unsec["high"])

    def test_tornado_drivers_decimal_input(self):
        """tornado_drivers accepts Decimal for base_ev and collateral_adjustment; returns Decimal."""
        tranches = [{"name": "A", "claim": 50}]
        out = tornado_drivers(tranches, base_ev=Decimal("100"), collateral_adjustment=Decimal("0"))
        self.assertEqual(len(out), 2)
        ev_d = next(d for d in out if d["driver"] == "EV")
        self.assertIsInstance(ev_d["base"], Decimal)
        self.assertEqual(ev_d["base"], Decimal("100"))
        self.assertEqual(len(ev_d["recovery_by_tranche"]), 1)
        self.assertIsInstance(ev_d["recovery_by_tranche"][0]["base"], Decimal)
        self.assertEqual(ev_d["recovery_by_tranche"][0]["base"], Decimal("100"))


class TestAPRViolations(unittest.TestCase):
    """Test Absolute Priority Rule (APR) violation detection."""

    def test_no_violation_all_full_recovery(self):
        """All tranches 100%: no violation."""
        recoveries = [
            {"name": "Senior", "claim": Decimal("100"), "recovered": Decimal("100"), "recovery_pct": Decimal("100")},
            {"name": "Junior", "claim": Decimal("50"), "recovered": Decimal("50"), "recovery_pct": Decimal("100")},
        ]
        violations = _detect_apr_violations(recoveries)
        self.assertEqual(violations, [])

    def test_no_violation_junior_gets_nothing(self):
        """Senior partial, junior 0%: no violation (APR respected)."""
        recoveries = [
            {"name": "Senior", "claim": Decimal("100"), "recovered": Decimal("80"), "recovery_pct": Decimal("80")},
            {"name": "Junior", "claim": Decimal("50"), "recovered": Decimal("0"), "recovery_pct": Decimal("0")},
        ]
        violations = _detect_apr_violations(recoveries)
        self.assertEqual(violations, [])

    def test_violation_senior_partial_junior_gets_value(self):
        """Senior 80%, junior 20%: APR violation."""
        recoveries = [
            {"name": "Senior", "claim": Decimal("100"), "recovered": Decimal("80"), "recovery_pct": Decimal("80")},
            {"name": "Junior", "claim": Decimal("50"), "recovered": Decimal("10"), "recovery_pct": Decimal("20")},
        ]
        violations = _detect_apr_violations(recoveries)
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v["senior_tranche"], "Senior")
        self.assertEqual(v["senior_recovery_pct"], "80")
        self.assertEqual(v["junior_tranche"], "Junior")
        self.assertEqual(v["junior_recovery"], "10")
        self.assertEqual(v["violation_type"], "APR")

    def test_violation_multiple_juniors(self):
        """Senior partial, multiple juniors get value: violation for each."""
        recoveries = [
            {"name": "Senior", "claim": Decimal("100"), "recovered": Decimal("50"), "recovery_pct": Decimal("50")},
            {"name": "Mezz", "claim": Decimal("50"), "recovered": Decimal("10"), "recovery_pct": Decimal("20")},
            {"name": "Unsecured", "claim": Decimal("50"), "recovered": Decimal("5"), "recovery_pct": Decimal("10")},
        ]
        violations = _detect_apr_violations(recoveries)
        self.assertEqual(len(violations), 2)
        self.assertEqual(violations[0]["junior_tranche"], "Mezz")
        self.assertEqual(violations[1]["junior_tranche"], "Unsecured")

    def test_no_violation_multiple_seniors_first_full(self):
        """First senior 100%, second senior partial, junior 0%: no violation."""
        recoveries = [
            {"name": "Senior A", "claim": Decimal("100"), "recovered": Decimal("100"), "recovery_pct": Decimal("100")},
            {"name": "Senior B", "claim": Decimal("100"), "recovered": Decimal("50"), "recovery_pct": Decimal("50")},
            {"name": "Junior", "claim": Decimal("50"), "recovered": Decimal("0"), "recovery_pct": Decimal("0")},
        ]
        violations = _detect_apr_violations(recoveries)
        self.assertEqual(violations, [])

    def test_waterfall_includes_apr_violations(self):
        """Integration: run_waterfall includes apr_violations in output."""
        tranches = [
            {"name": "Senior", "claim": 100},
            {"name": "Junior", "claim": 50},
        ]
        # EV = 130: Senior gets 100 (100%), Junior gets 30 (60%) → APR respected
        result = run_waterfall(tranches, 130)
        self.assertIn("apr_violations", result)
        self.assertEqual(result["apr_violations"], [])

        # EV = 80: Senior gets 80 (80%), Junior gets 0 (0%) → APR respected
        result = run_waterfall(tranches, 80)
        self.assertEqual(result["apr_violations"], [])

    def test_waterfall_detects_apr_violation_in_manual_structure(self):
        """Manually construct a recovery that violates APR (e.g. plan term sheet)."""
        # This would be detected if a term sheet shows senior at 85% and junior at 10%
        recoveries = [
            {"name": "Senior", "claim": Decimal("100"), "recovered": Decimal("85"), "recovery_pct": Decimal("85")},
            {"name": "Junior", "claim": Decimal("50"), "recovered": Decimal("5"), "recovery_pct": Decimal("10")},
        ]
        violations = _detect_apr_violations(recoveries)
        self.assertEqual(len(violations), 1)
        self.assertIn("Junior tranche 'Junior' recovered 5", violations[0]["note"])


if __name__ == "__main__":
    unittest.main()

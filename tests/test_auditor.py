"""Tests for signal_triage.agents.auditor (Auditor: stress-test, variance, gate)."""

import unittest
from signal_triage.agents.auditor import (
    stress_test_waterfall,
    reconcile_critical_variances,
    build_audit_trail,
    run_auditor,
)


class TestStressTestWaterfall(unittest.TestCase):
    """Auditor: APR and precision checks."""

    def test_apr_satisfied_when_senior_paid_first(self):
        """APR passes when senior tranche gets 100% before junior gets anything."""
        result = {
            "recoveries": [
                {"name": "Senior", "claim": 100.0, "recovered": 100.0, "recovery_pct": 100.0},
                {"name": "Junior", "claim": 50.0, "recovered": 0.0, "recovery_pct": 0.0},
            ],
            "ev_used": 100.0,
            "ev_remaining": 0.0,
        }
        out = stress_test_waterfall(result)
        self.assertTrue(out["passed"])
        self.assertTrue(out["apr_check"]["passed"])
        self.assertIn("APR satisfied", out["apr_check"]["message"])

    def test_apr_violation_when_junior_has_recovery_but_senior_not_full(self):
        """APR fails when a junior tranche has recovery while senior is not 100%%."""
        result = {
            "recoveries": [
                {"name": "Senior", "claim": 100.0, "recovered": 50.0, "recovery_pct": 50.0},
                {"name": "Junior", "claim": 50.0, "recovered": 25.0, "recovery_pct": 50.0},
            ],
            "ev_used": 75.0,
            "ev_remaining": 0.0,
        }
        out = stress_test_waterfall(result)
        self.assertFalse(out["apr_check"]["passed"])
        self.assertIn("APR violation", out["apr_check"]["message"])

    def test_precision_check_passed(self):
        """Precision check passes when ev_used/ev_remaining are numeric."""
        result = {
            "recoveries": [{"name": "A", "claim": 100.0, "recovered": 100.0, "recovery_pct": 100.0}],
            "ev_used": 100.0,
            "ev_remaining": 0.0,
        }
        out = stress_test_waterfall(result)
        self.assertTrue(out["precision_check"]["passed"])


class TestReconcileCriticalVariances(unittest.TestCase):
    """Auditor: Critical Variance reconciliation."""

    def test_no_critical_variance(self):
        """When no items have critical_variance, all_resolved is True."""
        variance = [
            {"tranche_name": "Senior", "critical_variance": False, "variance_pct": 5.0},
        ]
        out = reconcile_critical_variances(variance)
        self.assertFalse(out["has_critical_variance"])
        self.assertTrue(out["all_resolved"])

    def test_has_critical_variance_unresolved(self):
        """When critical_variance True and resolved False, all_resolved is False."""
        variance = [
            {"tranche_name": "Senior", "critical_variance": True, "variance_pct": 30.0},
        ]
        out = reconcile_critical_variances(variance)
        self.assertTrue(out["has_critical_variance"])
        self.assertFalse(out["all_resolved"])
        self.assertEqual(len(out["items"]), 1)
        self.assertFalse(out["items"][0]["resolved"])


class TestBuildAuditTrail(unittest.TestCase):
    """Auditor: audit trail for reproducibility."""

    def test_audit_trail_contains_config_and_sources(self):
        """Audit trail has config_versions, document_sources, market_data_dates."""
        out = build_audit_trail(
            {"signals_config": "1.0"},
            ["/path/to/doc.pdf"],
            market_data_dates="2024-01-15",
        )
        self.assertEqual(out["config_versions"], {"signals_config": "1.0"})
        self.assertEqual(out["document_sources"], ["/path/to/doc.pdf"])
        self.assertEqual(out["market_data_dates"], "2024-01-15")


class TestRunAuditor(unittest.TestCase):
    """Auditor: full run_auditor gate."""

    def test_run_auditor_passes_when_stress_and_no_critical_variance(self):
        """run_auditor passed True when stress test passes and no critical variance."""
        waterfall = {
            "recoveries": [
                {"name": "Senior", "claim": 100.0, "recovered": 100.0, "recovery_pct": 100.0},
                {"name": "Junior", "claim": 50.0, "recovered": 0.0, "recovery_pct": 0.0},
            ],
            "ev_used": 100.0,
            "ev_remaining": 0.0,
        }
        benchmarker = {"recovery_variance": [{"critical_variance": False}]}
        out = run_auditor(
            waterfall,
            benchmarker,
            {"signals_config": "1.0"},
            ["/path/to/doc.pdf"],
            require_gate=True,
        )
        self.assertTrue(out["passed"])
        self.assertIn("passed", out["for_reporter"].lower())

    def test_run_auditor_fails_gate_when_critical_variance_unresolved(self):
        """run_auditor passed False when critical variance unresolved and require_gate True."""
        waterfall = {
            "recoveries": [
                {"name": "Senior", "claim": 100.0, "recovered": 100.0, "recovery_pct": 100.0},
            ],
            "ev_used": 100.0,
            "ev_remaining": 0.0,
        }
        benchmarker = {"recovery_variance": [{"critical_variance": True, "tranche_name": "Senior"}]}
        out = run_auditor(
            waterfall,
            benchmarker,
            {},
            [],
            require_gate=True,
        )
        self.assertFalse(out["passed"])
        self.assertIn("do not publish", out["for_reporter"].lower())

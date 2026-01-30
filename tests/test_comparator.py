"""Tests for signal_triage.agents.comparator."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.agents.comparator import compare_two, run_comparator


class TestCompareTwo(unittest.TestCase):
    def test_score_delta_positive(self):
        """Higher current score yields positive delta and 'higher' in summary."""
        prior = {"score": 30.0, "tier": "low"}
        current = {"score": 55.0, "tier": "medium"}
        out = compare_two(prior, current, prior_id="2023", current_id="2024")
        self.assertEqual(out["score_delta"], 25.0)
        self.assertEqual(out["score_prior"], 30.0)
        self.assertEqual(out["score_current"], 55.0)
        self.assertTrue(out["tier_changed"])
        self.assertIn("higher", out["summary"].lower())

    def test_score_delta_negative(self):
        """Lower current score yields negative delta."""
        prior = {"score": 70.0, "tier": "high"}
        current = {"score": 40.0, "tier": "medium"}
        out = compare_two(prior, current)
        self.assertEqual(out["score_delta"], -30.0)
        self.assertIn("lower", out["summary"].lower())

    def test_new_and_removed_signal_types(self):
        """New/removed signal types are detected from lme_signals and covenant_signals."""
        prior = {
            "score": 50.0,
            "tier": "medium",
            "lme_signals": [{"type": "uptier_risk", "evidence": "x"}],
            "covenant_signals": [{"type": "covenant_risk", "evidence": "y"}],
        }
        current = {
            "score": 55.0,
            "tier": "medium",
            "lme_signals": [{"type": "uptier_risk"}, {"type": "dropdown_risk"}],
            "covenant_signals": [],
        }
        out = compare_two(prior, current)
        self.assertIn("dropdown_risk", out["new_signal_types"])
        self.assertIn("covenant_risk", out["removed_signal_types"])
        self.assertNotIn("uptier_risk", out["new_signal_types"])
        self.assertNotIn("uptier_risk", out["removed_signal_types"])

    def test_no_material_change(self):
        """Same score and tier yields tier_changed False and coherent summary."""
        prior = {"score": 50.0, "tier": "medium"}
        current = {"score": 50.0, "tier": "medium"}
        out = compare_two(prior, current, prior_id="A", current_id="B")
        self.assertEqual(out["score_delta"], 0.0)
        self.assertFalse(out["tier_changed"])
        self.assertEqual(out["new_signal_types"], [])
        self.assertEqual(out["removed_signal_types"], [])


class TestRunComparator(unittest.TestCase):
    def test_empty_snapshots(self):
        """Empty snapshots returns mode 'none' and narrative."""
        out = run_comparator([])
        self.assertEqual(out["mode"], "none")
        self.assertEqual(out["comparisons"], [])
        self.assertIn("No snapshots", out["narrative"])

    def test_single_snapshot(self):
        """Single snapshot returns mode 'single' and no comparisons."""
        out = run_comparator([{"id": "Only", "score": 40.0}])
        self.assertEqual(out["mode"], "single")
        self.assertEqual(out["comparisons"], [])
        self.assertIn("Single snapshot", out["narrative"])

    def test_pair_mode_two_snapshots(self):
        """Two snapshots without baseline yields one comparison (pair mode)."""
        snapshots = [
            {"id": "2023-10-K", "score": 35.0, "tier": "low"},
            {"id": "2024-10-K", "score": 60.0, "tier": "medium"},
        ]
        out = run_comparator(snapshots)
        self.assertEqual(out["mode"], "pair")
        self.assertEqual(len(out["comparisons"]), 1)
        self.assertEqual(out["comparisons"][0]["prior_id"], "2023-10-K")
        self.assertEqual(out["comparisons"][0]["current_id"], "2024-10-K")
        self.assertEqual(out["comparisons"][0]["score_delta"], 25.0)

    def test_baseline_mode(self):
        """With baseline_index, each snapshot is compared to baseline."""
        snapshots = [
            {"id": "baseline", "score": 50.0, "tier": "medium"},
            {"id": "peer_a", "score": 70.0, "tier": "high"},
            {"id": "peer_b", "score": 30.0, "tier": "low"},
        ]
        out = run_comparator(snapshots, baseline_index=0)
        self.assertEqual(out["mode"], "baseline")
        self.assertEqual(len(out["comparisons"]), 2)
        deltas = [c["score_delta"] for c in out["comparisons"]]
        self.assertIn(20.0, deltas)
        self.assertIn(-20.0, deltas)

    def test_multi_consecutive_pairs(self):
        """Three or more snapshots without baseline yields consecutive pair comparisons."""
        snapshots = [
            {"id": "t0", "score": 40.0},
            {"id": "t1", "score": 55.0},
            {"id": "t2", "score": 50.0},
        ]
        out = run_comparator(snapshots)
        self.assertEqual(out["mode"], "multi")
        self.assertEqual(len(out["comparisons"]), 2)
        self.assertEqual(out["comparisons"][0]["prior_id"], "t0")
        self.assertEqual(out["comparisons"][0]["current_id"], "t1")
        self.assertEqual(out["comparisons"][1]["prior_id"], "t1")
        self.assertEqual(out["comparisons"][1]["current_id"], "t2")

    def test_multi_mode_four_snapshots(self):
        """run_comparator with 4 snapshots (multi mode): 3 consecutive pairs, narrative joined."""
        snapshots = [
            {"id": "Q1", "score": 20.0, "tier": "low"},
            {"id": "Q2", "score": 35.0, "tier": "low"},
            {"id": "Q3", "score": 55.0, "tier": "medium"},
            {"id": "Q4", "score": 50.0, "tier": "medium"},
        ]
        out = run_comparator(snapshots)
        self.assertEqual(out["mode"], "multi")
        self.assertEqual(len(out["comparisons"]), 3)
        self.assertEqual(out["comparisons"][0]["prior_id"], "Q1")
        self.assertEqual(out["comparisons"][0]["current_id"], "Q2")
        self.assertEqual(out["comparisons"][0]["score_delta"], 15.0)
        self.assertEqual(out["comparisons"][1]["prior_id"], "Q2")
        self.assertEqual(out["comparisons"][1]["current_id"], "Q3")
        self.assertEqual(out["comparisons"][1]["score_delta"], 20.0)
        self.assertEqual(out["comparisons"][2]["prior_id"], "Q3")
        self.assertEqual(out["comparisons"][2]["current_id"], "Q4")
        self.assertEqual(out["comparisons"][2]["score_delta"], -5.0)
        self.assertIn(" | ", out["narrative"])
        self.assertEqual(len(out["narrative"].split(" | ")), 3)

    def test_baseline_index_middle(self):
        """baseline_index path: baseline in middle (e.g. 1); all others compared to it."""
        snapshots = [
            {"id": "peer_a", "score": 30.0, "tier": "low"},
            {"id": "baseline", "score": 50.0, "tier": "medium"},
            {"id": "peer_b", "score": 70.0, "tier": "high"},
            {"id": "peer_c", "score": 45.0, "tier": "medium"},
        ]
        out = run_comparator(snapshots, baseline_index=1)
        self.assertEqual(out["mode"], "baseline")
        self.assertEqual(len(out["comparisons"]), 3)
        base_id = "baseline"
        for c in out["comparisons"]:
            self.assertEqual(c["prior_id"], base_id)
        current_ids = {c["current_id"] for c in out["comparisons"]}
        self.assertEqual(current_ids, {"peer_a", "peer_b", "peer_c"})
        deltas = {c["current_id"]: c["score_delta"] for c in out["comparisons"]}
        self.assertEqual(deltas["peer_a"], -20.0)
        self.assertEqual(deltas["peer_b"], 20.0)
        self.assertEqual(deltas["peer_c"], -5.0)

    def test_baseline_index_last(self):
        """baseline_index at end: 3 snapshots, baseline_index=2 yields 2 comparisons."""
        snapshots = [
            {"id": "a", "score": 40.0},
            {"id": "b", "score": 60.0},
            {"id": "baseline", "score": 50.0},
        ]
        out = run_comparator(snapshots, baseline_index=2)
        self.assertEqual(out["mode"], "baseline")
        self.assertEqual(len(out["comparisons"]), 2)
        for c in out["comparisons"]:
            self.assertEqual(c["prior_id"], "baseline")
        current_ids = sorted(c["current_id"] for c in out["comparisons"])
        self.assertEqual(current_ids, ["a", "b"])

    def test_baseline_index_ignored_when_out_of_range(self):
        """baseline_index out of range falls back to multi (consecutive pairs)."""
        snapshots = [
            {"id": "t0", "score": 10.0},
            {"id": "t1", "score": 20.0},
            {"id": "t2", "score": 30.0},
        ]
        out = run_comparator(snapshots, baseline_index=10)
        self.assertEqual(out["mode"], "multi")
        self.assertEqual(len(out["comparisons"]), 2)


if __name__ == "__main__":
    unittest.main()

"""Tests for signal_triage.analyzer."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.analyzer import analyze_text, calculate_distress_score


class TestAnalyzer(unittest.TestCase):
    def test_analyze_text_empty_returns_zero_score(self):
        """Empty or whitespace-only text returns score 0 and empty keywords."""
        for text in ("", "   ", "\n\t"):
            result = analyze_text(text)
            self.assertEqual(result["score"], 0.0)
            self.assertEqual(result["keywords_found"], [])
            self.assertEqual(result["keyword_count"], 0)
            self.assertEqual(result["base_score"], 0.0)
            self.assertEqual(result["length_factor"], 0.0)
            self.assertIn("score_breakdown", result)
            self.assertIsInstance(result["score_breakdown"], dict)
            self.assertEqual(result["score_breakdown"].get("components"), [])
            self.assertEqual(result["score_breakdown"].get("signals"), [])
            self.assertEqual(result["tier"], "low")
            self.assertIn("tier_label", result)
            self.assertIn("tier_thresholds", result)

    def test_analyze_text_score_in_range(self):
        """Score is always between 0 and 100."""
        result = analyze_text("any content here")
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 100.0)

    def test_analyze_text_keywords_found(self):
        """Matched credit phrases are reported; generic sentiment words are not signals."""
        result = analyze_text("Substantial doubt exists. An event of default has occurred.")
        self.assertIn("substantial doubt", result["keywords_found"])
        self.assertIn("event of default", result["keywords_found"])
        self.assertEqual(result["keyword_count"], len(result["keywords_found"]))
        self.assertGreater(result["base_score"], 0)
        self.assertEqual(analyze_text("We need help urgently. This is a crisis.")["score"], 0.0)

    def test_score_independent_of_length(self):
        """Padding a document with neutral text does not change its score."""
        core = "There is substantial doubt about the Company's ability to continue as a going concern."
        padded = core + " Revenue was in line with expectations." * 500
        self.assertEqual(analyze_text(core)["score"], analyze_text(padded)["score"])
        self.assertEqual(analyze_text("Quarterly update. " * 2000)["score"], 0.0)

    def test_negated_language_does_not_score(self):
        """Compliance boilerplate denying a condition is not a distress signal."""
        for text in (
            "No Event of Default has occurred and is continuing.",
            "Management's plans have alleviated substantial doubt about going concern.",
            "The Company was not in covenant breach at quarter end.",
        ):
            self.assertEqual(analyze_text(text)["score"], 0.0, text)

    def test_phrases_match_on_word_boundaries(self):
        """Short phrases do not fire inside unrelated words (e.g. 'dip' in 'dipped')."""
        self.assertEqual(analyze_text("The stock dipped on the news.")["score"], 0.0)

    def test_overlapping_phrase_counted_once(self):
        """A phrase listed under several rules is attributed to one signal only."""
        result = analyze_text("A covenant breach occurred.")
        types = [s["type"] for s in result["score_breakdown"]["signals"]]
        self.assertEqual(len(types), 1)

    def test_going_concern_floor_forces_high_tier(self):
        """A going-concern doubt alone is enough for the high tier."""
        result = analyze_text("There is substantial doubt about our ability to continue.")
        self.assertEqual(result["tier"], "high")
        self.assertEqual(result["floor_applied"], "going_concern")

    def test_analyze_text_has_required_keys(self):
        """Result dict has all keys used by CLI."""
        result = analyze_text("sample text")
        required = [
            "score", "keywords_found", "keyword_count", "base_score", "length_factor",
            "score_breakdown", "tier", "tier_thresholds",
        ]
        for key in required:
            self.assertIn(key, result)

    def test_calculate_distress_score_delegates(self):
        """calculate_distress_score returns analyze_text score."""
        text = "covenant breach and event of default"
        self.assertEqual(calculate_distress_score(text), analyze_text(text)["score"])

    def test_analyze_text_includes_lme_signals(self):
        """Result includes lme_signals list (for LME integration)."""
        result = analyze_text("uptiering and dropdown language.")
        self.assertIn("lme_signals", result)
        self.assertIsInstance(result["lme_signals"], list)

    def test_analyze_text_includes_analyst_checklist(self):
        """Result includes analyst_checklist list."""
        result = analyze_text("covenant breach and waiver.")
        self.assertIn("analyst_checklist", result)
        self.assertIsInstance(result["analyst_checklist"], list)

    def test_covenant_language_produces_checklist(self):
        """Covenant/waiver language produces non-empty analyst_checklist."""
        result = analyze_text("There was a covenant breach and we seek a waiver.")
        self.assertGreater(len(result["analyst_checklist"]), 0)

    def test_default_language_produces_checklist(self):
        """Default/acceleration language produces potential_default checklist items."""
        result = analyze_text("Event of default under the credit agreement.")
        self.assertGreater(len(result["analyst_checklist"]), 0)

    def test_analyze_text_returns_structured_score_breakdown(self):
        """Result includes score_breakdown with components and signals (weights, confidence)."""
        result = analyze_text("sample text with some content")
        self.assertIn("score_breakdown", result)
        breakdown = result["score_breakdown"]
        self.assertIsInstance(breakdown, dict)
        self.assertIn("components", breakdown)
        self.assertIn("signals", breakdown)
        for comp in breakdown["components"]:
            self.assertIn("name", comp)
            self.assertIn("contribution", comp)
            self.assertIn("weight", comp)
            self.assertIn("confidence", comp)
        for sig in breakdown["signals"]:
            self.assertIn("type", sig)
            self.assertIn("weight", sig)
            self.assertIn("confidence", sig)

    def test_analyze_text_returns_tier(self):
        """Result includes tier label (low/medium/high)."""
        result = analyze_text("sample text")
        self.assertIn("tier", result)
        self.assertIn(result["tier"], ("low", "medium", "high"))

    def test_analyze_text_tier_low_for_low_score(self):
        """Low score yields low tier (thresholds from settings, e.g. low max 25)."""
        result = analyze_text("x")
        self.assertLessEqual(result["score"], 100.0)
        thresholds = result.get("tier_thresholds", [])
        low_max = next((t["max"] for t in thresholds if t.get("name") == "low"), 33)
        if result["score"] <= low_max:
            self.assertEqual(result["tier"], "low")

    def test_analyze_text_returns_tier_thresholds(self):
        """Result includes tier_thresholds used for explainability."""
        result = analyze_text("sample text")
        self.assertIn("tier_thresholds", result)
        self.assertIsInstance(result["tier_thresholds"], list)
        for entry in result["tier_thresholds"]:
            self.assertIn("name", entry)
            self.assertIn("min", entry)
            self.assertIn("max", entry)

    def test_analyze_text_returns_tier_label(self):
        """Result includes tier_label for display (e.g. Low distress)."""
        result = analyze_text("sample text")
        self.assertIn("tier_label", result)
        self.assertIsInstance(result["tier_label"], str)
        self.assertGreater(len(result["tier_label"]), 0)


if __name__ == "__main__":
    unittest.main()

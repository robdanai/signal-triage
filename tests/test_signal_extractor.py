"""Tests for signal_triage.agents.signal_extractor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from signal_triage.agents.signal_extractor import extract_signals, run_signal_extractor


class TestSignalExtractor(unittest.TestCase):
    def test_extract_signals_empty_returns_empty(self):
        """Empty or whitespace-only text returns no signals."""
        for text in ("", "   ", "\n\t"):
            result = extract_signals(text)
            self.assertEqual(result, [])

    def test_extract_signals_returns_list_of_dicts(self):
        """extract_signals returns a list of signal dicts."""
        result = extract_signals("Some neutral text.")
        self.assertIsInstance(result, list)

    def test_extract_signals_covenant_language_produces_signal(self):
        """Covenant/waiver language produces covenant_risk signal with evidence and confidence."""
        text = "There was a covenant breach and we seek a waiver."
        signals = extract_signals(text)
        covenant = [s for s in signals if s.get("type") == "covenant_risk"]
        self.assertGreater(len(covenant), 0)
        s = covenant[0]
        self.assertIn("evidence", s)
        self.assertIn("confidence", s)
        self.assertIn("weight", s)
        self.assertIn("covenant", (s.get("evidence") or "").lower())
        self.assertGreaterEqual(s["confidence"], 0)
        self.assertLessEqual(s["confidence"], 1)

    def test_extract_signals_default_language_produces_signal(self):
        """Default/acceleration language produces potential_default signal."""
        text = "Event of default under the credit agreement."
        signals = extract_signals(text)
        default_sigs = [s for s in signals if s.get("type") == "potential_default"]
        self.assertGreater(len(default_sigs), 0)
        s = default_sigs[0]
        self.assertIn("evidence", s)
        self.assertIn("confidence", s)
        self.assertIn("default", (s.get("evidence") or "").lower())

    def test_extract_signals_lme_produces_signals(self):
        """LME phrases (dropdown, uptiering, etc.) produce signals with evidence."""
        text = "The document mentions dropdown and uptiering and first lien collateral."
        signals = extract_signals(text)
        types = {s.get("type") for s in signals}
        self.assertTrue(
            types & {"dropdown", "sprime_leakage", "uptiering"},
            f"Expected at least one LME type in {types}",
        )
        for s in signals:
            self.assertIn("evidence", s)
            self.assertIn("confidence", s)
            self.assertIn("weight", s)

    def test_extract_signals_going_concern_produces_signal(self):
        """Going concern language produces going_concern signal."""
        text = "There is substantial doubt about our ability to continue as a going concern."
        signals = extract_signals(text)
        gc = [s for s in signals if s.get("type") == "going_concern"]
        self.assertGreater(len(gc), 0)
        self.assertIn("evidence", gc[0])
        self.assertIn("confidence", gc[0])

    def test_run_signal_extractor_returns_signals_key(self):
        """run_signal_extractor returns dict with 'signals' key."""
        out = run_signal_extractor("Any text.")
        self.assertIn("signals", out)
        self.assertIsInstance(out["signals"], list)

    def test_run_signal_extractor_signals_match_extract_signals(self):
        """run_signal_extractor signals match extract_signals output."""
        text = "covenant breach and waiver."
        out = run_signal_extractor(text)
        direct = extract_signals(text)
        self.assertEqual(len(out["signals"]), len(direct))
        self.assertEqual(out["signals"], direct)

    def test_extract_signals_accepts_settings(self):
        """extract_signals accepts optional settings dict."""
        settings = {
            "signal_weights": {"covenant_risk": 25},
            "default_signal_confidence": 0.9,
        }
        text = "covenant breach in the agreement."
        signals = extract_signals(text, settings=settings)
        covenant = [s for s in signals if s.get("type") == "covenant_risk"]
        self.assertGreater(len(covenant), 0)
        self.assertEqual(covenant[0]["confidence"], 0.9)
        self.assertEqual(covenant[0]["weight"], 25)

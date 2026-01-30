"""Tests for signal_triage.signals_io (Librarian handoff)."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from signal_triage.signals_io import (
    read_signals,
    scan_document_and_write_signals,
    DEFAULT_CAPITAL_STRUCTURE,
)


class TestSignalsIO(unittest.TestCase):
    def test_read_signals(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"source_file": "x.txt", "trap_doors": [], "lme_signals": [], "capital_structure": None}, f)
            path = f.name
        try:
            data = read_signals(path)
            self.assertEqual(data["source_file"], "x.txt")
            self.assertEqual(data["trap_doors"], [])
        finally:
            Path(path).unlink(missing_ok=True)

    def test_scan_document_and_write_signals_creates_file(self):
        root = Path(__file__).resolve().parent.parent
        example = root / "example.txt"
        if not example.exists():
            self.skipTest("example.txt not found")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            signals_path = f.name
        try:
            payload = scan_document_and_write_signals(example, signals_path=signals_path)
            self.assertIn("source_file", payload)
            self.assertIn("trap_doors", payload)
            self.assertIn("lme_signals", payload)
            self.assertIn("capital_structure", payload)
            self.assertTrue(Path(signals_path).exists())
            data = read_signals(signals_path)
            self.assertEqual(data["trap_doors"], payload["trap_doors"])
            self.assertEqual(len(data["capital_structure"]["tranches"]), 3)
        finally:
            Path(signals_path).unlink(missing_ok=True)

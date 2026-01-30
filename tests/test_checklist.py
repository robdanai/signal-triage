"""Tests for signal_triage.checklist."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from signal_triage.checklist import generate_checklist, SIGNAL_CHECKLISTS


class TestChecklist(unittest.TestCase):
    def test_empty_signals_returns_empty(self):
        self.assertEqual(generate_checklist([]), [])

    def test_unknown_type_ignored(self):
        self.assertEqual(generate_checklist([{"type": "unknown_xyz"}]), [])

    def test_covenant_risk_returns_steps(self):
        out = generate_checklist([{"type": "covenant_risk"}])
        self.assertGreater(len(out), 0)
        self.assertIn("covenant", out[0].lower() or "waiver" in out[0].lower())

    def test_dropdown_returns_steps(self):
        out = generate_checklist([{"type": "dropdown"}])
        self.assertGreater(len(out), 0)

    def test_deduplication(self):
        out = generate_checklist([
            {"type": "covenant_risk"},
            {"type": "covenant_risk"},
        ])
        self.assertEqual(len(out), len(set(out)))

    def test_multiple_types_merge(self):
        out = generate_checklist([
            {"type": "dropdown"},
            {"type": "uptiering"},
        ])
        self.assertGreater(len(out), 2)

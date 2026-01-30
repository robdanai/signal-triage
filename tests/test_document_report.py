"""Tests for signal_triage.reports.document_report."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.reports.document_report import build_document_report, build_auditable_report, build_auditable_report


class TestDocumentReport(unittest.TestCase):
    def test_build_document_report_minimal(self):
        """Report includes score, tier, provenance and pass-through keys."""
        result = {
            "score": 50.0,
            "tier": "medium",
            "tier_label": "Medium distress",
            "score_breakdown": {"signals": []},
            "lme_signals": [],
            "covenant_signals": [],
            "analyst_checklist": [],
        }
        report = build_document_report(result, source_path="/path/to/doc.txt", text_length=1000)
        self.assertEqual(report["score"], 50.0)
        self.assertEqual(report["tier"], "medium")
        self.assertEqual(report["tier_label"], "Medium distress")
        self.assertEqual(report["file"], "/path/to/doc.txt")
        self.assertEqual(report["provenance"]["source_path"], "/path/to/doc.txt")
        self.assertEqual(report["provenance"]["text_length"], 1000)
        self.assertEqual(report["top_signals"], [])
        self.assertEqual(report["evidence_snippets"], [])

    def test_build_document_report_with_signals(self):
        """Top signals and evidence snippets are derived from score_breakdown."""
        result = {
            "score": 60.0,
            "tier": "high",
            "tier_label": "High distress",
            "score_breakdown": {
                "signals": [
                    {"type": "going_concern", "evidence": "substantial doubt about ability..."},
                    {"type": "covenant_risk", "evidence": "breach of financial covenant..."},
                ],
            },
            "lme_signals": [],
            "covenant_signals": [{"type": "covenant_risk"}],
            "analyst_checklist": ["Review covenant breach"],
        }
        report = build_document_report(result, source_path="doc.pdf", text_length=5000)
        self.assertEqual(len(report["top_signals"]), 2)
        self.assertEqual(report["top_signals"][0]["type"], "going_concern")
        self.assertIn("substantial doubt", report["top_signals"][0]["evidence"])
        self.assertEqual(len(report["evidence_snippets"]), 2)
        self.assertEqual(report["lme_signals"], [])
        self.assertEqual(len(report["covenant_signals"]), 1)


class TestBuildAuditableReport(unittest.TestCase):
    """Reporter: auditable report schema and Auditor gate."""

    def test_auditor_gate_blocks_publish_when_failed(self):
        """When require_audit_gate True and auditor passed False, published is False."""
        doc_report = {
            "score": 50.0,
            "tier": "medium",
            "tier_label": "Medium distress",
            "file": "/path/to/doc.pdf",
            "provenance": {"source_path": "/path/to/doc.pdf", "text_length": 1000},
            "top_signals": [],
            "evidence_snippets": [],
        }
        auditor_result = {
            "passed": False,
            "for_reporter": "Auditor gate not passed; do not publish final report.",
            "audit_trail": {"config_versions": {}, "document_sources": []},
        }
        report = build_auditable_report(
            doc_report,
            auditor_result=auditor_result,
            require_audit_gate=True,
        )
        self.assertFalse(report["published"])
        self.assertIn("do not publish", (report.get("analyst_note") or "").lower())
        self.assertEqual(report["report_format"], "auditable_report")
        self.assertEqual(report["document"], doc_report)

    def test_auditor_gate_allows_publish_when_passed(self):
        """When auditor passed True, published is True."""
        doc_report = {"score": 10.0, "tier": "low", "file": "/path/to/doc.pdf", "provenance": {}}
        auditor_result = {"passed": True, "for_reporter": "Auditor passed; report may be published."}
        report = build_auditable_report(
            doc_report,
            auditor_result=auditor_result,
            require_audit_gate=True,
        )
        self.assertTrue(report["published"])
        self.assertEqual(report["report_format"], "auditable_report")

    def test_no_audit_gate_ignores_auditor_fail(self):
        """When require_audit_gate False, published stays True even if auditor failed."""
        doc_report = {"score": 50.0, "tier": "medium", "file": "/x", "provenance": {}}
        auditor_result = {"passed": False, "for_reporter": "Do not publish."}
        report = build_auditable_report(
            doc_report,
            auditor_result=auditor_result,
            require_audit_gate=False,
        )
        self.assertTrue(report["published"])


class TestBuildAuditableReport(unittest.TestCase):
    """Reporter: auditable report schema and Auditor gate."""

    def test_auditor_gate_blocks_publish_when_failed(self):
        """When auditor passed=False and require_audit_gate=True, published is False."""
        doc_report = {
            "score": 50.0,
            "tier": "medium",
            "tier_label": "Medium distress",
            "file": "/path/to/doc.pdf",
            "provenance": {"source_path": "/path/to/doc.pdf", "text_length": 1000},
            "top_signals": [],
            "evidence_snippets": [],
        }
        auditor_result = {
            "passed": False,
            "for_reporter": "Auditor gate not passed; do not publish final report.",
            "audit_trail": {"config_versions": {}, "document_sources": []},
        }
        report = build_auditable_report(
            doc_report,
            auditor_result=auditor_result,
            require_audit_gate=True,
        )
        self.assertFalse(report["published"])
        self.assertIn("do not publish", (report.get("analyst_note") or "").lower())
        self.assertEqual(report["report_format"], "auditable_report")
        self.assertEqual(report["document"], doc_report)

    def test_auditor_gate_allows_publish_when_passed(self):
        """When auditor passed=True, published is True even with require_audit_gate."""
        doc_report = {"score": 10.0, "tier": "low", "file": "/path/to/doc", "provenance": {}}
        auditor_result = {"passed": True, "for_reporter": "Auditor passed; report may be published."}
        report = build_auditable_report(
            doc_report,
            auditor_result=auditor_result,
            require_audit_gate=True,
        )
        self.assertTrue(report["published"])
        self.assertEqual(report["report_format"], "auditable_report")

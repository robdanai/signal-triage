"""
Tests for IC memo generator.
"""

import unittest
from pathlib import Path
import tempfile

from signal_triage.reports.memo_generator import (
    generate_ic_memo,
    _build_investment_thesis,
    _build_narrative_synthesis,
    _format_decimal,
)
from decimal import Decimal


class TestMemoGenerator(unittest.TestCase):
    """Test IC memo generation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.document_report = {
            "score": 65.5,
            "tier": "T3",
            "tier_label": "Moderate Distress",
            "top_signals": [
                {"type": "going_concern_doubt", "evidence": "Substantial doubt about ability to continue"},
                {"type": "covenant_breach", "evidence": "Leverage covenant breach"},
                {"type": "dropdown_risk", "evidence": "Absence of IP transfer blocker"},
            ],
            "evidence_snippets": ["Evidence 1", "Evidence 2"],
            "provenance": {
                "source_path": "test_document.txt",
                "text_length": 1000,
            },
        }

        self.quant_result = {
            "recoveries": [
                {"name": "1st Lien", "claim": Decimal("100.0"), "recovered": Decimal("100.0"), "recovery_pct": Decimal("100.0")},
                {"name": "2nd Lien", "claim": Decimal("75.0"), "recovered": Decimal("50.0"), "recovery_pct": Decimal("66.67")},
                {"name": "Unsecured", "claim": Decimal("50.0"), "recovered": Decimal("0.0"), "recovery_pct": Decimal("0.0")},
            ],
            "fulcrum_security": "2nd Lien",
            "ev_used": Decimal("150.0"),
            "ev_remaining": Decimal("0.0"),
            "apr_violations": [],
        }

        self.librarian_result = {
            "baskets": [
                {
                    "name": "Investment Basket",
                    "amount": "$50M",
                    "section": "6.04",
                    "page": 42,
                }
            ],
            "collateral_leakage_flags": [
                {
                    "type": "J.Crew Blocker Absent",
                    "description": "No IP transfer restrictions",
                    "section": "6.04(b)",
                    "page": 43,
                    "severity": "critical",
                }
            ],
        }

        self.benchmarker_result = {
            "market_multiple": {
                "ev_ebitda": 7.5,
                "peers_analyzed": 5,
            },
            "recovery_variance": [
                {
                    "tranche": "1st Lien",
                    "model_recovery": 100,
                    "precedent_recovery": 95,
                    "variance_pct": 5.0,
                    "critical_variance": False,
                },
                {
                    "tranche": "2nd Lien",
                    "model_recovery": 66.67,
                    "precedent_recovery": 40,
                    "variance_pct": 26.67,
                    "critical_variance": True,
                },
            ],
        }

        self.auditor_result = {
            "passed": True,
            "audit_trail": {
                "config_version": "1.0",
                "sources": ["test_document.txt"],
            },
            "for_reporter": "All checks passed.",
        }

    def test_generate_ic_memo_basic(self):
        """Test basic IC memo generation."""
        memo = generate_ic_memo(
            self.document_report,
            librarian_result=None,
            quant_result=None,
            benchmarker_result=None,
            auditor_result=None,
        )

        # Check that memo contains key sections
        self.assertIn("# INVESTMENT COMMITTEE MEMORANDUM", memo)
        self.assertIn("## 1. EXECUTIVE SUMMARY", memo)
        self.assertIn("## 2. CAPITAL STRUCTURE OVERVIEW", memo)
        self.assertIn("## 3. STRUCTURAL RISK SCORECARD", memo)
        self.assertIn("## 4. SO WHAT?", memo)

    def test_generate_ic_memo_full(self):
        """Test IC memo generation with all components."""
        memo = generate_ic_memo(
            self.document_report,
            librarian_result=self.librarian_result,
            quant_result=self.quant_result,
            benchmarker_result=self.benchmarker_result,
            auditor_result=self.auditor_result,
        )

        # Check executive summary
        self.assertIn("**Distress Score:** 65.5/100", memo)
        self.assertIn("**Tier:** T3", memo)

        # Check capital structure
        self.assertIn("**Fulcrum Security:** 2nd Lien", memo)
        self.assertIn("**Enterprise Value (Applied):** $150.00M", memo)

        # Check that recovery table is present
        self.assertIn("| Tranche | Claim ($M) | Recovered ($M) | Recovery (%) | Fulcrum |", memo)
        self.assertIn("| 1st Lien |", memo)
        self.assertIn("| 2nd Lien |", memo)

        # Check structural risks
        self.assertIn("J.Crew Blocker Absent", memo)
        self.assertIn("Section 6.04(b)", memo)
        self.assertIn("Page 43", memo)

        # Check market context
        self.assertIn("## 6. MARKET CONTEXT", memo)
        self.assertIn("7.5x", memo)

        # Check audit trail
        self.assertIn("## 7. AUDIT TRAIL", memo)
        self.assertIn("✅ PASSED", memo)

    def test_generate_ic_memo_with_apr_violations(self):
        """Test IC memo with APR violations."""
        quant_with_violations = self.quant_result.copy()
        quant_with_violations["apr_violations"] = [
            {
                "senior_tranche": "1st Lien",
                "senior_recovery_pct": "80.0",
                "junior_tranche": "Unsecured",
                "junior_recovery": "10.0",
            }
        ]

        memo = generate_ic_memo(
            self.document_report,
            quant_result=quant_with_violations,
        )

        self.assertIn("⚠️ ABSOLUTE PRIORITY RULE (APR) VIOLATIONS DETECTED", memo)
        self.assertIn("1st Lien", memo)
        self.assertIn("Unsecured", memo)

    def test_generate_ic_memo_write_to_file(self):
        """Test writing memo to file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            temp_path = f.name

        try:
            memo = generate_ic_memo(
                self.document_report,
                output_path=temp_path,
            )

            # Check file was written
            self.assertTrue(Path(temp_path).exists())

            # Check file contents
            with open(temp_path, "r", encoding="utf-8") as f:
                file_contents = f.read()
                self.assertEqual(file_contents, memo)

        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_build_investment_thesis(self):
        """Test investment thesis construction."""
        thesis = _build_investment_thesis(
            self.document_report,
            self.quant_result,
            self.benchmarker_result,
        )

        self.assertIsInstance(thesis, str)
        self.assertGreater(len(thesis), 0)
        self.assertIn("MODERATE RISK", thesis)  # Score is 65.5
        self.assertIn("2nd Lien", thesis)  # Fulcrum

    def test_build_narrative_synthesis(self):
        """Test narrative synthesis."""
        narrative = _build_narrative_synthesis(
            self.document_report,
            self.librarian_result,
            self.quant_result,
            self.benchmarker_result,
        )

        self.assertIsInstance(narrative, str)
        self.assertGreater(len(narrative), 0)

        # Should contain institutional context
        self.assertIn("Dropdown Risk", narrative)
        self.assertIn("Going concern", narrative.lower())

    def test_format_decimal(self):
        """Test decimal formatting."""
        # Test with Decimal
        self.assertEqual(_format_decimal(Decimal("123.456")), "123.46")

        # Test with float
        self.assertEqual(_format_decimal(123.456), "123.46")

        # Test with int
        self.assertEqual(_format_decimal(123), "123.00")

        # Test with string (should just return string)
        self.assertEqual(_format_decimal("N/A"), "N/A")

    def test_memo_with_high_distress(self):
        """Test memo generation with high distress score."""
        high_distress_report = self.document_report.copy()
        high_distress_report["score"] = 85.0
        high_distress_report["tier"] = "T5"
        high_distress_report["tier_label"] = "Critical Distress"

        memo = generate_ic_memo(high_distress_report)

        self.assertIn("**HIGH RISK**", memo)
        self.assertIn("85.0/100", memo)

    def test_memo_with_low_distress(self):
        """Test memo generation with low distress score."""
        low_distress_report = self.document_report.copy()
        low_distress_report["score"] = 15.0
        low_distress_report["tier"] = "T1"
        low_distress_report["tier_label"] = "Minimal Distress"

        memo = generate_ic_memo(low_distress_report)

        self.assertIn("**LOW RISK**", memo)
        self.assertIn("15.0/100", memo)

    def test_memo_sensitivity_table(self):
        """Test that sensitivity table is included when quant results present."""
        memo = generate_ic_memo(
            self.document_report,
            quant_result=self.quant_result,
        )

        self.assertIn("## 5. RECOVERY SENSITIVITY TABLE", memo)
        self.assertIn("Bear", memo)
        self.assertIn("Base", memo)
        self.assertIn("Bull", memo)


if __name__ == "__main__":
    unittest.main()

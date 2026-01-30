"""Tests for signal_triage.pipeline (Author: one-command pipeline)."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from signal_triage.ingest.reader import DocumentChunk
from signal_triage.pipeline import run_pipeline, run_pipeline_batch, _is_url, _is_edgar_accession


class TestRunPipeline(unittest.TestCase):
    """Author: pipeline single-file run and report shape."""

    def setUp(self):
        self.fixture_dir = Path(__file__).resolve().parent / "fixtures" / "benchmark_corpus"
        self.low_distress = self.fixture_dir / "low_distress.txt"
        self.high_distress = self.fixture_dir / "high_distress.txt"

    def test_run_pipeline_returns_auditable_report(self):
        """Single-file run returns report_format auditable_report and document."""
        if not self.low_distress.exists():
            self.skipTest("Fixture low_distress.txt not found")
        signals_path = self.fixture_dir / "signals_pipeline_test.json"
        try:
            report = run_pipeline(
                self.low_distress,
                signals_path=signals_path,
                require_audit_gate=False,
            )
        finally:
            if signals_path.exists():
                signals_path.unlink(missing_ok=True)
        self.assertEqual(report.get("report_format"), "auditable_report")
        self.assertIn("document", report)
        doc = report["document"]
        self.assertIn("score", doc)
        self.assertIn("tier", doc)
        self.assertIn("provenance", doc)
        self.assertIn("published", report)
        self.assertIn("audit_trail", report)
        self.assertIn("config_versions", report)
        self.assertIn("document_sources", report)
        self.assertEqual(len(report["document_sources"]), 1)

    def test_run_pipeline_missing_file_returns_error_report(self):
        """Missing file returns error report with published False."""
        report = run_pipeline(Path("/nonexistent/doc.txt"), require_audit_gate=False)
        self.assertEqual(report.get("report_format"), "auditable_report")
        self.assertFalse(report.get("published", True))
        self.assertIn("error", report)

    @patch("signal_triage.pipeline.ingest_url")
    def test_run_pipeline_url_uses_web_ingestion_and_document_sources(self, mock_ingest_url):
        """When input is a URL, pipeline uses web ingestion and document_sources contains the URL (Phase 5)."""
        url = "https://example.com/indenture.pdf"
        mock_chunk = DocumentChunk(
            content="Sample covenant text.",
            page_number=None,
            section_label=f"url={url} | fetched_date=2024-01-01 | source_name=example.com",
            start_char=0,
            end_char=20,
        )
        mock_ingest_url.return_value = [mock_chunk]

        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "benchmark_corpus"
        signals_path = fixture_dir / "signals_url_test.json"
        try:
            report = run_pipeline(
                url,
                signals_path=signals_path,
                require_audit_gate=False,
            )
            mock_ingest_url.assert_called_once()
            self.assertEqual(report.get("report_format"), "auditable_report")
            self.assertIn("document_sources", report)
            self.assertEqual(report["document_sources"], [url])
            self.assertIn("document", report)
            self.assertIn("provenance", report.get("document", {}))
            self.assertEqual(report["document"]["provenance"].get("source_path"), url)
        finally:
            if signals_path.exists():
                signals_path.unlink(missing_ok=True)


class TestPipelineUrlEdgarDetection(unittest.TestCase):
    """Phase 5: URL and EDGAR accession detection."""

    def test_is_url_accepts_http_https(self):
        self.assertTrue(_is_url("https://example.com/doc"))
        self.assertTrue(_is_url("http://sec.gov/Archives/edgar/data/123/0001234567-21-000789.htm"))
        self.assertFalse(_is_url("/path/to/file.pdf"))
        self.assertFalse(_is_url("0001234567-21-000789"))

    def test_is_edgar_accession_accepts_standard_form(self):
        self.assertTrue(_is_edgar_accession("0001234567-21-000789"))
        self.assertTrue(_is_edgar_accession("1652044/0001193125-25-261546"))
        self.assertFalse(_is_edgar_accession("https://sec.gov/Archives/edgar/"))
        self.assertFalse(_is_edgar_accession("doc.pdf"))


class TestRunPipelineBatch(unittest.TestCase):
    """Author: pipeline batch run, portfolio, comparator."""

    def setUp(self):
        self.fixture_dir = Path(__file__).resolve().parent / "fixtures" / "benchmark_corpus"
        self.batch_folder = self.fixture_dir

    def test_run_pipeline_batch_returns_batch_report(self):
        """Batch run returns report_format pipeline_batch, results, portfolio."""
        if not self.batch_folder.is_dir():
            self.skipTest("Fixture benchmark_corpus folder not found")
        report = run_pipeline_batch(
            self.batch_folder,
            require_audit_gate=False,
        )
        self.assertEqual(report.get("report_format"), "pipeline_batch")
        self.assertIn("results", report)
        self.assertIn("portfolio", report)
        self.assertIn("published", report)
        self.assertIn("config_versions", report)
        self.assertIn("document_sources", report)
        portfolio = report["portfolio"]
        self.assertIn("ranked", portfolio)
        self.assertIn("top_risks", portfolio)
        self.assertIn("summary", portfolio)

    def test_run_pipeline_batch_with_two_plus_docs_includes_comparator(self):
        """When 2+ docs, comparator key is present with comparisons or narrative."""
        if not self.batch_folder.is_dir():
            self.skipTest("Fixture benchmark_corpus folder not found")
        report = run_pipeline_batch(self.batch_folder, require_audit_gate=False)
        self.assertIn("comparator", report)
        comp = report.get("comparator")
        if comp is not None:
            self.assertIn("mode", comp)
            self.assertIn("comparisons", comp)

    def test_run_pipeline_batch_nonexistent_dir_returns_error(self):
        """Non-directory path returns error and published False."""
        report = run_pipeline_batch(Path("/nonexistent/folder"), require_audit_gate=False)
        self.assertEqual(report.get("report_format"), "pipeline_batch")
        self.assertFalse(report.get("published", True))
        self.assertIn("error", report)
        self.assertEqual(report.get("results"), [])

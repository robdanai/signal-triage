"""Tests for signal_triage.ingest.web (Author: Phase 5 web/EDGAR ingestion)."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from signal_triage.ingest.web import (
    ingest_url,
    ingest_edgar_filing,
    SEC_USER_AGENT,
)


class TestIngestUrl(unittest.TestCase):
    """Author: ingest_url fetches URL and returns DocumentChunk list with provenance."""

    def test_ingest_url_invalid_scheme_raises(self):
        """URL must be http or https."""
        with self.assertRaises(ValueError) as ctx:
            ingest_url("ftp://example.com/doc.txt")
        self.assertIn("http", str(ctx.exception))

    @patch("signal_triage.ingest.web.requests")
    def test_ingest_url_returns_chunks_with_provenance(self, mock_requests):
        """ingest_url returns list of DocumentChunk with url and source_name in section_label."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body>Hello world</body></html>"
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        chunks = ingest_url("https://example.com/doc.html")
        self.assertEqual(len(chunks), 1)
        self.assertIn("https://example.com/doc.html", chunks[0].section_label or "")
        self.assertIn("source_name=", chunks[0].section_label or "")
        self.assertIn("fetched_date=", chunks[0].section_label or "")
        self.assertIn("Hello world", chunks[0].content)
        mock_requests.get.assert_called_once()
        call_kw = mock_requests.get.call_args[1]
        self.assertIn("User-Agent", call_kw["headers"])

    @patch("signal_triage.ingest.web.requests")
    def test_ingest_url_plain_text_passthrough(self, mock_requests):
        """Non-HTML content is returned as-is (no tag stripping)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "Plain text document."
        mock_resp.headers = {"Content-Type": "text/plain"}
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        chunks = ingest_url("https://example.com/doc.txt")
        self.assertEqual(chunks[0].content, "Plain text document.")

    @patch("signal_triage.ingest.web.requests")
    def test_ingest_url_uses_cache_when_provided(self, mock_requests):
        """When cache_dir is set and cache hit, no request is made."""
        cache_dir = Path(__file__).resolve().parent / "fixtures" / "web_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key_file = list(cache_dir.glob("*.txt"))
        try:
            # Pre-populate cache by hashing "url:https://example.com/cached"
            from signal_triage.ingest.web import _write_cache
            key = "url:https://example.com/cached"
            _write_cache(cache_dir, key, "Cached content here")
            chunks = ingest_url("https://example.com/cached", cache_dir=cache_dir)
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0].content, "Cached content here")
            mock_requests.get.assert_not_called()
        finally:
            for f in cache_dir.glob("*.txt"):
                f.unlink(missing_ok=True)
            if cache_dir.exists() and not any(cache_dir.iterdir()):
                cache_dir.rmdir()


class TestIngestEdgarFiling(unittest.TestCase):
    """Author: ingest_edgar_filing fetches by accession and returns chunks with source=EDGAR."""

    @patch("signal_triage.ingest.web.requests")
    def test_ingest_edgar_filing_returns_chunks_with_provenance(self, mock_requests):
        """ingest_edgar_filing returns DocumentChunk with accession_number and source=EDGAR."""
        index_resp = MagicMock()
        index_resp.status_code = 200
        index_resp.json.return_value = {
            "directory": {
                "filingDate": "2024-01-15",
                "item": [{"name": "doc.htm"}, {"name": "index.json"}],
            },
        }
        index_resp.raise_for_status = MagicMock()

        doc_resp = MagicMock()
        doc_resp.status_code = 200
        doc_resp.text = "<html><body>10-K content</body></html>"
        doc_resp.raise_for_status = MagicMock()

        mock_requests.get.side_effect = [index_resp, doc_resp]

        chunks = ingest_edgar_filing("0001234567-24-000001")
        self.assertEqual(len(chunks), 1)
        self.assertIn("accession_number=", chunks[0].section_label or "")
        self.assertIn("source=EDGAR", chunks[0].section_label or "")
        self.assertIn("filing_date=2024-01-15", chunks[0].section_label or "")
        self.assertIn("10-K content", chunks[0].content)
        self.assertEqual(mock_requests.get.call_count, 2)
        # First call: index.json; second: primary doc
        self.assertIn("index.json", mock_requests.get.call_args_list[0][0][0])
        call_headers = mock_requests.get.call_args_list[0][1]["headers"]
        self.assertEqual(call_headers.get("User-Agent"), SEC_USER_AGENT)

    @patch("signal_triage.ingest.web.requests")
    def test_ingest_edgar_filing_404_raises(self, mock_requests):
        """EDGAR 404 raises ValueError with accession hint."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_requests.get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            ingest_edgar_filing("0001234567-24-000001")
        self.assertIn("EDGAR", str(ctx.exception))
        self.assertIn("0001234567", str(ctx.exception))

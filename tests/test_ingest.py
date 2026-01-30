"""Tests for signal_triage.ingest (unified text + PDF pipeline)."""

import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.ingest.reader import (
    read_document,
    full_text,
    DocumentChunk,
)


class TestIngestReader(unittest.TestCase):
    def test_read_text_file_returns_single_chunk(self):
        """Plain .txt file returns one chunk with no page number."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Covenant breach and waiver.")
            path = f.name
        try:
            chunks = read_document(path)
            self.assertEqual(len(chunks), 1)
            self.assertIsNone(chunks[0].page_number)
            self.assertEqual(chunks[0].content, "Covenant breach and waiver.")
            self.assertEqual(full_text(chunks), "Covenant breach and waiver.")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_read_document_unsupported_format_raises(self):
        """Unsupported extension raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b")
            path = f.name
        try:
            with self.assertRaises(ValueError) as cm:
                read_document(path)
            self.assertIn("Unsupported format", str(cm.exception))
        finally:
            Path(path).unlink(missing_ok=True)

    def test_read_document_missing_file_raises(self):
        """Missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            read_document(Path("/nonexistent/file.txt"))

    def test_full_text_concatenates_chunks(self):
        """full_text concatenates chunk content in order."""
        chunks = [
            DocumentChunk(content="Page one. ", page_number=1),
            DocumentChunk(content="Page two.", page_number=2),
        ]
        self.assertEqual(full_text(chunks), "Page one. Page two.")

    def test_read_pdf_returns_page_chunks(self):
        """PDF file returns one chunk per page with page numbers (when pypdf available)."""
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest("pypdf not installed")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            w = PdfWriter()
            w.add_blank_page(612, 792)
            w.add_blank_page(612, 792)
            with open(pdf_path, "wb") as out:
                w.write(out)
            chunks = read_document(pdf_path)
            self.assertEqual(len(chunks), 2)
            self.assertEqual(chunks[0].page_number, 1)
            self.assertEqual(chunks[1].page_number, 2)
            self.assertEqual(full_text(chunks), chunks[0].content + chunks[1].content)
        finally:
            Path(pdf_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

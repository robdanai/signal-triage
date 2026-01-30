"""Tests for signal_triage.cli."""

import sys
from pathlib import Path
from unittest.mock import patch

import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.cli import main


class TestCLI(unittest.TestCase):
    def _exit_raiser(self, code=None):
        raise SystemExit(code)

    def test_cli_missing_file_exits_nonzero(self):
        """CLI exits with code 1 when file does not exist."""
        with patch("sys.argv", ["signal-triage", "nonexistent_file_xyz.txt"]):
            with patch("sys.exit", side_effect=self._exit_raiser):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_cli_directory_not_file_exits_nonzero(self):
        """CLI exits with 1 when path is a directory."""
        import os
        dir_path = os.path.abspath(os.path.dirname(__file__))
        with patch("sys.argv", ["signal-triage", dir_path]):
            with patch("sys.exit", side_effect=self._exit_raiser):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_cli_valid_file_prints_score(self):
        """CLI with valid file prints a numeric score (non-verbose)."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Some content.")
            path = f.name
        try:
            with patch("sys.argv", ["signal-triage", path]):
                exit_code = main()
            self.assertEqual(exit_code, 0)
        finally:
            import os
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_cli_verbose_includes_file_and_score(self):
        """Verbose mode prints File and Distress Score."""
        import tempfile
        import io
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("distress and crisis")
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.argv", ["signal-triage", "-v", path]):
                with patch("sys.stdout", buf):
                    main()
            out_str = buf.getvalue()
            self.assertIn("File:", out_str)
            self.assertIn("Distress Score:", out_str)
            self.assertIn("Tier:", out_str)
            self.assertIn("Score breakdown", out_str)
            self.assertIn("Explanation:", out_str)
            self.assertIn("Keywords found:", out_str)
        finally:
            import os
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_cli_checklist_only_prints_checklist(self):
        """--checklist-only prints only checklist lines (no score)."""
        import tempfile
        import io
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Covenant breach and waiver requested.")
            path = f.name
        try:
            buf = io.StringIO()
            with patch("sys.argv", ["signal-triage", "--checklist-only", path]):
                with patch("sys.stdout", buf):
                    main()
            out_str = buf.getvalue()
            self.assertIn("covenant", out_str.lower() or "waiver" in out_str.lower())
            self.assertNotIn("Distress Score", out_str)
        finally:
            import os
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_cli_waterfall_runs(self):
        """--waterfall with --ev and --tranches prints recovery and fulcrum."""
        import io
        buf = io.StringIO()
        with patch("sys.argv", [
            "signal-triage", "--waterfall",
            "--ev", "150",
            "--tranches", "Senior:100,Mezz:100,Unsecured:50",
        ]):
            with patch("sys.stdout", buf):
                exit_code = main()
        self.assertEqual(exit_code, 0)
        out_str = buf.getvalue()
        self.assertIn("Fulcrum Security", out_str)
        self.assertIn("Mezz", out_str)
        self.assertIn("recovery_pct", out_str or "100" in out_str)

    def test_cli_batch_processes_folder_and_prints_summary(self):
        """--batch FOLDER processes .txt/.pdf files and prints a summary report."""
        import io
        batch_dir = Path(__file__).resolve().parent / "fixtures" / "batch_folder"
        buf = io.StringIO()
        with patch("sys.argv", ["signal-triage", "--batch", str(batch_dir)]):
            with patch("sys.stdout", buf):
                exit_code = main()
        self.assertEqual(exit_code, 0)
        out_str = buf.getvalue()
        self.assertIn("Batch summary report", out_str)
        self.assertIn("Files processed: 2/2", out_str)
        self.assertIn("Score range", out_str)
        self.assertIn("a.txt", out_str)
        self.assertIn("b.txt", out_str)

    def test_cli_batch_nonexistent_folder_exits_nonzero(self):
        """--batch with nonexistent folder exits with code 1."""
        with patch("sys.argv", ["signal-triage", "--batch", "nonexistent_batch_folder_xyz"]):
            with patch("sys.exit", side_effect=self._exit_raiser):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_cli_batch_json_output(self):
        """--batch with --json outputs summary and results as JSON."""
        import io
        import json
        batch_dir = Path(__file__).resolve().parent / "fixtures" / "batch_folder"
        buf = io.StringIO()
        with patch("sys.argv", ["signal-triage", "--batch", str(batch_dir), "--json"]):
            with patch("sys.stdout", buf):
                exit_code = main()
        self.assertEqual(exit_code, 0)
        out = json.loads(buf.getvalue())
        self.assertIn("summary", out)
        self.assertIn("results", out)
        self.assertGreaterEqual(out["summary"]["total_files"], 1)
        self.assertGreaterEqual(out["summary"]["processed"], 1)
        self.assertIsInstance(out["results"], list)
        self.assertGreaterEqual(len(out["results"]), 1)
        self.assertIn("score", out["results"][0])
        self.assertIn("file", out["results"][0])

    def test_cli_unsupported_format_exits_nonzero(self):
        """CLI exits with 1 and message for unsupported file format (e.g. .csv)."""
        import tempfile
        import io
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b,c\n1,2,3")
            path = f.name
        try:
            err = io.StringIO()
            with patch("sys.argv", ["signal-triage", path]):
                with patch("sys.stderr", err):
                    with patch("sys.exit", side_effect=self._exit_raiser):
                        with self.assertRaises(SystemExit) as cm:
                            main()
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Unsupported format", err.getvalue())
        finally:
            import os
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_cli_pdf_ingest_runs(self):
        """CLI ingests PDF via unified pipeline and prints score (PDF text extraction)."""
        import tempfile
        import io
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest("pypdf not installed")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        try:
            w = PdfWriter()
            w.add_blank_page(612, 792)
            with open(pdf_path, "wb") as out:
                w.write(out)
            buf = io.StringIO()
            with patch("sys.argv", ["signal-triage", pdf_path]):
                with patch("sys.stdout", buf):
                    exit_code = main()
            self.assertEqual(exit_code, 0)
            out_str = buf.getvalue()
            # Blank PDF yields empty text -> numeric score (e.g. 0.00 or low)
            self.assertRegex(out_str, r"^\d+\.\d+\s*$", msg="CLI should print a numeric score for PDF")
        finally:
            import os
            try:
                os.unlink(pdf_path)
            except Exception:
                pass

    def test_cli_pdf_json_includes_page_count(self):
        """With --json, PDF output includes page_count from ingest pipeline."""
        import tempfile
        import io
        import json as json_mod
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
            buf = io.StringIO()
            with patch("sys.argv", ["signal-triage", "--json", pdf_path]):
                with patch("sys.stdout", buf):
                    main()
            out = json_mod.loads(buf.getvalue())
            self.assertIn("page_count", out)
            self.assertEqual(out["page_count"], 2)
        finally:
            import os
            try:
                os.unlink(pdf_path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()

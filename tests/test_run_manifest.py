"""Tests for run manifest and repro_from_manifest (Phase 6: reproducibility)."""

import json
import tempfile
import unittest
from pathlib import Path

from signal_triage.pipeline import (
    build_run_manifest,
    run_pipeline,
    run_pipeline_batch,
    write_run_manifest,
)


class TestBuildRunManifest(unittest.TestCase):
    """Run manifest builder: config_versions, document_sources, timestamp."""

    def test_build_run_manifest_has_required_keys(self):
        manifest = build_run_manifest(
            {"signals_config": "1.0"},
            ["/path/to/doc.txt"],
        )
        self.assertIn("config_versions", manifest)
        self.assertIn("document_sources", manifest)
        self.assertIn("timestamp", manifest)
        self.assertEqual(manifest["config_versions"], {"signals_config": "1.0"})
        self.assertEqual(manifest["document_sources"], ["/path/to/doc.txt"])

    def test_build_run_manifest_with_input_path_and_report_path(self):
        manifest = build_run_manifest(
            {},
            ["/a/doc.txt"],
            pipeline_mode="single",
            input_path="/a/doc.txt",
            report_path="/out/report.json",
        )
        self.assertEqual(manifest["pipeline_mode"], "single")
        self.assertEqual(manifest["input_path"], str(Path("/a/doc.txt").resolve()))
        self.assertEqual(manifest["report_path"], str(Path("/out/report.json").resolve()))


class TestWriteRunManifest(unittest.TestCase):
    """Writing run_manifest.json next to report."""

    def test_write_run_manifest_creates_file_next_to_report(self):
        report = {
            "report_format": "auditable_report",
            "config_versions": {"signals_config": "1.0"},
            "document_sources": ["/path/to/doc.txt"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            manifest_path = write_run_manifest(
                report_path,
                report,
                pipeline_mode="single",
                input_path="/path/to/doc.txt",
            )
            self.assertEqual(manifest_path, Path(tmp) / "run_manifest.json")
            self.assertTrue(manifest_path.exists())
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(data["config_versions"], {"signals_config": "1.0"})
            self.assertEqual(data["document_sources"], ["/path/to/doc.txt"])
            self.assertIn("timestamp", data)
            self.assertEqual(data["pipeline_mode"], "single")


class TestReproFromManifest(unittest.TestCase):
    """Replay a run from run_manifest.json."""

    def setUp(self):
        self.fixture_dir = Path(__file__).resolve().parent / "fixtures" / "benchmark_corpus"
        self.low_distress = self.fixture_dir / "low_distress.txt"

    def test_repro_from_manifest_single_doc(self):
        """Repro runs pipeline for single doc when manifest has input_path."""
        if not self.low_distress.exists():
            self.skipTest("Fixture low_distress.txt not found")
        from signal_triage.run_manifest import repro_from_manifest

        with tempfile.TemporaryDirectory() as tmp:
            report = run_pipeline(
                self.low_distress,
                signals_path=Path(tmp) / "signals.json",
                require_audit_gate=False,
            )
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            write_run_manifest(
                report_path,
                report,
                pipeline_mode="single",
                input_path=self.low_distress,
            )
            # Re-run from manifest (by report path: finds run_manifest.json alongside)
            rerun = repro_from_manifest(report_path)
            self.assertEqual(rerun.get("report_format"), "auditable_report")
            self.assertIn("document", rerun)

    def test_repro_from_manifest_via_manifest_path(self):
        """Repro runs when given path to run_manifest.json directly."""
        if not self.low_distress.exists():
            self.skipTest("Fixture low_distress.txt not found")
        from signal_triage.run_manifest import repro_from_manifest

        with tempfile.TemporaryDirectory() as tmp:
            report = run_pipeline(
                self.low_distress,
                signals_path=Path(tmp) / "signals.json",
                require_audit_gate=False,
            )
            report_path = Path(tmp) / "report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            manifest_path = write_run_manifest(
                report_path,
                report,
                pipeline_mode="single",
                input_path=self.low_distress,
            )
            rerun = repro_from_manifest(manifest_path)
            self.assertEqual(rerun.get("report_format"), "auditable_report")

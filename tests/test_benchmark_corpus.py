"""
Validate scoring behavior against the benchmark corpus.
Uses tests/fixtures/benchmark_corpus/manifest.json for expected score ranges and signals.
"""

import json
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.analyzer import analyze_text


BENCHMARK_DIR = Path(__file__).resolve().parent / "fixtures" / "benchmark_corpus"
MANIFEST_PATH = BENCHMARK_DIR / "manifest.json"


class TestBenchmarkCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest("Benchmark corpus manifest not found")
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)
        cls.documents = cls.manifest.get("documents") or []

    def test_benchmark_corpus_manifest_loaded(self):
        """Manifest has version and documents list."""
        self.assertIn("version", self.manifest)
        self.assertIsInstance(self.documents, list)
        self.assertGreater(len(self.documents), 0)

    def test_each_document_score_within_range(self):
        """For each document in the corpus, analyzer score is within manifest [score_min, score_max]."""
        for doc in self.documents:
            file_name = doc.get("file")
            self.assertIsNotNone(file_name, f"document entry missing 'file': {doc}")
            path = BENCHMARK_DIR / file_name
            self.assertTrue(path.exists(), f"benchmark file not found: {path}")
            text = path.read_text(encoding="utf-8", errors="replace")
            result = analyze_text(text)
            score = result.get("score")
            self.assertIsNotNone(score, f"analyzer returned no score for {file_name}")
            score_min = doc.get("score_min", 0)
            score_max = doc.get("score_max", 100)
            self.assertGreaterEqual(
                score, score_min,
                f"{file_name}: score {score} below min {score_min}",
            )
            self.assertLessEqual(
                score, score_max,
                f"{file_name}: score {score} above max {score_max}",
            )

    def test_each_document_tier_matches_when_expected(self):
        """When manifest has expected_tier, analyzer tier matches."""
        for doc in self.documents:
            expected_tier = doc.get("expected_tier")
            if expected_tier is None:
                continue
            file_name = doc.get("file")
            path = BENCHMARK_DIR / file_name
            text = path.read_text(encoding="utf-8", errors="replace")
            result = analyze_text(text)
            actual_tier = result.get("tier")
            self.assertEqual(
                actual_tier,
                expected_tier,
                f"{file_name}: expected tier {expected_tier}, got {actual_tier}",
            )

    def test_expected_signal_types_present_for_high_distress(self):
        """When manifest lists expected_signal_types, at least one such signal is present."""
        for doc in self.documents:
            expected_types = doc.get("expected_signal_types") or []
            if not expected_types:
                continue
            file_name = doc.get("file")
            path = BENCHMARK_DIR / file_name
            text = path.read_text(encoding="utf-8", errors="replace")
            result = analyze_text(text)
            breakdown = result.get("score_breakdown") or {}
            signals = breakdown.get("signals") or []
            detected_types = {s.get("type") for s in signals if s.get("type")}
            overlap = detected_types & set(expected_types)
            self.assertGreater(
                len(overlap),
                0,
                f"{file_name}: expected at least one of {expected_types}, got {detected_types}",
            )


if __name__ == "__main__":
    unittest.main()

"""Tests for signal_triage.agents.market_data_client."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import unittest
from unittest.mock import patch, MagicMock

from signal_triage.agents.market_data_client import (
    _citation,
    _today_iso,
    _parse_edgar_atom_feed,
    get_benchmarker_live_config,
    edgar_get_recent_8k_comparables,
    ninefin_get_recovery_benchmarks,
    ninefin_get_exit_multiples,
)


class TestCitation(unittest.TestCase):
    def test_citation_adds_source_and_date(self):
        datum = {"name": "Acme", "value": 1}
        _citation(datum, "SEC EDGAR", "2024-01-15")
        self.assertEqual(datum["source"], "Source: SEC EDGAR.")
        self.assertEqual(datum["date"], "2024-01-15")

    def test_citation_mutates_and_returns(self):
        datum = {}
        out = _citation(datum, "Test", "2024-01-01")
        self.assertIs(out, datum)
        self.assertIn("source", datum)
        self.assertIn("date", datum)


class TestGetBenchmarkerLiveConfig(unittest.TestCase):
    def test_default_is_stub(self):
        with patch.dict(os.environ, {"BENCHMARKER_USE_LIVE": "", "BENCHMARKER_DATA_SOURCE": ""}):
            use_live, data_source = get_benchmarker_live_config()
        self.assertFalse(use_live)
        self.assertEqual(data_source, "stub")

    def test_use_live_accepts_1_true_yes(self):
        for val in ("1", "true", "yes"):
            with patch.dict(os.environ, {"BENCHMARKER_USE_LIVE": val, "BENCHMARKER_DATA_SOURCE": "edgar"}):
                use_live, _ = get_benchmarker_live_config()
                self.assertTrue(use_live, f"BENCHMARKER_USE_LIVE={val!r} should enable live")

    def test_data_source_edgar(self):
        with patch.dict(os.environ, {"BENCHMARKER_USE_LIVE": "1", "BENCHMARKER_DATA_SOURCE": "edgar"}):
            _, data_source = get_benchmarker_live_config()
            self.assertEqual(data_source, "edgar")


class TestParseEdgarAtomFeed(unittest.TestCase):
    def test_empty_or_invalid_returns_empty_list(self):
        self.assertEqual(_parse_edgar_atom_feed(""), [])
        self.assertEqual(_parse_edgar_atom_feed("not xml"), [])

    def test_parses_atom_entries(self):
        # Minimal Atom feed with one entry (namespace as used by SEC)
        xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>8-K - Sample Corp (0001234567)</title>
    <updated>2024-06-15T18:30:00Z</updated>
    <link href="https://www.sec.gov/Archives/edgar/data/1234567/000123456724000789/0001234567-24-000789.txt"/>
  </entry>
</feed>"""
        entries = _parse_edgar_atom_feed(xml)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "Sample Corp")
        self.assertEqual(entries[0]["form_type"], "8-K")
        self.assertEqual(entries[0]["filing_date"], "2024-06-15")
        self.assertEqual(entries[0]["cik"], "0001234567")


class TestEdgarGetRecent8kComparables(unittest.TestCase):
    def test_requires_requests(self):
        with patch("signal_triage.agents.market_data_client.requests", None):
            with self.assertRaises(ImportError) as ctx:
                edgar_get_recent_8k_comparables(limit=5)
            self.assertIn("requests", str(ctx.exception))

    @patch("signal_triage.agents.market_data_client.requests")
    def test_returns_comparables_with_source_and_date(self, mock_requests):
        xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>8-K - Live Company (0001111111)</title>
    <updated>2024-07-01T12:00:00Z</updated>
    <link href="https://www.sec.gov/Archives/edgar/data/1111111/000111111124000001.txt"/>
  </entry>
</feed>"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = xml
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = edgar_get_recent_8k_comparables(limit=10, industry="Retail", geography="US")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for item in result:
            self.assertIn("name", item)
            self.assertIn("industry", item)
            self.assertIn("geography", item)
            self.assertIn("restructuring_date", item)
            self.assertIn("source", item)
            self.assertIn("date", item)
            self.assertIn("SEC EDGAR", item["source"])


class TestNinefinStubs(unittest.TestCase):
    def test_recovery_benchmarks_empty_without_api_key(self):
        with patch.dict(os.environ, {"NINEFIN_API_KEY": ""}):
            result = ninefin_get_recovery_benchmarks(limit=5)
        self.assertEqual(result, [])

    def test_exit_multiples_empty_without_api_key(self):
        with patch.dict(os.environ, {"NINEFIN_API_KEY": ""}):
            result = ninefin_get_exit_multiples(limit=5)
        self.assertEqual(result, [])

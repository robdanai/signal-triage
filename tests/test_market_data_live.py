"""Tests for signal_triage.agents.market_data_live."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import unittest
from unittest.mock import patch, MagicMock

from signal_triage.agents.market_data_live import (
    _today_iso,
    _cache_get,
    _cache_set,
    edgar_get_company_financials,
    edgar_detect_8k_distress_events,
    edgar_get_filing_history,
    edgar_get_recent_distressed_filings,
    fred_get_treasury_yield,
    calculate_yield_spread,
    alphavantage_get_stock_price,
    alphavantage_get_bond_yield,
    yahoo_get_stock_quote,
    yahoo_get_company_financials,
    fmp_get_company_profile,
    fmp_get_financial_ratios,
    finnhub_get_company_news,
    finnhub_get_sentiment,
    polygon_get_stock_quote,
    worldbank_get_gdp_growth,
    bls_get_unemployment_rate,
    openfigi_lookup_security,
    iexcloud_get_stock_quote,
    iexcloud_get_company_financials,
    get_cds_spread,
    calculate_credit_spread,
    get_sp_credit_rating,
    get_moodys_credit_rating,
    get_fitch_credit_rating,
    get_aggregate_credit_ratings,
    ninefin_get_recovery_rates_live,
    ninefin_get_precedent_transactions,
    reorg_get_distressed_companies,
    debtwire_get_distressed_deals,
    get_stock_quote_with_fallback,
    get_company_financials_with_fallback,
    check_api_health,
    get_available_apis,
    get_recommended_setup,
)


class TestTodayIso(unittest.TestCase):
    def test_returns_iso_date_string(self):
        result = _today_iso()
        self.assertIsInstance(result, str)
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}")


# ===== SEC EDGAR Tests =====


class TestEdgarGetCompanyFinancials(unittest.TestCase):
    def test_requires_requests(self):
        with patch("signal_triage.agents.market_data_live.requests", None):
            result = edgar_get_company_financials("0001652044")
            self.assertIn("error", result)
            self.assertIn("requests not installed", result["error"])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_company_facts(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "cik": "1652044",
            "entityName": "Sonder Holdings Inc.",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {
                                    "form": "10-K",
                                    "val": 123456789,
                                    "filed": "2024-03-15",
                                    "end": "2023-12-31",
                                }
                            ]
                        }
                    },
                    "LongTermDebt": {
                        "units": {
                            "USD": [
                                {"form": "10-K", "val": 500000000}
                            ]
                        }
                    },
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = edgar_get_company_financials("0001652044")
        self.assertEqual(result["cik"], "0001652044")
        self.assertEqual(result["revenue"], 123456789)
        self.assertEqual(result["total_debt"], 500000000)
        self.assertIn("SEC EDGAR", result["source"])


class TestEdgarDetect8kDistressEvents(unittest.TestCase):
    def test_requires_requests(self):
        with patch("signal_triage.agents.market_data_live.requests", None):
            result = edgar_detect_8k_distress_events("0001652044")
            self.assertEqual(result, [])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_8k_filings(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "filings": {
                "recent": {
                    "form": ["8-K", "10-K", "8-K"],
                    "filingDate": ["2024-06-15", "2024-03-15", "2024-01-10"],
                    "accessionNumber": ["0001234567-24-000123", "0001234567-24-000100", "0001234567-24-000050"],
                    "primaryDocument": ["d123456d8k.htm", "d123456d10k.htm", "d123456d8k.htm"],
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = edgar_detect_8k_distress_events("0001652044", limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["form_type"], "8-K")
        self.assertEqual(result[0]["filing_date"], "2024-06-15")


class TestEdgarGetFilingHistory(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_filing_history(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "10-K", "8-K"],
                    "filingDate": ["2024-03-15", "2024-05-15", "2023-03-15", "2024-06-01"],
                    "accessionNumber": ["0001-24-001", "0001-24-002", "0001-23-001", "0001-24-003"],
                    "primaryDocument": ["10k.htm", "10q.htm", "10k.htm", "8k.htm"],
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = edgar_get_filing_history("0001652044", form_type="10-K", limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["form_type"], "10-K")
        self.assertIn("document_url", result[0])


# ===== FRED Tests =====


class TestFredGetTreasuryYield(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"FRED_API_KEY": ""}):
            result = fred_get_treasury_yield("10Y")
            self.assertIsNone(result["yield_pct"])
            self.assertIn("no API key", result["source"])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_treasury_yield(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "observations": [
                {"date": "2024-06-15", "value": "4.25"}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"FRED_API_KEY": "test_key"}):
            result = fred_get_treasury_yield("10Y")
            self.assertEqual(result["yield_pct"], 4.25)
            self.assertEqual(result["maturity"], "10Y")
            self.assertIn("FRED", result["source"])


class TestCalculateYieldSpread(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.fred_get_treasury_yield")
    def test_calculates_spread(self, mock_fred):
        mock_fred.return_value = {
            "yield_pct": 4.25,
            "maturity": "10Y",
            "source": "FRED",
            "date": "2024-06-15",
        }

        result = calculate_yield_spread(12.5, treasury_maturity="10Y")
        self.assertEqual(result["spread_bps"], 825.0)  # (12.5 - 4.25) * 100
        self.assertEqual(result["target_yield"], 12.5)
        self.assertEqual(result["treasury_yield"], 4.25)


# ===== Alpha Vantage Tests =====


class TestAlphaVantageGetStockPrice(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"ALPHAVANTAGE_API_KEY": ""}):
            result = alphavantage_get_stock_price("AAPL")
            self.assertIsNone(result["price"])
            self.assertIn("no API key", result["source"])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_stock_price(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "05. price": "150.25",
                "07. latest trading day": "2024-06-14",
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"ALPHAVANTAGE_API_KEY": "test_key"}):
            result = alphavantage_get_stock_price("AAPL")
            self.assertEqual(result["price"], 150.25)
            self.assertEqual(result["symbol"], "AAPL")


class TestAlphaVantageGetBondYield(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_bond_yield(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {"date": "2024-06-15", "value": "4.30"}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"ALPHAVANTAGE_API_KEY": "test_key"}):
            result = alphavantage_get_bond_yield("10year")
            self.assertEqual(result["yield_pct"], 4.30)


# ===== IEX Cloud Tests =====


class TestIexCloudGetStockQuote(unittest.TestCase):
    def test_requires_api_token(self):
        with patch.dict(os.environ, {"IEXCLOUD_API_TOKEN": ""}):
            result = iexcloud_get_stock_quote("AAPL")
            self.assertIsNone(result["price"])
            self.assertIn("no API token", result["source"])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_stock_quote(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "symbol": "AAPL",
            "latestPrice": 150.50,
            "latestVolume": 50000000,
            "marketCap": 2500000000000,
            "peRatio": 28.5,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"IEXCLOUD_API_TOKEN": "test_token"}):
            result = iexcloud_get_stock_quote("AAPL")
            self.assertEqual(result["price"], 150.50)
            self.assertEqual(result["symbol"], "AAPL")


# ===== CDS and Credit Spread Tests =====


class TestGetCdsSpread(unittest.TestCase):
    def test_returns_stub(self):
        result = get_cds_spread("AAPL", maturity="5Y")
        self.assertIsNone(result["cds_spread_bps"])
        self.assertIn("Bloomberg", result["source"])


class TestCalculateCreditSpread(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.fred_get_treasury_yield")
    def test_calculates_credit_spread(self, mock_fred):
        mock_fred.return_value = {
            "yield_pct": 4.25,
            "maturity": "10Y",
            "source": "FRED",
            "date": "2024-06-15",
        }

        result = calculate_credit_spread(8.5, treasury_maturity="10Y")
        self.assertEqual(result["spread_bps"], 425.0)  # (8.5 - 4.25) * 100
        self.assertEqual(result["bond_yield"], 8.5)


# ===== Credit Ratings Tests =====


class TestGetSpCreditRating(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"SP_CAPITAL_IQ_API_KEY": ""}):
            result = get_sp_credit_rating("AAPL")
            self.assertIsNone(result["rating"])
            self.assertIn("no API key", result["source"])


class TestGetMoodysCreditRating(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"MOODYS_API_KEY": ""}):
            result = get_moodys_credit_rating("AAPL")
            self.assertIsNone(result["rating"])
            self.assertIn("no API key", result["source"])


class TestGetFitchCreditRating(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"FITCH_API_KEY": ""}):
            result = get_fitch_credit_rating("AAPL")
            self.assertIsNone(result["rating"])
            self.assertIn("no API key", result["source"])


class TestGetAggregateCreditRatings(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.get_sp_credit_rating")
    @patch("signal_triage.agents.market_data_live.get_moodys_credit_rating")
    @patch("signal_triage.agents.market_data_live.get_fitch_credit_rating")
    def test_aggregates_ratings(self, mock_fitch, mock_moodys, mock_sp):
        mock_sp.return_value = {"rating": "BBB", "outlook": "Stable"}
        mock_moodys.return_value = {"rating": "Baa2", "outlook": "Stable"}
        mock_fitch.return_value = {"rating": "BBB+", "outlook": "Stable"}

        result = get_aggregate_credit_ratings("TEST")
        self.assertEqual(result["sp_rating"], "BBB")
        self.assertEqual(result["moodys_rating"], "Baa2")
        self.assertEqual(result["fitch_rating"], "BBB+")
        self.assertIn(result["consensus_level"], ["Investment Grade", "N/A"])


# ===== 9fin Tests =====


class TestNinefinGetRecoveryRatesLive(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"NINEFIN_API_KEY": ""}):
            result = ninefin_get_recovery_rates_live(industry="Retail")
            self.assertEqual(result, [])


class TestNinefinGetPrecedentTransactions(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"NINEFIN_API_KEY": ""}):
            result = ninefin_get_precedent_transactions(industry="Retail")
            self.assertEqual(result, [])


# ===== Reorg Research Tests =====


class TestReorgGetDistressedCompanies(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"REORG_API_KEY": ""}):
            result = reorg_get_distressed_companies(industry="Retail")
            self.assertEqual(result, [])


# ===== Debtwire Tests =====


class TestDebtwireGetDistressedDeals(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"DEBTWIRE_API_KEY": ""}):
            result = debtwire_get_distressed_deals(industry="Retail")
            self.assertEqual(result, [])


# ===== API Configuration Tests =====


class TestGetAvailableApis(unittest.TestCase):
    def test_returns_api_status_dict(self):
        result = get_available_apis()
        self.assertIsInstance(result, dict)
        self.assertIn("sec_edgar", result)
        self.assertIn("fred", result)
        self.assertIn("alphavantage", result)
        self.assertIn("iexcloud", result)
        self.assertIn("ninefin", result)
        self.assertIn("sp_capital_iq", result)
        self.assertIn("moodys", result)
        self.assertIn("fitch", result)

    @patch("signal_triage.agents.market_data_live.requests", None)
    def test_requires_requests_for_all_apis(self):
        result = get_available_apis()
        self.assertFalse(result["sec_edgar"])
        self.assertFalse(result["fred"])


class TestGetRecommendedSetup(unittest.TestCase):
    def test_returns_setup_instructions(self):
        result = get_recommended_setup()
        self.assertIsInstance(result, str)
        self.assertIn("SEC EDGAR", result)
        self.assertIn("FRED", result)
        self.assertIn("Alpha Vantage", result)

    @patch("signal_triage.agents.market_data_live.requests", None)
    def test_warns_when_requests_not_installed(self):
        result = get_recommended_setup()
        self.assertIn("pip install requests", result)


# ===== Cache Tests =====


class TestCacheFunctions(unittest.TestCase):
    def test_cache_set_and_get(self):
        _cache_set("test_key", {"value": 123})
        result = _cache_get("test_key")
        self.assertEqual(result["value"], 123)

    def test_cache_expiry(self):
        _cache_set("test_key", {"value": 456})
        # Cache should return None after TTL (testing with 0 TTL)
        result = _cache_get("test_key", ttl_seconds=0)
        self.assertIsNone(result)


# ===== Yahoo Finance Tests =====


class TestYahooGetStockQuote(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_stock_quote(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "quoteSummary": {
                "result": [{
                    "price": {
                        "regularMarketPrice": {"raw": 150.50},
                        "currency": "USD",
                        "marketCap": {"raw": 2500000000000}
                    },
                    "summaryDetail": {
                        "volume": {"raw": 50000000},
                        "trailingPE": {"raw": 28.5}
                    },
                    "defaultKeyStatistics": {
                        "beta": {"raw": 1.2}
                    }
                }]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = yahoo_get_stock_quote("AAPL")
        self.assertEqual(result["price"], 150.50)
        self.assertEqual(result["symbol"], "AAPL")


class TestYahooGetCompanyFinancials(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_financials(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "quoteSummary": {
                "result": [{
                    "financialData": {
                        "totalRevenue": {"raw": 394000000000},
                        "totalDebt": {"raw": 120000000000},
                        "ebitda": {"raw": 130000000000}
                    }
                }]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = yahoo_get_company_financials("AAPL")
        self.assertEqual(result["revenue"], 394000000000)
        self.assertEqual(result["total_debt"], 120000000000)


# ===== FMP Tests =====


class TestFmpGetCompanyProfile(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"FMP_API_KEY": ""}):
            result = fmp_get_company_profile("AAPL")
            self.assertIn("error", result)

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_profile(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            "companyName": "Apple Inc.",
            "industry": "Technology",
            "sector": "Consumer Electronics",
            "mktCap": 2500000000000,
            "price": 150.25
        }]
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"FMP_API_KEY": "test_key"}):
            result = fmp_get_company_profile("AAPL")
            self.assertEqual(result["company_name"], "Apple Inc.")
            self.assertEqual(result["industry"], "Technology")


# ===== Finnhub Tests =====


class TestFinnhubGetCompanyNews(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"FINNHUB_API_KEY": ""}):
            result = finnhub_get_company_news("AAPL")
            self.assertEqual(result, [])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_news(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {
                "headline": "Apple announces new product",
                "summary": "Summary text",
                "url": "https://example.com/news",
                "datetime": 1640000000,
                "source": "Reuters"
            }
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"FINNHUB_API_KEY": "test_key"}):
            result = finnhub_get_company_news("AAPL", days=7)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["headline"], "Apple announces new product")


# ===== Polygon Tests =====


class TestPolygonGetStockQuote(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict(os.environ, {"POLYGON_API_KEY": ""}):
            result = polygon_get_stock_quote("AAPL")
            self.assertIsNone(result["price"])

    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_quote(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [{
                "o": 150.00,
                "h": 152.00,
                "l": 149.50,
                "c": 151.00,
                "v": 50000000
            }]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        with patch.dict(os.environ, {"POLYGON_API_KEY": "test_key"}):
            result = polygon_get_stock_quote("AAPL")
            self.assertEqual(result["price"], 151.00)
            self.assertEqual(result["close"], 151.00)


# ===== World Bank Tests =====


class TestWorldBankGetGdpGrowth(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_gdp_growth(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {},  # Metadata
            [
                {"country": {"value": "United States"}, "date": "2023", "value": 2.5},
                {"country": {"value": "United States"}, "date": "2022", "value": 2.1}
            ]
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = worldbank_get_gdp_growth("US", years=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["gdp_growth_pct"], 2.5)


# ===== BLS Tests =====


class TestBlsGetUnemploymentRate(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_fetches_unemployment(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Results": {
                "series": [{
                    "data": [
                        {"value": "3.8", "year": "2024", "periodName": "January"}
                    ]
                }]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests.get.return_value = mock_resp

        result = bls_get_unemployment_rate()
        self.assertEqual(result["unemployment_rate"], 3.8)


# ===== OpenFIGI Tests =====


class TestOpenFigiLookupSecurity(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.requests")
    def test_looks_up_security(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            "data": [{
                "figi": "BBG000B9XRY4",
                "cusip": "037833100",
                "isin": "US0378331005",
                "ticker": "AAPL",
                "name": "APPLE INC"
            }]
        }]
        mock_resp.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_resp

        result = openfigi_lookup_security("AAPL", id_type="TICKER")
        self.assertEqual(result["figi"], "BBG000B9XRY4")
        self.assertEqual(result["cusip"], "037833100")


# ===== Fallback Tests =====


class TestGetStockQuoteWithFallback(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.yahoo_get_stock_quote")
    def test_uses_yahoo_first(self, mock_yahoo):
        mock_yahoo.return_value = {"symbol": "AAPL", "price": 150.0}
        
        result = get_stock_quote_with_fallback("AAPL")
        self.assertEqual(result["price"], 150.0)
        self.assertIn("Yahoo Finance", result.get("fallback_note", ""))

    @patch("signal_triage.agents.market_data_live.yahoo_get_stock_quote")
    @patch("signal_triage.agents.market_data_live.alphavantage_get_stock_price")
    def test_falls_back_to_alphavantage(self, mock_av, mock_yahoo):
        mock_yahoo.return_value = {"symbol": "AAPL", "price": None}  # Yahoo fails
        mock_av.return_value = {"symbol": "AAPL", "price": 151.0}
        
        result = get_stock_quote_with_fallback("AAPL")
        self.assertEqual(result["price"], 151.0)
        self.assertIn("Alpha Vantage", result.get("fallback_note", ""))


class TestGetCompanyFinancialsWithFallback(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.edgar_get_company_financials")
    def test_uses_edgar_when_cik_provided(self, mock_edgar):
        mock_edgar.return_value = {"revenue": 1000000, "total_debt": 500000}
        
        result = get_company_financials_with_fallback("AAPL", cik="0000320193")
        self.assertEqual(result["revenue"], 1000000)
        self.assertIn("SEC EDGAR", result.get("fallback_note", ""))


# ===== API Health Tests =====


class TestCheckApiHealth(unittest.TestCase):
    @patch("signal_triage.agents.market_data_live.edgar_get_company_financials")
    @patch("signal_triage.agents.market_data_live.yahoo_get_stock_quote")
    def test_checks_api_health(self, mock_yahoo, mock_edgar):
        mock_edgar.return_value = {"revenue": 1000000}
        mock_yahoo.return_value = {"price": 150.0}
        
        health = check_api_health()
        self.assertIn("sec_edgar", health)
        self.assertIn("yahoo_finance", health)
        self.assertIn("_warnings", health)


if __name__ == "__main__":
    unittest.main()

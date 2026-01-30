"""
Integration tests for live market data APIs.

⚠️ WARNING: These tests make REAL API calls and count against rate limits!

Only run these when:
1. You have API keys configured
2. You want to verify production behavior
3. You understand rate limit implications

Usage:
    # Run all integration tests (careful!)
    pytest tests/test_integration_live_apis.py -v
    
    # Run specific test
    pytest tests/test_integration_live_apis.py::TestLiveAPIs::test_yahoo_finance -v
    
    # Skip integration tests normally
    pytest -m "not integration"
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import time

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestLiveAPIs:
    """Integration tests with real API calls."""
    
    def test_yahoo_finance(self):
        """Test Yahoo Finance API (free, no key)."""
        from signal_triage.agents.market_data_live import yahoo_get_stock_quote
        
        result = yahoo_get_stock_quote("AAPL")
        
        # Should have price
        assert result.get("price") is not None, f"No price returned: {result}"
        assert result["price"] > 0, "Price should be positive"
        
        # Should have source
        assert "Yahoo Finance" in result.get("source", "")
        
        print(f"✅ Yahoo Finance: AAPL = ${result['price']:.2f}")
    
    def test_sec_edgar(self):
        """Test SEC EDGAR API (free, no key)."""
        from signal_triage.agents.market_data_live import edgar_get_company_financials
        
        # Apple Inc CIK
        result = edgar_get_company_financials("0000320193")
        
        # Should have some financial data
        assert result.get("revenue") or result.get("total_debt"), \
            f"No financial data returned: {result}"
        
        print(f"✅ SEC EDGAR: CIK 0000320193 revenue = ${result.get('revenue', 0) / 1e9:.1f}B")
    
    def test_fallback_chain(self):
        """Test fallback mechanism works."""
        from signal_triage.agents.market_data_live import get_stock_quote_with_fallback
        
        result = get_stock_quote_with_fallback("AAPL")
        
        assert result.get("price") is not None, "Fallback chain failed completely"
        assert "fallback_note" in result or "source" in result, "Missing source attribution"
        
        print(f"✅ Fallback chain: {result.get('fallback_note', result.get('source'))}")
    
    @pytest.mark.skipif(
        not os.environ.get("FRED_API_KEY"),
        reason="FRED_API_KEY not set"
    )
    def test_fred_api(self):
        """Test FRED API (requires free key)."""
        from signal_triage.agents.market_data_live import fred_get_treasury_yield
        
        result = fred_get_treasury_yield("10Y")
        
        assert result.get("yield_pct") is not None, f"No yield data: {result}"
        assert 0 < result["yield_pct"] < 50, "Unrealistic yield"
        
        print(f"✅ FRED: 10Y Treasury = {result['yield_pct']:.2f}%")
    
    @pytest.mark.skipif(
        not os.environ.get("FMP_API_KEY"),
        reason="FMP_API_KEY not set"
    )
    def test_fmp_api(self):
        """Test Financial Modeling Prep API (requires free key)."""
        from signal_triage.agents.market_data_live import fmp_get_financial_ratios
        
        result = fmp_get_financial_ratios("AAPL")
        
        assert result.get("debt_equity_ratio") is not None, f"No ratios: {result}"
        
        print(f"✅ FMP: AAPL D/E = {result.get('debt_equity_ratio', 0):.2f}")
    
    def test_resilience_features(self):
        """Test rate limiting and circuit breaker."""
        from signal_triage.agents.market_data_resilience import (
            check_rate_limit,
            check_circuit,
            get_rate_limit_stats,
            get_circuit_status,
        )
        
        # Rate limit should allow first call
        allowed, reason = check_rate_limit("yahoo")
        assert allowed, f"Rate limit blocking: {reason}"
        
        # Circuit should be closed initially
        allowed, reason = check_circuit("yahoo")
        assert allowed, f"Circuit breaker blocking: {reason}"
        
        # Get stats
        stats = get_rate_limit_stats("yahoo")
        assert "daily_used" in stats
        
        status = get_circuit_status("yahoo")
        assert status["state"] == "closed"
        
        print("✅ Resilience features operational")
    
    def test_metrics_collection(self):
        """Test metrics are being collected."""
        from signal_triage.agents.market_data_resilience import get_metrics
        from signal_triage.agents.market_data_live import yahoo_get_stock_quote
        
        # Make a call to generate metrics
        yahoo_get_stock_quote("AAPL")
        
        # Check metrics exist
        metrics = get_metrics()
        assert len(metrics) > 0, "No metrics collected"
        
        print(f"✅ Metrics collected for {len(metrics)} APIs")
    
    def test_caching_works(self):
        """Test caching reduces API calls."""
        from signal_triage.agents.market_data_live import get_stock_quote_with_fallback
        
        # First call (cache miss)
        start = time.time()
        result1 = get_stock_quote_with_fallback("MSFT")
        time1 = time.time() - start
        
        # Second call (cache hit)
        start = time.time()
        result2 = get_stock_quote_with_fallback("MSFT")
        time2 = time.time() - start
        
        # Cached call should be much faster
        assert time2 < time1 / 2, f"Cache not working: {time1:.3f}s vs {time2:.3f}s"
        assert result1["price"] == result2["price"], "Cached result different"
        
        print(f"✅ Cache working: {time1*1000:.0f}ms → {time2*1000:.0f}ms")


class TestBenchmarkerIntegration:
    """Test benchmarker integration with live APIs."""
    
    def test_get_comprehensive_market_data(self):
        """Test benchmarker function with live APIs."""
        from signal_triage.agents.benchmarker import get_comprehensive_market_data
        
        result = get_comprehensive_market_data("AAPL", cik="0000320193")
        
        # Should have multiple data sources
        assert "stock_quote" in result
        assert "financials" in result
        assert "sources" in result
        
        # At least some sources should succeed
        assert len(result["sources"]) > 0, "No data sources succeeded"
        
        print(f"✅ Comprehensive data: {result['api_coverage']}")
    
    def test_benchmarker_fallback(self):
        """Test benchmarker handles API failures gracefully."""
        from signal_triage.agents.benchmarker import get_comprehensive_market_data
        
        # Even with a bad symbol, should not crash
        result = get_comprehensive_market_data("INVALID_SYMBOL_12345")
        
        # Should return data structure even if no data
        assert isinstance(result, dict)
        assert "symbol" in result
        
        print("✅ Benchmarker handles failures gracefully")


@pytest.mark.skipif(
    not os.environ.get("RUN_SLOW_TESTS"),
    reason="Set RUN_SLOW_TESTS=1 to run async tests"
)
class TestAsyncSupport:
    """Test async/parallel API calls."""
    
    @pytest.mark.asyncio
    async def test_parallel_quotes(self):
        """Test fetching multiple quotes in parallel."""
        from signal_triage.agents.market_data_async import fetch_stock_quotes_async
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        start = time.time()
        results = await fetch_stock_quotes_async(symbols)
        elapsed = time.time() - start
        
        # Should get results for all symbols
        assert len(results) == len(symbols)
        
        # Parallel should be faster than sequential
        # (Would be 3x slower if sequential)
        assert elapsed < 2.0, f"Too slow: {elapsed:.2f}s"
        
        print(f"✅ Parallel fetch: {len(symbols)} symbols in {elapsed:.2f}s")


# Integration test configuration
def pytest_configure(config):
    """Add integration marker."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real APIs)"
    )


if __name__ == "__main__":
    print("⚠️  WARNING: Running integration tests with REAL API calls!")
    print("This will count against your rate limits.")
    print()
    
    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])

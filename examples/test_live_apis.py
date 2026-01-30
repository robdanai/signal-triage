"""
Working Example: Test Live Market Data APIs

This script demonstrates how to use the live market data integration
with actual API calls (requires API keys for some sources).

Usage:
    python examples/test_live_apis.py

Setup:
    1. Set environment variables for APIs you want to test:
       - FRED_API_KEY (free, register at fred.stlouisfed.org)
       - FMP_API_KEY (free, 250/day at financialmodelingprep.com)
       - FINNHUB_API_KEY (free, 60/min at finnhub.io)
       - etc.
    
    2. Run this script to test which APIs are working
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import signal_triage
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import logging

# Enable debug logging to see API fallback chain
logging.basicConfig(level=logging.INFO)

from signal_triage.agents.market_data_live import (
    # Status checks
    get_available_apis,
    get_recommended_setup,
    check_api_health,
    
    # Fallback functions (recommended)
    get_stock_quote_with_fallback,
    get_company_financials_with_fallback,
    
    # Individual APIs (for testing)
    yahoo_get_stock_quote,
    fred_get_treasury_yield,
    fmp_get_financial_ratios,
    finnhub_get_sentiment,
    worldbank_get_gdp_growth,
    bls_get_unemployment_rate,
)


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_api_status():
    """Test 1: Check which APIs are available."""
    print_section("TEST 1: API Availability Status")
    
    apis = get_available_apis()
    for api_name, is_available in apis.items():
        status = "✅ Available" if is_available else "❌ Not Available"
        print(f"{status:20} | {api_name}")
    
    print("\n" + "-" * 80)
    print(get_recommended_setup())


def test_free_no_key_apis():
    """Test 2: APIs that work without any API key."""
    print_section("TEST 2: Free APIs (No Key Required)")
    
    # Yahoo Finance - Stock quote
    print("Testing Yahoo Finance (stock quote for AAPL)...")
    try:
        quote = yahoo_get_stock_quote("AAPL")
        if quote.get("price"):
            print(f"  ✅ Price: ${quote['price']:.2f}")
            print(f"  📊 Market Cap: ${quote.get('market_cap', 0) / 1e9:.1f}B")
            print(f"  📈 PE Ratio: {quote.get('pe_ratio', 'N/A')}")
        else:
            print(f"  ⚠️ No price data: {quote.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # World Bank - GDP growth
    print("\nTesting World Bank (US GDP growth)...")
    try:
        gdp_data = worldbank_get_gdp_growth("US", years=3)
        if gdp_data:
            print(f"  ✅ Got {len(gdp_data)} years of data")
            for entry in gdp_data[:3]:
                print(f"     {entry['year']}: {entry['gdp_growth_pct']:.2f}%")
        else:
            print("  ⚠️ No GDP data returned")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # BLS - Unemployment
    print("\nTesting BLS (US unemployment rate)...")
    try:
        unemployment = bls_get_unemployment_rate()
        if unemployment.get("unemployment_rate"):
            print(f"  ✅ Unemployment: {unemployment['unemployment_rate']:.1f}%")
            print(f"     Period: {unemployment.get('period', 'N/A')} {unemployment.get('year', '')}")
        else:
            print(f"  ⚠️ No data: {unemployment.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_free_with_key_apis():
    """Test 3: APIs that require free API keys."""
    print_section("TEST 3: Free APIs (API Key Required)")
    
    # FRED - Treasury yields
    print("Testing FRED (10Y Treasury yield)...")
    if not os.environ.get("FRED_API_KEY"):
        print("  ⚠️ FRED_API_KEY not set - skipping")
        print("     Register at: https://fred.stlouisfed.org/docs/api/api_key.html")
    else:
        try:
            treasury = fred_get_treasury_yield("10Y")
            if treasury.get("yield_pct"):
                print(f"  ✅ 10Y Treasury: {treasury['yield_pct']:.2f}%")
                print(f"     Date: {treasury.get('date', 'N/A')}")
            else:
                print(f"  ⚠️ No data: {treasury.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # FMP - Financial ratios
    print("\nTesting Financial Modeling Prep (AAPL ratios)...")
    if not os.environ.get("FMP_API_KEY"):
        print("  ⚠️ FMP_API_KEY not set - skipping")
        print("     Register at: https://site.financialmodelingprep.com/developer/docs")
    else:
        try:
            ratios = fmp_get_financial_ratios("AAPL")
            if ratios.get("debt_equity_ratio"):
                print(f"  ✅ Debt/Equity: {ratios['debt_equity_ratio']:.2f}")
                print(f"     Current Ratio: {ratios.get('current_ratio', 'N/A')}")
                print(f"     Interest Coverage: {ratios.get('interest_coverage', 'N/A'):.1f}x")
            else:
                print(f"  ⚠️ No data: {ratios.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Finnhub - Sentiment
    print("\nTesting Finnhub (AAPL sentiment)...")
    if not os.environ.get("FINNHUB_API_KEY"):
        print("  ⚠️ FINNHUB_API_KEY not set - skipping")
        print("     Register at: https://finnhub.io/register")
    else:
        try:
            sentiment = finnhub_get_sentiment("AAPL")
            if sentiment.get("sentiment_score") is not None:
                print(f"  ✅ Sentiment Score: {sentiment['sentiment_score']:.2f}")
                print(f"     Buzz: {sentiment.get('buzz_score', 'N/A')} articles/week")
            else:
                print(f"  ⚠️ No data: {sentiment.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_fallback_chain():
    """Test 4: Fallback mechanism."""
    print_section("TEST 4: Smart Fallback Chain")
    
    print("Testing stock quote fallback for AAPL...")
    print("(Will try: Yahoo → Alpha Vantage → Polygon → IEX Cloud)")
    try:
        quote = get_stock_quote_with_fallback("AAPL")
        if quote.get("price"):
            print(f"  ✅ Success: ${quote['price']:.2f}")
            print(f"     Source: {quote.get('fallback_note', 'Unknown')}")
            print(f"     Cached: {'Yes' if 'fallback_note' not in quote else 'No'}")
        else:
            print(f"  ❌ All sources failed")
            print(f"     Error: {quote.get('source', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\nTesting company financials fallback for AAPL...")
    print("(Will try: SEC EDGAR → Yahoo → IEX Cloud → FMP)")
    try:
        financials = get_company_financials_with_fallback("AAPL", cik="0000320193")
        if financials.get("revenue"):
            print(f"  ✅ Success")
            print(f"     Revenue: ${financials['revenue'] / 1e9:.1f}B")
            print(f"     Total Debt: ${financials.get('total_debt', 0) / 1e9:.1f}B")
            print(f"     Source: {financials.get('fallback_note', 'Unknown')}")
        else:
            print(f"  ❌ All sources failed")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_api_health():
    """Test 5: API health check."""
    print_section("TEST 5: API Health Check")
    
    print("Running health checks (this makes actual API calls)...")
    print("⚠️  Warning: This counts against rate limits!\n")
    
    try:
        health = check_api_health()
        
        for api_name, status in health.items():
            if api_name == "_warnings":
                continue
            
            if isinstance(status, dict):
                available = status.get("available", False)
                latency = status.get("latency_ms")
                error = status.get("error")
                
                status_icon = "✅" if available else "❌"
                print(f"{status_icon} {api_name:20} | ", end="")
                
                if available and latency:
                    print(f"Latency: {latency:.0f}ms")
                elif error:
                    print(f"Error: {error}")
                else:
                    print("Unknown status")
        
        # Print warnings
        warnings = health.get("_warnings", {})
        if warnings:
            print("\n⚠️  Warnings:")
            for key, value in warnings.items():
                if isinstance(value, dict):
                    print(f"\nRate Limits:")
                    for api, limit in value.items():
                        print(f"  - {api}: {limit}")
                else:
                    print(f"  - {key}: {value}")
    
    except Exception as e:
        print(f"❌ Health check failed: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  SIGNAL TRIAGE - Live Market Data API Test Suite")
    print("="*80)
    print("\nThis script tests all available market data APIs.")
    print("Some tests require API keys (free registration).")
    print("\nSet up API keys: export FRED_API_KEY=your_key (Linux/Mac)")
    print("                 $env:FRED_API_KEY=\"your_key\" (Windows PowerShell)")
    
    try:
        test_api_status()
        test_free_no_key_apis()
        test_free_with_key_apis()
        test_fallback_chain()
        
        print("\n" + "-"*80)
        response = input("\nRun API health check? (makes actual API calls, counts against limits) [y/N]: ")
        if response.lower() == 'y':
            test_api_health()
        else:
            print("Skipping health check.")
        
        print_section("✅ Test Suite Complete")
        print("Next steps:")
        print("  1. Register for free API keys at the URLs shown above")
        print("  2. Set environment variables for the APIs you want to use")
        print("  3. Re-run this script to see all APIs working")
        print("  4. Check docs/LIVE_DATA_SETUP.md for detailed setup instructions")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Live API Quick Start Guide

This guide shows how to use Signal Triage's live market data APIs for real-time analysis.

---

## Overview

Signal Triage integrates with multiple live data providers:

- **SEC EDGAR** (free, no API key) - Company filings, financials, 8-K distress events
- **Alpha Vantage** (free tier: 25/day) - Stock prices, company data
- **IEX Cloud** (commercial) - Premium stock/financial data
- **FRED** (free with registration) - Treasury yields, macroeconomic data
- **9fin** (commercial, when available) - Distressed debt recovery rates

---

## Quick Setup

### 1. Enable Live Data for Benchmarker

```bash
# Enable live APIs
export BENCHMARKER_USE_LIVE=1
export BENCHMARKER_DATA_SOURCE=edgar

# Required for SEC EDGAR (include your email)
export SEC_USER_AGENT="YourApp/1.0 (your.email@example.com)"
```

### 2. Optional: Add API Keys for Enhanced Data

```bash
# Treasury yields (free, register at fred.stlouisfed.org)
export FRED_API_KEY=your_fred_key_here

# Stock prices (free tier: alphavantage.co)
export ALPHAVANTAGE_API_KEY=your_alphavantage_key_here

# Premium financials (commercial: iexcloud.io)
export IEXCLOUD_API_TOKEN=your_iex_token_here

# Distressed debt recovery data (when available)
export NINEFIN_API_KEY=your_ninefin_key_here
```

### 3. Run Pipeline with Live Data

```bash
# Single document with live benchmarking
python -m signal_triage.cli --pipeline example.txt

# EDGAR filing with live comparables
python -m signal_triage.cli --pipeline "0001193125-25-261546"

# URL ingestion with live market data
python -m signal_triage.cli --pipeline "https://example.com/credit_agreement.pdf"
```

---

## Using the API Clients Directly

### SEC EDGAR Client

```python
from signal_triage.api import SECEdgarClient

client = SECEdgarClient()

# Lookup CIK by ticker
cik = client.lookup_cik("AAPL")  # Returns "0000320193"

# Get company info
info = client.get_company_info(cik)
print(info["name"])  # "Apple Inc."

# Get recent 10-K filings
filings = client.get_filings(cik, form_type="10-K", limit=5)
for filing in filings:
    print(f"{filing['filing_date']}: {filing['document_url']}")

# Get company financials (XBRL)
financials = client.get_company_financials(cik)
print(f"Revenue: ${financials['revenue']:,.0f}")
print(f"Total Debt: ${financials['total_debt']:,.0f}")
print(f"EBITDA: ${financials['ebitda']:,.0f}")

# Detect distress events in recent 8-Ks
events = client.detect_8k_distress_events(cik, limit=10)
for event in events:
    print(f"{event['filing_date']}: {event['items_detected']}")

# Get recent 8-K comparables across all companies
comparables = client.get_recent_8k_comparables(limit=20, industry="Retail")
for comp in comparables:
    print(f"{comp['name']}: {comp['restructuring_date']}")
```

### Market Pricing Client

```python
from signal_triage.api import MarketPricingClient

client = MarketPricingClient()  # Auto-selects best available provider

# Get stock price
quote = client.get_stock_price("TSLA")
print(f"Price: ${quote['price']:.2f}")
print(f"Source: {quote['source']}")

# Get Treasury yield
treasury = client.get_treasury_yield("10Y")
print(f"10Y Treasury: {treasury['yield_pct']:.2f}%")

# Calculate credit spread
spread = client.calculate_yield_spread(
    target_yield=12.5,  # Distressed bond yield
    treasury_maturity="10Y"
)
print(f"Spread: {spread['spread_bps']:.0f} bps")

# Get company financials (IEX Cloud only)
financials = client.get_company_financials("AAPL")
print(f"Revenue: ${financials['revenue']:,.0f}")
```

### Benchmarker Integration

The Benchmarker automatically uses live APIs when configured:

```python
from signal_triage.agents.benchmarker import run_benchmarker

# Run with live data (uses BENCHMARKER_USE_LIVE env var)
result = run_benchmarker(
    industry="Retail",
    geography="US",
    model_recoveries=[
        {"name": "1L", "recovery_pct": 85.0},
        {"name": "2L", "recovery_pct": 45.0}
    ],
    critical_variance_threshold_pct=25.0
)

# Check what data sources were used
print("Comparables source:", result['precedents']['comparables'][0]['source'])
print("Recovery benchmarks source:", result['precedents']['recovery_benchmarks'][0]['source'])
print("Market multiple source:", result['market_multiple']['source'])

# Review recovery variance (Critical Variance flags for Auditor)
for variance in result['recovery_variance']:
    if variance['critical_variance']:
        print(f"⚠️ CRITICAL: {variance['for_auditor']}")
```

---

## Environment Variables Reference

### Required for SEC EDGAR

| Variable | Description | Example |
|----------|-------------|---------|
| `SEC_USER_AGENT` | User-Agent with contact email (SEC requirement) | `"MyApp/1.0 (my.email@example.com)"` |

### Benchmarker Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `BENCHMARKER_USE_LIVE` | Enable live APIs (1/true/yes) | `0` (disabled) |
| `BENCHMARKER_DATA_SOURCE` | Preferred source (edgar/ninefin/stub) | `stub` |

### Optional API Keys

| Variable | Provider | Free Tier | Sign Up |
|----------|----------|-----------|---------|
| `FRED_API_KEY` | Federal Reserve (Treasury yields) | ✅ Yes | [fred.stlouisfed.org](https://fred.stlouisfed.org) |
| `ALPHAVANTAGE_API_KEY` | Alpha Vantage (stock prices) | ✅ 25/day | [alphavantage.co](https://www.alphavantage.co) |
| `IEXCLOUD_API_TOKEN` | IEX Cloud (premium data) | ❌ No | [iexcloud.io](https://iexcloud.io) |
| `NINEFIN_API_KEY` | 9fin (distressed debt) | ❌ No | [9fin.com](https://9fin.com) |

---

## Rate Limits & Caching

The API clients include automatic rate limiting and caching:

### SEC EDGAR
- **Rate Limit:** 10 requests/second (per SEC guidelines)
- **Cache TTL:** 1 hour for filings, 24 hours for company info
- **No API Key:** Free, just provide User-Agent

### Alpha Vantage
- **Rate Limit:** 5 requests/second (free tier: 25/day)
- **Cache TTL:** 15 minutes for stock prices
- **Free Tier:** 25 API calls/day

### IEX Cloud
- **Rate Limit:** Per your plan (typically 100/second)
- **Cache TTL:** 15 minutes for prices, 24 hours for financials
- **Commercial:** Pay-as-you-go pricing

### FRED
- **Rate Limit:** 120 requests/minute
- **Cache TTL:** 1 hour for yields
- **Free:** Unlimited with API key

---

## Infrastructure Features

All API clients include:

- ✅ **Rate Limiting:** Automatic per-provider token bucket algorithm
- ✅ **Caching:** In-memory TTL-based caching reduces API calls
- ✅ **Circuit Breaker:** Prevents cascading failures  
- ✅ **Retry Logic:** Exponential backoff with jitter
- ✅ **Error Handling:** Graceful degradation to fallbacks/stubs
- ✅ **Source Citation:** Every datum includes source and date

---

## Fallback Behavior

When live APIs are unavailable or fail, the system gracefully falls back:

1. **Primary:** Live API (if enabled and available)
2. **Secondary:** Alternative provider (e.g., IEX Cloud → Alpha Vantage)
3. **Tertiary:** Enhanced historical stubs (Moody's/S&P averages)

Example:
```python
# Benchmarker recovery benchmarks fallback chain:
# 1. Try 9fin API (if NINEFIN_API_KEY set)
# 2. Try SEC EDGAR precedents (if BENCHMARKER_USE_LIVE=1)
# 3. Fall back to historical averages (Moody's/S&P research)

result = get_recovery_benchmarks(tranche_type="1st Lien", industry="Retail")
print(result[0]['source'])  # Shows which source was used
```

---

## Example: Full Pipeline with Live Data

```python
from signal_triage.pipeline import run_pipeline
from pathlib import Path
import json
import os

# Configure live APIs
os.environ['BENCHMARKER_USE_LIVE'] = '1'
os.environ['BENCHMARKER_DATA_SOURCE'] = 'edgar'
os.environ['SEC_USER_AGENT'] = 'SignalTriage/1.0 (analyst@example.com)'
os.environ['FRED_API_KEY'] = 'your_fred_key'

# Run pipeline on EDGAR filing
report = run_pipeline(
    "1652044/0001193125-25-261546",  # J.Crew EDGAR accession
    signals_path="signals.json",
    industry="Retail",
    geography="US",
    require_audit_gate=True,
    include_tornado=True,
    cache_dir="cache"  # Optional: cache EDGAR fetches
)

# Check data sources in report
print("\n=== DATA SOURCES USED ===")
benchmarker = report.get('benchmarker_summary', {})
print("Comparables:", benchmarker.get('precedents', {}).get('comparables', [{}])[0].get('source'))
print("Recovery benchmarks:", benchmarker.get('precedents', {}).get('recovery_benchmarks', [{}])[0].get('source'))
print("Market multiple:", benchmarker.get('market_multiple', {}).get('source'))

# Check if Auditor flagged Critical Variance
auditor = report.get('auditor_summary', {})
if not auditor.get('passed'):
    print("\n⚠️ AUDIT FAILED:")
    for issue in auditor.get('issues', []):
        print(f"  - {issue}")

# Save report with manifest for reproducibility
output_path = Path("reports/jcrew_analysis.json")
output_path.parent.mkdir(exist_ok=True, parents=True)
with open(output_path, 'w') as f:
    json.dump(report, f, indent=2)

# Write run manifest for repro
from signal_triage.pipeline import write_run_manifest
write_run_manifest(
    output_path,
    report,
    pipeline_mode="single",
    input_path="1652044/0001193125-25-261546"
)
print(f"\n✅ Report saved: {output_path}")
print(f"✅ Manifest saved: {output_path.parent}/run_manifest.json")
```

---

## Troubleshooting

### SEC EDGAR 403 Forbidden
**Problem:** `requests.exceptions.HTTPError: 403 Forbidden`  
**Solution:** Set `SEC_USER_AGENT` with your email:
```bash
export SEC_USER_AGENT="YourApp/1.0 (your.email@example.com)"
```

### Rate Limit Errors
**Problem:** `Too many requests` or `429` errors  
**Solution:** The client automatically rate-limits, but if you're hitting limits:
- Increase cache TTL in config
- Reduce concurrent requests
- Upgrade to higher-tier API plan

### API Key Not Found
**Problem:** `API key not configured` errors  
**Solution:** Set the required environment variable:
```bash
# Check what's missing
python -c "from signal_triage.config import get_config; c = get_config(); print(c.api)"
```

### Stubs Being Used Instead of Live Data
**Problem:** Seeing "Source: Stub" in reports  
**Solution:** 
1. Verify `BENCHMARKER_USE_LIVE=1` is set
2. Check API keys are valid
3. Review logs for API errors: `export SIGNAL_TRIAGE_LOG_LEVEL=DEBUG`

---

## Advanced: Custom API Integration

To add a new data provider:

```python
# 1. Create client in signal_triage/api/
class NewProviderClient:
    def __init__(self):
        self.config = get_config()
        self.rate_limiter = get_rate_limiter()
        self.cache = get_cache_manager()
    
    def get_data(self):
        # Use infrastructure components
        self.rate_limiter.acquire("new_provider")
        # ... make API call ...
        
# 2. Integrate in benchmarker.py
def get_recovery_benchmarks(...):
    # Try new provider first
    if config.new_provider_enabled:
        client = NewProviderClient()
        data = client.get_data()
        if data:
            return data
    # Fall back to existing providers
    ...
```

---

## Next Steps

1. **Start with SEC EDGAR** (free, no API key): Set `SEC_USER_AGENT` and `BENCHMARKER_USE_LIVE=1`
2. **Add Treasury yields** (free): Register for FRED API key at fred.stlouisfed.org
3. **Enhance with stock data** (free tier): Get Alpha Vantage key at alphavantage.co
4. **Go premium** (optional): IEX Cloud for comprehensive financials, 9fin for recovery data

For more details, see:
- `docs/API_GUIDE.md` - Comprehensive API documentation
- `docs/PLAN_IMPLEMENTATION_COMPLETE.md` - Full implementation details
- `signal_triage/api/` - API client source code
- `tests/test_market_data_*.py` - Example usage in tests

---

**Date:** January 29, 2026  
**Status:** ✅ All live APIs operational

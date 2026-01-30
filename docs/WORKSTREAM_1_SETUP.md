# Workstream 1: Live Market Data Setup Guide

**Status:** Production-Ready  
**Date:** January 29, 2026

## Overview

Workstream 1 replaces stub data with live SEC EDGAR data and other market data APIs. This guide shows you how to configure and enable live data sources.

---

## Quick Start (5 minutes)

### Step 1: Configure SEC EDGAR (Required - Free)

SEC EDGAR requires a User-Agent with your contact email. Set this environment variable:

**PowerShell (Windows):**
```powershell
$env:SEC_USER_AGENT = "YourCompany/1.0 (your.email@example.com)"
```

**Bash (Linux/Mac):**
```bash
export SEC_USER_AGENT="YourCompany/1.0 (your.email@example.com)"
```

**Important:** Replace `your.email@example.com` with your actual email address. SEC requires this to contact you if there are issues with your usage.

### Step 2: Enable Live Data

```powershell
$env:BENCHMARKER_USE_LIVE = "1"
$env:BENCHMARKER_DATA_SOURCE = "edgar"
```

### Step 3: Verify Setup

```powershell
py demo_live_data.py
```

You should see:
- ✅ Live SEC EDGAR data is enabled
- ✅ Successfully fetched X comparables
- ✅ CONFIRMED: Using live SEC EDGAR data!

---

## What You Get (Free - No API Keys Required)

### SEC EDGAR Integration
- ✅ Recent 8-K filings (distress events, restructuring announcements)
- ✅ Company financials (revenue, debt, EBITDA from 10-K/10-Q filings)
- ✅ Filing history and amendments
- ✅ Bankruptcy and distress event detection

**Rate Limit:** 10 requests/second (SEC guideline)  
**Cost:** Free (no API key required)  
**Setup Time:** 2 minutes

---

## Enhanced Data (Free API Keys)

### FRED - Federal Reserve Economic Data

Get live US Treasury yields for credit spread calculations.

**Setup:**
1. Register at https://fred.stlouisfed.org/docs/api/api_key.html (2 minutes)
2. Get your free API key
3. Set environment variable:
   ```powershell
   $env:FRED_API_KEY = "your_fred_api_key_here"
   ```

**What You Get:**
- Live Treasury yields (2Y, 5Y, 10Y, 30Y)
- Credit spread calculations (bond yield vs Treasury)
- Macro indicators (GDP, unemployment, etc.)

**Rate Limit:** 120 requests/minute  
**Cost:** Free

---

### Alpha Vantage

Get real-time stock prices and bond yields.

**Setup:**
1. Register at https://www.alphavantage.co/support/#api-key (2 minutes)
2. Get your free API key  
3. Set environment variable:
   ```powershell
   $env:ALPHAVANTAGE_API_KEY = "your_alphavantage_api_key_here"
   ```

**What You Get:**
- Real-time stock quotes
- Treasury yields (alternative to FRED)
- Company fundamentals

**Rate Limit:** 25 requests/day (free tier) or 500/day (premium)  
**Cost:** Free tier available, premium plans start at $49.99/month

---

## Commercial Data Sources (Optional)

### IEX Cloud

Professional-grade stock data and company financials.

**Setup:**
1. Register at https://iexcloud.io/
2. Get API token (pay-as-you-go pricing)
3. Set environment variable:
   ```powershell
   $env:IEXCLOUD_API_TOKEN = "your_iex_token_here"
   ```

**What You Get:**
- Real-time stock quotes with market cap, P/E ratio, 52-week highs/lows
- Company financials (revenue, debt, EBITDA)
- Historical data

**Rate Limit:** Varies by plan  
**Cost:** Pay-as-you-go (starts at $9/month)

---

### 9fin (Restructuring Intelligence)

Precedent recovery rates, exit multiples, and transaction data.

**Setup:**
1. Subscribe at https://www.9fin.com/ (enterprise subscription required)
2. Get API key from 9fin
3. Set environment variable:
   ```powershell
   $env:NINEFIN_API_KEY = "your_9fin_api_key_here"
   ```

**What You Get:**
- Recovery rates by tranche and industry
- Precedent restructuring transactions
- Exit multiples (EV/EBITDA at emergence)
- Deal terms and structures

**Cost:** Contact 9fin for enterprise pricing

---

### Bloomberg Terminal

Comprehensive market data, CDS spreads, and peer analysis.

**Setup:**
1. Install blpapi: `pip install blpapi`
2. Ensure Bloomberg Terminal is running
3. Optionally set API key if using Bloomberg API:
   ```powershell
   $env:BLOOMBERG_API_KEY = "your_bloomberg_api_key_here"
   ```

**What You Get:**
- CDS spreads (credit default swap pricing)
- Peer EV/EBITDA multiples
- Comprehensive market data
- Credit curves

**Cost:** Bloomberg Terminal subscription (~$24k/year)

---

## Troubleshooting

### SEC EDGAR: 403 Forbidden

**Problem:** SEC is rejecting your requests with 403 Forbidden error.

**Solution:**
1. Make sure you set `SEC_USER_AGENT` with a **real email address**
2. SEC requires a valid contact email, not a placeholder
3. Example:
   ```powershell
   $env:SEC_USER_AGENT = "MyFund/1.0 (john.doe@myfund.com)"
   ```

**Note:** SEC will use this email to contact you if there are issues with your usage (e.g., exceeding rate limits).

---

### SEC EDGAR: 404 Not Found

**Problem:** Company financials not found (404 error).

**Possible Causes:**
1. Company doesn't file XBRL data with SEC (e.g., private companies)
2. CIK is incorrect
3. Company is foreign filer or exempt from XBRL

**Solution:**
- Verify CIK is correct
- Check if company files 10-K/10-Q with SEC
- Use alternative data sources (IEX Cloud, Alpha Vantage) for stock ticker lookup

---

### Rate Limiting

**Problem:** Getting rate limit errors or slow responses.

**Solution:**
- SEC EDGAR: Max 10 requests/second (automatic rate limiting built-in)
- FRED: Max 120 requests/minute
- Alpha Vantage: 25 requests/day (free) or 500/day (paid)

The system automatically handles rate limiting and retries. If you consistently hit limits:
1. Reduce request frequency
2. Upgrade to paid API plans (Alpha Vantage, IEX Cloud)
3. Enable caching (already enabled by default)

---

### Still Seeing Stub Data

**Problem:** Even with `BENCHMARKER_USE_LIVE=1`, you're still getting stub data.

**Checklist:**
1. ✅ Set `SEC_USER_AGENT` with real email
2. ✅ Set `BENCHMARKER_USE_LIVE=1`
3. ✅ Set `BENCHMARKER_DATA_SOURCE=edgar`
4. ✅ Run `py demo_live_data.py` to verify setup
5. ✅ Check console output for error messages

**Note:** If live API calls fail (network issues, rate limits, authentication errors), the system automatically falls back to stubs to ensure the pipeline continues running.

---

## Environment Variables Reference

### Core Configuration
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEC_USER_AGENT` | **Yes** | sample@example.com | Your contact email for SEC EDGAR |
| `BENCHMARKER_USE_LIVE` | No | `0` | Set to `1` to enable live data |
| `BENCHMARKER_DATA_SOURCE` | No | `stub` | Set to `edgar` for SEC EDGAR data |

### Free APIs (Optional)
| Variable | Description |
|----------|-------------|
| `FRED_API_KEY` | Federal Reserve Economic Data API key |
| `ALPHAVANTAGE_API_KEY` | Alpha Vantage API key |

### Commercial APIs (Optional)
| Variable | Description |
|----------|-------------|
| `IEXCLOUD_API_TOKEN` | IEX Cloud API token |
| `NINEFIN_API_KEY` | 9fin API key |
| `REORG_API_KEY` | Reorg Research API key |
| `DEBTWIRE_API_KEY` | Debtwire API key |
| `BLOOMBERG_API_KEY` | Bloomberg API key |
| `SP_CAPITAL_IQ_API_KEY` | S&P Capital IQ API key |
| `MOODYS_API_KEY` | Moody's Analytics API key |
| `FITCH_API_KEY` | Fitch Solutions API key |

---

## Testing Your Setup

### Run Demo Script
```powershell
py demo_live_data.py
```

Expected output:
```
✅ Live SEC EDGAR data is enabled
✅ Successfully fetched 5 comparables
✅ CONFIRMED: Using live SEC EDGAR data!
```

### Check API Status
```python
from signal_triage.agents.market_data_live import get_available_apis, get_recommended_setup

# See which APIs are configured
print(get_available_apis())

# Get setup instructions
print(get_recommended_setup())
```

---

## Production Checklist

Before deploying to production:

- [ ] Set `SEC_USER_AGENT` with valid email
- [ ] Enable live data (`BENCHMARKER_USE_LIVE=1`)
- [ ] Set data source (`BENCHMARKER_DATA_SOURCE=edgar`)
- [ ] Test with `py demo_live_data.py`
- [ ] Verify no 403/404 errors in logs
- [ ] Optional: Add FRED API key for Treasury yields
- [ ] Optional: Add commercial API keys (9fin, IEX Cloud, etc.)
- [ ] Monitor rate limits and API usage
- [ ] Set up error alerting for API failures

---

## Next Steps

1. **Complete Workstream 1 Setup:**
   - Configure SEC EDGAR (required)
   - Add FRED API key (recommended)
   - Test with demo script

2. **Run Full Pipeline:**
   ```powershell
   py -m signal_triage.cli your_document.pdf --pipeline
   ```

3. **Verify Live Data:**
   - Check benchmarker outputs include "SEC EDGAR" sources
   - Verify Treasury yields are live (when FRED configured)
   - Monitor API usage and rate limits

4. **Optional Enhancements:**
   - Add commercial API keys (9fin, Bloomberg, etc.)
   - Set up Redis caching for high-volume usage
   - Configure monitoring and alerts

---

## Support

- **SEC EDGAR API:** https://www.sec.gov/edgar/sec-api-documentation
- **FRED API:** https://fred.stlouisfed.org/docs/api/
- **Signal Triage Issues:** See docs/TROUBLESHOOTING.md

---

## Summary

**Minimum Setup (5 minutes):**
- Set `SEC_USER_AGENT` with your email
- Set `BENCHMARKER_USE_LIVE=1` and `BENCHMARKER_DATA_SOURCE=edgar`
- Run demo script to verify

**Recommended Setup (15 minutes):**
- Add FRED API key (free, 2 minutes to register)
- Add Alpha Vantage API key (free, 2 minutes to register)
- Test with full pipeline

**Production Setup:**
- Consider commercial APIs (9fin, IEX Cloud, Bloomberg)
- Set up monitoring and alerts
- Configure Redis caching for scale

**You're now ready to use live market data in Signal Triage! 🚀**

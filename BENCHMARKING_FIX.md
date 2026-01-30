# Benchmarking Fixes - January 29, 2026

## Issues Fixed

### 1. KeyError in Market Benchmarking Page ❌ → ✅
**Problem:** The app was crashing with `KeyError: slice(None, 5, None)` when displaying precedent data.

**Root Cause:** The code was treating `precedents` as a list, but it's actually a dictionary with nested keys:
- `comparables` - Recent restructuring filings
- `recovery_benchmarks` - Historical recovery rates by tranche
- `exit_multiples` - EV/EBITDA multiples for emerged/sold companies

**Fix:** Updated all three tabs to correctly access the nested data structure:
- **Tab 1 (Market Multiples):** Now displays exit multiples, comparables count, and market multiple source
- **Tab 2 (Precedent Comparables):** Now shows recovery benchmarks and comparables with proper data structure access
- **Tab 3 (Critical Variance):** Now correctly filters and displays critical variances from `recovery_variance` list

### 2. Live Data Not Pulling ❌ → ✅
**Problem:** Live market data wasn't fetching from SEC EDGAR or other sources.

**Root Cause:** Configuration issue in `.env` file:
```bash
BENCHMARKER_USE_LIVE=0  # ❌ Live data DISABLED
```

**Fix:** Enabled live data in `.env`:
```bash
BENCHMARKER_USE_LIVE=1  # ✅ Live data ENABLED
```

## Configuration Guide

### Required Setup for Live Data

#### 1. Enable Live Data (✅ Already Done)
```bash
# In .env file
BENCHMARKER_USE_LIVE=1
BENCHMARKER_DATA_SOURCE=edgar
```

#### 2. Configure SEC EDGAR User-Agent
The SEC requires a valid User-Agent with your contact email.

**Current (placeholder):**
```bash
SEC_USER_AGENT=SignalTriage/1.0 (distressed.analyst@example.com)
```

**Update to your email:**
```bash
SEC_USER_AGENT=SignalTriage/1.0 (your.actual.email@domain.com)
```

**Why?** SEC blocks requests without proper identification. See: https://www.sec.gov/os/webmaster-faq

#### 3. Optional: Add Free API Keys for Enhanced Data

**FRED (Treasury Yields) - FREE**
```bash
# Register at: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY=your_api_key_here
```

**Alpha Vantage (Stock Prices) - FREE**
```bash
# Register at: https://www.alphavantage.co/support/#api-key
# Free tier: 25 calls/day
ALPHAVANTAGE_API_KEY=your_api_key_here
```

**IEX Cloud (Company Financials) - PAID**
```bash
# Register at: https://iexcloud.io/
IEXCLOUD_API_TOKEN=your_token_here
```

#### 4. Optional: Commercial Data (9fin, Bloomberg, Rating Agencies)
```bash
# 9fin - Recovery rates and exit multiples
NINEFIN_API_KEY=your_key_here

# Bloomberg Terminal
BLOOMBERG_API_KEY=your_key_here

# Credit Rating Agencies
SP_CAPITAL_IQ_API_KEY=your_key_here
MOODYS_API_KEY=your_key_here
FITCH_API_KEY=your_key_here
```

## Data Sources Hierarchy

The benchmarker uses a **fallback chain** for each data type:

### Recovery Benchmarks
1. **9fin API** (if `NINEFIN_API_KEY` set) - Most comprehensive
2. **SEC EDGAR** (if `BENCHMARKER_USE_LIVE=1`) - Free, limited scope
3. **Historical Averages** (stub) - Fallback with empirical defaults

### Market Multiples
1. **9fin API** (if `NINEFIN_API_KEY` set)
2. **Historical Industry Averages** (stub)

### Comparables
1. **SEC EDGAR Recent 8-Ks** (if `BENCHMARKER_USE_LIVE=1`) - Free
2. **Stub Data** (demo)

## What Data You'll Get Now

### With Current Setup (BENCHMARKER_USE_LIVE=1, no API keys)

✅ **Live Data:**
- SEC EDGAR recent 8-K filings (recent restructurings)
- Company names, filing dates, CIKs

❌ **Stub/Historical Data:**
- Recovery rates (historical averages by tranche type)
- Exit multiples (historical industry averages)
- Treasury yields (need FRED_API_KEY)
- Stock prices (need ALPHAVANTAGE_API_KEY)

**Example Recovery Rate Defaults (Historical Averages):**
- 1st Lien Senior Secured: 72%
- 2nd Lien: 48%
- Senior Unsecured: 45%
- Subordinated: 25%

**Example Exit Multiple Defaults (Historical Averages):**
- Retail: 5.5x EBITDA
- Energy: 6.0x
- Healthcare: 7.5x
- Technology: 8.0x

### With Free API Keys Added

✅ **Additional Live Data:**
- Real-time Treasury yields (FRED)
- Stock prices (Alpha Vantage - 25/day limit)
- Company financials (IEX Cloud if paid)

### With Commercial APIs (9fin, Bloomberg, etc.)

✅ **Full Live Data:**
- Actual recovery rates from recent restructurings
- Real-time exit multiples from precedent transactions
- Professional-grade credit analysis
- News sentiment and market signals

## Testing the Fix

1. **Restart your Streamlit app:**
```bash
# Stop the current app (Ctrl+C)
# Restart it
streamlit run signal_triage/ui/1_🏠_Signal_Triage.py
```

2. **Navigate to Market Benchmarking** (Page 3)

3. **Test Tab 1 (Market Multiples):**
   - Click "🚀 Run Benchmarking"
   - Should see:
     - Market EV/EBITDA metric
     - Comparables count
     - Exit multiples cards with company names
     - Data freshness info

4. **Test Tab 2 (Precedent Comparables):**
   - Set model recovery percentages (e.g., Senior 80%, Mezz 40%, Unsecured 10%)
   - Click "📊 Run Precedent Comparison"
   - Should see:
     - Recovery Benchmarks section with tranche types and percentages
     - Recent Comparables section with SEC EDGAR filings
     - Source citations showing data quality

5. **Test Tab 3 (Critical Variance):**
   - After running Precedent Comparison in Tab 2
   - Should see:
     - Variance checks for each tranche
     - Red boxes for critical variances (>25% difference)
     - Green box if all within bounds
     - "Enable NINEFIN_API_KEY" message (expected without paid API)

## Expected Behavior

### Success Indicators ✅
- No `KeyError` crashes
- Benchmark results display correctly
- Precedent data shows recovery benchmarks and comparables
- Data sources are cited (stub vs live)
- Critical variance analysis works

### Known Limitations (Expected)
- Recovery rates are **historical averages** (not live) without NINEFIN_API_KEY
- Exit multiples are **industry averages** (not live) without 9fin
- SEC EDGAR provides filings but not recovery percentages
- Message: "Enable NINEFIN_API_KEY for live recovery benchmarks" is **normal**

## Troubleshooting

### Issue: Still seeing KeyError
**Solution:** Make sure you restarted the Streamlit app after the code changes.

### Issue: "Data freshness: unknown" or "stale"
**Solution:** This is expected for stub data. Add API keys for live data freshness.

### Issue: SEC EDGAR returns no results
**Solution:** Check your SEC_USER_AGENT in `.env` has a valid email.

### Issue: "No recovery benchmarks available"
**Solution:** This is expected without NINEFIN_API_KEY. The message is informational.

### Issue: Variance check says "Cannot check variance"
**Solution:** Expected when recovery_pct is None (SEC EDGAR comparables don't have this data). Add NINEFIN_API_KEY for actual recovery rates.

## Next Steps (Optional)

### To Get Live Recovery Rates
1. Sign up for 9fin API (commercial): https://www.9fin.com/
2. Add `NINEFIN_API_KEY` to `.env`
3. Restart app

### To Get Live Market Data
1. Register for free FRED API key
2. Register for free Alpha Vantage API key
3. Add keys to `.env`
4. Restart app

### To Improve Data Quality
The benchmarker will automatically prefer live data when available:
- 9fin > SEC EDGAR > Historical Averages (recovery rates)
- Live APIs > Stub (market data)

## Summary

✅ **Fixed:** KeyError crash when displaying precedent data
✅ **Fixed:** Data structure access in all three tabs
✅ **Enabled:** Live SEC EDGAR data (BENCHMARKER_USE_LIVE=1)
✅ **Documented:** Configuration and data source hierarchy
⚠️ **Note:** Without commercial APIs (9fin), recovery rates are historical averages
💡 **Recommended:** Add free FRED and Alpha Vantage keys for better live data coverage

---

**Questions or Issues?** Check the logs for specific error messages and verify your `.env` configuration matches this guide.

# Signal Triage Quick Start Guide

**Goal:** Run your first distressed debt analysis in **5 minutes**.

---

## Prerequisites

```bash
# Install Signal Triage (if not already installed)
pip install -e .

# Verify installation
signal-triage --help
```

---

## Tutorial 1: Basic Analysis (J.Crew)

### Step 1: Run Basic Analysis
```bash
signal-triage examples/jcrew/jcrew_credit_agreement.txt
```

**Expected Output:**
```
=== DISTRESS SCORE ===
Score: 82/100 (CRITICAL DISTRESS)
Tier: Tier 4 (Distressed)

=== TOP SIGNALS ===
1. dropdown (weight: 10, severity: high)
2. asset_sale_basket (weight: 8, severity: high)
3. transfer_to_unrestricted_sub (weight: 9, severity: high)
...
```

**What Happened:**
- Signal Triage scanned the credit agreement
- Detected 3 LME patterns (dropdown, asset transfer, unrestricted sub)
- Calculated distress score based on signal weights
- Assigned Tier 4 (Distressed) classification

---

### Step 2: Get JSON Output
```bash
signal-triage examples/jcrew/jcrew_credit_agreement.txt --json > jcrew_output.json
```

**Use Case:** Feed into portfolio management system or custom dashboards.

---

### Step 3: Run Librarian (Covenant Extraction)
```bash
signal-triage examples/jcrew/jcrew_credit_agreement.txt --librarian
```

**Expected Output:**
```json
{
  "baskets_detected": [
    {
      "basket_type": "asset_sale",
      "size": "greater of $50M or 15% of Consolidated Assets",
      "restrictions": ["No consent required if <$50M"],
      "risk_level": "HIGH"
    },
    {
      "basket_type": "unrestricted_subsidiary_investment",
      "size": "$250M or 25% of Consolidated Assets",
      "restrictions": ["One-time transfer allowed"],
      "risk_level": "CRITICAL"
    }
  ],
  "collateral_leakage_flags": [
    "unrestricted_sub_transfer",
    "ip_carveout"
  ]
}
```

**What Happened:**
- Librarian extracted basket definitions from the agreement
- Identified sizes and restrictions for each basket
- Flagged collateral leakage risks (IP transfer, unrestricted sub)

---

## Tutorial 2: Recovery Waterfall (Hertz)

### Step 1: Basic Waterfall
```bash
signal-triage --waterfall --ev 9000 \
  --tranches "DIP:1000,FirstLien:6500,SecondLien:1500,Unsecured:3000"
```

**Expected Output:**
```
=== RECOVERY WATERFALL ===
Enterprise Value: $9,000M

DIP (Claim: $1,000M)
  Recovery: $1,000M (100.0%)
  Status: PAID IN FULL

First Lien (Claim: $6,500M)
  Recovery: $6,500M (100.0%)
  Status: PAID IN FULL

Second Lien (Claim: $1,500M) ← FULCRUM SECURITY
  Recovery: $1,500M (100.0%)
  Status: PAID IN FULL

Unsecured (Claim: $3,000M)
  Recovery: $0M (0.0%)
  Status: OUT OF THE MONEY

=== SITUATIONAL SUMMARY ===
Fulcrum: Second Lien (100.0% recovery)
Critical Tier: Unsecured (0.0% recovery)
```

**What Happened:**
- Waterfall distributed $9B EV across $12B of claims
- Fulcrum identified at Second Lien (last tranche paid in full)
- Unsecured creditors out of the money

---

### Step 2: EV Sensitivity Analysis
```bash
signal-triage --waterfall --ev 9000 \
  --tranches "DIP:1000,FirstLien:6500,SecondLien:1500,Unsecured:3000" \
  --ev-sensitivity 7000,9000,11000
```

**Expected Output:**
```
=== EV SENSITIVITY ===

Scenario: EV = $7,000M (Bear)
  DIP: 100.0%
  First Lien: 92.3% ← FULCRUM
  Second Lien: 0.0%
  Unsecured: 0.0%

Scenario: EV = $9,000M (Base)
  DIP: 100.0%
  First Lien: 100.0%
  Second Lien: 100.0% ← FULCRUM
  Unsecured: 0.0%

Scenario: EV = $11,000M (Bull)
  DIP: 100.0%
  First Lien: 100.0%
  Second Lien: 100.0%
  Unsecured: 33.3% ← FULCRUM
```

**What Happened:**
- Ran waterfall across 3 EV scenarios
- Fulcrum migrates as EV changes (1L → 2L → Unsecured)
- Shows recovery range for each tranche

---

### Step 3: APR Violation Check
```bash
signal-triage --waterfall --ev 9000 \
  --tranches "DIP:1000,FirstLien:6500,SecondLien:1200,Unsecured:3000" \
  --check-apr
```

**Expected Output:**
```
⚠️ APR VIOLATION DETECTED

First Lien recovered: 98.5% (not paid in full)
Second Lien recovered: 100.0% (junior made whole while senior impaired)

Critical Issue: Junior creditors receiving full recovery while senior lenders underwater.
This violates Absolute Priority Rule (APR) and may trigger litigation risk.
```

**What Happened:**
- Detected that 2L received 100% recovery while 1L only got 98.5%
- Flagged as APR violation (junior paid before senior made whole)
- This would be challenged in bankruptcy court

---

## Tutorial 3: Full Pipeline (Serta)

### Step 1: Run Complete Pipeline
```bash
signal-triage examples/serta/serta_credit_agreement.txt --pipeline
```

**What Happens (Sequential):**
1. **Ingest** — Parse document, extract text chunks
2. **Librarian** — Extract covenants, baskets, collateral leakage flags
3. **Quant** — Run waterfall (if data available) or identify required inputs
4. **Benchmarker** — Compare to market precedents (stub in basic mode)
5. **Auditor** — Stress-test precision, validate APR, check for Critical Variance
6. **Reporter** — Generate single auditable report

**Expected Output:** `serta_auditable_report.json` in current directory.

---

### Step 2: Batch Mode (All Examples)
```bash
signal-triage --pipeline --batch examples/
```

**What Happens:**
- Runs pipeline on ALL documents in examples/ directory
- Comparator activates (compares J.Crew vs Serta vs Hertz)
- Generates portfolio summary: `batch_portfolio_report.json`

**Portfolio Summary Includes:**
- Score distribution across portfolio
- Most common LME patterns
- High-risk holdings requiring immediate attention
- Tier migration (e.g., "Hertz moved from Tier 3 to Tier 4")

---

## Tutorial 4: Dashboard Visualization

### Step 1: Launch Dashboard
```bash
streamlit run signal_triage/ui/dashboard.py
```

**Opens Bloomberg-style interface in browser at http://localhost:8501**

---

### Step 2: Upload Document
1. Click "Upload Credit Agreement / 10-K"
2. Select `examples/jcrew/jcrew_credit_agreement.txt`
3. Click "Analyze"

---

### Step 3: Explore Interactive Features

**Score Card:**
- Distress score gauge (color-coded: green → yellow → red)
- Tier assignment (Tier 1–5)
- Top 5 signals with severity badges

**LME Flags Panel:**
- Click any LME category for full definition
- Hover for severity level and market precedents
- Export to PDF for client presentations

**Recovery Waterfall:**
- Adjust EV slider to see real-time fulcrum migration
- Toggle "Show APR Violations" to highlight issues
- Export waterfall to Excel

**Covenant Headroom:**
- Gauge showing leverage and FCCR headroom
- Critical distress threshold (<15%) highlighted
- EBITDA normalization with add-back haircuts

---

## Common Commands Cheat Sheet

```bash
# Basic analysis
signal-triage <file>

# JSON output (for automation)
signal-triage <file> --json

# Verbose (debugging)
signal-triage <file> --verbose

# Librarian only (covenant extraction)
signal-triage <file> --librarian

# Waterfall with custom tranches
signal-triage --waterfall --ev <value> --tranches "Tranche1:Amt,Tranche2:Amt"

# EV sensitivity
signal-triage --waterfall --ev <base> --ev-sensitivity <low>,<base>,<high> \
  --tranches "<tranches>"

# Full pipeline (single file)
signal-triage <file> --pipeline

# Batch pipeline (folder)
signal-triage --pipeline --batch <folder>

# Dashboard
streamlit run signal_triage/ui/dashboard.py
```

---

## Understanding the Output

### Distress Score Scale
- **0-30:** Investment Grade (low risk)
- **31-50:** Crossover (monitoring)
- **51-70:** High Yield (elevated risk)
- **71-85:** Distressed (restructuring likely)
- **86-100:** Critical Distress (imminent default)

### Tier Assignments
- **Tier 1:** Minimal LME risk, strong covenant package
- **Tier 2:** Standard market terms, some trap doors
- **Tier 3:** Cov-lite with moderate LME exposure
- **Tier 4:** Distressed, active LME vulnerabilities
- **Tier 5:** Critical, multiple severe LME exploits detected

### Severity Levels (LME Signals)
- **LOW:** Monitoring warranted, not immediate threat
- **MEDIUM:** Elevated risk, requires analysis
- **HIGH:** Material risk, potential value impairment
- **CRITICAL:** Severe risk, likely value destruction

---

## Next Steps

### For Credit Analysts
1. Run batch mode on your portfolio holdings
2. Export JSON for integration with risk systems
3. Set up daily monitoring via API (see [docs/QUICK_START_API.md](../docs/QUICK_START_API.md))

### For Distressed Investors
1. Deep-dive into Hertz waterfall with your EV assumptions
2. Model fulcrum migration across EV scenarios
3. Validate APR in proposed plans of reorganization

### For Restructuring Advisors
1. Study J.Crew and Serta patterns in client agreements
2. Use Librarian to extract basket language
3. Generate client-ready reports via Dashboard → Export to PDF

### For Developers
1. Explore API endpoints: `python run_api_server.py`
2. Read [docs/API_INFRASTRUCTURE.md](../docs/API_INFRASTRUCTURE.md)
3. Contribute new LME patterns or improve detection logic

---

## Troubleshooting

### "Module not found: signal_triage"
```bash
# Reinstall in development mode
pip install -e .
```

### "No signals detected in document"
- Ensure document contains covenant language (not just financials)
- Try `--verbose` flag to see what text was ingested
- Check that file is readable (UTF-8 encoding preferred)

### "Waterfall requires --tranches"
- Format: `"TrancheName:ClaimAmount,TrancheName2:ClaimAmount"`
- Example: `"Senior:100,Mezz:50,Unsecured:25"`
- No spaces, comma-separated, colon between name and amount

### Dashboard won't launch
```bash
# Install Streamlit if missing
pip install streamlit

# Try specifying port
streamlit run signal_triage/ui/dashboard.py --server.port 8502
```

---

## 🎓 Learning Path

**Beginner (Day 1):**
- Tutorial 1: J.Crew basic analysis
- Understand distress scores and tiers
- Learn to read LME signal output

**Intermediate (Week 1):**
- Tutorial 2: Hertz waterfall
- EV sensitivity and fulcrum identification
- APR violation detection

**Advanced (Month 1):**
- Tutorial 3: Full pipeline on Serta
- Batch mode for portfolio analysis
- Dashboard visualization and export

**Expert (Ongoing):**
- API integration for automated monitoring
- Custom LME pattern development
- Contributing to open-source enhancements

---

## 📞 Support

- **Documentation:** `docs/` directory
- **Issues:** GitHub Issues (if applicable)
- **Community:** See main README for contact info

---

**Ready to analyze real distressed debt? Start with Tutorial 1 above!**

---

**Last Updated:** January 2026

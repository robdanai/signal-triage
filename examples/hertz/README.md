# Hertz Case Study: APR Violations & Recovery Waterfall

## Executive Summary

**Company:** The Hertz Corporation  
**Event Date:** May 2020 (Chapter 11 Filing)  
**Focus:** Recovery Waterfall, Fulcrum Analysis, APR Violation Detection  
**Key Issues:** Junior creditors/equity receiving value while seniors underwater; going concern vs. liquidation  
**Outcome:** Controversial emergence with equity receiving value (rare for Ch. 11)

---

## Background

### The Chapter 11 Filing
Hertz filed for Chapter 11 bankruptcy protection in May 2020, catalyzed by the COVID-19 pandemic's impact on travel and rental car demand:

1. **Liquidity Crisis:** Travel demand collapsed 90%+ in March-April 2020
2. **Asset-Backed Debt:** $19B+ of asset-backed debt secured by rental car fleet
3. **Unsecured Creditors:** Significant unsecured debt and lease obligations
4. **Equity Value:** Initially assumed worthless; later, retail trading surge created apparent value

### Capital Structure (At Filing, Simplified)
- **DIP Financing:** $1.0B debtor-in-possession facility
- **Asset-Backed First Lien (Fleet):** $6.5B secured by rental car fleet
- **Corporate Second Lien:** $1.5B secured by corporate assets (junior to fleet ABS)
- **Unsecured Debt:** $3.0B (bonds, trade claims, lease rejection damages)
- **Equity:** Common stock (pre-petition value: ~$0)

### The Controversy: Meme Stock & APR Concerns
During bankruptcy:
- **Retail Trading Surge:** Hertz equity traded up from $0.50 to $6.00+ (June 2020)
- **Proposed Equity Offering:** Hertz sought court approval to issue new stock to retail investors (while in bankruptcy)
- **APR Concerns:** If equity had value, were unsecured creditors being impaired while equity got value?
- **Market Speculation:** Asset values (rental cars) recovered faster than expected; enterprise potentially solvent

---

## Key Analytical Signals

### 1. **Fulcrum Security Identification**
**Definition:** Fulcrum security is the most senior tranche in the capital structure that does NOT receive full recovery (first tranche to be impaired).

**Hertz Analysis:**
```
Scenario: EV = $9.0B (going concern)

DIP (Claim: $1.0B)
  Recovery: $1.0B (100%)
  Status: PAID IN FULL

First Lien ABS (Claim: $6.5B)
  Recovery: $6.5B (100%)
  Status: PAID IN FULL

Second Lien (Claim: $1.5B) ← FULCRUM
  Recovery: $1.5B (100%)
  Status: PAID IN FULL (at edge)

Unsecured (Claim: $3.0B)
  Recovery: $0B (0%)
  Status: OUT OF THE MONEY

Interpretation: Second Lien is fulcrum (last class paid in full). Unsecured is deeply underwater.
```

### 2. **APR Violation Risk**
**Definition:** Absolute Priority Rule (APR) requires senior creditors be paid in full before junior creditors/equity receive any value.

**Hertz Red Flags:**
- **Equity Trading:** If equity had market value ($2B+ market cap at peak), why?
- **Going Concern Premium:** EV potentially higher than liquidation (asset value recovery)
- **Unsecured Impairment:** If unsecured creditors not paid in full, equity should get nothing

**APR Test:**
```
If EV = $11.0B (upside case):
  DIP: $1.0B (100%)
  First Lien: $6.5B (100%)
  Second Lien: $1.5B (100%)
  Unsecured: $2.0B / $3.0B (67%)
  Equity: $0 (APR prevents equity value while unsecured impaired)

If EV = $13.0B+ (bull case):
  DIP: $1.0B (100%)
  First Lien: $6.5B (100%)
  Second Lien: $1.5B (100%)
  Unsecured: $3.0B (100%)
  Equity: $1.0B+ (67% to equity ONLY if unsecured paid in full)

Actual Market (June 2020): Equity traded as if EV = $13B+ (implied equity value $2B)
Reality Check: Was EV truly $13B+, or was retail speculation disconnected from fundamentals?
```

### 3. **Going Concern vs. Liquidation**
**Key Question:** Is the enterprise worth more as a going concern (continued operations) or in liquidation (piecemeal asset sales)?

**Hertz Valuation:**
| Valuation Method | Estimated Value | Waterfall Result |
|------------------|-----------------|------------------|
| **Liquidation (Piecemeal)** | $7.0B | Unsecured gets $0; equity worthless |
| **Going Concern (Distressed)** | $9.0B | Unsecured gets $0; equity worthless |
| **Going Concern (Recovery)** | $11.5B | Unsecured gets 67%; equity worthless |
| **Going Concern (Optimistic)** | $13.5B+ | Unsecured gets 100%; equity has value |

**Market Implication:** Retail equity surge suggested market believed in $13B+ going concern value (optimistic case). Credit investors skeptical.

---

## Signal Triage Analysis

### Run Analysis
```bash
# Basic waterfall
signal-triage --waterfall --ev 9000 \
  --tranches "DIP:1000,FirstLien:6500,SecondLien:1500,Unsecured:3000"

# EV sensitivity (bear to bull)
signal-triage --waterfall --ev 9000 --ev-sensitivity 7000,9000,11000,13000 \
  --tranches "DIP:1000,FirstLien:6500,SecondLien:1500,Unsecured:3000"

# APR violation check
signal-triage --waterfall --ev 11000 \
  --tranches "DIP:1000,FirstLien:6500,SecondLien:1500,Unsecured:3000,Equity:0" \
  --check-apr
```

### Expected Distress Score: **72/100 (DISTRESSED)**

### Key Signals Detected:
1. **fulcrum_security** (Second Lien)
2. **apr_violation_risk** (if equity receives value while unsecured impaired)
3. **going_concern_vs_liquidation** (material valuation gap)
4. **covenant_breach** (leverage, liquidity covenants failed)
5. **ch11_feasibility** (reorganization vs. liquidation analysis)

---

## Recovery Waterfall Scenarios

### Scenario 1: Liquidation (Bear Case, EV = $7.0B)
```
Enterprise Value: $7,000M (piecemeal liquidation)

DIP (Claim: $1,000M)
  Recovery: $1,000M (100.0%)
  Status: PAID IN FULL (DIP super-priority)

First Lien ABS (Claim: $6,500M)
  Recovery: $6,000M (92.3%) ← FULCRUM
  Status: IMPAIRED (underwater by $500M)

Second Lien (Claim: $1,500M)
  Recovery: $0M (0.0%)
  Status: OUT OF THE MONEY

Unsecured (Claim: $3,000M)
  Recovery: $0M (0.0%)
  Status: OUT OF THE MONEY

Equity
  Recovery: $0M (worthless)

Interpretation: Liquidation destroys value. Even first lien ABS (secured by cars) takes haircut due to distressed asset sale pricing.
```

### Scenario 2: Going Concern (Base Case, EV = $9.0B)
```
Enterprise Value: $9,000M

DIP (Claim: $1,000M)
  Recovery: $1,000M (100.0%)

First Lien ABS (Claim: $6,500M)
  Recovery: $6,500M (100.0%)

Second Lien (Claim: $1,500M) ← FULCRUM
  Recovery: $1,500M (100.0%)
  Status: Made whole (at edge)

Unsecured (Claim: $3,000M)
  Recovery: $0M (0.0%)
  Status: OUT OF THE MONEY (deeply underwater)

Equity
  Recovery: $0M (no APR violation)

Interpretation: Going concern preserves value for secured creditors. Unsecured creditors and equity out of the money. This is APR-compliant (seniors paid before juniors).
```

### Scenario 3: Recovery (Upside Case, EV = $11.5B)
```
Enterprise Value: $11,500M

DIP (Claim: $1,000M)
  Recovery: $1,000M (100.0%)

First Lien ABS (Claim: $6,500M)
  Recovery: $6,500M (100.0%)

Second Lien (Claim: $1,500M)
  Recovery: $1,500M (100.0%)

Unsecured (Claim: $3,000M) ← FULCRUM
  Recovery: $2,500M (83.3%)
  Status: Impaired but receiving material value

Equity
  Recovery: $0M (APR prevents equity value while unsecured impaired)
  Status: Worthless (no distribution)

APR CHECK: COMPLIANT (equity receiving $0 while unsecured impaired)

Interpretation: Unsecured creditors receive partial recovery. Equity still worthless per APR. Market capitalization ($2B in June 2020) disconnected from bankruptcy fundamentals.
```

### Scenario 4: Bull Case (EV = $13.5B - Optimistic)
```
Enterprise Value: $13,500M

DIP (Claim: $1,000M)
  Recovery: $1,000M (100.0%)

First Lien ABS (Claim: $6,500M)
  Recovery: $6,500M (100.0%)

Second Lien (Claim: $1,500M)
  Recovery: $1,500M (100.0%)

Unsecured (Claim: $3,000M)
  Recovery: $3,000M (100.0%)

Equity ← FULCRUM
  Recovery: $1,500M (value to equity)
  Status: IN THE MONEY

APR CHECK: COMPLIANT (equity only receives value after all creditors paid in full)

Interpretation: Only in bull case ($13.5B+ EV) does equity have value. This would require travel demand recovery exceeding pre-COVID levels. Retail trading in June 2020 suggested belief in this scenario.
```

---

## APR Violation Analysis

### What is APR?
**Absolute Priority Rule (11 U.S.C. § 1129(b)):** In a cramdown (non-consensual plan), no junior class may receive any value unless all senior classes are paid in full.

**Hierarchy:**
```
1. DIP Financing (super-priority)
2. Secured Claims (by lien priority)
3. Priority Unsecured Claims (e.g., taxes, wages)
4. General Unsecured Claims
5. Subordinated Claims
6. Equity
```

### Hertz APR Analysis

#### Compliant Scenario (Base Case, EV = $9.0B):
```
Unsecured: $0 (0%)
Equity: $0 (0%)

APR Status: COMPLIANT
Rationale: Equity receiving nothing while unsecured also receiving nothing. Both out of the money. No violation.
```

#### Violation Scenario (Hypothetical):
```
Unsecured: $2,000M / $3,000M (67%)
Equity: $500M (value distribution to equity holders)

APR Status: VIOLATION
Rationale: Equity receiving value while unsecured not paid in full. Violates absolute priority rule.

Creditor Remedy: Object to plan; seek cramdown denying equity any value.
```

#### Actual Hertz Outcome (June 2021):
```
Confirmed Plan:
  First Lien: Paid in full
  Second Lien: Converted to equity in reorganized Hertz
  Unsecured: 70-80% recovery (better than expected)
  Old Equity: Worthless (cancelled)
  New Equity: Issued to creditors and new investors

APR Status: COMPLIANT (old equity cancelled; new equity issued as part of reorganization)
Market Anomaly: Old equity traded at $2-6 during bankruptcy despite being cancelled in plan
Explanation: Retail speculation; disconnect between trading price and bankruptcy outcome
```

---

## Forensic Questions for Ch. 11 Analysis

### 1. **What is the Fulcrum Security?**
- Run waterfall across EV scenarios
- Identify last tranche to receive 100% recovery
- Focus investment on securities at or near fulcrum (highest risk-adjusted return)

### 2. **Is There APR Violation Risk?**
- Check if equity receiving value (distributions, retained ownership, warrants)
- Verify all senior creditors paid in full before equity gets anything
- Look for "gifting" (junior classes paying senior classes to allow junior to retain value)

### 3. **Going Concern vs. Liquidation: What's the Spread?**
- **Large spread (>30%):** Strong incentive to reorganize; creditor value maximized via Ch. 11
- **Small spread (<10%):** Liquidation may be preferable; reorganization costly and uncertain

### 4. **Are Valuation Assumptions Reasonable?**
- EBITDA multiples: Compare to public comps and precedent transactions
- Discount rates: Risk-adjust for distressed operations and bankruptcy uncertainty
- Terminal value: Is perpetual growth assumption justified?

### 5. **What is the Break-Even Enterprise Value?**
- Calculate EV at which each tranche becomes in-the-money
- Example: Unsecured creditors in-the-money if EV > $9.0B (Hertz base case)

---

## Lessons Learned

### **For Credit Investors:**
1. **Fulcrum is Golden:** Highest risk-adjusted returns typically at fulcrum security
2. **APR Protections:** Ensure plan complies with absolute priority; object if equity receives value while you're impaired
3. **Valuation is Key:** Enterprise value drives recovery; scrutinize management projections
4. **Retail Speculation ≠ Fundamentals:** Hertz equity trading disconnected from bankruptcy reality

### **For Equity Investors:**
1. **Bankruptcy = Wipeout (Usually):** Equity worthless unless enterprise solvent (rare)
2. **APR Applies:** Equity cannot receive value unless all creditors paid in full
3. **Trading During Bankruptcy:** High risk; prices often irrational (Hertz meme stock)

### **For Restructuring Professionals:**
1. **Going Concern Value Creation:** Maximize EV via operational improvements, asset sales
2. **Creditor Negotiations:** Fulcrum creditors control the process; focus negotiations there
3. **APR Compliance:** Ensure plan structure complies with APR to avoid litigation and confirmation risk

---

## Dashboard Visualization

### Run Dashboard with Hertz Data
```bash
streamlit run signal_triage/ui/dashboard.py

# Upload: examples/hertz/hertz_10k_excerpt.txt
# Configure waterfall:
#   - EV: $9,000M
#   - Tranches: DIP:1000, FirstLien:6500, SecondLien:1500, Unsecured:3000
# Adjust EV slider: Watch fulcrum migrate from SecondLien → Unsecured → Equity
```

### Key Dashboard Features for Hertz Analysis:
- **EV Sensitivity Slider:** Real-time fulcrum identification as EV changes
- **APR Violation Indicator:** Red flag if junior receives value while senior impaired
- **Recovery Table:** % recovery for each tranche across scenarios
- **Waterfall Chart:** Visual representation of value distribution

---

## Comparative Analysis: Hertz vs. Other Ch. 11 Cases

| Company | Filing Date | Fulcrum Security | Equity Outcome | APR Compliant? |
|---------|-------------|------------------|----------------|----------------|
| **Hertz** | May 2020 | Second Lien | Cancelled (worthless) | YES |
| **J.Crew** | May 2020 | First Lien Term Loan | Cancelled | YES |
| **Neiman Marcus** | May 2020 | Second Lien / Unsecured | Cancelled | YES |
| **Chesapeake Energy** | Jun 2020 | Unsecured | Cancelled | YES |
| **Pier 1** | Feb 2020 | Secured (liquidation) | Cancelled | N/A (liquidation) |

**Observation:** Equity almost always wiped out in Ch. 11. Hertz was unusual only in that old equity traded at high prices during bankruptcy (retail speculation), but ultimate outcome was cancellation (APR-compliant).

---

## Conclusion

**Bottom Line:** Hertz demonstrates the importance of **recovery waterfall analysis** and **APR enforcement** in distressed investing. Fulcrum security identification and enterprise valuation are critical to assessing recovery prospects. Signal Triage's waterfall and APR violation detection capabilities enable rapid triage of Ch. 11 situations.

**Key Takeaways:**
1. **Fulcrum Investing:** Focus on securities at the fulcrum (last to be paid in full) for best risk-reward
2. **APR Protection:** Equity cannot receive value while creditors impaired (strictly enforced in cramdown)
3. **Valuation Drives Recovery:** Small EV changes can cause large fulcrum migration
4. **Retail Speculation ≠ Reality:** Hertz equity meme stock trading disconnected from bankruptcy outcomes

**Practical Application:** Use Signal Triage to run EV sensitivity analyses and identify fulcrum securities in your distressed portfolio. Export waterfalls to Excel for client presentations and investment committee memos.

---

**Case Study Author:** Signal Triage Development Team  
**Last Updated:** January 2026  
**Related Topics:** Recovery Waterfall, APR Violations, Fulcrum Analysis, Chapter 11 Modeling

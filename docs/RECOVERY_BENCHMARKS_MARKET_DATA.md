# RECOVERY BENCHMARKS & MARKET DATA SUPPLEMENT

**Research Date:** January 29, 2026  
**Purpose:** Provide market benchmarks for distressed debt recovery modeling and adversarial precedent analysis  
**Companion Document:** NON_PRO_RATA_PRECEDENTS.md  
**Sources:** BankruptcyData, S&P Global, LSTA, Pitchbook LCD, Moody's, Skadden Research

---

## 1. HISTORICAL RECOVERY RATES BY LIEN POSITION

### A. Chapter 11 Bankruptcy Outcomes (2023 H1)

**Source:** BankruptcyData 2023 1H Recovery Report

| Debt Class | Average Recovery | Recovery Context |
|------------|------------------|------------------|
| **First Lien Secured** | **68%** | Senior-most position, collateral-backed |
| **Second Lien Secured** | **50%** | Subordinated secured position |
| **Unsecured Funded Debt** | **35%** | No collateral backing |
| **General Unsecured Claims (GUC)** | **48%** | Trade claims, deficiency claims |

**Key Insight:** First lien holders recover **36% more** than second lien holders on average (68% vs. 50%).

---

### B. Industry Standard Recovery Ranges

**Source:** Skadden Private Credit Deep Dive (2024); S&P Global Research

| Debt Class | Recovery Range | Typical Scenario |
|------------|----------------|------------------|
| **First Lien Loans** | **60-70%** | Normal distressed scenario, adequate collateral |
| **Second Lien Debt** | **20-40%** | Subordinated to first lien, residual value |
| **Unsecured Bonds** | **30-50%** | Covenant-heavy, structural protections |
| **Equity** | **0-5%** | Out-of-the-money in most distressed scenarios |

**Application for Signal-Triage:**
- Use **65%** as Base Case for first lien absent specific precedent
- Use **30%** as Base Case for second lien absent specific precedent
- Flag Critical Variance if model exceeds these ranges without strong justification

---

### C. Historical Benchmarks (Pre-Crisis vs. Crisis)

**Source:** Moody's Default and Recovery Rates (2009); Defaultrisk.com

| Period | Senior Secured Bank Loans | Senior Unsecured Bonds |
|--------|---------------------------|------------------------|
| **Normal (1998)** | **87%** | **79%** |
| **Pre-Crisis (2007)** | ~75% (est.) | **53.3%** |
| **Crisis (2008)** | ~60% (est.) | **33.8%** |

**Key Takeaway:** Recovery rates compress by 20-30% during systemic crises.

**Modeling Recommendation:**  
Apply **macro adjustment factor** for "Worst Case" scenarios:
- Normal environment: Use historical averages
- Distressed environment (CCC/D migration >5%): Reduce Base Case by 15%
- Crisis environment (yield spreads >800bps): Reduce Base Case by 25%

---

## 2. UPTIER/DROPDOWN IMPACT ON RECOVERY

### A. Non-Pro Rata Transaction Recovery Haircuts

**Comparison Table: Normal Recovery vs. Post-LME Recovery**

| Precedent | Original Position | Normal Recovery (Est.) | Post-LME Recovery | Haircut |
|-----------|-------------------|------------------------|-------------------|---------|
| **J. Crew (Dropdown)** | 1st Lien Secured | 65% | **41%** | **-37%** |
| **Serta Simmons (Non-Participant)** | 1st Lien | 68% | **<30%** | **-56%** |
| **Incora (Non-Participant)** | 1st Lien Notes | 68% | **<10%** | **-85%** |
| **Robertshaw (Non-Participant)** | 1st-2nd Lien | 60% | **33%** | **-45%** |

**Average Non-Pro Rata Haircut:** **-56%** (median: -50%)

### B. Recovery Adjustment Framework

**For Signal-Triage Recovery Engine:**

```
IF credit_agreement contains:
    - OMP language WITHOUT "public market" definition, OR
    - Unrestricted subsidiary flexibility WITHOUT IP blocker, OR
    - Simple majority amendment WITHOUT subordination carve-out

THEN:
    Worst_Case_Recovery = Base_Case_Recovery * 0.44  # Apply 56% haircut
    
    IF jurisdiction == "5th Circuit":
        Worst_Case_Probability = 0.20  # Lower risk post-Serta
    ELIF jurisdiction == "NY Courts":
        Worst_Case_Probability = 0.35  # Higher risk post-Mitel
    ELSE:
        Worst_Case_Probability = 0.30  # Mixed jurisdiction
```

---

## 3. SECONDARY LOAN TRADING MARKET DATA (2024-2025)

### A. Market Volumes and Activity

**Source:** LSTA Secondary Trading Monthly (2024-2025)

| Period | Trading Volume | YoY Change | Notes |
|--------|----------------|------------|-------|
| **2024 Full Year** | **$821B** | +15% | Near-record activity |
| **2022 (Record)** | $824B | -- | Previous peak |
| **April 2025** | $109B | -- | 3rd busiest month on record |
| **2025 Annualized** | ~$1.1T (projected) | +34% vs 2022 | Record-breaking pace |

**Key Insight:** High trading volumes indicate **robust price discovery** and **liquid distressed markets**.

---

### B. Price Levels and Spreads (2024-2025)

**Source:** LSTA Monthly Reports; Invesco Loan Index

| Metric | Jan 2024 | Dec 2024 | April 2025 | Trend |
|--------|----------|----------|------------|-------|
| **Avg Trade Price** | 96.25 | 97.97 | 96.30 | Volatile, near-par |
| **Median Trade Price** | -- | -- | 98.20 | Stable |
| **Par-Plus Trading (%)** | ~30% | ~29% | **8%** | Sharp April decline |
| **Distressed Trading (<80)** | ~5% | ~4% | ~7% | Modest increase |

**Bid-Ask Spreads (April 2025):**
- **Average:** 98 bps (2-year high)
- **Median:** 88 bps
- **Interpretation:** Widening spreads indicate increased uncertainty/volatility

---

### C. Distressed Debt Activity Surge

**Source:** Pitchbook LCD; LSTA; FTI Consulting 2025 Survey

| Metric | Value | Context |
|--------|-------|---------|
| **Leveraged Loan Default Rate (2024)** | **5.6%** | Decade high |
| **COVID Peak (2020)** | 4.5% | Lower than 2024 |
| **Distressed LMEs (Dec 2024)** | **38** | Record high |
| **Distressed LMEs (Dec 2023)** | 21 | +81% YoY |
| **Distressed LMEs (Dec 2022)** | 9 | +322% over 2 years |

**Key Driver:** 90%+ of senior loans now **covenant-lite**, giving borrowers flexibility for LMEs.

---

### D. Credit Spreads and Pricing

**Source:** FTI Consulting Survey; Invesco

| Credit Quality | Spread (2024) | All-In Cost | Trend vs. 2020 |
|----------------|---------------|-------------|----------------|
| **Single-B Rated** | 345 bps (late 2025) | **8.0%** | Tightest since 2008 |
| **Market Average** | 376 bps (early 2025) | ~8.9% | Compressed 31 bps YTD |
| **2020 Average** | <200 bps (est.) | <5% | Zero-rate era |

**Interpretation:**  
- Spreads **compressed** despite rising defaults → indicates strong **technical demand** from CLOs/private credit
- **Paradox:** Tighter spreads with higher defaults = borrower-friendly refinancing environment

---

## 4. DEFAULT FORECASTS & MATURITY WALL

### A. Default Rate Projections

**Source:** Invesco; FTI Consulting; S&P Global

| Year | Projected Default Rate | Primary Drivers |
|------|------------------------|-----------------|
| **2024 Actual** | 5.6% | Distressed exchanges, maturity liquidity |
| **2025 Forecast** | 4.5-5.0% | Continued LME activity |
| **2026 Forecast** | **4.0%** | Maturity-driven restructurings |

**Composition:**
- **Distressed exchanges:** ~60% of default volume (not traditional Chapter 11)
- **Maturity/liquidity-driven:** ~30%
- **Operational failures:** ~10%

---

### B. Leveraged Loan Return Expectations

**Source:** Invesco US Loan Market Outlook (2025-2026)

| Component | 2025 YTD | 2026 Projection |
|-----------|----------|-----------------|
| **Total Return** | 5.22% | **7.0-7.5%** |
| **Coupon Income** | 7.43% | ~7.5% |
| **Price Change** | -2.21% | +0.5% (est.) |

**Key Insight:** Returns driven by **income**, not price appreciation → stable for first lien holders.

---

## 5. COVENANT PROTECTION EVOLUTION

### A. Market Adoption of LME Protections (2020-2025)

**Source:** Harvard Bankruptcy Roundtable; LSTA Market Advisory

| Protection Type | Pre-2020 | Post-2022 | Change | Impact |
|-----------------|----------|-----------|--------|--------|
| **Uptier Blockers** | 40% | **85%** | +45 pts | Explicit superpriority prohibition |
| **J. Crew Blockers** | <20% | **90%+** | +70 pts | IP transfer restrictions |
| **Unanimous Subordination Consent** | 50% | **70%** | +20 pts | Require 100% lender consent |
| **Covenant-Lite (Overall)** | 85% | **92%** | +7 pts | PARADOX: More protections but weaker overall packages |

**Key Takeaway:** Lenders have responded to uptier/dropdown precedents by adding **targeted blockers**, but overall covenant packages remain **weak** due to covenant-lite structures.

---

### B. Vintage Analysis for Signal-Triage

**Risk Scoring by Credit Agreement Vintage:**

| Vintage | Uptier Risk | Dropdown Risk | Covenant Quality | Priority for Audit |
|---------|-------------|---------------|------------------|-------------------|
| **Pre-2017 (Pre-J. Crew)** | HIGH | **EXTREME** | Very Weak | **CRITICAL** |
| **2017-2020 (Post-J. Crew, Pre-Serta)** | HIGH | Medium | Weak | **HIGH** |
| **2020-2022 (Post-Serta)** | MEDIUM | Low | Moderate | Medium |
| **2023+ (Post-Incora)** | LOW | Low | Strong (targeted) | Low |

**Application:**  
Flag any credit with vintage **<2020** for **manual covenant forensics review** if distressed indicators present.

---

## 6. INTEGRATION WITH SIGNAL-TRIAGE RECOVERY ENGINE

### A. Decision Tree for Recovery Estimates

```
STEP 1: Determine Base Case Recovery
    - First Lien: 65%
    - Second Lien: 30%
    - Unsecured: 35%

STEP 2: Apply Macro Adjustment
    - Normal environment: No adjustment
    - Distressed environment (CCC migration >5%): -15%
    - Crisis environment (spreads >800bps): -25%

STEP 3: Apply LME Risk Adjustment (if indicators present)
    - IF covenant_gaps_detected AND distressed_trading:
        Worst_Case = Base_Case * 0.44  # 56% haircut
    - ELSE:
        Worst_Case = Base_Case * 0.70  # 30% haircut

STEP 4: Calculate Probability-Weighted Recovery
    - Best_Case (no default): 100%
    - Base_Case (normal Ch. 11): [Step 1 + Step 2]
    - Worst_Case (LME/precedent): [Step 3]
    
    Weighted_Recovery = (P_best * Best) + (P_base * Base) + (P_worst * Worst)

STEP 5: Flag Critical Variance
    - IF Weighted_Recovery > 70% AND covenant_vintage < 2020:
        Flag "Optimistic - Review Covenant Gaps"
    - IF Weighted_Recovery < 30% AND no_specific_precedent:
        Flag "Pessimistic - Verify LME Risk"
```

---

### B. Benchmarking Trigger Points

**For Auditor Agent to Flag Critical Variances:**

| Model Output | Market Benchmark | Variance | Action |
|--------------|------------------|----------|--------|
| **First Lien >80%** | 68% (Ch. 11 avg) | +18% | **FLAG** - Verify collateral coverage |
| **First Lien <40%** | 68% (Ch. 11 avg) | -41% | **FLAG** - Justify LME risk/dropdown |
| **Second Lien >60%** | 50% (Ch. 11 avg) | +20% | **FLAG** - Review intercreditor agreement |
| **Second Lien <20%** | 50% (Ch. 11 avg) | -60% | **FLAG** - Document precedent (e.g., Serta) |

**Critical Variance Threshold:** ±20% from benchmark average requires **documented justification** citing specific precedent or collateral analysis.

---

## 7. PRECEDENT-SPECIFIC BENCHMARKING GUIDANCE

### A. When to Cite Serta Simmons

**Use Serta (30% recovery) as Worst Case if:**
- Credit agreement contains OMP language
- Company in 5th Circuit jurisdiction OR similar pro-creditor venue
- Majority lenders forming "cooperation agreement"
- Distressed trading (<70¢) with maturity within 18 months

**Probability Weight:** 20-35% depending on jurisdiction

---

### B. When to Cite J. Crew

**Use J. Crew (41% recovery) as Worst Case if:**
- Significant IP/brand value (>30% of enterprise value)
- Credit agreement allows unrestricted subsidiary flexibility
- Investment baskets >$100M without IP carve-outs
- Vintage <2020

**Probability Weight:** 25-40% depending on covenant gaps

---

### C. When to Cite Incora

**Use Incora (<10% recovery) as Worst Case if:**
- Indenture allows simple majority amendments
- No explicit 2/3 supermajority for lien releases
- Participating lenders hold 60-67% (close to control threshold)
- Evidence of new note issuance to manipulate voting

**Probability Weight:** 15-25% (extreme scenario, less common)

---

## 8. MARKET INTELLIGENCE SOURCES FOR ONGOING MONITORING

### A. Free/Public Sources

| Source | Coverage | Update Frequency | Best For |
|--------|----------|------------------|----------|
| **LSTA.org** | Loan market data, volumes | Monthly | Trading activity, spread data |
| **Reuters/Bloomberg (free)** | Major restructurings | Daily | Breaking precedent news |
| **Court dockets (PACER)** | Bankruptcy filings | Real-time | Legal outcomes, plan details |
| **SEC EDGAR** | 10-K/10-Q, 8-K filings | Real-time | Covenant packages, amendments |
| **Harvard Bankruptcy Roundtable** | Academic analysis | Quarterly | In-depth precedent analysis |

### B. Subscription/Premium Sources

| Source | Coverage | Cost Model | Best For |
|--------|----------|------------|----------|
| **9fin** | Distressed debt intelligence | Subscription | Trading levels, LME tracker |
| **Pitchbook LCD** | Leveraged loan market data | Subscription | Pricing, default rates, covenant trends |
| **S&P Global Ratings** | Recovery studies, default data | Subscription/Free tier | Historical recovery benchmarks |
| **Debtwire** | Restructuring news | Subscription | Real-time LME activity |
| **Reorg** | Bankruptcy intelligence | Subscription | Creditor group formations |

**Recommendation for Benchmarker Agent:**  
Monitor **LSTA (free)** monthly + set **Google Alerts** for "uptier transaction" OR "dropdown transaction" OR "liability management exercise" to capture new precedents.

---

## 9. SUMMARY: KEY BENCHMARKS FOR SIGNAL-TRIAGE

### Quick Reference Table

| Metric | Value | Source | Use Case |
|--------|-------|--------|----------|
| **First Lien Ch. 11 Recovery** | **68%** | BankruptcyData 2023 | Base Case default scenario |
| **First Lien Range** | 60-70% | Skadden/S&P | Normal distressed range |
| **Second Lien Ch. 11 Recovery** | **50%** | BankruptcyData 2023 | Base Case default scenario |
| **Second Lien Range** | 20-40% | Skadden/S&P | Normal distressed range |
| **Non-Pro Rata Haircut** | **-56%** (avg) | Precedent analysis | Worst Case LME scenario |
| **J. Crew Left-Behind** | **41¢/$** | Reuters/Market data | Dropdown precedent |
| **Serta Non-Participant** | **<30¢/$** | Court filings | Uptier precedent (5th Cir.) |
| **Incora Non-Participant** | **<10¢/$** | Plan docs | Vote manipulation precedent |
| **Leveraged Loan Default Rate** | **5.6%** (2024) | LCD/FTI | Probability of default input |
| **Distressed LME Count** | **38** (Dec 2024) | Octus/9fin | Market trend indicator |
| **Uptier Blocker Adoption** | **85%** (post-2022) | LSTA | Covenant protection benchmark |

---

## 10. CRITICAL VARIANCE FLAGS FOR AUDITOR

**Automatic triggers for Auditor Agent review:**

1. **Recovery Optimism (>20% above benchmark):**
   - First lien model output >80% vs. 68% Ch. 11 average
   - Second lien model output >60% vs. 50% Ch. 11 average

2. **Recovery Pessimism (>30% below benchmark):**
   - First lien model output <45% vs. 68% Ch. 11 average WITHOUT LME precedent citation
   - Second lien model output <30% vs. 50% Ch. 11 average WITHOUT specific justification

3. **LME Risk Underestimation:**
   - Model shows >60% recovery for vintage <2020 credit with OMP language
   - Worst Case probability <15% when covenant gaps + distressed trading present

4. **Precedent Misapplication:**
   - Serta cited for NY jurisdiction case (conflicting with Mitel)
   - J. Crew cited when IP blockers present in credit agreement
   - Incora cited when indenture has 2/3 supermajority protection

---

**Document prepared by:** Benchmarker Agent  
**Last updated:** January 29, 2026  
**Companion Document:** NON_PRO_RATA_PRECEDENTS.md  
**Next review:** Quarterly or upon new material precedent

# Serta Simmons Case Study: The "Uptier Exchange"

## Executive Summary

**Company:** Serta Simmons Bedding, LLC  
**Event Date:** February 2020  
**LME Type:** Uptier Exchange, Priming Transaction, Required Lender Override  
**Amount:** $1.1 billion term loan ($675M converted to super-priority)  
**Outcome:** 50.1% lenders primed minority; spawned market-wide covenant reforms

---

## Background

### The Transaction
In February 2020, Serta Simmons executed a highly controversial "uptier" transaction:

1. **Incremental Facility:** Borrowed $200M via new "super-priority" term loan (priming existing term loan)
2. **Exchange Offer:** Invited existing term loan lenders to exchange into super-priority at par
3. **Required Lender Amendment:** 50.1% of term loan lenders (participating in exchange) voted to permit the incremental facility
4. **Result:** $675M (of $1.1B term loan) exchanged into super-priority; $425M minority remained in subordinated position

### Capital Structure (Pre-Transaction)
- **Term Loan B:** $1.1B (LIBOR + 350bps), first lien on substantially all assets
- **ABL Facility:** $200M, super-priority on current assets
- **Sponsor:** Advent International

### The Mechanics
The transaction exploited three interrelated covenant provisions:

1. **Incremental Facility Basket:** Allowed borrower to incur additional first lien debt up to $250M
2. **Amendment Rights:** Required Lenders (>50%) could amend "relative priority" of debt via amendment
3. **Credit Agreement Amendment:** Required Lenders voted to permit incremental facility with super-priority over existing term loan

---

## Key LME Signals Detected

### 1. **Incremental Facility with Priming (Critical Severity)**
**Pattern:** "Additional first lien debt... may be incurred... and may share in the Collateral on a pari passu or junior basis"

**Risk:** Ambiguous language doesn't explicitly prohibit **super-priority** incremental facilities that prime existing term loan.

**Serta Language:**
```
"The Borrower may incur Incremental Term Loans... secured on a first lien 
basis by the Collateral, provided that such Incremental Term Loans may rank 
pari passu with or junior to (but not senior to) the existing Term Loans, 
unless otherwise approved by Required Lenders"
```

**Loophole:** "unless otherwise approved by Required Lenders" → 50.1% can prime minority.

**Impact:**
- $200M incremental facility incurred with **super-priority** (junior to ABL, senior to existing term loan)
- Existing term loan lenders who did not exchange were structurally subordinated
- Minority lenders lost ~$425M of effective first lien claim (became 1.5 lien)

---

### 2. **Required Lender Override (50.1%) (Critical Severity)**
**Pattern:** "Required Lenders may approve modifications to priority and lien sharing"

**Risk:** Bare majority can change relative priorities, priming minority without their consent.

**Serta Language:**
```
"Required Lenders" means Lenders holding more than 50% of the aggregate 
principal amount of the Term Loans then outstanding.

Section 10.01: "No amendment or waiver of any provision of this Agreement... 
shall be effective unless consented to by Required Lenders, except that... 
amendments affecting the relative priority of Liens may be approved by 
Required Lenders"
```

**Exploitation:**
- Sponsor (via distressed debt funds) acquired slightly >50% of term loan on secondary market
- As Required Lenders, voted to approve super-priority incremental facility
- Exchanged their holdings into super-priority at par
- Minority lenders (remaining 49.9%) were primed without consent

**Voting Dynamics:**
```
Pre-Transaction Ownership:
  Sponsor-aligned funds: 51% of term loan
  Third-party lenders:   49% of term loan

Post-Exchange:
  Super-Priority ($200M incr + $675M exchange): $875M
    → Held by sponsor-aligned (77% of super-priority)
  Subordinated Term Loan (minority): $425M
    → Held by third-party lenders (100% of subordinated)

Result: Sponsor-aligned lenders primed minority via majority vote
```

---

### 3. **Ratable/Pro Rata Sharing Ambiguity (High Severity)**
**Pattern:** Pro rata sharing language doesn't explicitly protect against priming via new debt issuance

**Risk:** Even with "pro rata" provisions, new debt layers can prime existing debt if approved by Required Lenders.

**Serta Language:**
```
"Payments of principal and interest shall be made pro rata to all Lenders 
based on their respective outstanding Term Loans."
```

**Loophole:** Pro rata applies **within** each tranche of debt, but does NOT prevent **new tranches** from priming via incremental facility.

---

### 4. **Vague "Pari Passu or Junior" Language (High Severity)**
**Pattern:** "may rank pari passu with or junior to (but not senior to) the existing Term Loans"

**Issue:** "but not senior to" seems to prohibit super-priority, but "unless otherwise approved" creates exception.

**Serta Language:**
```
"Incremental Term Loans... may rank pari passu with or junior to (but not 
senior to) the existing Term Loans, unless otherwise approved by Required Lenders"
```

**Ambiguity:**
- Does "but not senior to" create absolute prohibition? **NO** → "unless otherwise approved" exception
- Can Required Lenders override priority restrictions? **YES** → precedent set by Serta
- Is super-priority an "amendment" requiring higher threshold? **NO** → only Required Lenders needed

---

## Financial Impact

### Recovery Shift (Estimated)
| Tranche | Pre-Uptier Recovery | Post-Uptier Recovery | Change |
|---------|---------------------|----------------------|---------|
| **ABL** (super-super-priority) | 100% | 100% | 0% |
| **Exchanging Lenders** (new super-priority) | 60-70% | 85-95% | +25-35% |
| **Non-Exchanging Lenders** (subordinated 1L) | 60-70% | 30-40% | -30-40% |

### Market Reaction
- **Term Loan Price (Non-Exchanging):** Dropped from ~70 to ~40 (30-point decline)
- **Litigation:** Minority lenders sued; settled for enhanced recovery (details confidential)
- **Sponsor:** Maintained control without equity infusion; effectively primed out minority at distressed price

---

## Lessons Learned

### **For Lenders:**
1. **Incremental Facility Language:** Explicitly prohibit super-priority incremental facilities; require "pari passu **at worst**"
2. **Amendment Thresholds:** Priority changes should require **unanimous consent** (not Required Lenders)
3. **Anti-Priming Provisions:** Add explicit covenant: "No Indebtedness may be incurred that is senior in right of payment or priority to existing Term Loans"
4. **Voting Rights:** Consider "minority protection" requiring consent of **>66.7%** for priority changes
5. **Lien Sharing:** Explicitly state all first lien debt must share **pro rata** in collateral; no super-priority layers

### **For Borrowers/Sponsors:**
1. **Market Standard (Pre-2020):** Incremental facilities assumed to be pari passu or junior; super-priority not contemplated
2. **Serta Innovation:** Exploit Required Lender amendment + incremental facility to create priming layer
3. **Post-Serta:** Market closed this loophole; now nearly impossible to execute

### **Market Impact:**
Post-Serta, credit agreements include:
- **"Serta Blocker" Language:** Incremental facilities may be pari passu or junior, **period** (no "unless Required Lenders approve" exception)
- **Unanimous Consent for Priority Changes:** Amendments affecting priority require 100% lender consent
- **Enhanced Minority Protections:** Some deals now have "Yank-the-Bank" provisions allowing minority to opt out if primed

---

## Signal Triage Analysis

### Run Analysis
```bash
signal-triage examples/serta/serta_credit_agreement.txt --pipeline
```

### Expected Distress Score: **88/100 (CRITICAL)**

### Key Signals Detected:
1. **uptier_exchange** (weight: 10, severity: critical)
2. **required_lender_priming** (weight: 10, severity: critical)
3. **incremental_facility_ambiguity** (weight: 9, severity: high)
4. **priority_override_risk** (weight: 9, severity: high)
5. **pro_rata_sharing_loophole** (weight: 7, severity: high)

### Collateral Leakage Flags:
- `priming_via_incremental`
- `required_lender_override`
- `minority_squeeze_out`

### Librarian Output:
```json
{
  "incremental_facility_mechanics": {
    "basket_size": "$250M or 1.0x Consolidated EBITDA",
    "permitted_priority": "pari passu or junior (unless Required Lenders approve senior)",
    "approval_threshold": "Required Lenders (>50%)",
    "risk_level": "CRITICAL",
    "commentary": "Required Lender exception allows bare majority to prime minority"
  },
  "amendment_provisions": {
    "required_lenders_threshold": "50%",
    "unanimous_consent_required_for": [
      "Principal reduction",
      "Interest rate reduction",
      "Maturity extension"
    ],
    "required_lenders_can_approve": [
      "Priority changes",
      "Lien modifications",
      "Most covenant amendments"
    ],
    "risk_level": "CRITICAL"
  },
  "collateral_leakage_flags": [
    "priming_via_incremental",
    "required_lender_override",
    "minority_protection_absent"
  ]
}
```

---

## Forensic Questions to Ask

When reviewing a credit agreement post-Serta, ask:

1. **Can incremental facilities be super-priority?**
   - Look for: "Incremental debt may rank pari passu or junior to existing debt, **period**" (no exceptions)
   - Red flag: "unless Required Lenders approve" or similar override language

2. **What consent is required to change debt priority?**
   - Look for: Unanimous consent for priority changes
   - Red flag: Required Lenders (>50%) can modify priority

3. **Is there explicit anti-priming language?**
   - Look for: "No Indebtedness may be incurred that ranks senior to the Term Loans"
   - Red flag: Vague "pari passu or junior" without absolute prohibition

4. **Can minority lenders opt out if primed?**
   - Look for: "Yank-the-Bank" provisions allowing exit at par if priority changes
   - Red flag: No minority protection mechanisms

5. **What is the Required Lender threshold?**
   - Look for: >66.7% or >75% for material amendments
   - Red flag: >50% for priority/lien amendments

---

## Recovery Waterfall Analysis

### Scenario 1: Pre-Uptier (Base Case)
```
Enterprise Value: $1,400M

ABL (Claim: $150M)
  Collateral: Current assets ($200M)
  Recovery: $150M (100.0%)
  Status: PAID IN FULL

Term Loan B (Claim: $1,100M)
  Collateral: All assets ($1,400M), junior to ABL
  Available: $1,250M ($1,400M - $150M ABL)
  Recovery: $1,100M (100.0%)
  Status: PAID IN FULL
  
Fulcrum: No fulcrum (enterprise solvent)
```

### Scenario 2: Post-Uptier (Priming Transaction)
```
Enterprise Value: $1,600M (includes $200M new money)

ABL (Claim: $150M)
  Recovery: $150M (100.0%)

Super-Priority Term Loan (New + Exchange):
  New Incremental: $200M
  Exchanged: $675M
  Total Claim: $875M
  Available: $1,450M (after ABL)
  Recovery: $875M (100.0%)
  Status: PAID IN FULL

Subordinated Term Loan (Non-Exchanging):
  Claim: $425M
  Available: $575M (after ABL and super-priority)
  Recovery: $425M (100.0%)
  Status: PAID IN FULL (in this scenario)

Fulcrum: Subordinated Term Loan (if EV < $1,600M)
```

### Scenario 3: Stressed Case (EV = $1,200M)
```
Enterprise Value: $1,200M (worse than expected)

ABL (Claim: $150M)
  Recovery: $150M (100.0%)

Super-Priority Term Loan (Claim: $875M)
  Available: $1,050M (after ABL)
  Recovery: $875M (100.0%)
  Status: PAID IN FULL

Subordinated Term Loan (Claim: $425M) ← FULCRUM
  Available: $175M (after ABL and super-priority)
  Recovery: $175M (41.2%)
  Status: OUT OF THE MONEY FOR ~$250M

APR VIOLATION CHECK:
  Senior (super-priority) paid in full: YES (100%)
  Junior (subordinated) impaired: YES (41.2%)
  Violation: NONE (APR preserved; senior paid first)
  
BUT: Economic result is minority lenders who didn't exchange recovered 41%
     while exchanging lenders (same original position) recovered 100%
     
This is NOT an APR violation (exchanging lenders provided new money in incremental)
This IS a "priming squeeze-out" (minority economically disadvantaged by majority vote)
```

---

## Auditor Findings

### Stress Test Results
```
=== AUDITOR REPORT ===

Stress Test: Uptier Exchange / Required Lender Priming

Test Parameters:
- Incremental Facility: $200M (super-priority)
- Exchange Offer: $675M existing term loan → super-priority
- Non-Exchanging: $425M remains subordinated
- Required Lender Approval: YES (>50% voted to approve)

Critical Variance Detected:
  Pre-Uptier Recovery (All Lenders):         70-80% (pari passu)
  Post-Uptier (Exchanging Lenders):          95-100% (super-priority)
  Post-Uptier (Non-Exchanging Lenders):      35-45% (subordinated)
  Variance:                                  -35 to -45 points (non-exchanging)

Priority Inversion:
  Lenders with identical original claims experienced 50-60 point recovery 
  spread based solely on exchange participation (not based on APR priority)

Audit Trail:
  - Config Version: v2.0.1
  - Document Source: serta_credit_agreement.txt
  - Analysis Date: 2026-01-29
  - Precision Test: PASSED
  - APR Test: PASSED (no APR violation; super-priority created via new money)
  - Minority Protection Test: FAILED (no opt-out or consent rights)

Gate Status: PUBLISHED WITH CRITICAL WARNINGS
Reason: Required Lender override enables minority priming; recovery variance >30 points
```

---

## Legal & Market Response

### **Litigation**
- **Minority Lenders:** Sued in Delaware Chancery Court alleging breach of implied covenant of good faith and fair dealing
- **Argument:** Required Lenders used voting rights to unfairly advantage themselves at minority's expense
- **Outcome:** Settled; terms confidential but likely involved enhanced recovery for minority

### **Regulatory / Market Response**
- **LSTA:** Issued guidance discouraging uptier exchanges
- **Credit Agreements (2020+):** Nearly all new deals include explicit anti-priming language
- **Pricing:** Serta-style covenant packages now trade at wider spreads (50-75bps penalty)

### **"Serta Blocker" Language (Now Standard)**
```
"Notwithstanding anything to the contrary in this Agreement, no Incremental 
Facility may rank senior to the existing Term Loans in right of payment or 
priority of Liens on the Collateral, and any such Incremental Facility must 
share pari passu (on a pro rata basis) with the existing Term Loans. This 
provision may not be amended without the consent of each Lender adversely 
affected by such amendment."
```

---

## Comparative Analysis

### Serta vs. J.Crew (LME Comparison)
| Dimension | J.Crew | Serta |
|-----------|--------|-------|
| **LME Type** | Dropdown + Asset Transfer | Uptier via Incremental |
| **Mechanism** | Unrestricted sub + Investment basket | Required Lender vote + Incremental facility |
| **Approval Required** | None (unilateral borrower action) | Required Lenders (>50%) |
| **Minority Protection** | Pro rata blocker (coordination barrier) | No consent or opt-out rights |
| **Value Transfer** | $1.65B IP to unrestricted sub | $425M term loan subordinated |
| **Recovery Impact** | -25 to -35 points (all lenders) | -35 to -45 points (minority only) |
| **Market Fix** | "J.Crew blocker" (IP carveout) | "Serta blocker" (no super-priority) |

---

## Conclusion

**Bottom Line:** The Serta credit agreement allowed a bare majority (>50%) of term loan lenders to prime the minority by approving a super-priority incremental facility and exchanging into it. This represents a **CRITICAL DISTRESS** scenario with minority lenders facing **-35 to -45 point** recovery impact.

**Historical Note:** This transaction sparked immediate market-wide reforms. Post-February 2020, virtually all credit agreements explicitly prohibit super-priority incremental facilities and require unanimous consent for priority changes.

**Lesson:** "Required Lenders may approve" + "Incremental facility" + Ambiguous priority language = Minority priming risk. Modern credit agreements have closed this loophole via "Serta blocker" language requiring pari passu sharing.

---

**Report Date:** January 2026  
**Analysis by:** Signal Triage Development Team  
**Related LME Categories:** Uptier Exchange, Required Lender Override, Priming, Incremental Facility

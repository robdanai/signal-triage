# J.Crew Case Study: The "Trap Door" Asset Transfer

## Executive Summary

**Company:** J.Crew Group, Inc.  
**Event Date:** March 2017  
**LME Type:** Dropdown, Asset Transfer to Unrestricted Subsidiary, Blocker Structure  
**Amount:** ~$1.65 billion intellectual property (IP) transfer  
**Outcome:** Lenders effectively subordinated; triggered wave of covenant reforms

---

## Background

### The Transaction
In March 2017, J.Crew executed one of the most controversial liability management exercises in credit markets:

1. **Asset Transfer:** Transferred $1.65B of intellectual property (trademarks, brand value) from credit group (restricted subsidiaries) to unrestricted subsidiary
2. **New Debt Issuance:** Unrestricted subsidiary issued new debt collateralized by the transferred IP
3. **Structural Subordination:** Existing term loan lenders lost collateral coverage, became structurally subordinated to new debt

### Capital Structure (Pre-Transaction)
- **Term Loan:** $1.7B (LIBOR + 300bps), secured by substantially all assets including IP
- **Second Lien:** ~$250M
- **Equity:** TPG Capital, Leonard Green & Partners

### The Covenant "Trap Door"
J.Crew's credit agreement contained two key provisions that enabled the transaction:

1. **Investment Basket:** Allowed transfers to unrestricted subsidiaries up to greater of $250M or 25% of Consolidated Assets
2. **Unrestricted Subsidiary Definition:** Did not explicitly prohibit valuable IP from being held in unrestricted subs
3. **Blocker Mechanism:** Pro rata sharing provisions prevented individual lenders from suing (required supermajority consent)

---

## Key LME Signals Detected

### 1. **Asset Transfer Basket (High Severity)**
**Pattern:** "permitted to transfer assets to unrestricted subsidiaries not to exceed..."

**Risk:** Allows crown jewel assets (IP, brands) to be moved outside credit group collateral package.

**J.Crew Language:**
```
"Investments in Unrestricted Subsidiaries in an aggregate amount not to exceed 
the greater of (x) $250,000,000 and (y) 25% of Consolidated Total Assets"
```

**Impact:**
- $1.65B IP transfer fit within 25% of Consolidated Assets basket
- Term loan lenders lost collateral coverage
- Structural subordination: unrestricted sub debt senior to term loan

---

### 2. **Unrestricted Subsidiary Dropdown (Critical Severity)**
**Pattern:** Subsidiary designation allowing assets to exit credit group

**Risk:** Combined with asset transfer basket, creates path to strip collateral.

**J.Crew Language:**
```
"The Company may designate any Subsidiary as an Unrestricted Subsidiary... 
provided that such designation is permitted as an Investment"
```

**Impact:**
- J.Crew created new unrestricted sub
- Designated it to receive IP transfer
- Unrestricted sub issued $350M first lien term loan secured by IP (priming term loan lenders)

---

### 3. **Blocker Structure (High Severity)**
**Pattern:** Pro rata sharing or Required Lender thresholds preventing individual lender action

**Risk:** Individual lenders cannot sue even if harm is material; requires supermajority.

**J.Crew Language:**
```
"Any lender seeking to bring an action... shall not be entitled to recover 
unless it is bringing such action on behalf of all lenders on a pro rata basis"
```

**Impact:**
- TPG/Leonard Green controlled equity and likely had influence over lender coordination
- Minority lenders could not block transaction
- By the time majority organized, transaction was complete

---

## Financial Impact

### Valuation Shift (Estimated)
| Component | Pre-Transfer | Post-Transfer | Change |
|-----------|--------------|---------------|---------|
| **Term Loan Recovery** | ~70-80% | ~40-50% | -30-40% |
| **IP Collateral Value** | $1.65B (in credit group) | $0 (moved to unres. sub) | -$1.65B |
| **Structural Subordination** | None | $350M priming debt | New senior layer |

### Market Reaction
- **Term Loan Price:** Dropped from ~95 to ~75 (20-point decline)
- **Lender Litigation:** Attempted but blocked by pro rata sharing provision
- **Bankruptcy (2020):** J.Crew eventually filed Ch. 11; term loan lenders recovered ~65%

---

## Lessons Learned

### **For Lenders:**
1. **Scrutinize Unrestricted Subsidiary Definitions:** Explicitly prohibit IP, material contracts, and crown jewels from being designated as unrestricted
2. **Limit Asset Transfer Baskets:** Cap at dollar amount (not % of assets which can be subjective)
3. **Remove Pro Rata Blockers:** Allow individual lender standing to sue for breaches
4. **Require Consent for IP Transfers:** Material IP should require supermajority or unanimous consent

### **For Borrowers:**
1. **Trap Doors Exist:** Well-drafted credit agreements may have unintended loopholes
2. **Structuring Matters:** Unrestricted subsidiary structures can unlock financing flexibility
3. **Lender Coordination Risk:** Divided lender groups may be unable to block transactions

### **Market Impact:**
Post-J.Crew, credit agreements increasingly include:
- **"J.Crew Blocker" Language:** Explicit prohibitions on material IP transfers
- **Tighter Unrestricted Subsidiary Baskets:** Hard dollar caps (e.g., $50M, not 25% of assets)
- **Enhanced Lender Consent Rights:** Lower thresholds for IP/crown jewel transactions

---

## Signal Triage Analysis

### Run Analysis
```bash
signal-triage examples/jcrew/jcrew_credit_agreement.txt --pipeline
```

### Expected Distress Score: **82/100 (CRITICAL)**

### Key Signals Detected:
1. **dropdown** (weight: 10, severity: critical)
2. **transfer_to_unrestricted_sub** (weight: 9, severity: high)
3. **asset_sale_basket** (weight: 8, severity: high)
4. **structural_subordination** (weight: 9, severity: high)
5. **blocker_mechanism** (weight: 7, severity: medium)

### Collateral Leakage Flags:
- `unrestricted_sub_transfer`
- `ip_carveout`
- `material_asset_transfer`

### Librarian Output:
```json
{
  "baskets": [
    {
      "type": "unrestricted_subsidiary_investment",
      "size": "greater of $250M or 25% Consolidated Assets",
      "risk_level": "CRITICAL",
      "commentary": "Percentage-based basket allows large transfers as company grows"
    }
  ],
  "collateral_leakage_flags": [
    "unrestricted_sub_transfer",
    "ip_carveout"
  ]
}
```

---

## Forensic Questions to Ask

When reviewing a credit agreement post-J.Crew, ask:

1. **Can assets be transferred to unrestricted subsidiaries? If so, what limit?**
   - Look for: "Investments in Unrestricted Subsidiaries not to exceed..."
   - Red flag: Percentage-based baskets (10%+) or undefined "material" thresholds

2. **What assets are explicitly included in collateral package?**
   - Look for: "all present and future assets including intellectual property"
   - Red flag: Vague definitions that don't enumerate key IP/contracts

3. **Can subsidiaries be designated as unrestricted? What limits?**
   - Look for: "Company may designate any Subsidiary as Unrestricted provided..."
   - Red flag: Only financial test required (no asset quality restrictions)

4. **Do lenders have individual standing to sue?**
   - Look for: Pro rata sharing provisions or Required Lender thresholds
   - Red flag: "no individual lender may bring action unless on behalf of all lenders"

5. **What consent is required for material IP transfers?**
   - Look for: Supermajority or unanimous consent for IP/brand transfers
   - Red flag: No consent required if within basket limits

---

## Related Precedents

### **Similar Transactions:**
- **Neiman Marcus (2016):** MyTheresa asset transfer to unrestricted sub
- **Revlon (2020):** BrandCo IP transfer attempt (blocked by lenders)

### **Covenant Reforms:**
Post-J.Crew, credit agreements include:
- "J.Crew blocker" language
- IP carveout restrictions
- Tighter unrestricted sub baskets

---

## Additional Resources

- **Court Documents:** *J.Crew Group, Inc.* bankruptcy filings (S.D.N.Y. 2020)
- **Market Analysis:** Moody's "Asset Stripping Transactions" (2017)
- **Legal Commentary:** Wachtell Lipton "The J.Crew 'Trap Door'" (2017)

---

## Appendix: Simplified Credit Agreement Excerpt

See [`jcrew_credit_agreement.txt`](jcrew_credit_agreement.txt) for the sample document analyzed in this case study.

---

**Case Study Author:** Signal Triage Development Team  
**Last Updated:** January 2026  
**Related LME Categories:** Dropdown, Asset Transfer, Blocker Structure, Structural Subordination

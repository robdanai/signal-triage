# Enhanced Parser - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install pdfplumber pytesseract Pillow tabulate
```

### Step 2: Run Demo
```bash
python demo_enhanced_parser.py
```

**Output:** `forensic_extraction_result.json` with full analysis

---

## 📊 What It Does

### 1. Capital Structure Table Extraction
**Automatically parses debt tables from PDFs**

```python
from signal_triage.document_intel import extract_forensic_data

result = extract_forensic_data("credit_agreement.pdf")

for tranche in result.debt_tranches:
    print(f"{tranche.tranche_name}: {tranche.claim_amount}")
    print(f"  Seniority: {tranche.seniority}")
    print(f"  Page: {tranche.page_number}")
```

**Output:**
```
First Lien Term Loan: $500,000,000
  Seniority: Senior Secured
  Page: 5

Second Lien Notes: $200,000,000
  Seniority: Second Lien
  Page: 5
```

---

### 2. EBITDA Normalizer
**Flags aggressive EBITDA add-backs**

```python
ebitda = result.ebitda_definition

print(f"Risk Score: {ebitda.addback_risk_score:.1f}/10.0")
print(f"Synergies Flagged: {ebitda.synergies_flagged}")
print(f"Future Savings Flagged: {ebitda.future_cost_savings_flagged}")
```

**Output:**
```
Risk Score: 7.5/10.0
Synergies Flagged: True
Future Savings Flagged: True

Red Flags:
  🚩 Run-Rate Synergies (Risk: 3.0)
  🚩 Anticipated Cost Savings (Risk: 2.5)
```

**Risk Levels:**
- **0-3:** Conservative (standard add-backs)
- **4-6:** Moderate (some pro-forma adjustments)
- **7-10:** Aggressive (synergies, future savings)

---

### 3. LME Leakage Risk Scoring
**Quantifies collateral leakage risk**

```python
for risk in result.lme_risks:
    print(f"{risk.category}: {risk.leakage_risk_score:.1f}/10.0")
    print(f"  Basket: {risk.basket_size}")
    print(f"  Factors: {', '.join(risk.risk_factors)}")
```

**Output:**
```
Investment in Unrestricted Subsidiary: 9.0/10.0
  Basket: $100,000,000 or 15% of Total Assets
  Factors: IP transfer permitted, No lender consent, J.Crew precedent

Asset Sale Basket: 5.5/10.0
  Basket: $150,000,000
  Factors: No mandatory prepayment/sweep, Ordinary course exemption
```

**Risk Scale:**
- **0-2:** Low (small baskets, strong protections)
- **3-5:** Medium (moderate baskets)
- **6-8:** High (large baskets, weak sweeps)
- **9-10:** Critical (uncapped, no protections)

---

## 💻 Usage Patterns

### Pattern 1: Quick Analysis
```python
from signal_triage.document_intel import extract_forensic_data

# Extract everything at once
result = extract_forensic_data("document.pdf")

# Access results
print(f"Tranches: {len(result.debt_tranches)}")
print(f"EBITDA Risk: {result.ebitda_definition.addback_risk_score:.1f}")
print(f"LME Risks: {len(result.lme_risks)}")
```

### Pattern 2: Integrated Extraction
```python
from signal_triage.document_intel import extract_baskets_and_covenants_enhanced

# Run both standard + enhanced extraction
standard, enhanced = extract_baskets_and_covenants_enhanced("document.pdf")

# Standard covenants
print(f"Baskets found: {len(standard.baskets)}")

# Enhanced forensics
if enhanced:
    print(f"Debt tranches: {len(enhanced.debt_tranches)}")
    print(f"LME risks: {len(enhanced.lme_risks)}")
```

### Pattern 3: Export to JSON
```python
result = extract_forensic_data("document.pdf")

# Export everything
data = result.to_dict()

import json
with open("forensic_output.json", "w") as f:
    json.dump(data, f, indent=2)
```

---

## 🎯 Key Features

| Feature | Description | Output |
|---------|-------------|--------|
| **Table Extraction** | Parse capital structure tables from PDFs | `DebtTranche` objects with seniority, amount, collateral |
| **Tranche Classification** | Auto-identify Senior/2nd Lien/Unsecured | Based on name, collateral, guarantee language |
| **EBITDA Analysis** | Flag aggressive add-backs | Risk score (0-10), flags for synergies/future savings |
| **LME Risk Scoring** | Quantify leakage risk | Risk score (0-10), specific risk factors |
| **Page Citations** | Track source pages for all data | Page numbers for audit trail |

---

## 🔍 Understanding Risk Scores

### EBITDA Add-Back Risks

| Add-Back Type | Risk Weight | Example |
|---------------|-------------|---------|
| Run-Rate Synergies | 3.0 (HIGH) | "Synergies to be realized within 12 months" |
| Anticipated Savings | 2.5 (HIGH) | "Pro-forma cost reductions" |
| Pro-Forma Adjustments | 2.0 (MEDIUM) | "EBITDA as if acquisition occurred day 1" |
| Restructuring Charges | 1.5 (MEDIUM) | "One-time restructuring expenses" |
| Non-Cash Items | 0.5-1.0 (LOW) | "Stock-based compensation" |

### LME Leakage Risks

**Asset Sale Baskets:**
- Basket >$500M: +4.0
- No sweep requirement: +2.0
- No lender consent: +2.0
- Ordinary course exemption: +1.0

**Unrestricted Subsidiary:**
- IP transfer permitted: +3.0
- J.Crew/Chewy language: +2.0
- No lender consent: +2.0
- Large basket (>$100M): +4.0

---

## 📋 Demo Output Example

Run `python demo_enhanced_parser.py` to see:

```
================================================================================
ENHANCED DOCUMENT FORENSICS PARSER - DEMONSTRATION
================================================================================

--------------------------------------------------------------------------------
STEP 2: Capital Structure Analysis
--------------------------------------------------------------------------------

Found 4 debt tranches:

1. First Lien Term Loan
   Seniority: Senior Secured
   Claim: $500,000,000
   Collateral: First Priority Lien on All Assets
   Maturity: December 2028
   Rate: SOFR + 450 bps
   Page: 5

--------------------------------------------------------------------------------
STEP 3: EBITDA Normalizer & Add-Back Analysis
--------------------------------------------------------------------------------

ADD-BACK RISK SCORE: 7.5/10.0
  Risk Level: HIGH (Aggressive)

Red Flags:
  🚩 SYNERGIES: Run-rate synergies or anticipated benefits
  🚩 FUTURE SAVINGS: Forward-looking cost save assumptions
  ℹ️  NON-CASH: Standard non-cash add-backs present

--------------------------------------------------------------------------------
STEP 4: LME Leakage Risk Scoring
--------------------------------------------------------------------------------

1. Investment in Unrestricted Subsidiary
   Risk Score: 9.0/10.0 🔴 CRITICAL
   Basket Size: $100,000,000 or 15% of Total Assets
   Risk Factors:
     - IP transfer permitted
     - No lender consent required
     - J.Crew/Chewy precedent language
   Page: 42

OVERALL FORENSIC RISK SCORE: 7.8/10.0
  ⚠️  HIGH RISK: Material structural leakage concerns
```

---

## 🛠️ Troubleshooting

**"Enhanced parser not available"**
→ Install pdfplumber: `pip install pdfplumber`

**"No capital structure table found"**
→ Requires PDF with embedded tables (not scanned images)

**"EBITDA definition not found"**
→ Parser looks for `"Consolidated EBITDA" means` pattern

**Risk scores seem off**
→ Scoring is heuristic; review `enhanced_parser.py` for custom weights

---

## 📚 More Information

- **Full Documentation:** `docs/ENHANCED_PARSER.md`
- **Implementation Details:** `docs/ENHANCED_PARSER_IMPLEMENTATION.md`
- **API Reference:** `signal_triage/document_intel/enhanced_parser.py`
- **Tests:** `tests/test_enhanced_parser.py`

---

## 🚦 Quick Decision Guide

**Use Enhanced Parser When:**
- ✅ Analyzing credit agreements or indentures
- ✅ Need capital structure reconstruction
- ✅ Evaluating EBITDA covenant quality
- ✅ Assessing LME/collateral leakage risk
- ✅ Working with PDF documents

**Use Standard Extractor When:**
- ✅ Simple text-based covenant extraction
- ✅ No table parsing needed
- ✅ Fast pattern-matching only
- ✅ Working with TXT files

---

## 🎓 Best Practices

1. **Always verify table extraction** - Check that tranches match source document
2. **Focus on high-risk scores** - Prioritize LME risks ≥7.0 and EBITDA risks ≥6.0
3. **Use page citations** - Cross-reference extracted data with source pages
4. **Export to JSON** - Save results for downstream analysis
5. **Review risk factors** - Don't just trust scores; read the specific risk factors

---

## 📞 Getting Help

**Issues or Questions?**
- Review `docs/ENHANCED_PARSER.md` for detailed documentation
- Check `tests/test_enhanced_parser.py` for usage examples
- Run `python demo_enhanced_parser.py` for interactive demo

**Version:** 1.0.0  
**Last Updated:** January 29, 2026

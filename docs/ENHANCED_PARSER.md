# Enhanced Document Forensics Parser

## Overview

The **Enhanced Parser** is a forensic document analysis system designed for senior restructuring analysts. It implements a "Table-First" approach to automatically extract 100% of capital structure and covenant data from raw documents, minimizing manual input and maximizing analytical accuracy.

## Key Features

### 1. Capital Structure Table Extraction
**Goal:** Reconstruct the complete debt capital structure from document tables.

#### Capabilities
- **Automatic Table Detection:** Scans PDFs for capital structure tables using `pdfplumber`
- **Multi-Column Layout Handling:** Parses complex table structures with varying column arrangements
- **Tranche Identification:** Automatically classifies debt tranches by seniority:
  - **Senior Secured** (First Lien)
  - **Second Lien** (Junior Secured)
  - **Unsecured** (Senior Unsecured Notes)
  - **Subordinated** (Junior/Sub Debt)

#### Classification Logic
Tranche seniority is determined using a forensic hierarchy:

1. **Explicit Seniority Column:** If table has a "Seniority" or "Rank" column, use that value
2. **Name-Based Inference:** 
   - "First Lien", "1st Lien", "Senior Secured" → `Senior Secured`
   - "Second Lien", "2nd Lien", "Junior Secured" → `Second Lien`
   - "Unsecured", "Senior Unsecured", "Non-Secured" → `Unsecured`
   - "Subordinated", "Junior" → `Subordinated`
3. **Collateral-Based Inference:**
   - "First Priority Lien", "Security Interest" → `Senior Secured`
   - "Second Priority Lien" → `Second Lien`
   - "No Collateral" → `Unsecured`
4. **Guarantee-Based Inference:**
   - "Guaranteed by All Subsidiaries" + Collateral → `Senior Secured`
   - "Non-Guaranteed" + No Collateral → `Unsecured`

#### Output Schema
```python
@dataclass
class DebtTranche:
    tranche_name: str           # "First Lien Term Loan"
    seniority: str              # "Senior Secured", "Second Lien", etc.
    claim_amount: str | None    # "$500,000,000"
    collateral_type: str | None # "First Priority Lien on All Assets"
    guarantee_status: str | None # "Guaranteed by Subsidiaries"
    maturity_date: str | None   # "2028-12-31"
    interest_rate: str | None   # "L+500", "8.5%"
    page_number: int | None     # Source page citation
    section_reference: str | None
```

---

### 2. EBITDA Normalizer & Add-Back Analysis
**Goal:** Flag aggressive EBITDA definitions that inflate borrowing capacity.

#### Red Flag Categories

| Category | Risk Level | Examples | Risk Weight |
|----------|------------|----------|-------------|
| **Run-Rate Synergies** | HIGH (3.0) | "Run-rate cost savings anticipated to be realized within 12 months" | Future benefits not yet captured |
| **Anticipated Savings** | HIGH (2.5) | "Pro-forma adjustments for pending acquisitions" | Forward-looking assumptions |
| **Pro-Forma Adjustments** | MEDIUM (2.0) | "EBITDA as if acquisition occurred on day 1" | As-if scenarios |
| **Extraordinary Items** | MEDIUM (1.5) | "Extraordinary losses, restructuring charges" | One-time events (legitimate but watch for abuse) |
| **Non-Cash Charges** | LOW (0.5-1.0) | "Stock-based compensation, depreciation" | Standard add-backs |

#### Risk Scoring

**Formula:** Sum of individual add-back risk weights, capped at 10.0

- **0.0 - 3.0:** Conservative (standard EBITDA adjustments only)
- **3.1 - 6.0:** Moderate (some pro-forma adjustments)
- **6.1 - 10.0:** Aggressive (synergies, future cost savings)

#### Flags
```python
@dataclass
class EBITDADefinition:
    base_definition: str
    addbacks: list[dict]            # List of detected add-backs
    addback_risk_score: float       # 0.0 - 10.0
    synergies_flagged: bool         # Run-rate synergies present?
    future_cost_savings_flagged: bool  # Anticipated savings?
    non_cash_gains_flagged: bool    # Non-cash adjustments?
```

#### Example Output
```json
{
  "base_definition": "Consolidated EBITDA means...",
  "addback_risk_score": 7.5,
  "synergies_flagged": true,
  "future_cost_savings_flagged": true,
  "addbacks": [
    {
      "type": "Run-Rate Synergies",
      "context": "...synergies anticipated to be realized within 12 months...",
      "risk_weight": 3.0
    },
    {
      "type": "Anticipated Cost Savings",
      "context": "...anticipated cost savings from restructuring...",
      "risk_weight": 2.5
    }
  ]
}
```

---

### 3. LME Leakage Risk Scoring
**Goal:** Quantify collateral leakage risk from Asset Sale Baskets and Unrestricted Subsidiary investments.

#### Asset Sale Basket Risk Factors

| Factor | Risk Impact | Description |
|--------|-------------|-------------|
| **Basket Size** | +1.0 to +5.0 | >$500M = +4.0; >$100M = +3.0; >$50M = +2.0 |
| **No Sweep Requirement** | +2.0 | No mandatory prepayment of proceeds |
| **Consent Bypass** | +2.0 | "Without lender consent" language |
| **Ordinary Course Exemption** | +1.0 | Sales in "ordinary course of business" |

#### Unrestricted Subsidiary Risk Factors

| Factor | Risk Impact | Description |
|--------|-------------|-------------|
| **Basket Size** | +2.0 to +5.0 | >$100M = +4.0; >$50M = +3.0 |
| **IP Transfer Permitted** | +3.0 | Intellectual property can be moved out |
| **Consent Bypass** | +2.0 | "Without lender consent" |
| **J.Crew Precedent** | +2.0 | "Dropdown", "J.Crew", "Chewy" language |

#### Risk Scoring Scale
- **0.0 - 2.0:** Low risk (small baskets, strong protections)
- **3.0 - 5.0:** Medium risk (moderate baskets, partial sweeps)
- **6.0 - 8.0:** High risk (large baskets, weak sweeps)
- **9.0 - 10.0:** Critical risk (uncapped, no sweeps, J.Crew-style dropdown)

#### Output Schema
```python
@dataclass
class LMELeakageRisk:
    category: str                  # "Asset Sale Basket", "Investment in Unrestricted Sub"
    basket_size: str | None        # "$100,000,000" or "15% of EBITDA"
    leakage_risk_score: float      # 0.0 - 10.0
    risk_factors: list[str]        # Specific concerns
    page_number: int | None
    section_reference: str | None
    evidence_snippet: str | None   # Verbatim text
```

---

## Usage

### Basic Usage

```python
from signal_triage.document_intel import extract_forensic_data

# Extract from PDF or TXT file
result = extract_forensic_data("credit_agreement.pdf")

# Access results
print(f"Found {len(result.debt_tranches)} debt tranches")
print(f"EBITDA Risk Score: {result.ebitda_definition.addback_risk_score:.1f}/10.0")
print(f"LME Risks: {len(result.lme_risks)}")

# Export to JSON
data = result.to_dict()
```

### Integrated Usage (Standard + Enhanced)

```python
from signal_triage.document_intel import extract_baskets_and_covenants_enhanced

# Run both standard and enhanced extraction
standard_result, enhanced_result = extract_baskets_and_covenants_enhanced(
    path="credit_agreement.pdf"
)

# Standard covenant extraction
print(f"Baskets found: {len(standard_result.baskets)}")

# Enhanced forensic data
if enhanced_result:
    print(f"Capital Structure:")
    for tranche in enhanced_result.debt_tranches:
        print(f"  {tranche.tranche_name}: {tranche.claim_amount}")
    
    print(f"\nEBITDA Risk: {enhanced_result.ebitda_definition.addback_risk_score:.1f}/10.0")
    
    print(f"\nLME Risks:")
    for risk in enhanced_result.lme_risks:
        print(f"  {risk.category}: {risk.leakage_risk_score:.1f}/10.0")
```

### Command-Line Usage

```bash
# Run demo with sample document
python demo_enhanced_parser.py

# Analyze specific document
python demo_enhanced_parser.py path/to/credit_agreement.pdf

# Output saved to: forensic_extraction_result.json
```

---

## Technical Details

### Dependencies

```txt
pdfplumber>=0.10.0    # Table extraction from PDFs
pytesseract>=0.3.10   # OCR fallback (optional)
Pillow>=10.0.0        # Image processing for OCR
tabulate>=0.9.0       # Table formatting
```

Install with:
```bash
pip install pdfplumber pytesseract Pillow tabulate
```

### Architecture

```
signal_triage/document_intel/
├── enhanced_parser.py      # NEW: Forensic extraction engine
├── extractor.py            # Standard covenant extraction (updated)
├── patterns.py             # Regex patterns for baskets/covenants
├── schema.py               # Data structures
├── segmenter.py            # Document segmentation
└── __init__.py             # Exports
```

### Integration with Existing Pipeline

The enhanced parser integrates seamlessly with the existing document intelligence pipeline:

1. **Extractor (`extractor.py`):** Calls enhanced parser when available
2. **Librarian Agent (`.cursor/agents/librarian.md`):** Updated instructions for forensic extraction
3. **CLI (`cli.py`):** Can add `--forensic` flag for enhanced extraction
4. **Recovery Engine:** Consumes forensic data for waterfall modeling

---

## Example Output

### Capital Structure Table

```
Found 4 debt tranches:

1. First Lien Term Loan
   Seniority: Senior Secured
   Claim: $500,000,000
   Collateral: First Priority Lien on All Assets
   Maturity: December 2028
   Rate: SOFR + 450 bps
   Page: 5

2. Second Lien Notes
   Seniority: Second Lien
   Claim: $200,000,000
   Collateral: Second Priority Lien on All Assets
   Maturity: June 2029
   Rate: 8.50% Fixed
   Page: 5
```

### EBITDA Analysis

```
ADD-BACK RISK SCORE: 7.5/10.0
Risk Level: HIGH (Aggressive)

Red Flags:
  🚩 SYNERGIES: Run-rate synergies or anticipated benefits
  🚩 FUTURE SAVINGS: Forward-looking cost save assumptions
  ℹ️  NON-CASH: Standard non-cash add-backs present

Add-Backs Detected (6):
  🔴 Run-Rate Synergies (Risk: 3.0)
  🔴 Anticipated Cost Savings (Risk: 2.5)
  🟡 Pro-Forma Adjustments (Risk: 2.0)
  🟡 Restructuring Charges (Risk: 1.5)
  🟢 Stock-Based Compensation (Risk: 0.5)
```

### LME Risk Scoring

```
Found 2 LME risk factors:

1. Investment in Unrestricted Subsidiary
   Risk Score: 9.0/10.0 🔴 CRITICAL
   Basket Size: greater of $100,000,000 and 15% of Consolidated Total Assets
   Risk Factors:
     - IP transfer permitted
     - No lender consent required
     - J.Crew/Chewy precedent language
   Page: 42

2. Asset Sale Basket
   Risk Score: 5.5/10.0 🟠 HIGH
   Basket Size: $150,000,000
   Risk Factors:
     - No mandatory prepayment/sweep
     - Ordinary course exemption
   Page: 38
```

---

## Best Practices

### For Analysts

1. **Review Table Extraction:** Always verify that extracted tranches match the document
2. **Check EBITDA Flags:** High synergy/future savings = reduced borrowing capacity in distress
3. **Score LME Risks:** Focus on 7.0+ risk scores (critical leakage concerns)
4. **Cross-Reference:** Use page citations to verify all extracted data

### For Integration

1. **Graceful Fallback:** Enhanced parser requires `pdfplumber`; check `ENHANCED_PARSER_AVAILABLE`
2. **Error Handling:** Table extraction may fail on complex layouts; always handle exceptions
3. **Page Mapping:** For accurate page citations, maintain `page_by_char` mapping
4. **JSON Export:** All results are JSON-serializable for downstream consumption

### For Testing

1. **Unit Tests:** See `tests/test_enhanced_parser.py`
2. **Sample Documents:** Use `demo_enhanced_parser.py` for end-to-end testing
3. **Edge Cases:** Test with missing tables, no EBITDA definition, empty documents

---

## Librarian Agent Integration

The **Librarian Agent** (`.cursor/agents/librarian.md`) now uses enhanced forensic extraction:

### Updated Workflow

1. **Ingest Document:** Read PDF or TXT file
2. **Run Standard Extraction:** Covenant/basket detection via regex patterns
3. **Run Forensic Extraction:** Table parsing, EBITDA analysis, LME scoring
4. **Merge Results:** Combine standard + forensic data
5. **Flag Collateral Leakage:** High-risk LME baskets → Quant Agent
6. **Emit JSON:** Structured output for recovery waterfall

### Agent Capabilities (New)

- **Capital Structure Reconstruction:** Automatically parse debt table from PDF
- **Tranche Classification:** Distinguish Senior/Second Lien/Unsecured
- **EBITDA Red Flags:** Score add-back aggressiveness (0-10 scale)
- **LME Risk Quantification:** Asset sale + unrestricted sub leakage scores

---

## Future Enhancements

### Planned Features

1. **OCR Integration:** Use `pytesseract` for scanned PDFs
2. **Multi-Page Tables:** Handle tables spanning multiple pages
3. **Covenant Headroom:** Calculate distance to breach for financial covenants
4. **Priming Risk Matrix:** Cross-reference incremental facilities + amendment provisions
5. **Dropdown Detection:** Advanced J.Crew-style transaction pattern matching
6. **Collateral Coverage:** Calculate collateral value vs. secured debt
7. **Recovery Analysis:** Integrate with recovery waterfall for tranche-level recovery rates

### Roadmap

- **Q1 2026:** OCR fallback for scanned documents
- **Q2 2026:** Multi-page table stitching
- **Q3 2026:** Covenant headroom calculator
- **Q4 2026:** Full priming risk matrix integration

---

## Troubleshooting

### Common Issues

**Issue:** "Enhanced parser not available"  
**Solution:** Install `pdfplumber`: `pip install pdfplumber`

**Issue:** "No capital structure table found"  
**Solution:** Table extraction requires PDF format with embedded tables. Convert scanned PDFs to text-based PDFs or use OCR.

**Issue:** "EBITDA definition not found"  
**Solution:** Parser looks for `"Consolidated EBITDA" means` pattern. Check that definition uses standard terminology.

**Issue:** "LME risks score too low/high"  
**Solution:** Risk scoring is heuristic-based. Review `_score_asset_sale_basket()` and `_score_unrestricted_sub_basket()` for custom weighting.

---

## API Reference

See `signal_triage/document_intel/enhanced_parser.py` for full API documentation.

### Key Functions

- **`extract_forensic_data(path, text, page_by_char)`:** Main entry point
- **`extract_tables_from_pdf(pdf_path)`:** PDF table extraction
- **`parse_capital_structure_table(table_dict)`:** Parse debt tranches
- **`extract_ebitda_definition(text, page_by_char)`:** EBITDA analysis
- **`score_lme_leakage_risk(text, page_by_char)`:** LME risk scoring

### Key Classes

- **`DebtTranche`:** Single debt tranche (name, seniority, amount, collateral)
- **`EBITDADefinition`:** EBITDA definition with add-back risk score
- **`LMELeakageRisk`:** Single LME risk factor (category, size, score)
- **`EnhancedExtractionResult`:** Complete forensic extraction result

---

## Credits

**Author:** Senior Restructuring Analyst (Document Forensics)  
**Version:** 1.0.0  
**Date:** January 2026  
**License:** Internal Use

**Special Thanks:**
- J.Crew Bondholders (for the LME precedent that inspired this tool)
- Serta Simmons Minority Lenders (for the priming risk patterns)
- Chewy Lenders (for the unrestricted subsidiary dropdown case study)

---

## Contact & Support

For questions, bug reports, or feature requests, contact the **Librarian Agent** or open an issue in the Signal-Triage repository.

**Documentation Version:** 1.0  
**Last Updated:** January 29, 2026

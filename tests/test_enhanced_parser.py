"""
Test suite for Enhanced Parser (Document Forensics)
Tests table extraction, EBITDA analysis, and LME risk scoring.
"""

import pytest
from pathlib import Path

from signal_triage.document_intel.enhanced_parser import (
    extract_forensic_data,
    extract_ebitda_definition,
    score_lme_leakage_risk,
    parse_capital_structure_table,
    identify_capital_structure_table,
    _infer_seniority,
    _extract_dollar_or_formula,
    _score_asset_sale_basket,
    _score_unrestricted_sub_basket,
)


# ============================================================================
# SAMPLE DOCUMENTS FOR TESTING
# ============================================================================

SAMPLE_CREDIT_AGREEMENT = """
CREDIT AGREEMENT

dated as of December 15, 2023

ARTICLE I
DEFINITIONS

"Consolidated EBITDA" means, for any period, Consolidated Net Income for such period plus:

(a) interest expense, to the extent deducted in computing Consolidated Net Income;
(b) income tax expense, to the extent deducted in computing Consolidated Net Income;
(c) depreciation and amortization expense;
(d) non-cash charges and expenses, including stock-based compensation;
(e) restructuring charges and one-time expenses;
(f) run-rate cost savings and synergies anticipated to be realized within 12 months;
(g) pro-forma adjustments for acquisitions;
(h) extraordinary losses and non-recurring charges.

ARTICLE VII
NEGATIVE COVENANTS

Section 7.05. Asset Sales. The Borrower shall not, and shall not permit any Subsidiary to, 
dispose of any asset or property except (a) sales of inventory in the ordinary course of business, 
(b) dispositions of obsolete or worn-out equipment, and (c) other asset sales in an aggregate amount 
not to exceed $150,000,000 in any fiscal year, provided that the Net Cash Proceeds of any such sale 
in excess of $50,000,000 shall be applied to mandatory prepayment of the Term Loans.

Section 7.08. Investments in Unrestricted Subsidiaries. The Borrower may designate any Subsidiary 
as an Unrestricted Subsidiary and may make investments in or transfer assets (including intellectual 
property) to any Unrestricted Subsidiary, provided that the aggregate amount of such investments and 
transfers shall not exceed the greater of $100,000,000 and 15% of Consolidated Total Assets at the 
time of such investment or transfer, without the consent of the Required Lenders.

Section 7.12. Incremental Facilities. The Borrower may incur additional Incremental Term Loans or 
establish Incremental Revolving Commitments in an aggregate principal amount not to exceed 
$200,000,000, which may be incurred at the sole discretion of the Borrower without the consent of 
any Lender other than the Incremental Lenders providing such facility.
"""

SAMPLE_CAPITAL_STRUCTURE_TABLE = {
    "page": 5,
    "table_index": 0,
    "table": [
        ["Facility", "Principal Amount", "Maturity", "Interest Rate", "Security", "Guarantees"],
        ["First Lien Term Loan", "$500,000,000", "December 2028", "SOFR + 450 bps", "First Priority Lien on All Assets", "Guaranteed by All Subsidiaries"],
        ["Second Lien Notes", "$200,000,000", "June 2029", "8.50% Fixed", "Second Priority Lien on All Assets", "Guaranteed by All Subsidiaries"],
        ["Senior Unsecured Notes", "$150,000,000", "December 2027", "9.25% Fixed", "No Collateral", "Non-Guaranteed"],
        ["Revolving Credit Facility", "$50,000,000", "December 2026", "SOFR + 400 bps", "First Priority Lien (Pari Passu)", "Guaranteed by All Subsidiaries"],
    ],
    "bbox": None,
}


# ============================================================================
# TESTS: EBITDA NORMALIZER
# ============================================================================

def test_extract_ebitda_definition():
    """Test EBITDA definition extraction and add-back analysis."""
    result = extract_ebitda_definition(SAMPLE_CREDIT_AGREEMENT)
    
    assert result is not None
    assert "Consolidated EBITDA" in result.base_definition
    
    # Check add-backs detected
    assert len(result.addbacks) > 0
    
    # Check flags
    assert result.synergies_flagged is True  # "run-rate cost savings and synergies"
    assert result.future_cost_savings_flagged is True  # "anticipated to be realized"
    assert result.non_cash_gains_flagged is True  # "non-cash charges"
    
    # Risk score should be elevated due to synergies and anticipated savings
    assert result.addback_risk_score >= 4.0, f"Expected risk score >= 4.0, got {result.addback_risk_score}"
    
    # Check specific add-backs
    addback_types = [a["type"] for a in result.addbacks]
    assert "Run-Rate Synergies" in addback_types or "Synergies" in addback_types
    assert any("Stock-Based Compensation" in t or "Non-Cash" in t for t in addback_types)


def test_ebitda_conservative_definition():
    """Test EBITDA definition with only standard add-backs (low risk)."""
    conservative_text = """
    "Consolidated EBITDA" means, for any period, net income plus:
    (a) interest expense;
    (b) income tax expense;
    (c) depreciation and amortization.
    """
    
    result = extract_ebitda_definition(conservative_text)
    
    assert result is not None
    assert result.synergies_flagged is False
    assert result.future_cost_savings_flagged is False
    assert result.addback_risk_score <= 1.0  # Should be very low risk


def test_ebitda_aggressive_definition():
    """Test EBITDA definition with aggressive add-backs (high risk)."""
    aggressive_text = """
    "Consolidated EBITDA" means net income plus:
    (a) interest, taxes, depreciation, amortization;
    (b) run-rate synergies from acquisitions expected to be realized within 24 months;
    (c) anticipated cost savings from restructuring initiatives;
    (d) pro-forma adjustments for pending acquisitions;
    (e) extraordinary losses and non-recurring items.
    """
    
    result = extract_ebitda_definition(aggressive_text)
    
    assert result is not None
    assert result.synergies_flagged is True
    assert result.future_cost_savings_flagged is True
    assert result.addback_risk_score >= 7.0  # Should be high risk


# ============================================================================
# TESTS: LME LEAKAGE RISK SCORING
# ============================================================================

def test_score_asset_sale_basket_high_risk():
    """Test asset sale basket with high leakage risk."""
    risks = score_lme_leakage_risk(SAMPLE_CREDIT_AGREEMENT)
    
    # Should find at least one asset sale basket
    asset_sale_risks = [r for r in risks if r.category == "Asset Sale Basket"]
    assert len(asset_sale_risks) > 0
    
    risk = asset_sale_risks[0]
    assert risk.basket_size is not None
    assert "$150" in risk.basket_size or "$50" in risk.basket_size
    
    # Risk score should be medium-high due to $150M basket with partial sweep
    assert risk.leakage_risk_score >= 3.0


def test_score_unrestricted_sub_basket_high_risk():
    """Test unrestricted subsidiary basket with high leakage risk."""
    risks = score_lme_leakage_risk(SAMPLE_CREDIT_AGREEMENT)
    
    # Should find unrestricted subsidiary basket
    unrestricted_risks = [r for r in risks if r.category == "Investment in Unrestricted Subsidiary"]
    assert len(unrestricted_risks) > 0
    
    risk = unrestricted_risks[0]
    assert risk.basket_size is not None
    assert "100,000,000" in risk.basket_size or "15%" in risk.basket_size
    
    # Risk score should be high due to IP transfer + large basket
    assert risk.leakage_risk_score >= 6.0
    
    # Check risk factors
    assert any("IP transfer" in f or "consent" in f for f in risk.risk_factors)


def test_extract_dollar_or_formula():
    """Test dollar amount and formula extraction."""
    # Test dollar amount
    assert _extract_dollar_or_formula("amount not to exceed $150,000,000") == "$150,000,000"
    assert _extract_dollar_or_formula("$50M basket") == "$50M"
    
    # Test percentage formula
    assert "15% of Consolidated Total Assets" in _extract_dollar_or_formula(
        "not to exceed 15% of Consolidated Total Assets"
    )
    
    # Test no match
    assert _extract_dollar_or_formula("no specific limit mentioned") is None


def test_score_asset_sale_basket_with_sweep():
    """Test asset sale basket with sweep (lower risk)."""
    context_with_sweep = """
    Asset sales permitted up to $50,000,000 per year, provided that 100% of Net Cash Proceeds 
    shall be applied to mandatory prepayment of the Term Loans.
    """
    
    score = _score_asset_sale_basket(context_with_sweep, "$50,000,000")
    
    # Should be lower risk due to full sweep requirement
    assert score < 5.0


def test_score_asset_sale_basket_no_sweep():
    """Test asset sale basket without sweep (higher risk)."""
    context_no_sweep = """
    Asset sales permitted up to $200,000,000 per year at the sole discretion of the Borrower, 
    without the consent of any Lender.
    """
    
    score = _score_asset_sale_basket(context_no_sweep, "$200,000,000")
    
    # Should be high risk: large basket + no sweep + no consent
    assert score >= 7.0


# ============================================================================
# TESTS: CAPITAL STRUCTURE TABLE PARSING
# ============================================================================

def test_identify_capital_structure_table():
    """Test identification of capital structure table."""
    tables = [
        SAMPLE_CAPITAL_STRUCTURE_TABLE,
        {
            "page": 3,
            "table_index": 0,
            "table": [
                ["Item", "Value"],
                ["Company Name", "Acme Corp"],
            ],
        },
    ]
    
    result = identify_capital_structure_table(tables)
    
    assert result is not None
    assert result["page"] == 5


def test_parse_capital_structure_table():
    """Test parsing of capital structure table."""
    tranches = parse_capital_structure_table(SAMPLE_CAPITAL_STRUCTURE_TABLE)
    
    assert len(tranches) == 4  # 4 debt tranches (excluding header)
    
    # Check first tranche (First Lien Term Loan)
    first_lien = tranches[0]
    assert first_lien.tranche_name == "First Lien Term Loan"
    assert first_lien.seniority == "Senior Secured"
    assert "$500,000,000" in first_lien.claim_amount
    assert first_lien.page_number == 5
    
    # Check second tranche (Second Lien Notes)
    second_lien = tranches[1]
    assert second_lien.tranche_name == "Second Lien Notes"
    assert second_lien.seniority == "Second Lien"
    assert "$200,000,000" in second_lien.claim_amount
    
    # Check unsecured notes
    unsecured = tranches[2]
    assert unsecured.tranche_name == "Senior Unsecured Notes"
    assert unsecured.seniority == "Unsecured"
    assert "$150,000,000" in unsecured.claim_amount


def test_infer_seniority_from_name():
    """Test seniority inference from tranche name."""
    assert _infer_seniority("First Lien Term Loan", None, None, None) == "Senior Secured"
    assert _infer_seniority("Second Lien Notes", None, None, None) == "Second Lien"
    assert _infer_seniority("Senior Unsecured Notes", None, None, None) == "Unsecured"
    assert _infer_seniority("Subordinated Debentures", None, None, None) == "Subordinated"


def test_infer_seniority_from_collateral():
    """Test seniority inference from collateral description."""
    assert _infer_seniority(
        "Term Loan A", None, "First Priority Lien on All Assets", None
    ) == "Senior Secured"
    
    assert _infer_seniority(
        "Notes", None, "No Collateral", None
    ) == "Unsecured"


# ============================================================================
# TESTS: FULL INTEGRATION
# ============================================================================

def test_extract_forensic_data_from_text():
    """Test full forensic extraction from text (no PDF)."""
    # Create a temporary text file
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(SAMPLE_CREDIT_AGREEMENT)
        temp_path = f.name
    
    try:
        result = extract_forensic_data(temp_path)
        
        # Check EBITDA extraction
        assert result.ebitda_definition is not None
        assert result.ebitda_definition.synergies_flagged is True
        
        # Check LME risks
        assert len(result.lme_risks) >= 2  # Asset sale + unrestricted sub
        
        # Check metadata
        assert result.metadata["ebitda_definition_found"] is True
        assert result.metadata["lme_risks_identified"] >= 2
        
    finally:
        Path(temp_path).unlink()


def test_extract_forensic_data_handles_missing_sections():
    """Test forensic extraction with minimal document."""
    minimal_text = """
    CREDIT AGREEMENT
    
    Section 7.05. Asset Sales. Permitted up to $50M.
    """
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(minimal_text)
        temp_path = f.name
    
    try:
        result = extract_forensic_data(temp_path)
        
        # Should not crash, but may have minimal results
        assert result is not None
        assert result.metadata["ebitda_definition_found"] is False
        
    finally:
        Path(temp_path).unlink()


# ============================================================================
# TESTS: EDGE CASES
# ============================================================================

def test_ebitda_extraction_with_no_definition():
    """Test EBITDA extraction when no definition present."""
    text_no_ebitda = "This is a contract with no EBITDA definition."
    
    result = extract_ebitda_definition(text_no_ebitda)
    
    assert result is None


def test_lme_scoring_with_no_baskets():
    """Test LME risk scoring when no baskets present."""
    text_no_baskets = "This document has no asset sale or unrestricted subsidiary language."
    
    risks = score_lme_leakage_risk(text_no_baskets)
    
    assert len(risks) == 0


def test_capital_structure_with_empty_table():
    """Test capital structure parsing with empty table."""
    empty_table = {
        "page": 1,
        "table_index": 0,
        "table": [],
    }
    
    tranches = parse_capital_structure_table(empty_table)
    
    assert len(tranches) == 0


def test_capital_structure_with_malformed_table():
    """Test capital structure parsing with malformed table."""
    malformed_table = {
        "page": 1,
        "table_index": 0,
        "table": [
            ["Header 1", "Header 2"],
            [None, None],  # Empty row
            ["Data", None],  # Partial row
        ],
    }
    
    # Should not crash
    tranches = parse_capital_structure_table(malformed_table)
    
    # May or may not find valid tranches, but should not error
    assert isinstance(tranches, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

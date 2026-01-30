"""
Demo: Enhanced Document Forensics Parser
Demonstrates table extraction, EBITDA analysis, and LME risk scoring.

Usage:
    python demo_enhanced_parser.py [document_path]
    
If no document path provided, uses built-in sample document.
"""

import sys
import json
from pathlib import Path

from signal_triage.document_intel import (
    extract_baskets_and_covenants_enhanced,
    ENHANCED_PARSER_AVAILABLE,
)


# Sample credit agreement for demo
SAMPLE_CREDIT_AGREEMENT = """
CREDIT AGREEMENT
dated as of December 15, 2023

Between DISTRESSED BORROWER INC. and SENIOR LENDERS

═══════════════════════════════════════════════════════════════════════════════
CAPITAL STRUCTURE SUMMARY
═══════════════════════════════════════════════════════════════════════════════

The Company's debt structure as of the Closing Date:

Facility                      Principal Amount    Maturity        Interest Rate                Security                    Guarantees
First Lien Term Loan          $500,000,000       Dec 31, 2028    SOFR + 450 bps              First Priority Lien         Guaranteed by All Subs
Second Lien Term Loan         $200,000,000       Jun 30, 2029    SOFR + 850 bps              Second Priority Lien        Guaranteed by All Subs
Senior Unsecured Notes        $150,000,000       Dec 31, 2027    9.25% Fixed                 No Collateral               Non-Guaranteed
Revolving Credit Facility     $50,000,000        Dec 31, 2026    SOFR + 400 bps              First Priority (Pari)       Guaranteed by All Subs

Total Debt: $900,000,000

═══════════════════════════════════════════════════════════════════════════════
ARTICLE I - DEFINITIONS
═══════════════════════════════════════════════════════════════════════════════

Section 1.01. Defined Terms.

"Consolidated EBITDA" means, for any period, Consolidated Net Income for such period, plus:

(a) interest expense and bank fees, to the extent deducted in computing Consolidated Net Income;

(b) income tax expense (including franchise taxes), to the extent deducted in computing 
    Consolidated Net Income;

(c) depreciation and amortization expense (including amortization of intangibles and 
    deferred financing costs);

(d) non-cash charges and expenses, including:
    (i) stock-based compensation expense;
    (ii) write-offs of deferred financing costs;
    (iii) non-cash losses on asset dispositions;

(e) restructuring charges, severance costs, and facility closure expenses incurred in 
    connection with business optimization initiatives;

(f) one-time transaction expenses related to acquisitions, dispositions, or refinancings;

(g) run-rate cost savings and synergies (certified by a Financial Officer) anticipated to 
    be realized within 12 months of the relevant transaction, not to exceed 15% of 
    Consolidated EBITDA calculated without giving effect to this clause (g);

(h) pro-forma adjustments for acquisitions completed during the measurement period, 
    calculated as if such acquisitions had been consummated on the first day of such period;

(i) extraordinary losses and non-recurring charges or expenses.

EBITDA ADD-BACK RED FLAGS:
• Clause (g): Run-rate synergies capped at 15% - AGGRESSIVE
• Clause (h): Pro-forma adjustments for acquisitions - FORWARD-LOOKING
• Clause (f): One-time expenses - POTENTIAL FOR ABUSE

═══════════════════════════════════════════════════════════════════════════════
ARTICLE VII - NEGATIVE COVENANTS
═══════════════════════════════════════════════════════════════════════════════

Section 7.05. Limitation on Asset Sales.

The Borrower shall not, and shall not permit any Restricted Subsidiary to, make any Asset 
Sale, except:

(a) sales of inventory in the ordinary course of business;

(b) dispositions of obsolete, worn-out, or surplus equipment or property that is no longer 
    useful in the business of the Borrower or any Subsidiary;

(c) other Asset Sales in an aggregate amount not to exceed $150,000,000 in any fiscal year;

PROVIDED that:

(i) all Asset Sales are made for fair market value;

(ii) at least 75% of the consideration consists of cash or Cash Equivalents; and

(iii) the Net Cash Proceeds of any Asset Sale in excess of $50,000,000 in the aggregate 
      during any fiscal year shall be applied to the mandatory prepayment of the Term Loans 
      in accordance with Section 2.05(b).

LEAKAGE ANALYSIS:
• $150M basket - MATERIAL SIZE
• Only 50% sweep threshold ($50M) - WEAK PROTECTION
• 75% cash requirement - ALLOWS 25% NON-CASH CONSIDERATION
• Fair market value standard - VALUATION GAMING RISK

═══════════════════════════════════════════════════════════════════════════════

Section 7.08. Investments in Unrestricted Subsidiaries.

The Borrower may:

(a) designate any existing Restricted Subsidiary as an Unrestricted Subsidiary;

(b) make investments in or loans to any Unrestricted Subsidiary;

(c) transfer assets (including, without limitation, intellectual property, brands, trademarks, 
    patents, and other intangible assets) to any Unrestricted Subsidiary;

PROVIDED that the aggregate amount of all such designations, investments, loans, and asset 
transfers shall not exceed the greater of:

    (i) $100,000,000, and
    (ii) 15% of Consolidated Total Assets at the time of such transaction,

without the consent of Required Lenders (as defined in Section 10.01).

CRITICAL LME RISK:
• J.Crew-style dropdown basket: $100M or 15% of assets
• IP transfer explicitly permitted - CROWN JEWELS AT RISK
• Only Required Lenders (>50%) consent needed - MINORITY SQUEEZE
• No restrictions on use of proceeds by Unrestricted Sub
• LEAKAGE RISK SCORE: 9.0/10.0 (CRITICAL)

═══════════════════════════════════════════════════════════════════════════════

Section 7.12. Incremental Facilities.

Subject to the terms and conditions set forth in this Agreement, the Borrower may from time 
to time incur Incremental Term Loans or establish Incremental Revolving Commitments in an 
aggregate principal amount not to exceed the sum of:

(a) $200,000,000 (the "Free and Clear Basket"); plus

(b) an unlimited amount, so long as, after giving pro forma effect to the incurrence of such 
    Incremental Debt, the Secured Leverage Ratio does not exceed 4.00:1.00 (the "Ratio Basket").

The Incremental Facilities may be incurred at the sole discretion of the Borrower and may be 
pari passu with or junior to the existing First Lien Term Loan, without the consent of any 
Lender other than the Incremental Lenders providing such facility.

PRIMING RISK ANALYSIS:
• $200M free-and-clear basket - NO LEVERAGE TEST
• Unlimited ratio basket at 4.0x - UNCAPPED IF TEST MET
• Pari passu permitted WITHOUT LENDER CONSENT
• Classic "Serta-style" priming risk
• Required Lenders (>50%) can amend lien priority per Section 10.01
• PRIMING RISK: HIGH

═══════════════════════════════════════════════════════════════════════════════

Section 10.01. Amendments; Required Lenders.

Amendments to this Agreement require the consent of Required Lenders (Lenders holding more 
than 50% of the aggregate outstanding principal amount of the Term Loans), EXCEPT that 
unanimous Lender consent is required to:

(a) reduce the principal amount or interest rate;
(b) extend the maturity date;
(c) release all or substantially all of the Collateral (other than as permitted by this Agreement).

Notably, amendments to lien priority, security interests, or the addition of pari passu or 
junior Incremental Facilities do NOT require unanimous consent and may be approved by 
Required Lenders.

VOTING SQUEEZE:
• Majority (>50%) can modify lien priority
• Minority lenders can be primed without consent
• No "sacred rights" protection for collateral value
"""


def demo_enhanced_parser(document_path: str | None = None):
    """
    Demonstrate enhanced parser capabilities.
    """
    print("=" * 80)
    print("ENHANCED DOCUMENT FORENSICS PARSER - DEMONSTRATION")
    print("=" * 80)
    print()
    
    if not ENHANCED_PARSER_AVAILABLE:
        print("WARNING: Enhanced parser not available (pdfplumber not installed)")
        print("Install with: pip install pdfplumber")
        print()
    
    # Create temporary document if none provided
    if document_path is None:
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write(SAMPLE_CREDIT_AGREEMENT)
            document_path = f.name
        
        print(f"Using sample credit agreement (saved to: {document_path})")
        created_temp = True
    else:
        print(f"Analyzing document: {document_path}")
        created_temp = False
    
    print()
    print("-" * 80)
    print("STEP 1: Running Enhanced Extraction")
    print("-" * 80)
    
    # Run extraction
    standard_result, enhanced_result = extract_baskets_and_covenants_enhanced(
        path=document_path
    )
    
    print(f"✓ Standard extraction complete")
    print(f"  - Segments found: {len(standard_result.segments)}")
    print(f"  - Baskets found: {len(standard_result.baskets)}")
    print()
    
    if enhanced_result:
        print(f"✓ Enhanced forensic extraction complete")
        print()
        
        # =====================================================================
        # CAPITAL STRUCTURE
        # =====================================================================
        print("-" * 80)
        print("STEP 2: Capital Structure Analysis")
        print("-" * 80)
        print()
        
        if enhanced_result.debt_tranches:
            print(f"Found {len(enhanced_result.debt_tranches)} debt tranches:\n")
            
            total_debt = 0
            for i, tranche in enumerate(enhanced_result.debt_tranches, 1):
                print(f"{i}. {tranche.tranche_name}")
                print(f"   Seniority: {tranche.seniority}")
                print(f"   Claim: {tranche.claim_amount or 'Not specified'}")
                print(f"   Collateral: {tranche.collateral_type or 'None'}")
                print(f"   Maturity: {tranche.maturity_date or 'Not specified'}")
                print(f"   Rate: {tranche.interest_rate or 'Not specified'}")
                print(f"   Page: {tranche.page_number or 'N/A'}")
                print()
                
                # Try to extract dollar amount for total
                if tranche.claim_amount:
                    import re
                    m = re.search(r'\$[\d,]+', tranche.claim_amount)
                    if m:
                        amount_str = m.group(0).replace('$', '').replace(',', '')
                        try:
                            total_debt += float(amount_str)
                        except:
                            pass
            
            if total_debt > 0:
                print(f"Total Debt (calculated): ${total_debt:,.0f}")
                print()
        else:
            print("No capital structure table found in document")
            print("(Table extraction requires PDF format with pdfplumber)")
            print()
        
        # =====================================================================
        # EBITDA ANALYSIS
        # =====================================================================
        print("-" * 80)
        print("STEP 3: EBITDA Normalizer & Add-Back Analysis")
        print("-" * 80)
        print()
        
        if enhanced_result.ebitda_definition:
            ebitda = enhanced_result.ebitda_definition
            
            print("EBITDA Definition Found:")
            print(f"  Base Definition: {ebitda.base_definition[:150]}...")
            print()
            
            print(f"ADD-BACK RISK SCORE: {ebitda.addback_risk_score:.1f}/10.0")
            
            if ebitda.addback_risk_score <= 3.0:
                risk_label = "LOW (Conservative)"
            elif ebitda.addback_risk_score <= 6.0:
                risk_label = "MEDIUM (Moderate)"
            else:
                risk_label = "HIGH (Aggressive)"
            
            print(f"  Risk Level: {risk_label}")
            print()
            
            print("Red Flags:")
            if ebitda.synergies_flagged:
                print("  🚩 SYNERGIES: Run-rate synergies or anticipated benefits")
            if ebitda.future_cost_savings_flagged:
                print("  🚩 FUTURE SAVINGS: Forward-looking cost save assumptions")
            if ebitda.non_cash_gains_flagged:
                print("  ℹ️  NON-CASH: Standard non-cash add-backs present")
            print()
            
            if ebitda.addbacks:
                print(f"Add-Backs Detected ({len(ebitda.addbacks)}):")
                for ab in ebitda.addbacks:
                    risk_marker = "🔴" if ab['risk_weight'] >= 2.0 else "🟡" if ab['risk_weight'] >= 1.0 else "🟢"
                    print(f"  {risk_marker} {ab['type']} (Risk: {ab['risk_weight']:.1f})")
                print()
        else:
            print("No EBITDA definition found in document")
            print()
        
        # =====================================================================
        # LME RISK SCORING
        # =====================================================================
        print("-" * 80)
        print("STEP 4: LME Leakage Risk Scoring")
        print("-" * 80)
        print()
        
        if enhanced_result.lme_risks:
            print(f"Found {len(enhanced_result.lme_risks)} LME risk factors:\n")
            
            # Sort by risk score (highest first)
            sorted_risks = sorted(
                enhanced_result.lme_risks,
                key=lambda r: r.leakage_risk_score,
                reverse=True
            )
            
            for i, risk in enumerate(sorted_risks, 1):
                # Risk level emoji
                if risk.leakage_risk_score >= 7.0:
                    risk_emoji = "🔴 CRITICAL"
                elif risk.leakage_risk_score >= 5.0:
                    risk_emoji = "🟠 HIGH"
                elif risk.leakage_risk_score >= 3.0:
                    risk_emoji = "🟡 MEDIUM"
                else:
                    risk_emoji = "🟢 LOW"
                
                print(f"{i}. {risk.category}")
                print(f"   Risk Score: {risk.leakage_risk_score:.1f}/10.0 {risk_emoji}")
                print(f"   Basket Size: {risk.basket_size or 'Not specified'}")
                
                if risk.risk_factors:
                    print(f"   Risk Factors:")
                    for factor in risk.risk_factors:
                        print(f"     - {factor}")
                
                print(f"   Page: {risk.page_number or 'N/A'}")
                print()
        else:
            print("No LME risks detected in document")
            print()
        
        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("-" * 80)
        print("STEP 5: Forensic Summary")
        print("-" * 80)
        print()
        
        print("Extraction Metadata:")
        for key, value in enhanced_result.metadata.items():
            print(f"  {key}: {value}")
        print()
        
        # Calculate overall risk
        ebitda_risk = enhanced_result.ebitda_definition.addback_risk_score if enhanced_result.ebitda_definition else 0
        max_lme_risk = max([r.leakage_risk_score for r in enhanced_result.lme_risks], default=0)
        
        overall_risk = (ebitda_risk * 0.3 + max_lme_risk * 0.7)  # Weight LME risk more heavily
        
        print(f"OVERALL FORENSIC RISK SCORE: {overall_risk:.1f}/10.0")
        
        if overall_risk >= 7.0:
            print("  ⚠️  HIGH RISK: Material structural leakage concerns")
        elif overall_risk >= 4.0:
            print("  ⚠️  MEDIUM RISK: Moderate leakage/covenant concerns")
        else:
            print("  ✓ LOW RISK: Conservative covenant package")
        print()
        
        # Export to JSON
        print("-" * 80)
        print("Exporting results to JSON...")
        print("-" * 80)
        
        output_data = {
            "standard_extraction": standard_result.to_dict(),
            "forensic_extraction": enhanced_result.to_dict(),
        }
        
        output_path = Path("forensic_extraction_result.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✓ Results saved to: {output_path.resolve()}")
        print()
    
    else:
        print("Enhanced extraction not available (requires pdfplumber)")
        print()
    
    # Cleanup
    if created_temp:
        Path(document_path).unlink()
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Check for document path argument
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
    else:
        doc_path = None
    
    demo_enhanced_parser(doc_path)

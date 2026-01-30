"""
Validation Scenarios for Enhanced Parser Testing
Centralized scenario definitions to avoid circular imports

WORKSTREAM 3: Enhanced Parser Validation
"""

# Scenario 1: Investment Grade - Conservative Structure
INVESTMENT_GRADE_AGREEMENT = """
CREDIT AGREEMENT
ABC CORPORATION (Investment Grade)
Dated: January 15, 2024

CAPITAL STRUCTURE

Facility                    Principal          Maturity        Rate              Security
Senior Secured Term Loan    $300,000,000      Jan 2029        SOFR + 200        First Priority
Revolving Credit Facility   $100,000,000      Jan 2028        SOFR + 175        First Priority

"Consolidated EBITDA" means, for any period, net income plus:
(a) interest expense;
(b) income tax expense;
(c) depreciation and amortization.

Section 7.05. Asset Sales. Permitted only with lender consent or in ordinary course.
100% of net proceeds shall be applied to mandatory prepayment.

Section 7.08. Investments. No investments in Unrestricted Subsidiaries permitted.
"""

# Scenario 2: Distressed Borrower - Aggressive EBITDA
DISTRESSED_AGGRESSIVE_EBITDA = """
CREDIT AGREEMENT
DISTRESSED CORP (Covenant-Lite Structure)
Dated: March 2024

"Consolidated EBITDA" means net income plus:
(a) interest, taxes, depreciation, amortization;
(b) non-cash charges including stock-based compensation;
(c) restructuring charges and one-time expenses;
(d) run-rate cost savings expected to be realized within 18 months, not to exceed 20% of EBITDA;
(e) run-rate synergies from acquisitions anticipated within 24 months;
(f) pro-forma EBITDA adjustments as if all acquisitions occurred on first day of period;
(g) anticipated cost savings from pending restructuring initiatives;
(h) extraordinary and non-recurring losses;
(i) future cost savings certified by CFO.

This definition includes multiple forward-looking adjustments.
"""

# Scenario 3: High LME Risk - J.Crew Style Dropdown
HIGH_LME_RISK_JCREW = """
CREDIT AGREEMENT
RETAIL BORROWER INC.
Dated: June 2024

Section 7.08. Unrestricted Subsidiaries.

The Borrower may designate any Subsidiary as Unrestricted and may transfer assets
(including intellectual property, brands, trademarks, patents, and other intangible assets)
to any Unrestricted Subsidiary without lender consent, provided that:

(a) aggregate transfers do not exceed the greater of $250,000,000 and 25% of Total Assets;
(b) the Borrower delivers a certificate from the CFO.

This is a "J.Crew" or "Chewy" style dropdown transaction structure.
No sweep required. IP transfer explicitly permitted.
"""

# Scenario 4: Asset Sale Basket - Large with Weak Sweep
LARGE_ASSET_SALE_BASKET = """
CREDIT AGREEMENT
MANUFACTURING CO.
Dated: September 2024

Section 7.05. Asset Dispositions.

Permitted Asset Sales:
(a) up to $500,000,000 in any fiscal year without lender consent;
(b) in the ordinary course of business;
(c) fair market value required.

Net Cash Proceeds in excess of $200,000,000 shall be applied to prepayment.
No consent required. No restrictions on use of first $200M.
"""

# Scenario 5: Multiple Tranches - Complex Capital Structure
COMPLEX_CAPITAL_STRUCTURE = """
CREDIT AGREEMENT
LEVERAGED BUYOUT TARGET
Dated: October 2024

CAPITAL STRUCTURE SUMMARY

Facility                          Amount            Maturity      Rate            Security              Guarantees
Super Senior RCF                  $75,000,000      Oct 2027      SOFR+300        First Priority        All Subs
First Lien Term Loan A            $400,000,000     Oct 2029      SOFR+450        First Priority        All Subs
First Lien Term Loan B            $600,000,000     Oct 2030      SOFR+500        First Priority        All Subs
Second Lien Term Loan             $300,000,000     Oct 2031      SOFR+850        Second Priority       All Subs
Senior Unsecured Notes            $200,000,000     Oct 2028      9.50% Fixed     No Collateral         Non-Guaranteed
Subordinated PIK Toggle Notes     $100,000,000     Oct 2032      12.00%/14.00%   No Collateral         Non-Guaranteed

Total Debt: $1,675,000,000
"""

# Scenario 6: Incremental Facilities - Priming Risk
INCREMENTAL_PRIMING_RISK = """
CREDIT AGREEMENT
SERTA-STYLE BORROWER
Dated: November 2024

Section 7.12. Incremental Facilities.

The Borrower may incur Incremental Debt:
(a) up to $300,000,000 (Free and Clear Basket);
(b) unlimited amounts if Secured Leverage Ratio ≤ 5.00:1.00;
(c) pari passu with or senior to existing First Lien;
(d) without consent of any existing Lender.

Required Lenders (>50%) may approve amendments to lien priority.
Minority lenders can be primed without consent.
"""

# Scenario 7: Moderate Risk - Balanced Structure
MODERATE_BALANCED_STRUCTURE = """
CREDIT AGREEMENT
MIDDLE MARKET COMPANY
Dated: December 2024

Facility                    Amount              Maturity        Rate
First Lien Term Loan        $250,000,000       Dec 2029        SOFR+400
Second Lien Notes           $100,000,000       Dec 2030        8.25% Fixed

"Consolidated EBITDA" means net income plus:
(a) interest, taxes, depreciation, amortization;
(b) non-cash charges up to $5,000,000 per year;
(c) restructuring charges not to exceed $10,000,000 in aggregate;
(d) one-time transaction costs.

Section 7.05. Asset Sales up to $50,000,000 per year.
75% of proceeds over $25,000,000 applied to prepayment.

Section 7.08. Investments in Unrestricted Subs up to $25,000,000.
No IP transfer permitted.
"""

# Scenario 8: No EBITDA Definition - Minimalist Document
NO_EBITDA_DEFINITION = """
CREDIT AGREEMENT
SIMPLE BORROWER LLC
Dated: February 2024

Facility: Term Loan $100,000,000

Section 7.05. No asset sales permitted without consent.
Section 7.08. No unrestricted subsidiaries permitted.
"""

# Scenario 9: Non-Cash Heavy EBITDA - Tech Company
TECH_NONCASH_HEAVY = """
CREDIT AGREEMENT
TECH STARTUP INC.
Dated: May 2024

"Consolidated EBITDA" means net income plus:
(a) interest, taxes, depreciation, amortization;
(b) stock-based compensation expense (substantial);
(c) non-cash losses on asset write-downs;
(d) non-cash impairment charges;
(e) extraordinary losses from discontinued operations.

Minimal cash adjustments, mostly non-cash.
"""

# Scenario 10: Dividend Recap - Affiliate Transaction Risk
DIVIDEND_RECAP_RISK = """
CREDIT AGREEMENT
PRIVATE EQUITY PORTFOLIO CO.
Dated: July 2024

Section 7.15. Affiliate Transactions and Dividends.

The Borrower may make Restricted Payments (dividends to Parent):
(a) up to $100,000,000 annually;
(b) plus 50% of cumulative Consolidated Net Income since closing;
(c) plus 100% of equity issuance proceeds;
(d) without lender consent if Total Leverage Ratio ≤ 4.50:1.00.

Classic PE dividend recapitalization structure.
"""

# Scenario 11: Covenant-Lite - Minimal Restrictions
COVENANT_LITE_STRUCTURE = """
CREDIT AGREEMENT
COVENANT-LITE BORROWER
Dated: August 2024

INCURRENCE COVENANTS ONLY (No Maintenance Covenants)

Section 7.05. Asset Sales: Up to greater of $200,000,000 and 20% of Total Assets.
No sweep. No consent. Ordinary course exemption.

Section 7.08. Unrestricted Subs: Up to greater of $150,000,000 and 15% of Total Assets.
IP transfer permitted. No consent.

Section 7.12. Incremental: Unlimited if ratio test met. No consent.

"Cov-lite" = minimal lender protections.
"""

# Scenario 12: Multi-Currency and Complex Guarantees
MULTI_CURRENCY_COMPLEX = """
CREDIT AGREEMENT
MULTINATIONAL CORPORATION
Dated: September 2024

CAPITAL STRUCTURE

Facility                      Amount              Currency    Security                    Guarantees
USD Term Loan                 $500,000,000       USD         First Priority Lien         US Subsidiaries Only
EUR Term Loan                 €200,000,000       EUR         First Priority Lien         EU Subsidiaries Only
GBP Revolving Facility        £50,000,000        GBP         First Priority Lien         UK Subsidiaries Only
Senior Unsecured Notes        $300,000,000       USD         No Collateral               Non-Guaranteed

Cross-currency, multi-jurisdiction guarantees, structural subordination risk.
"""


# Scenario metadata for reporting
SCENARIOS = [
    {
        "name": "Investment Grade Borrower",
        "content": INVESTMENT_GRADE_AGREEMENT,
        "doc_type": "Investment Grade",
        "expected_tranches": 2,
    },
    {
        "name": "Aggressive EBITDA Definition",
        "content": DISTRESSED_AGGRESSIVE_EBITDA,
        "doc_type": "Distressed / Covenant-Lite",
        "expected_tranches": 0,
    },
    {
        "name": "J.Crew Style Dropdown Risk",
        "content": HIGH_LME_RISK_JCREW,
        "doc_type": "Retail / High LME Risk",
        "expected_tranches": 0,
    },
    {
        "name": "Large Asset Sale Basket",
        "content": LARGE_ASSET_SALE_BASKET,
        "doc_type": "Manufacturing / Weak Sweep",
        "expected_tranches": 0,
    },
    {
        "name": "Complex Capital Structure",
        "content": COMPLEX_CAPITAL_STRUCTURE,
        "doc_type": "Leveraged Buyout",
        "expected_tranches": 6,
    },
    {
        "name": "Incremental Priming Risk",
        "content": INCREMENTAL_PRIMING_RISK,
        "doc_type": "Serta-Style Priming",
        "expected_tranches": 0,
    },
    {
        "name": "Moderate Balanced Structure",
        "content": MODERATE_BALANCED_STRUCTURE,
        "doc_type": "Middle Market",
        "expected_tranches": 2,
    },
    {
        "name": "No EBITDA Definition (Edge Case)",
        "content": NO_EBITDA_DEFINITION,
        "doc_type": "Minimalist Document",
        "expected_tranches": 0,
    },
    {
        "name": "Tech Company (Non-Cash Heavy)",
        "content": TECH_NONCASH_HEAVY,
        "doc_type": "Technology Startup",
        "expected_tranches": 0,
    },
    {
        "name": "Dividend Recapitalization",
        "content": DIVIDEND_RECAP_RISK,
        "doc_type": "PE Portfolio Company",
        "expected_tranches": 0,
    },
    {
        "name": "Covenant-Lite Structure",
        "content": COVENANT_LITE_STRUCTURE,
        "doc_type": "Covenant-Lite",
        "expected_tranches": 0,
    },
    {
        "name": "Multi-Currency Complex",
        "content": MULTI_CURRENCY_COMPLEX,
        "doc_type": "Multinational",
        "expected_tranches": 4,
    },
]

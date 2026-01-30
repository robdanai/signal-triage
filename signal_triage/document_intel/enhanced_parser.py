"""
Enhanced Document Parser: Forensic Table & Capital Structure Extraction
Senior Restructuring Analyst (Document Forensics)

This module implements a "Table-First" approach to extract:
1. Capital Structure tables (Debt Tranches: Seniority, Claim, Collateral)
2. Covenant definitions (EBITDA add-backs, baskets)
3. LME risk scoring (Asset Sale Baskets, Investment in Unrestricted Subs)

Every extracted value is cited to a page and section.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

# Import pdfplumber for table extraction; fallback to text extraction if unavailable
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from signal_triage.document_intel.schema import SignalLevel


@dataclass
class DebtTranche:
    """
    A single tranche in the capital structure.
    """
    tranche_name: str  # e.g., "First Lien Term Loan", "Second Lien Notes"
    seniority: str  # "Senior Secured", "Second Lien", "Unsecured", "Subordinated"
    claim_amount: str | None  # e.g., "$500,000,000", "€200M"
    collateral_type: str | None  # "First Priority Lien on All Assets", "No Collateral"
    guarantee_status: str | None  # "Guaranteed by Subsidiaries", "Non-Guaranteed"
    maturity_date: str | None  # e.g., "2028-12-31"
    interest_rate: str | None  # e.g., "L+500", "8.5%"
    page_number: int | None
    section_reference: str | None
    raw_table_row: dict[str, str] | None = None  # Original table data for audit

    def to_dict(self) -> dict[str, Any]:
        return {
            "tranche_name": self.tranche_name,
            "seniority": self.seniority,
            "claim_amount": self.claim_amount,
            "collateral_type": self.collateral_type,
            "guarantee_status": self.guarantee_status,
            "maturity_date": self.maturity_date,
            "interest_rate": self.interest_rate,
            "page_number": self.page_number,
            "section_reference": self.section_reference,
        }


@dataclass
class EBITDADefinition:
    """
    EBITDA definition with add-backs and normalization adjustments.
    """
    base_definition: str  # Core EBITDA definition text
    addbacks: list[dict[str, Any]] = field(default_factory=list)  # List of add-back items
    addback_risk_score: float = 0.0  # 0.0 (conservative) to 10.0 (aggressive)
    synergies_flagged: bool = False
    future_cost_savings_flagged: bool = False
    non_cash_gains_flagged: bool = False
    page_number: int | None = None
    section_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_definition": self.base_definition,
            "addbacks": self.addbacks,
            "addback_risk_score": self.addback_risk_score,
            "synergies_flagged": self.synergies_flagged,
            "future_cost_savings_flagged": self.future_cost_savings_flagged,
            "non_cash_gains_flagged": self.non_cash_gains_flagged,
            "page_number": self.page_number,
            "section_reference": self.section_reference,
        }


@dataclass
class LMELeakageRisk:
    """
    Liability Management Exercise (LME) leakage risk assessment.
    """
    category: str  # "Asset Sale Basket", "Investment in Unrestricted Sub", etc.
    basket_size: str | None  # Dollar amount or formula
    leakage_risk_score: float  # 0.0 (low) to 10.0 (high)
    risk_factors: list[str] = field(default_factory=list)
    page_number: int | None = None
    section_reference: str | None = None
    evidence_snippet: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "basket_size": self.basket_size,
            "leakage_risk_score": self.leakage_risk_score,
            "risk_factors": self.risk_factors,
            "page_number": self.page_number,
            "section_reference": self.section_reference,
            "evidence_snippet": self.evidence_snippet,
        }


@dataclass
class EnhancedExtractionResult:
    """
    Complete forensic extraction result with tables and covenant data.
    """
    source_path: str | None = None
    debt_tranches: list[DebtTranche] = field(default_factory=list)
    ebitda_definition: EBITDADefinition | None = None
    lme_risks: list[LMELeakageRisk] = field(default_factory=list)
    raw_tables: list[dict[str, Any]] = field(default_factory=list)  # All extracted tables
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "debt_tranches": [t.to_dict() for t in self.debt_tranches],
            "ebitda_definition": self.ebitda_definition.to_dict() if self.ebitda_definition else None,
            "lme_risks": [r.to_dict() for r in self.lme_risks],
            "raw_tables": self.raw_tables,
            "metadata": self.metadata,
        }


# ============================================================================
# TABLE EXTRACTION & FORENSICS
# ============================================================================

def extract_tables_from_pdf(pdf_path: str | Path) -> list[dict[str, Any]]:
    """
    Extract all tables from PDF using pdfplumber.
    
    Returns:
        List of tables, each table is dict with:
        - page: page number
        - table: list of lists (rows x columns)
        - bbox: bounding box coordinates
    """
    if not PDFPLUMBER_AVAILABLE:
        return []
    
    tables = []
    pdf_path = Path(pdf_path)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract tables from this page
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    if table and len(table) > 1:  # At least header + 1 row
                        tables.append({
                            "page": page_num,
                            "table_index": table_idx,
                            "table": table,
                            "bbox": None,  # pdfplumber doesn't always provide bbox
                        })
    except Exception as e:
        # Log error but don't crash; fall back to text extraction
        print(f"Warning: pdfplumber extraction failed for {pdf_path}: {e}")
    
    return tables


def identify_capital_structure_table(
    tables: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Identify the capital structure table from extracted tables.
    
    Look for tables with headers like:
    - "Facility", "Tranche", "Debt"
    - "Amount", "Outstanding", "Principal"
    - "Maturity", "Rate", "Interest"
    - "Security", "Collateral", "Priority"
    """
    cap_structure_keywords = [
        "facility", "tranche", "debt", "loan", "notes",
        "amount", "outstanding", "principal", "claim",
        "maturity", "rate", "interest", "coupon",
        "security", "collateral", "priority", "lien", "senior",
    ]
    
    best_match = None
    best_score = 0
    
    for table_dict in tables:
        table = table_dict["table"]
        if not table or len(table) < 2:
            continue
        
        # Check header row (first row)
        header_row = table[0]
        if not header_row:
            continue
        
        # Score based on keyword matches in header
        score = 0
        header_text = " ".join([str(cell).lower() for cell in header_row if cell])
        
        for keyword in cap_structure_keywords:
            if keyword in header_text:
                score += 1
        
        # Bonus for multi-column tables (capital structure tables are typically wide)
        if len(header_row) >= 4:
            score += 2
        
        if score > best_score:
            best_score = score
            best_match = table_dict
    
    return best_match if best_score >= 3 else None


def parse_capital_structure_table(
    table_dict: dict[str, Any]
) -> list[DebtTranche]:
    """
    Parse capital structure table into DebtTranche objects.
    
    Automatically distinguishes between:
    - Senior Secured (1st Lien)
    - Second Lien
    - Unsecured
    - Subordinated
    
    Based on:
    - Explicit seniority column
    - Tranche name (e.g., "First Lien", "Second Lien")
    - Guarantee language
    - Collateral description
    """
    table = table_dict["table"]
    page_num = table_dict["page"]
    
    if not table or len(table) < 2:
        return []
    
    # Parse header row to map columns
    header_row = [str(cell).lower().strip() if cell else "" for cell in table[0]]
    
    # Find column indices
    col_map = {}
    for idx, header in enumerate(header_row):
        if any(kw in header for kw in ["facility", "tranche", "debt", "loan", "description"]):
            col_map["name"] = idx
        elif any(kw in header for kw in ["amount", "outstanding", "principal", "claim"]):
            col_map["amount"] = idx
        elif any(kw in header for kw in ["maturity", "due"]):
            col_map["maturity"] = idx
        elif any(kw in header for kw in ["rate", "interest", "coupon"]):
            col_map["rate"] = idx
        elif any(kw in header for kw in ["security", "collateral", "priority"]):
            col_map["collateral"] = idx
        elif any(kw in header for kw in ["guarantee", "guarantor"]):
            col_map["guarantee"] = idx
        elif any(kw in header for kw in ["seniority", "rank"]):
            col_map["seniority"] = idx
    
    # Parse data rows
    tranches = []
    for row_idx, row in enumerate(table[1:], start=1):
        if not row or not any(row):
            continue
        
        # Extract fields
        name = str(row[col_map["name"]]) if "name" in col_map and len(row) > col_map["name"] else f"Tranche {row_idx}"
        amount = str(row[col_map["amount"]]) if "amount" in col_map and len(row) > col_map["amount"] else None
        maturity = str(row[col_map["maturity"]]) if "maturity" in col_map and len(row) > col_map["maturity"] else None
        rate = str(row[col_map["rate"]]) if "rate" in col_map and len(row) > col_map["rate"] else None
        collateral = str(row[col_map["collateral"]]) if "collateral" in col_map and len(row) > col_map["collateral"] else None
        guarantee = str(row[col_map["guarantee"]]) if "guarantee" in col_map and len(row) > col_map["guarantee"] else None
        seniority_explicit = str(row[col_map["seniority"]]) if "seniority" in col_map and len(row) > col_map["seniority"] else None
        
        # Clean None values
        if amount == "None":
            amount = None
        if maturity == "None":
            maturity = None
        if rate == "None":
            rate = None
        if collateral == "None":
            collateral = None
        if guarantee == "None":
            guarantee = None
        if seniority_explicit == "None":
            seniority_explicit = None
        
        # Infer seniority
        seniority = _infer_seniority(name, seniority_explicit, collateral, guarantee)
        
        # Build raw table row for audit
        raw_row = {header_row[i]: str(row[i]) if i < len(row) else None for i in range(len(header_row))}
        
        tranche = DebtTranche(
            tranche_name=name,
            seniority=seniority,
            claim_amount=amount,
            collateral_type=collateral,
            guarantee_status=guarantee,
            maturity_date=maturity,
            interest_rate=rate,
            page_number=page_num,
            section_reference=None,  # Will be filled by section detection
            raw_table_row=raw_row,
        )
        tranches.append(tranche)
    
    return tranches


def _infer_seniority(
    name: str,
    seniority_explicit: str | None,
    collateral: str | None,
    guarantee: str | None
) -> str:
    """
    Infer seniority based on tranche name, collateral, and guarantee language.
    
    Rules:
    - "First Lien" / "Senior Secured" / "First Priority" -> "Senior Secured"
    - "Second Lien" / "Junior Secured" -> "Second Lien"
    - "Unsecured" / "Senior Unsecured" / "No Collateral" -> "Unsecured"
    - "Subordinated" / "Junior" -> "Subordinated"
    """
    if seniority_explicit:
        return seniority_explicit
    
    name_lower = name.lower()
    collateral_lower = (collateral or "").lower()
    guarantee_lower = (guarantee or "").lower()
    
    combined = f"{name_lower} {collateral_lower} {guarantee_lower}"
    
    # Check for explicit seniority keywords
    if any(kw in combined for kw in ["first lien", "1st lien", "senior secured", "first priority"]):
        return "Senior Secured"
    elif any(kw in combined for kw in ["second lien", "2nd lien", "junior secured"]):
        return "Second Lien"
    elif any(kw in combined for kw in ["subordinated", "junior unsecured"]):
        return "Subordinated"
    elif any(kw in combined for kw in ["unsecured", "senior unsecured", "no collateral", "non-secured"]):
        return "Unsecured"
    
    # Default: if collateral mentioned, assume Senior Secured; else Unsecured
    if any(kw in combined for kw in ["collateral", "secured", "lien", "security interest"]):
        return "Senior Secured"
    else:
        return "Unsecured"


# ============================================================================
# EBITDA NORMALIZER
# ============================================================================

def extract_ebitda_definition(text: str, page_by_char: list[tuple[int, int]] | None = None) -> EBITDADefinition | None:
    """
    Extract EBITDA definition and analyze add-backs for forensic red flags.
    
    Flags:
    - Synergies (run-rate synergies, anticipated synergies)
    - Future cost savings (anticipated savings, pro-forma adjustments)
    - Non-cash gains (stock-based comp, non-recurring items)
    
    Returns:
        EBITDADefinition with risk score (0.0 = conservative, 10.0 = aggressive)
    """
    # Find EBITDA definition section
    ebitda_match = re.search(
        r'"?(?:Consolidated\s+)?EBITDA"?\s+means[^.]{0,2000}',
        text,
        re.IGNORECASE | re.DOTALL
    )
    
    if not ebitda_match:
        return None
    
    definition_text = ebitda_match.group(0)
    definition_start = ebitda_match.start()
    
    # Extract longer definition if needed (up to next section or 5000 chars)
    end_pos = min(definition_start + 5000, len(text))
    for pattern in [r'\n\s*"[A-Z]', r'\nSection\s+\d+\.\d+', r'\nArticle\s+[IVXLC]+']:
        m = re.search(pattern, text[definition_start:end_pos])
        if m:
            end_pos = definition_start + m.start()
            break
    
    definition_full = text[definition_start:end_pos]
    
    # Find page number
    page_num = _get_page_for_offset(definition_start, page_by_char)
    
    # Extract add-backs
    addbacks = []
    risk_score = 0.0
    synergies_flagged = False
    future_cost_savings_flagged = False
    non_cash_gains_flagged = False
    
    # Pattern: look for "plus" or "add back" clauses
    addback_patterns = [
        (r"run[- ]?rate\s+(?:synergies|savings)", "Run-Rate Synergies", 3.0, "synergies"),
        (r"anticipated\s+(?:cost\s+)?savings", "Anticipated Cost Savings", 2.5, "future_savings"),
        (r"pro[- ]?forma\s+(?:EBITDA|adjustments?)", "Pro-Forma Adjustments", 2.0, "future_savings"),
        (r"synergies", "Synergies", 2.0, "synergies"),
        (r"one[- ]?time\s+(?:charges?|expenses?)", "One-Time Charges", 1.0, "non_cash"),
        (r"restructuring\s+charges?", "Restructuring Charges", 1.5, "non_cash"),
        (r"stock[- ]?based\s+compensation", "Stock-Based Compensation", 0.5, "non_cash"),
        (r"non[- ]?recurring\s+(?:charges?|expenses?)", "Non-Recurring Charges", 1.0, "non_cash"),
        (r"non[- ]?cash\s+(?:charges?|expenses?)", "Non-Cash Charges", 0.5, "non_cash"),
        (r"extraordinary\s+(?:charges?|losses?)", "Extraordinary Items", 1.5, "non_cash"),
    ]
    
    for pattern, label, risk_weight, flag_type in addback_patterns:
        matches = list(re.finditer(pattern, definition_full, re.IGNORECASE))
        if matches:
            for m in matches:
                # Extract context around match
                start = max(0, m.start() - 50)
                end = min(len(definition_full), m.end() + 100)
                context = definition_full[start:end].replace("\n", " ").strip()
                
                addbacks.append({
                    "type": label,
                    "context": context,
                    "risk_weight": risk_weight,
                })
                risk_score += risk_weight
                
                if flag_type == "synergies":
                    synergies_flagged = True
                elif flag_type == "future_savings":
                    future_cost_savings_flagged = True
                elif flag_type == "non_cash":
                    non_cash_gains_flagged = True
    
    # Cap risk score at 10.0
    risk_score = min(risk_score, 10.0)
    
    return EBITDADefinition(
        base_definition=definition_text[:500],  # Truncate for storage
        addbacks=addbacks,
        addback_risk_score=risk_score,
        synergies_flagged=synergies_flagged,
        future_cost_savings_flagged=future_cost_savings_flagged,
        non_cash_gains_flagged=non_cash_gains_flagged,
        page_number=page_num,
        section_reference=None,
    )


def _get_page_for_offset(char_offset: int, page_by_char: list[tuple[int, int]] | None) -> int | None:
    """Get page number for character offset."""
    if not page_by_char:
        return None
    
    for start_char, page_num in reversed(page_by_char):
        if char_offset >= start_char:
            return page_num
    
    return page_by_char[0][1] if page_by_char else None


# ============================================================================
# LME LEAKAGE RISK SCORING
# ============================================================================

def score_lme_leakage_risk(text: str, page_by_char: list[tuple[int, int]] | None = None) -> list[LMELeakageRisk]:
    """
    Scan for Asset Sale Baskets and Investment in Unrestricted Subsidiary language.
    Score leakage risk based on dollar size and permissiveness.
    
    Risk Scoring:
    - 0-2: Low risk (small baskets, strong sweep requirements)
    - 3-5: Medium risk (moderate baskets, partial sweeps)
    - 6-8: High risk (large baskets, weak sweeps)
    - 9-10: Critical risk (uncapped baskets, no sweeps, unlimited unrestricted sub transfers)
    """
    risks = []
    
    # Asset Sale Basket patterns
    asset_sale_patterns = [
        r"asset\s+sale\s+basket",
        r"disposition\s+of\s+(?:any\s+)?(?:assets?|property|collateral)",
        r"sale\s+of\s+(?:assets?|property|collateral)",
        r"permitted\s+dispositions?",
    ]
    
    for pattern in asset_sale_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Extract context (500 chars)
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 300)
            context = text[start:end]
            
            # Extract dollar limit
            basket_size = _extract_dollar_or_formula(context)
            
            # Score risk
            risk_score = _score_asset_sale_basket(context, basket_size)
            
            # Risk factors
            risk_factors = _identify_asset_sale_risk_factors(context)
            
            page_num = _get_page_for_offset(match.start(), page_by_char)
            
            risks.append(LMELeakageRisk(
                category="Asset Sale Basket",
                basket_size=basket_size,
                leakage_risk_score=risk_score,
                risk_factors=risk_factors,
                page_number=page_num,
                section_reference=None,
                evidence_snippet=context[:300],
            ))
    
    # Unrestricted Subsidiary patterns
    unrestricted_patterns = [
        r"unrestricted\s+subsidiary",
        r"investment\s+in\s+(?:an?\s+)?unrestricted",
        r"designat(?:e|ion)\s+as\s+unrestricted",
        r"transfer\s+(?:of\s+)?(?:assets?|property|IP|intellectual\s+property)\s+to\s+(?:an?\s+)?(?:unrestricted|subsidiary)",
    ]
    
    for pattern in unrestricted_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 300)
            context = text[start:end]
            
            basket_size = _extract_dollar_or_formula(context)
            risk_score = _score_unrestricted_sub_basket(context, basket_size)
            risk_factors = _identify_unrestricted_sub_risk_factors(context)
            
            page_num = _get_page_for_offset(match.start(), page_by_char)
            
            risks.append(LMELeakageRisk(
                category="Investment in Unrestricted Subsidiary",
                basket_size=basket_size,
                leakage_risk_score=risk_score,
                risk_factors=risk_factors,
                page_number=page_num,
                section_reference=None,
                evidence_snippet=context[:300],
            ))
    
    return risks


def _extract_dollar_or_formula(text: str) -> str | None:
    """Extract dollar amount or formula (e.g., '$50M', '10% of EBITDA')."""
    # Try dollar amount
    m = re.search(r"\$[\d,]+(?:\.\d+)?\s*(?:million|MM|M|billion|B)?", text, re.IGNORECASE)
    if m:
        return m.group(0).strip()
    
    # Try percentage formula
    m = re.search(r"\d+(?:\.\d+)?\s*%\s+of\s+(?:Consolidated\s+)?(?:EBITDA|Total\s+Assets|Net\s+Worth)", text, re.IGNORECASE)
    if m:
        return m.group(0).strip()
    
    # Try "greater of" formula
    m = re.search(r"greater\s+of\s+\$[\d,]+[^,.]+ and \d+%[^,.]+", text, re.IGNORECASE)
    if m:
        return m.group(0).strip()
    
    return None


def _score_asset_sale_basket(context: str, basket_size: str | None) -> float:
    """
    Score asset sale basket risk (0.0 - 10.0).
    
    High risk factors:
    - Large basket size (>$100M = +3.0, >$50M = +2.0, >$25M = +1.0)
    - No sweep requirement (+2.0)
    - "Without lender consent" (+2.0)
    - "Ordinary course" exemption (+1.0)
    """
    score = 0.0
    context_lower = context.lower()
    
    # Basket size risk
    if basket_size:
        if any(kw in basket_size.lower() for kw in ["billion", "b"]):
            score += 5.0
        elif re.search(r"\$\s*[5-9]\d\d", basket_size) or re.search(r"\$\s*\d{4,}", basket_size):
            # >$500M
            score += 4.0
        elif re.search(r"\$\s*[1-4]\d\d", basket_size):
            # $100M-$499M
            score += 3.0
        elif re.search(r"\$\s*[5-9]\d", basket_size):
            # $50M-$99M
            score += 2.0
        else:
            score += 1.0
    else:
        # No explicit limit = potentially uncapped
        if "unlimited" in context_lower or "without limit" in context_lower:
            score += 5.0
        else:
            score += 1.0
    
    # Sweep requirement (lack of = higher risk)
    if not any(kw in context_lower for kw in ["mandatory prepay", "sweep", "100% of proceeds", "net cash proceeds"]):
        score += 2.0
    
    # Consent bypass
    if any(kw in context_lower for kw in ["without consent", "no consent", "without lender consent"]):
        score += 2.0
    
    # Ordinary course exemption
    if "ordinary course" in context_lower:
        score += 1.0
    
    return min(score, 10.0)


def _identify_asset_sale_risk_factors(context: str) -> list[str]:
    """Identify specific risk factors for asset sale basket."""
    factors = []
    context_lower = context.lower()
    
    if any(kw in context_lower for kw in ["without consent", "no consent"]):
        factors.append("No lender consent required")
    
    if not any(kw in context_lower for kw in ["mandatory prepay", "sweep", "100% of proceeds"]):
        factors.append("No mandatory prepayment/sweep")
    
    if "ordinary course" in context_lower:
        factors.append("Ordinary course exemption")
    
    if any(kw in context_lower for kw in ["unlimited", "without limit"]):
        factors.append("Uncapped basket")
    
    if "fair market value" in context_lower or "fmv" in context_lower:
        factors.append("Fair market value sale (valuation risk)")
    
    return factors


def _score_unrestricted_sub_basket(context: str, basket_size: str | None) -> float:
    """
    Score unrestricted subsidiary basket risk (0.0 - 10.0).
    
    High risk factors:
    - Large basket (>$50M = +3.0)
    - IP/assets can be transferred (+3.0)
    - "Without lender consent" (+2.0)
    - "J.Crew" / "dropdown" language (+2.0)
    """
    score = 0.0
    context_lower = context.lower()
    
    # Basket size
    if basket_size:
        if any(kw in basket_size.lower() for kw in ["billion", "b"]):
            score += 5.0
        elif re.search(r"\$\s*[1-9]\d\d", basket_size):
            # >$100M
            score += 4.0
        elif re.search(r"\$\s*[5-9]\d", basket_size):
            # $50M-$99M
            score += 3.0
        else:
            score += 2.0
    else:
        if "unlimited" in context_lower or "without limit" in context_lower:
            score += 5.0
        else:
            score += 1.0
    
    # IP/asset transfer
    if any(kw in context_lower for kw in ["intellectual property", "ip", "assets", "property", "transfer"]):
        score += 3.0
    
    # Consent bypass
    if any(kw in context_lower for kw in ["without consent", "no consent", "without lender consent"]):
        score += 2.0
    
    # J.Crew / dropdown precedent
    if any(kw in context_lower for kw in ["j.crew", "j crew", "dropdown", "chewy"]):
        score += 2.0
    
    return min(score, 10.0)


def _identify_unrestricted_sub_risk_factors(context: str) -> list[str]:
    """Identify specific risk factors for unrestricted subsidiary basket."""
    factors = []
    context_lower = context.lower()
    
    if any(kw in context_lower for kw in ["intellectual property", "ip"]):
        factors.append("IP transfer permitted")
    
    if any(kw in context_lower for kw in ["without consent", "no consent"]):
        factors.append("No lender consent required")
    
    if any(kw in context_lower for kw in ["j.crew", "j crew", "dropdown", "chewy"]):
        factors.append("J.Crew/Chewy precedent language")
    
    if "designation" in context_lower:
        factors.append("Designation as unrestricted permitted")
    
    if any(kw in context_lower for kw in ["unlimited", "without limit"]):
        factors.append("Uncapped basket")
    
    return factors


# ============================================================================
# MAIN EXTRACTION ORCHESTRATOR
# ============================================================================

def extract_forensic_data(
    path: str | Path,
    text: str | None = None,
    page_by_char: list[tuple[int, int]] | None = None,
) -> EnhancedExtractionResult:
    """
    Main entry point for enhanced forensic extraction.
    
    Performs:
    1. Table extraction (capital structure)
    2. EBITDA definition parsing and add-back analysis
    3. LME risk scoring (asset sale baskets, unrestricted subs)
    
    Args:
        path: Path to PDF or TXT file
        text: Optional pre-extracted text (for testing)
        page_by_char: Optional page mapping (char_offset -> page_num)
    
    Returns:
        EnhancedExtractionResult with debt tranches, EBITDA definition, LME risks
    """
    path = Path(path) if path else None
    source_path = str(path.resolve()) if path else None
    
    # Extract tables from PDF
    raw_tables = []
    debt_tranches = []
    
    if path and path.suffix.lower() == ".pdf" and PDFPLUMBER_AVAILABLE:
        raw_tables = extract_tables_from_pdf(path)
        
        # Identify capital structure table
        cap_table = identify_capital_structure_table(raw_tables)
        if cap_table:
            debt_tranches = parse_capital_structure_table(cap_table)
    
    # Extract text if not provided
    if text is None and path:
        if path.suffix.lower() == ".pdf":
            # Use pdfplumber to extract text
            if PDFPLUMBER_AVAILABLE:
                try:
                    import pdfplumber
                    with pdfplumber.open(path) as pdf:
                        text_parts = []
                        for page in pdf.pages:
                            text_parts.append(page.extract_text() or "")
                        text = "\n".join(text_parts)
                except Exception as e:
                    text = ""
            else:
                text = ""
        else:
            # Read text file
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
    
    text = text or ""
    
    # Extract EBITDA definition
    ebitda_def = extract_ebitda_definition(text, page_by_char)
    
    # Score LME risks
    lme_risks = score_lme_leakage_risk(text, page_by_char)
    
    # Metadata
    metadata = {
        "total_tables_extracted": len(raw_tables),
        "capital_structure_table_found": len(debt_tranches) > 0,
        "ebitda_definition_found": ebitda_def is not None,
        "lme_risks_identified": len(lme_risks),
        "pdfplumber_available": PDFPLUMBER_AVAILABLE,
        "pytesseract_available": PYTESSERACT_AVAILABLE,
    }
    
    return EnhancedExtractionResult(
        source_path=source_path,
        debt_tranches=debt_tranches,
        ebitda_definition=ebitda_def,
        lme_risks=lme_risks,
        raw_tables=[{"page": t["page"], "row_count": len(t["table"])} for t in raw_tables],
        metadata=metadata,
    )

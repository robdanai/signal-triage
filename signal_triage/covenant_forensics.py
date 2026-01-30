"""
Covenant Headroom & EBITDA Forensics.

Calculates distance to maintenance covenant breach; strips aggressive add-backs
to find "Normalized EBITDA"; flags when headroom < 15% (critical distress).

Institutional Restructuring Desk: This is the "cushion" analysis that determines
if the borrower is genuinely healthy or propped up by accounting gimmicks.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

QUANT = Decimal("0.01")


def _to_decimal(x: float | int | Decimal | None) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


# Add-back classifications by aggressiveness
ADDBACK_AGGRESSIVENESS = {
    "one_time_charges": 0.8,  # 80% credible
    "restructuring_charges": 0.8,
    "stock_comp": 0.9,
    "pro_forma_adjustments": 0.5,  # 50% credible
    "run_rate_synergies": 0.3,  # 30% credible (aggressive)
    "anticipated_savings": 0.2,  # 20% credible (highly aggressive)
    "future_cost_cuts": 0.1,  # 10% credible (toxic)
}


def normalize_ebitda(
    reported_ebitda: float | Decimal,
    addbacks: dict[str, float | Decimal],
    aggressiveness_haircut: bool = True,
) -> dict[str, Any]:
    """
    Strip add-backs to find normalized EBITDA.

    Args:
        reported_ebitda: Reported/adjusted EBITDA from issuer.
        addbacks: Dict of {category: amount}. Categories: one_time_charges,
            restructuring_charges, stock_comp, pro_forma_adjustments,
            run_rate_synergies, anticipated_savings, future_cost_cuts.
        aggressiveness_haircut: If True, apply credibility haircut to aggressive add-backs.

    Returns:
        Dict with normalized_ebitda, total_addbacks, aggressive_addbacks (run-rate, anticipated),
        and haircut_applied.
    """
    ebitda_d = _to_decimal(reported_ebitda)
    total_addbacks = Decimal("0")
    aggressive_addbacks = Decimal("0")
    haircut_amount = Decimal("0")

    aggressive_categories = {"run_rate_synergies", "anticipated_savings", "future_cost_cuts"}

    for category, amount in addbacks.items():
        amt_d = _to_decimal(amount)
        total_addbacks += amt_d

        if category in aggressive_categories:
            aggressive_addbacks += amt_d

        # Apply haircut if requested and category has credibility < 100%
        if aggressiveness_haircut and category in ADDBACK_AGGRESSIVENESS:
            credibility = Decimal(str(ADDBACK_AGGRESSIVENESS[category]))
            # Haircut = amount * (1 - credibility)
            haircut = amt_d * (Decimal("1") - credibility)
            haircut_amount += haircut

    # Normalized EBITDA = Reported - haircut
    normalized = ebitda_d - haircut_amount

    return {
        "reported_ebitda": ebitda_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "total_addbacks": total_addbacks.quantize(QUANT, rounding=ROUND_HALF_UP),
        "aggressive_addbacks": aggressive_addbacks.quantize(QUANT, rounding=ROUND_HALF_UP),
        "haircut_applied": haircut_amount.quantize(QUANT, rounding=ROUND_HALF_UP),
        "normalized_ebitda": normalized.quantize(QUANT, rounding=ROUND_HALF_UP),
    }


def calculate_leverage_headroom(
    normalized_ebitda: float | Decimal,
    total_debt: float | Decimal,
    leverage_covenant: float | Decimal,
) -> dict[str, Any]:
    """
    Calculate leverage ratio and headroom to covenant breach.

    Args:
        normalized_ebitda: Normalized EBITDA (after stripping add-backs).
        total_debt: Total Debt (or First Lien Debt for First Lien Leverage).
        leverage_covenant: Maximum leverage ratio (e.g. 6.0x means debt/EBITDA <= 6.0).

    Returns:
        Dict with actual_leverage, covenant_leverage, headroom_pct, critical_distress.
    """
    ebitda_d = _to_decimal(normalized_ebitda)
    debt_d = _to_decimal(total_debt)
    covenant_d = _to_decimal(leverage_covenant)

    if ebitda_d <= 0:
        # EBITDA zero or negative: infinite leverage, always breach
        return {
            "actual_leverage": "N/A (EBITDA <= 0)",
            "covenant_leverage": covenant_d.quantize(QUANT, rounding=ROUND_HALF_UP),
            "headroom_pct": Decimal("0.00"),
            "critical_distress": True,
            "note": "EBITDA is zero or negative; leverage covenant breached.",
        }

    actual_leverage = debt_d / ebitda_d

    # Headroom: (covenant - actual) / covenant
    # If actual = 5.5x and covenant = 6.0x, headroom = (6.0 - 5.5) / 6.0 = 8.3%
    if covenant_d > 0:
        headroom = (covenant_d - actual_leverage) / covenant_d
    else:
        headroom = Decimal("0")

    headroom_pct = (headroom * Decimal("100")).quantize(QUANT, rounding=ROUND_HALF_UP)

    # Critical distress if headroom < 15%
    critical_distress = headroom < Decimal("0.15")

    return {
        "actual_leverage": actual_leverage.quantize(QUANT, rounding=ROUND_HALF_UP),
        "covenant_leverage": covenant_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "headroom_pct": headroom_pct,
        "critical_distress": critical_distress,
        "note": "Critical distress flag if headroom < 15%" if critical_distress else None,
    }


def calculate_fccr_headroom(
    normalized_ebitda: float | Decimal,
    cash_interest: float | Decimal,
    capex: float | Decimal,
    fccr_covenant: float | Decimal,
) -> dict[str, Any]:
    """
    Calculate Fixed Charge Coverage Ratio (FCCR) and headroom.

    FCCR = (EBITDA - CapEx) / Cash Interest

    Args:
        normalized_ebitda: Normalized EBITDA.
        cash_interest: Cash interest expense.
        capex: Capital expenditures (maintenance CapEx for covenant purposes).
        fccr_covenant: Minimum FCCR (e.g. 1.1x means FCCR >= 1.1).

    Returns:
        Dict with actual_fccr, covenant_fccr, headroom_pct, critical_distress.
    """
    ebitda_d = _to_decimal(normalized_ebitda)
    interest_d = _to_decimal(cash_interest)
    capex_d = _to_decimal(capex)
    covenant_d = _to_decimal(fccr_covenant)

    numerator = ebitda_d - capex_d

    if interest_d <= 0:
        # No interest expense: infinite FCCR (covenant always met)
        return {
            "actual_fccr": "N/A (no cash interest)",
            "covenant_fccr": covenant_d.quantize(QUANT, rounding=ROUND_HALF_UP),
            "headroom_pct": Decimal("100.00"),
            "critical_distress": False,
            "note": "No cash interest expense; FCCR covenant not applicable.",
        }

    actual_fccr = numerator / interest_d

    # Headroom: (actual - covenant) / covenant
    # If actual = 1.2x and covenant = 1.1x, headroom = (1.2 - 1.1) / 1.1 = 9.1%
    if covenant_d > 0:
        headroom = (actual_fccr - covenant_d) / covenant_d
    else:
        headroom = Decimal("0")

    headroom_pct = (headroom * Decimal("100")).quantize(QUANT, rounding=ROUND_HALF_UP)

    # Critical distress if headroom < 15%
    critical_distress = headroom < Decimal("0.15")

    return {
        "actual_fccr": actual_fccr.quantize(QUANT, rounding=ROUND_HALF_UP),
        "covenant_fccr": covenant_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "headroom_pct": headroom_pct,
        "critical_distress": critical_distress,
        "note": "Critical distress flag if headroom < 15%" if critical_distress else None,
    }


def calculate_headroom(
    reported_ebitda: float | Decimal,
    addbacks: dict[str, float | Decimal],
    total_debt: float | Decimal,
    leverage_covenant: float | Decimal,
    cash_interest: Optional[float | Decimal] = None,
    capex: Optional[float | Decimal] = None,
    fccr_covenant: Optional[float | Decimal] = None,
    aggressiveness_haircut: bool = True,
) -> dict[str, Any]:
    """
    Full covenant headroom analysis: normalize EBITDA, calculate leverage and FCCR headroom.

    Args:
        reported_ebitda: Reported/adjusted EBITDA from issuer.
        addbacks: Dict of {category: amount}.
        total_debt: Total Debt (or First Lien Debt for First Lien Leverage).
        leverage_covenant: Maximum leverage ratio.
        cash_interest: Cash interest expense (optional, for FCCR).
        capex: Capital expenditures (optional, for FCCR).
        fccr_covenant: Minimum FCCR (optional).
        aggressiveness_haircut: Apply credibility haircut to aggressive add-backs.

    Returns:
        Dict with normalized_ebitda_analysis, leverage_analysis, fccr_analysis (if applicable),
        overall_critical_distress.
    """
    # Step 1: Normalize EBITDA
    norm = normalize_ebitda(reported_ebitda, addbacks, aggressiveness_haircut)

    # Step 2: Leverage headroom
    leverage = calculate_leverage_headroom(
        norm["normalized_ebitda"], total_debt, leverage_covenant
    )

    # Step 3: FCCR headroom (if inputs provided)
    fccr = None
    if cash_interest is not None and capex is not None and fccr_covenant is not None:
        fccr = calculate_fccr_headroom(
            norm["normalized_ebitda"], cash_interest, capex, fccr_covenant
        )

    # Overall critical distress: ANY covenant in critical zone
    overall_critical = leverage.get("critical_distress", False)
    if fccr and fccr.get("critical_distress", False):
        overall_critical = True

    return {
        "normalized_ebitda_analysis": norm,
        "leverage_analysis": leverage,
        "fccr_analysis": fccr,
        "overall_critical_distress": overall_critical,
    }

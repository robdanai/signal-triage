"""
Chapter 11 Feasibility & Adequate Protection Modeling.

Models Going Concern vs Liquidation value; calculates adequate protection requirements
for secured lenders; assesses feasibility of reorganization vs liquidation.

Institutional Restructuring Desk: This is the "can this company reorganize?" analysis
that determines whether Ch. 11 is viable or if liquidation (Ch. 7) is inevitable.
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


# Liquidation haircuts (typical distressed scenarios)
LIQUIDATION_ORDERLY_HAIRCUT = Decimal("0.60")  # Orderly liquidation: 60% of GC value
LIQUIDATION_FORCED_HAIRCUT = Decimal("0.40")   # Forced liquidation: 40% of GC value
INTANGIBLE_LIQUIDATION_HAIRCUT = Decimal("0.10")  # Intangibles (IP, goodwill): 10% in liquidation


def calculate_liquidation_value(
    going_concern_ev: float | Decimal,
    tangible_asset_pct: float | Decimal = 0.5,  # % of EV that is tangible
    orderly: bool = True,
) -> dict[str, Any]:
    """
    Estimate liquidation value (orderly or forced) from going concern EV.

    Args:
        going_concern_ev: Going concern enterprise value.
        tangible_asset_pct: % of EV attributable to tangible assets (PP&E, inventory, AR);
            rest is intangible (IP, goodwill, brand). Default 50%.
        orderly: If True, orderly liquidation (more time, better recovery); if False, forced.

    Returns:
        Dict with going_concern_ev, tangible_ev, intangible_ev, liquidation_value,
        tangible_recovery_pct, intangible_recovery_pct, scenario ("orderly" / "forced").
    """
    gc_ev_d = _to_decimal(going_concern_ev)
    tangible_pct_d = _to_decimal(tangible_asset_pct)
    if tangible_pct_d > Decimal("1"):
        tangible_pct_d = Decimal("1")
    if tangible_pct_d < Decimal("0"):
        tangible_pct_d = Decimal("0")

    tangible_ev = gc_ev_d * tangible_pct_d
    intangible_ev = gc_ev_d - tangible_ev

    # Apply haircuts
    haircut = LIQUIDATION_ORDERLY_HAIRCUT if orderly else LIQUIDATION_FORCED_HAIRCUT
    tangible_liq_value = tangible_ev * haircut
    intangible_liq_value = intangible_ev * INTANGIBLE_LIQUIDATION_HAIRCUT

    liquidation_value = tangible_liq_value + intangible_liq_value

    return {
        "going_concern_ev": gc_ev_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "tangible_ev": tangible_ev.quantize(QUANT, rounding=ROUND_HALF_UP),
        "intangible_ev": intangible_ev.quantize(QUANT, rounding=ROUND_HALF_UP),
        "liquidation_value": liquidation_value.quantize(QUANT, rounding=ROUND_HALF_UP),
        "tangible_recovery_pct": (haircut * Decimal("100")).quantize(QUANT, rounding=ROUND_HALF_UP),
        "intangible_recovery_pct": (INTANGIBLE_LIQUIDATION_HAIRCUT * Decimal("100")).quantize(QUANT, rounding=ROUND_HALF_UP),
        "scenario": "orderly" if orderly else "forced",
    }


def calculate_adequate_protection(
    secured_debt: float | Decimal,
    monthly_discount_rate: float | Decimal = 0.01,  # 1% per month (~12% annualized)
) -> dict[str, Any]:
    """
    Calculate monthly adequate protection payment for secured debt.

    Adequate protection (§ 361, 363) ensures secured creditor is not harmed by
    depreciation or use of collateral during Ch. 11. Typically: monthly payment
    equal to secured debt * discount rate (to offset time value and depreciation).

    Args:
        secured_debt: Total secured debt balance.
        monthly_discount_rate: Monthly discount rate (default 1% = ~12% annual).

    Returns:
        Dict with secured_debt, monthly_discount_rate, monthly_adequate_protection,
        annual_adequate_protection.
    """
    debt_d = _to_decimal(secured_debt)
    rate_d = _to_decimal(monthly_discount_rate)

    monthly_ap = debt_d * rate_d
    annual_ap = monthly_ap * Decimal("12")

    return {
        "secured_debt": debt_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "monthly_discount_rate": rate_d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        "monthly_adequate_protection": monthly_ap.quantize(QUANT, rounding=ROUND_HALF_UP),
        "annual_adequate_protection": annual_ap.quantize(QUANT, rounding=ROUND_HALF_UP),
    }


def assess_feasibility(
    going_concern_ev: float | Decimal,
    liquidation_value: float | Decimal,
    secured_debt: float | Decimal,
    total_debt: float | Decimal,
    monthly_ebitda: Optional[float | Decimal] = None,
) -> dict[str, Any]:
    """
    Assess Ch. 11 reorganization feasibility vs liquidation.

    Reorganization is feasible if:
    1. Going concern EV > liquidation value (reorganization preserves more value), AND
    2. Secured debt is covered by going concern EV or collateral (secured lenders get adequate protection), AND
    3. (Optional) Monthly EBITDA can cover adequate protection payments.

    Args:
        going_concern_ev: Going concern enterprise value.
        liquidation_value: Orderly or forced liquidation value.
        secured_debt: Total secured debt.
        total_debt: Total debt (for context).
        monthly_ebitda: Optional monthly EBITDA (for cash flow feasibility check).

    Returns:
        Dict with feasibility ("reorganization_viable" / "liquidation_likely"),
        gc_ev_vs_liq_value (difference), collateral_coverage_gc (%), collateral_coverage_liq (%),
        adequate_protection_monthly, ebitda_covers_adequate_protection (bool if monthly_ebitda provided),
        feasibility_note.
    """
    gc_ev_d = _to_decimal(going_concern_ev)
    liq_value_d = _to_decimal(liquidation_value)
    secured_d = _to_decimal(secured_debt)
    total_d = _to_decimal(total_debt)
    monthly_ebitda_d = _to_decimal(monthly_ebitda) if monthly_ebitda is not None else None

    # 1. GC EV vs liquidation
    gc_ev_vs_liq = gc_ev_d - liq_value_d

    # 2. Collateral coverage
    coverage_gc = (gc_ev_d / secured_d * Decimal("100")) if secured_d > 0 else Decimal("0")
    coverage_liq = (liq_value_d / secured_d * Decimal("100")) if secured_d > 0 else Decimal("0")

    # 3. Adequate protection (monthly)
    ap = calculate_adequate_protection(secured_d)
    ap_monthly = ap["monthly_adequate_protection"]

    # Cash flow feasibility (if monthly EBITDA provided)
    ebitda_covers_ap = None
    if monthly_ebitda_d is not None:
        ebitda_covers_ap = monthly_ebitda_d >= ap_monthly

    # Feasibility assessment
    if gc_ev_d > liq_value_d and coverage_gc >= Decimal("100"):
        feasibility = "reorganization_viable"
        feasibility_note = "Going concern EV exceeds liquidation value and secured debt is covered; reorganization preserves value."
    elif gc_ev_d > liq_value_d and coverage_gc < Decimal("100"):
        feasibility = "reorganization_possible_but_secured_shortfall"
        feasibility_note = "Going concern EV exceeds liquidation, but secured lenders face shortfall (collateral coverage < 100%); adequate protection critical."
    else:
        feasibility = "liquidation_likely"
        feasibility_note = "Going concern EV does not exceed liquidation value or secured debt not covered; liquidation (Ch. 7) may be inevitable."

    if ebitda_covers_ap is False:
        feasibility_note += " WARNING: Monthly EBITDA insufficient to cover adequate protection; cash burn will erode secured recovery."

    return {
        "feasibility": feasibility,
        "going_concern_ev": gc_ev_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "liquidation_value": liq_value_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "gc_ev_vs_liq_value": gc_ev_vs_liq.quantize(QUANT, rounding=ROUND_HALF_UP),
        "secured_debt": secured_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "total_debt": total_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "collateral_coverage_gc_pct": coverage_gc.quantize(QUANT, rounding=ROUND_HALF_UP),
        "collateral_coverage_liq_pct": coverage_liq.quantize(QUANT, rounding=ROUND_HALF_UP),
        "adequate_protection_monthly": ap_monthly,
        "monthly_ebitda": monthly_ebitda_d.quantize(QUANT, rounding=ROUND_HALF_UP) if monthly_ebitda_d else None,
        "ebitda_covers_adequate_protection": ebitda_covers_ap,
        "feasibility_note": feasibility_note,
    }

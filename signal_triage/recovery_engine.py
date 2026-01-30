"""
Recovery waterfall: compute recovery rates across a capital structure
and identify the Fulcrum Security for a given Enterprise Value (EV).

All monetary and recovery values (ev, claim, recovered, ev_used, ev_remaining,
recovery_pct) use decimal.Decimal for exact arithmetic; no raw float.

Priority tier and pro-rata (Pari Passu):
- Tranches have an optional priority tier (key "tier" or "priority"; lower
  number = higher priority). Tiers are processed in ascending order.
- Within the same tier, claims are Pari Passu: equal treatment with allocation
  pro-rata by claim when EV is insufficient to pay the tier in full. That is,
  each tranche in the tier receives (claim / tier_total_claim) * pool, where
  pool = min(remaining_ev, tier_total_claim).
- If tier/priority is omitted, each tranche is treated as its own tier (strict
  order by list position).

Quant: reads signals.json for capital structure; runs EV sensitivity.
"""

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Optional

# Exact arithmetic: 2 decimal places for output only
QUANT = Decimal("0.01")


def _to_decimal(x: float | int | Decimal | None) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def run_waterfall(
    tranches: list[dict[str, Any]],
    ev: float | Decimal,
) -> dict[str, Any]:
    """
    Run a recovery waterfall with strict priority or Pari Passu within tiers.
    Uses Decimal for ev, claim, recovered so ev_used + ev_remaining == ev and
    sum(recovered) == ev_used (no raw float).

    Args:
        tranches: List of dicts with "name", "claim" (float/Decimal), and optional
            "tier" or "priority" (int). Lower tier = higher priority. Same tier =
            Pari Passu (pro-rata by claim when EV is insufficient). If omitted,
            strict order (each tranche its own tier).
        ev: Enterprise value to allocate (float or Decimal).

    Returns:
        Dict with recoveries (list of {name, claim, recovered, recovery_pct} as
        Decimal), fulcrum_security, ev_used, ev_remaining (Decimal, 2 dp).
    """
    ev_d = _to_decimal(ev)
    if ev_d < 0:
        ev_d = Decimal("0")
    if not tranches:
        ev_q = ev_d.quantize(QUANT, rounding=ROUND_HALF_UP)
        return {
            "recoveries": [],
            "fulcrum_security": None,
            "ev_used": ev_q,
            "ev_remaining": ev_q,
        }

    # Build list of (tier, name, claim); default tier = index for strict order
    indexed: list[tuple[int, str, Decimal]] = []
    for i, t in enumerate(tranches):
        name = t.get("name", "")
        claim = _to_decimal(t.get("claim", 0) or 0)
        if claim < 0:
            claim = Decimal("0")
        tier = t.get("tier", t.get("priority", i))
        indexed.append((tier, name, claim))

    # Group by tier (ascending), preserving order within tier
    tiers_seen: dict[int, list[tuple[str, Decimal]]] = {}
    for tier, name, claim in indexed:
        tiers_seen.setdefault(tier, []).append((name, claim))

    remaining = ev_d
    recoveries: list[dict[str, Any]] = []
    fulcrum_security = None

    for tier in sorted(tiers_seen.keys()):
        group = tiers_seen[tier]
        tier_claims = sum(c for _, c in group)
        if tier_claims <= 0:
            for name, claim in group:
                recoveries.append({
                    "name": name,
                    "claim": claim.quantize(QUANT, rounding=ROUND_HALF_UP),
                    "recovered": Decimal("0"),
                    "recovery_pct": Decimal("0"),
                })
                if fulcrum_security is None and claim > 0:
                    fulcrum_security = name
            continue

        pool = min(remaining, tier_claims)
        for name, claim in group:
            if tier_claims > 0:
                recovered = claim / tier_claims * pool  # exact Decimal; sum(recovered) == pool
            else:
                recovered = Decimal("0")
            recovery_pct = (recovered / claim * 100) if claim > 0 else Decimal("0")
            recoveries.append({
                "name": name,
                "claim": claim.quantize(QUANT, rounding=ROUND_HALF_UP),
                "recovered": recovered.quantize(QUANT, rounding=ROUND_HALF_UP),
                "recovery_pct": recovery_pct.quantize(QUANT, rounding=ROUND_HALF_UP),
            })
            if fulcrum_security is None and 0 < recovery_pct < 100:
                fulcrum_security = name
            if fulcrum_security is None and recovery_pct == 0 and claim > 0:
                fulcrum_security = name
        remaining = remaining - pool
        if remaining < 0:
            remaining = Decimal("0")

    ev_used = (ev_d - remaining).quantize(QUANT, rounding=ROUND_HALF_UP)
    
    # Detect APR violations
    apr_violations = _detect_apr_violations(recoveries)
    
    return {
        "recoveries": recoveries,
        "fulcrum_security": fulcrum_security,
        "ev_used": ev_used,
        "ev_remaining": remaining,
        "apr_violations": apr_violations,
    }


def trace_double_dip_recovery(
    tranches: list[dict[str, Any]],
    guarantee_stack: Optional[dict[str, dict[str, Any]]] = None,
) -> dict[str, Any]:
    """
    Trace guarantee stack and intercompany notes to identify double-dip / triple-dip structures.

    A double-dip occurs when the same economic exposure supports multiple claims:
    1. Loan to non-guarantor (empty-box) subsidiary
    2. Intercompany loan from that sub to a guarantor (or borrower)
    3. Parent or guarantor guarantee of the original loan

    Result: same $ of value backs 2 (or 3) claims at different levels of the cap structure.

    Args:
        tranches: List of {name, claim, ...}.
        guarantee_stack: Optional dict mapping entity names to {guarantor, guaranteed_claim, ...}.
            Example: {"Empty Box Sub": {"guarantor": "Parent", "guaranteed_claim": 50}}.

    Returns:
        Dict with double_dip_detected (bool), claims (list of tranche names), economic_exposure (true $),
        stated_claims (inflated $), dilution_ratio (stated / economic).
    """
    if not guarantee_stack:
        return {
            "double_dip_detected": False,
            "claims": [],
            "economic_exposure": Decimal("0"),
            "stated_claims": Decimal("0"),
            "dilution_ratio": Decimal("1.0"),
            "note": "No guarantee stack provided; double-dip analysis not performed.",
        }

    # Build a map of tranche name -> claim amount
    tranche_map = {t.get("name", ""): _to_decimal(t.get("claim", 0)) for t in tranches}

    # Identify double-dip patterns: if tranche A and tranche B both reference same economic exposure
    # Heuristic: if guarantee_stack shows entity X is guaranteed by Y, and both X and Y have claims,
    # and X's claim == guaranteed_claim, then it's a double-dip.
    double_dips = []
    for entity, info in guarantee_stack.items():
        guarantor = info.get("guarantor", "")
        guaranteed_claim = _to_decimal(info.get("guaranteed_claim", 0))

        # Check if both entity and guarantor have claims in tranches
        entity_claim = tranche_map.get(entity, Decimal("0"))
        guarantor_claim = tranche_map.get(guarantor, Decimal("0"))

        if entity_claim > 0 and guarantor_claim > 0:
            # If entity's claim matches guaranteed amount, it's likely a double-dip
            if entity_claim == guaranteed_claim or guarantor_claim == guaranteed_claim:
                double_dips.append({
                    "entity": entity,
                    "guarantor": guarantor,
                    "economic_exposure": guaranteed_claim,
                    "entity_claim": entity_claim,
                    "guarantor_claim": guarantor_claim,
                    "stated_claims": entity_claim + guarantor_claim,
                })

    if not double_dips:
        return {
            "double_dip_detected": False,
            "claims": [],
            "economic_exposure": Decimal("0"),
            "stated_claims": Decimal("0"),
            "dilution_ratio": Decimal("1.0"),
            "note": "No double-dip pattern detected in guarantee stack.",
        }

    # Aggregate
    total_economic = sum(d["economic_exposure"] for d in double_dips)
    total_stated = sum(d["stated_claims"] for d in double_dips)
    dilution_ratio = (total_stated / total_economic) if total_economic > 0 else Decimal("1.0")

    claim_names = []
    for d in double_dips:
        claim_names.extend([d["entity"], d["guarantor"]])

    return {
        "double_dip_detected": True,
        "double_dip_details": double_dips,
        "claims": list(set(claim_names)),  # dedupe
        "economic_exposure": total_economic.quantize(QUANT, rounding=ROUND_HALF_UP),
        "stated_claims": total_stated.quantize(QUANT, rounding=ROUND_HALF_UP),
        "dilution_ratio": dilution_ratio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "note": f"Double-dip detected: {len(double_dips)} instance(s). Existing lenders share EV with {dilution_ratio}x the stated claims.",
    }


def _detect_apr_violations(recoveries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Detect Absolute Priority Rule (APR) violations.

    APR states that senior creditors must be paid in full before junior creditors
    or equity receive any value. A violation occurs when:
    - A senior tranche has recovery < 100%, AND
    - Any junior tranche (later in the list) has recovery > 0.

    Args:
        recoveries: List of {name, claim, recovered, recovery_pct} in priority order.

    Returns:
        List of violation dicts: {senior_tranche, senior_recovery_pct, junior_tranche,
        junior_recovery, violation_type, note}.
    """
    violations = []
    for i, senior in enumerate(recoveries):
        senior_pct = senior.get("recovery_pct", Decimal("100"))
        if isinstance(senior_pct, str):
            continue  # skip non-numeric
        if senior_pct < Decimal("100"):
            # Check all junior tranches (i+1 onward)
            for junior in recoveries[i + 1:]:
                junior_recovered = junior.get("recovered", Decimal("0"))
                if isinstance(junior_recovered, str):
                    continue
                if junior_recovered > 0:
                    violations.append({
                        "senior_tranche": senior.get("name", ""),
                        "senior_recovery_pct": str(senior_pct),
                        "junior_tranche": junior.get("name", ""),
                        "junior_recovery": str(junior_recovered),
                        "violation_type": "APR",
                        "note": f"Junior tranche '{junior.get('name', '')}' recovered {junior_recovered} while senior tranche '{senior.get('name', '')}' only recovered {senior_pct}%.",
                    })
            break  # only need to check the first impaired senior tranche
    return violations


def _situational_summary(
    result: dict[str, Any],
    ev_used: Decimal | float,
    collateral_adjustment: Decimal | float = 0,
) -> str:
    """Quant: Plain-English situational summary for the Reporter."""
    ev_used_n = float(ev_used) if isinstance(ev_used, Decimal) else ev_used
    adj_n = float(collateral_adjustment) if isinstance(collateral_adjustment, Decimal) else collateral_adjustment
    fulcrum = result.get("fulcrum_security") or "N/A"
    recoveries = result.get("recoveries") or []
    lines = [
        f"Fulcrum security: {fulcrum}. "
        f"Enterprise value applied: {ev_used_n:.2f}."
    ]
    if adj_n > 0:
        lines.append(
            f"LME/collateral leakage adjustment applied: {adj_n:.2f} "
            "(Librarian flagged collateral leakage; EV reduced for waterfall)."
        )
    for r in recoveries[:5]:
        name = r.get("name", "")
        pct = r.get("recovery_pct", 0)
        pct_n = float(pct) if isinstance(pct, Decimal) else pct
        lines.append(f" {name}: {pct_n:.1f}% recovery.")
    return " ".join(lines)


def run_waterfall_from_signals(
    signals_path: str | Path,
    ev_override: float | None = None,
    collateral_leakage_ev_adjustment: float | None = None,
) -> dict[str, Any] | None:
    """
    Quant: Run waterfall using capital structure from signals.json.
    When Librarian has emitted collateral_leakage_flags, apply LME-adjusted EV
    (reduce EV by collateral_leakage_ev_adjustment if provided, else 0).

    Args:
        signals_path: Path to signals.json (written by Librarian).
        ev_override: If set, use this EV instead of signals' default_ev.
        collateral_leakage_ev_adjustment: If set (or inferred from signals when leakage flags
            present), subtract from EV before waterfall. When None, signals may contain
            collateral_leakage_ev_adjustment; if leakage flags present and no value, use 0.

    Returns:
        run_waterfall result dict plus situational_summary (and ev_adjustment when applied),
        or None if signals have no capital_structure/tranches.
    """
    from signal_triage.signals_io import read_signals

    signals = read_signals(signals_path)
    cap = signals.get("capital_structure")
    if not cap or not cap.get("tranches"):
        return None
    tranches = cap["tranches"]
    ev = ev_override if ev_override is not None else cap.get("default_ev")
    if ev is None:
        return None
    ev_d = _to_decimal(ev)
    leakage_flags = signals.get("collateral_leakage_flags") or []
    adjustment = collateral_leakage_ev_adjustment
    if adjustment is None and leakage_flags:
        adjustment = signals.get("collateral_leakage_ev_adjustment") or 0
    adjustment_d = _to_decimal(adjustment) if adjustment is not None else Decimal("0")
    if adjustment_d > 0:
        ev_d = max(Decimal("0"), ev_d - adjustment_d)
    result = run_waterfall(tranches, ev_d)
    result["situational_summary"] = _situational_summary(
        result, result.get("ev_used", Decimal("0")), adjustment_d
    )
    if adjustment_d > 0:
        result["collateral_leakage_ev_adjustment"] = adjustment_d
    return result


def ev_sensitivity(
    tranches: list[dict[str, Any]],
    ev_base: float | Decimal,
    ev_step: float | Decimal = Decimal("50.0"),
    steps: int = 5,
) -> list[dict[str, Any]]:
    """
    Quant: EV sensitivity analysis — run waterfall at ev_base ± steps around it.

    Returns:
        List of {"ev": Decimal, "result": run_waterfall(...)} for ev_base - steps*ev_step
        through ev_base + steps*ev_step (2*steps+1 points).
    """
    base_d = _to_decimal(ev_base)
    step_d = _to_decimal(ev_step)
    out = []
    for i in range(-steps, steps + 1):
        ev = base_d + i * step_d
        if ev < 0:
            ev = Decimal("0")
        out.append({"ev": ev, "result": run_waterfall(tranches, ev)})
    return out


def tornado_drivers(
    tranches: list[dict[str, Any]],
    base_ev: float | Decimal,
    collateral_adjustment: float | Decimal = 0,
    *,
    ev_step: float | Decimal = 50.0,
    collateral_step: float | Decimal | None = None,
) -> list[dict[str, Any]]:
    """
    Quant: Tornado-ready output for key drivers (EV, optional collateral leakage).
    Varies EV and optional collateral adjustment; returns low/base/high and
    recovery_by_tranche per driver for Tornado diagram use.

    Uses Decimal internally; keeps existing ev_sensitivity/run_waterfall behavior.

    Args:
        tranches: Same as run_waterfall (name, claim, optional tier).
        base_ev: Base enterprise value (float or Decimal).
        collateral_adjustment: Optional LME/collateral leakage adjustment to subtract from EV.
        ev_step: Step for EV driver low/high (default 50).
        collateral_step: Step for collateral driver high; default ev_step.

    Returns:
        List of driver dicts, e.g.:
        [
          {
            "driver": "EV",
            "low": float, "base": float, "high": float,
            "recovery_by_tranche": [{"name": str, "low": float, "base": float, "high": float}, ...],
          },
          {
            "driver": "collateral_adjustment",
            "low": float, "base": float, "high": float,
            "recovery_by_tranche": [...],
          },  # only when collateral_adjustment != 0 or collateral_step used
        ]
    """
    base_d = _to_decimal(base_ev)
    coll_d = _to_decimal(collateral_adjustment)
    ev_step_d = _to_decimal(ev_step)
    coll_step_d = coll_d if collateral_step is None else _to_decimal(collateral_step)
    if coll_d == 0 and coll_step_d == 0:
        coll_step_d = ev_step_d  # so we can still emit a collateral driver with 0,0,step

    drivers: list[dict[str, Any]] = []

    # EV driver: low = base - step, base = base, high = base + step
    ev_low = max(Decimal("0"), base_d - ev_step_d)
    ev_high = base_d + ev_step_d
    r_low = run_waterfall(tranches, ev_low)
    r_base = run_waterfall(tranches, base_d)
    r_high = run_waterfall(tranches, ev_high)
    names = [rec["name"] for rec in r_base["recoveries"]]
    zero_d = Decimal("0")
    by_low = {r["name"]: r["recovery_pct"] for r in r_low["recoveries"]}
    by_base = {r["name"]: r["recovery_pct"] for r in r_base["recoveries"]}
    by_high = {r["name"]: r["recovery_pct"] for r in r_high["recoveries"]}
    recovery_by_tranche = [
        {"name": name, "low": by_low.get(name, zero_d), "base": by_base.get(name, zero_d), "high": by_high.get(name, zero_d)}
        for name in names
    ]
    drivers.append({
        "driver": "EV",
        "low": ev_low.quantize(QUANT, rounding=ROUND_HALF_UP),
        "base": base_d.quantize(QUANT, rounding=ROUND_HALF_UP),
        "high": ev_high.quantize(QUANT, rounding=ROUND_HALF_UP),
        "recovery_by_tranche": recovery_by_tranche,
    })

    # Collateral adjustment driver: effective EV = base_ev - adj; low adj = high EV, high adj = low EV
    adj_low = Decimal("0")
    adj_base = coll_d
    adj_high = coll_d + coll_step_d
    ev_eff_low = max(Decimal("0"), base_d - adj_low)
    ev_eff_base = max(Decimal("0"), base_d - adj_base)
    ev_eff_high = max(Decimal("0"), base_d - adj_high)
    r_coll_low = run_waterfall(tranches, ev_eff_low)
    r_coll_base = run_waterfall(tranches, ev_eff_base)
    r_coll_high = run_waterfall(tranches, ev_eff_high)
    by_coll_low = {r["name"]: r["recovery_pct"] for r in r_coll_low["recoveries"]}
    by_coll_base = {r["name"]: r["recovery_pct"] for r in r_coll_base["recoveries"]}
    by_coll_high = {r["name"]: r["recovery_pct"] for r in r_coll_high["recoveries"]}
    recovery_by_tranche_coll = [
        {
            "name": name,
            "low": by_coll_low.get(name, zero_d),
            "base": by_coll_base.get(name, zero_d),
            "high": by_coll_high.get(name, zero_d),
        }
        for name in names
    ]
    drivers.append({
        "driver": "collateral_adjustment",
        "low": adj_low.quantize(QUANT, rounding=ROUND_HALF_UP),
        "base": adj_base.quantize(QUANT, rounding=ROUND_HALF_UP),
        "high": adj_high.quantize(QUANT, rounding=ROUND_HALF_UP),
        "recovery_by_tranche": recovery_by_tranche_coll,
    })

    return drivers

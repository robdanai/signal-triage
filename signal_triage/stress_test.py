"""
Priming stress test: quantify subordinated recoveries and fulcrum shifts.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

from signal_triage.recovery_engine import QUANT, run_waterfall
from signal_triage.signals_io import DEFAULT_CAPITAL_STRUCTURE, read_signals

NEW_MONEY_LABEL = "New Money Super-Priority"
PARTICIPATING_LABEL = "Senior Secured (Participating 50.1%)"
NON_PARTICIPATING_LABEL = "Senior Secured (Non-Participating 49.9%)"


def _to_decimal(value: float | int | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _clamp_share(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _find_senior_secured(tranches: list[dict[str, Any]]) -> dict[str, Any] | None:
    for tranche in tranches:
        name = str(tranche.get("name", "")).lower()
        if "senior" in name and "secured" in name:
            return tranche
    return tranches[0] if tranches else None


def _get_recovery(recoveries: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for rec in recoveries:
        if rec.get("name") == name:
            return rec
    return None


def build_pre_priming_tranches(capital_structure: dict[str, Any]) -> list[dict[str, Any]]:
    """Build baseline tranches in strict priority order."""
    tranches = capital_structure.get("tranches") or []
    out: list[dict[str, Any]] = []
    for i, tranche in enumerate(tranches):
        out.append({
            "name": tranche.get("name", ""),
            "claim": _to_decimal(tranche.get("claim", 0)),
            "tier": i,
        })
    return out


def build_post_priming_tranches(
    capital_structure: dict[str, Any],
    new_money: float | Decimal = Decimal("250"),
) -> list[dict[str, Any]]:
    """Build post-priming structure with new-money super-priority."""
    tranches = capital_structure.get("tranches") or []
    out: list[dict[str, Any]] = [{
        "name": NEW_MONEY_LABEL,
        "claim": _to_decimal(new_money),
        "tier": 0,
    }]
    for i, tranche in enumerate(tranches):
        out.append({
            "name": tranche.get("name", ""),
            "claim": _to_decimal(tranche.get("claim", 0)),
            "tier": i + 1,
        })
    return out


def build_non_participating_tranches(
    capital_structure: dict[str, Any],
    new_money: float | Decimal = Decimal("250"),
    non_participating_share: float | Decimal = Decimal("0.499"),
) -> list[dict[str, Any]]:
    """Build structure that subordinates the minority 1L holders."""
    tranches = capital_structure.get("tranches") or []
    senior = _find_senior_secured(tranches)
    if not senior:
        return build_post_priming_tranches(capital_structure, new_money=new_money)

    share = _clamp_share(_to_decimal(non_participating_share))
    senior_claim = _to_decimal(senior.get("claim", 0))
    non_part_claim = _quantize_money(senior_claim * share)
    participating_claim = _quantize_money(senior_claim - non_part_claim)

    out: list[dict[str, Any]] = [{
        "name": NEW_MONEY_LABEL,
        "claim": _to_decimal(new_money),
        "tier": 0,
    }]
    out.append({
        "name": PARTICIPATING_LABEL,
        "claim": participating_claim,
        "tier": 1,
    })
    out.append({
        "name": NON_PARTICIPATING_LABEL,
        "claim": non_part_claim,
        "tier": 2,
    })

    tail_index = 3
    for tranche in tranches:
        if tranche is senior:
            continue
        out.append({
            "name": tranche.get("name", ""),
            "claim": _to_decimal(tranche.get("claim", 0)),
            "tier": tail_index,
        })
        tail_index += 1

    return out


def break_even_ev_for_tranche(
    tranches: list[dict[str, Any]],
    tranche_name: str,
) -> Decimal:
    """Compute EV needed for a tranche to be made whole."""
    indexed: list[tuple[int, str, Decimal]] = []
    for i, tranche in enumerate(tranches):
        tier = tranche.get("tier", tranche.get("priority", i))
        indexed.append((int(tier), tranche.get("name", ""), _to_decimal(tranche.get("claim", 0))))

    tiers: dict[int, list[tuple[str, Decimal]]] = {}
    for tier, name, claim in indexed:
        tiers.setdefault(tier, []).append((name, claim))

    cumulative = Decimal("0")
    for tier in sorted(tiers.keys()):
        group = tiers[tier]
        tier_claims = sum(claim for _, claim in group)
        if any(name == tranche_name for name, _ in group):
            return _quantize_money(cumulative + tier_claims)
        cumulative += tier_claims
    return Decimal("0")


def run_priming_stress_test(
    signals_path: str | Path = "signals.json",
    *,
    evs: Iterable[float | Decimal] | None = None,
    new_money: float | Decimal = Decimal("250"),
    non_participating_share: float | Decimal = Decimal("0.499"),
) -> dict[str, Any]:
    """Run priming stress scenarios and quantify subordinated recoveries."""
    signals = read_signals(signals_path)
    capital_structure = signals.get("capital_structure") or DEFAULT_CAPITAL_STRUCTURE
    default_ev = _to_decimal(capital_structure.get("default_ev", 0))

    pre_tranches = build_pre_priming_tranches(capital_structure)
    post_tranches = build_post_priming_tranches(capital_structure, new_money=new_money)
    non_part_tranches = build_non_participating_tranches(
        capital_structure,
        new_money=new_money,
        non_participating_share=non_participating_share,
    )

    pre_default = run_waterfall(pre_tranches, default_ev)
    post_default = run_waterfall(post_tranches, default_ev)
    non_part_default = run_waterfall(non_part_tranches, default_ev)

    senior_name = _find_senior_secured(capital_structure.get("tranches") or []) or {}
    senior_label = senior_name.get("name", "Senior Secured")

    pre_senior = _get_recovery(pre_default["recoveries"], senior_label) or {}
    post_senior = _get_recovery(post_default["recoveries"], senior_label) or {}
    non_part = _get_recovery(non_part_default["recoveries"], NON_PARTICIPATING_LABEL) or {}

    pre_recovered = _to_decimal(pre_senior.get("recovered", 0))
    post_recovered = _to_decimal(post_senior.get("recovered", 0))
    senior_claim = _to_decimal(pre_senior.get("claim", 0))
    dilution_loss = _quantize_money(pre_recovered - post_recovered)
    dilution_pct = _quantize_money((dilution_loss / senior_claim * 100) if senior_claim > 0 else Decimal("0"))

    share = _clamp_share(_to_decimal(non_participating_share))
    baseline_non_part = _quantize_money(pre_recovered * share)
    non_part_recovered = _to_decimal(non_part.get("recovered", 0))
    non_part_loss = _quantize_money(baseline_non_part - non_part_recovered)

    ev_list = [
        _to_decimal(value) for value in (evs or [250, 350, 450, 550, 700])
    ]
    scenarios: list[dict[str, Any]] = []
    creditor_violence_breakdown: list[dict[str, Any]] = []
    for ev in ev_list:
        pre_result = run_waterfall(pre_tranches, ev)
        post_result = run_waterfall(post_tranches, ev)
        non_part_result = run_waterfall(non_part_tranches, ev)
        non_part_rec = _get_recovery(non_part_result["recoveries"], NON_PARTICIPATING_LABEL) or {}

        pre_senior_rec = _get_recovery(pre_result["recoveries"], senior_label) or {}
        pre_senior_recovered = _to_decimal(pre_senior_rec.get("recovered", 0))
        scenario_baseline_non_part = _quantize_money(pre_senior_recovered * share)
        scenario_non_part_recovered = _to_decimal(non_part_rec.get("recovered", 0))
        scenario_loss = _quantize_money(scenario_baseline_non_part - scenario_non_part_recovered)

        scenarios.append({
            "ev": _quantize_money(ev),
            "pre_priming": pre_result,
            "post_priming": post_result,
            "non_participating": non_part_result,
            "non_participating_recovery": non_part_rec,
        })
        creditor_violence_breakdown.append({
            "ev": _quantize_money(ev),
            "baseline_non_participating": scenario_baseline_non_part,
            "recovered_non_participating": _quantize_money(scenario_non_part_recovered),
            "loss_non_participating": scenario_loss,
        })

    break_even_ev = break_even_ev_for_tranche(non_part_tranches, NON_PARTICIPATING_LABEL)

    return {
        "default_ev": _quantize_money(default_ev),
        "pre_priming": pre_default,
        "post_priming": post_default,
        "non_participating": non_part_default,
        "recovery_dilution_analysis": {
            "senior_tranche": senior_label,
            "pre_priming_recovered": _quantize_money(pre_recovered),
            "post_priming_recovered": _quantize_money(post_recovered),
            "loss": dilution_loss,
            "loss_pct_of_claim": dilution_pct,
        },
        "fulcrum_migration": {
            "pre_priming": pre_default.get("fulcrum_security"),
            "post_priming": post_default.get("fulcrum_security"),
        },
        "subordinated_recovery": {
            "tranche": NON_PARTICIPATING_LABEL,
            "claim": _quantize_money(_to_decimal(non_part.get("claim", 0))),
            "recovered": _quantize_money(non_part_recovered),
            "recovery_pct": _to_decimal(non_part.get("recovery_pct", 0)),
        },
        "adversarial_scenarios": scenarios,
        "break_even_ev_non_participating": break_even_ev,
        "creditor_violence_impact": {
            "baseline_non_participating": baseline_non_part,
            "recovered_non_participating": _quantize_money(non_part_recovered),
            "loss_non_participating": non_part_loss,
            "scenario_breakdown": creditor_violence_breakdown,
        },
    }

from decimal import Decimal

from signal_triage.recovery_engine import run_waterfall
from signal_triage.stress_test import (
    NON_PARTICIPATING_LABEL,
    build_non_participating_tranches,
    build_post_priming_tranches,
    build_pre_priming_tranches,
    break_even_ev_for_tranche,
    run_priming_stress_test,
)


def _sample_capital_structure() -> dict:
    return {
        "tranches": [
            {"name": "Senior Secured", "claim": 300},
            {"name": "Mezz", "claim": 150},
            {"name": "Unsecured", "claim": 100},
        ],
        "default_ev": 350,
    }


def test_pre_priming_waterfall_default_ev() -> None:
    capital_structure = _sample_capital_structure()
    tranches = build_pre_priming_tranches(capital_structure)
    result = run_waterfall(tranches, Decimal("350"))
    recoveries = {r["name"]: r for r in result["recoveries"]}

    assert recoveries["Senior Secured"]["recovered"] == Decimal("300.00")
    assert recoveries["Mezz"]["recovered"] == Decimal("50.00")
    assert recoveries["Unsecured"]["recovered"] == Decimal("0.00")
    assert result["fulcrum_security"] == "Mezz"


def test_post_priming_waterfall_default_ev() -> None:
    capital_structure = _sample_capital_structure()
    tranches = build_post_priming_tranches(capital_structure, new_money=Decimal("250"))
    result = run_waterfall(tranches, Decimal("350"))
    recoveries = {r["name"]: r for r in result["recoveries"]}

    assert recoveries["New Money Super-Priority"]["recovered"] == Decimal("250.00")
    assert recoveries["Senior Secured"]["recovered"] == Decimal("100.00")
    assert result["fulcrum_security"] == "Senior Secured"


def test_non_participating_break_even_ev() -> None:
    capital_structure = _sample_capital_structure()
    tranches = build_non_participating_tranches(capital_structure, new_money=Decimal("250"))
    break_even = break_even_ev_for_tranche(tranches, NON_PARTICIPATING_LABEL)
    assert break_even == Decimal("550.00")


def test_run_priming_stress_test_outputs() -> None:
    result = run_priming_stress_test("signals.json")
    assert result["fulcrum_migration"]["pre_priming"] == "Mezz"
    assert result["fulcrum_migration"]["post_priming"] == "Senior Secured"
    assert result["break_even_ev_non_participating"] == Decimal("550.00")

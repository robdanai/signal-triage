"""
Credit Integrity Audit: Adversarial stress-test of recovery_engine and LME parser.
Run: python -m tests.credit_integrity_audit
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signal_triage.recovery_engine import run_waterfall
from signal_triage.lme_parser import detect_lme, LME_PATTERNS


def scenario_1_ev_below_first_lien():
    """Edge Case 1: EV drops below 1st Lien debt — fulcrum at 1L, 2L/Unsecured wiped."""
    tranches = [
        {"name": "1L", "claim": 500_000_000},
        {"name": "2L", "claim": 200_000_000},
        {"name": "Unsecured", "claim": 300_000_000},
    ]
    ev = 300_000_000  # Below 1L; 1L takes haircut
    return run_waterfall(tranches, ev)


def scenario_2_pari_passu_second_lien():
    """Edge Case 2: 2L claims Pari Passu with 1L via Intercreditor — code treats order as strict; first tranche gets all."""
    # Simulate: 1L and "2L Pari Passu" both in list; if truly pari passu they share pro-rata. Code does strict order.
    tranches = [
        {"name": "1L", "claim": 400_000_000},
        {"name": "2L_PariPassu", "claim": 100_000_000},  # In reality would share with 1L
        {"name": "Unsecured", "claim": 200_000_000},
    ]
    ev = 500_000_000  # Exactly 1L + 2L; under pari passu 2L should get 100%, code gives 1L 100%, 2L 100%, Unsec 0%
    out = run_waterfall(tranches, ev)
    # Under strict order: 1L 100%, 2L 100%, Unsec 0%. Under Pari Passu 1L/2L: 1L gets 400/500 * 500 = 400, 2L gets 100. Same. But if EV = 400: strict gives 1L 100%, 2L 0%. Pari Passu would give 1L 320, 2L 80. So we test EV=400.
    return out, run_waterfall(tranches, 400_000_000)


def scenario_3_fulcrum_boundary_and_cramdown():
    """Edge Case 3: EV exactly equals 1L (boundary); Cramdown / Priming — fulcrum identification."""
    tranches = [
        {"name": "1L", "claim": 250_000_000},
        {"name": "2L", "claim": 150_000_000},
    ]
    ev_exact = 250_000_000
    return run_waterfall(tranches, ev_exact)


def check_float_leakage():
    """Precision: large claims with float — do we get rounding leakage?"""
    # Many small allocations that should sum exactly to EV
    tranches = [
        {"name": "T1", "claim": 1_000_000.10},
        {"name": "T2", "claim": 2_000_000.20},
        {"name": "T3", "claim": 3_000_000.30},
    ]
    ev = 6_000_000.60  # Exact sum
    out = run_waterfall(tranches, ev)
    total_recovered = sum(r["recovered"] for r in out["recoveries"])
    ev_used = out["ev_used"]
    remaining = out["ev_remaining"]
    return {
        "ev": ev,
        "total_recovered": total_recovered,
        "ev_used": ev_used,
        "ev_remaining": remaining,
        "leakage": ev_used - total_recovered,
        "remaining_expected": 0.0,
    }


def check_lme_uptiering_variants():
    """LME: Does scanner miss common uptiering / structural language?"""
    tests = [
        ("uptier exchange and roll-up", "uptiering"),
        ("transfer to unrestricted subsidiary", "unrestricted"),
        ("asset sale proceeds to unrestricted sub", "asset sale / unrestricted"),
        ("investment basket used for restricted subsidiary", "investment basket"),
        ("J.Crew-style dropdown", "j.crew"),
        ("priming lien and DIP", "uptiering"),
        ("structural subordination of notes", "structural"),
    ]
    results = []
    for text, category in tests:
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        labels = [s["label"] for s in signals]
        results.append({
            "text": text[:50],
            "category": category,
            "signals_found": len(signals),
            "types": types,
            "labels": labels,
        })
    return results


def main():
    print("=" * 60)
    print("CREDIT INTEGRITY AUDIT — Adversarial Run")
    print("=" * 60)

    # --- Scenario 1 ---
    print("\n--- Scenario 1: EV below 1st Lien ---")
    out1 = scenario_1_ev_below_first_lien()
    for r in out1["recoveries"]:
        print(f"  {r['name']}: claim={r['claim']:.0f} recovered={r['recovered']:.0f} recovery_pct={r['recovery_pct']}")
    print(f"  Fulcrum: {out1['fulcrum_security']} | ev_used={out1['ev_used']} ev_remaining={out1['ev_remaining']}")

    # --- Scenario 2 ---
    print("\n--- Scenario 2: Pari Passu (EV=500M then EV=400M) ---")
    out2a, out2b = scenario_2_pari_passu_second_lien()
    print("  EV=500M:")
    for r in out2a["recoveries"]:
        print(f"    {r['name']}: recovery_pct={r['recovery_pct']}")
    print("  EV=400M (strict order: 1L 100%, 2L 0%; Pari Passu would give 1L 80%, 2L 20%):")
    for r in out2b["recoveries"]:
        print(f"    {r['name']}: recovered={r['recovered']:.0f} recovery_pct={r['recovery_pct']}")

    # --- Scenario 3 ---
    print("\n--- Scenario 3: Fulcrum boundary (EV = 1L exactly) ---")
    out3 = scenario_3_fulcrum_boundary_and_cramdown()
    for r in out3["recoveries"]:
        print(f"  {r['name']}: recovery_pct={r['recovery_pct']}")
    print(f"  Fulcrum: {out3['fulcrum_security']}")

    # --- Float leakage ---
    print("\n--- Math: Float leakage check (sum recovered vs ev_used) ---")
    leak = check_float_leakage()
    print(f"  EV={leak['ev']} total_recovered={leak['total_recovered']} ev_used={leak['ev_used']} ev_remaining={leak['ev_remaining']}")
    print(f"  Leakage (ev_used - total_recovered): {leak['leakage']}")

    # --- LME variants ---
    print("\n--- LME: Uptiering / basket / unrestricted language ---")
    for r in check_lme_uptiering_variants():
        print(f"  [{r['category']}] \"{r['text']}...\" -> signals={r['signals_found']} types={r['types']}")

    # Basket / Asset Sale in LME_PATTERNS?
    all_phrases = [p for phrases in LME_PATTERNS.values() for p in phrases]
    has_asset_sale = any("asset" in p.lower() or "sale" in p.lower() for p in all_phrases)
    has_investment_basket = any("investment" in p.lower() or "basket" in p.lower() for p in all_phrases)
    print(f"\n  LME_PATTERNS contains 'asset sale'?: {has_asset_sale}")
    print(f"  LME_PATTERNS contains 'investment basket'?: {has_investment_basket}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

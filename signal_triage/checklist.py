"""
Generate analyst to-do checklists from detected signals (e.g. default, covenant, LME).
"""

from typing import Any

# Map signal type -> list of checklist steps (order preserved; deduplicated globally)
SIGNAL_CHECKLISTS = {
    "going_concern": [
        "Assess management's going concern evaluation and time horizon",
        "Review material uncertainties and mitigation plans",
        "Check disclosure of substantial doubt and supporting assumptions",
    ],
    "liquidity_covenant": [
        "Identify breached covenant and financial maintenance levels",
        "Check waiver request status and consent requirements",
        "Review liquidity runway and funding sources",
    ],
    "debt_maturity_refinancing": [
        "Map upcoming maturities and refinancing needs",
        "Assess market access and refinancing uncertainty",
        "Review maturity concentration and covenant headroom",
    ],
    "auditor_emphasis": [
        "Review emphasis-of-matter paragraph and scope",
        "Confirm material uncertainty related to going concern if applicable",
        "Check for qualified opinion and management response",
    ],
    "potential_default": [
        "Confirm event of default and any grace/cure period",
        "Check cross-defaults and cross-acceleration",
        "Review lender group and required consents",
        "Document notice and cure rights",
    ],
    "covenant_risk": [
        "Identify breached covenant and financial maintenance levels",
        "Check waiver request status and consent requirements",
        "Review MAC and material adverse change language",
        "Assess cure period and forbearance",
    ],
    "dropdown": [
        "Trace subsidiary guarantee releases and dropdown structure",
        "Review restricted vs unrestricted subsidiary definitions",
        "Check dividend stoppers and upstream restrictions",
    ],
    "sprime_leakage": [
        "Map first lien vs second lien collateral and priming",
        "Review adequate protection and DIP/cash collateral orders",
        "Assess collateral leakage and S-Prime implications",
    ],
    "uptiering": [
        "Identify uptiering transaction and consent thresholds",
        "Review DIP/exit facility and superpriority treatment",
        "Assess roll-up and priming lien structure",
    ],
    "texas_two_step": [
        "Identify two-step or divisional merger structure and governing law",
        "Assess separation of liabilities from operating assets and creditor impact",
        "Review LMT/restructuring disclosure and precedent (e.g. mass tort, LTL).",
    ],
    "double_dip_triple_dip": [
        "Trace non-guarantor / empty-box structure and intercompany loan flow",
        "Assess multiple claims on same collateral or economic exposure",
        "Review guarantee stack and recovery impact on existing lenders.",
    ],
    "consent_solicitation_exchange": [
        "Identify consent solicitation / exchange offer / tender terms and consent thresholds",
        "Review consent payment and amend-and-extend mechanics",
        "Assess out-of-court path vs bankruptcy and creditor split (participating vs non-participating).",
    ],
    "equity_cure": [
        "Identify equity cure right and dollar/covenant limits",
        "Review equity injection and covenant cure mechanics",
        "Assess sponsor capacity and cure frequency caps.",
    ],
    "substantive_consolidation_cramdown": [
        "Assess substantive consolidation risk and impact on collateral/guarantees",
        "Review cramdown / absolute priority and plan confirmation language",
        "Check fair and equitable treatment and precedent.",
    ],
    "lender_voting_squeeze": [
        "Identify required lender / majority lender and amendment thresholds",
        "Review yank-a-bank, replaceable lender, and non-consenting lender treatment",
        "Assess amendment-without-consent and out-of-the-money lender risk.",
    ],
    "forbearance_standstill": [
        "Review forbearance period and standstill terms",
        "Check waiver and forbearance scope and expiry",
        "Assess runway and path to restructuring or default.",
    ],
    "crossover_prepack": [
        "Identify crossover / bridge facility and conversion or roll into Ch. 11",
        "Review prepack or pre-arranged bankruptcy and plan support agreement",
        "Assess timing and creditor alignment.",
    ],
    "make_whole_disallowance": [
        "Review make-whole and early redemption / acceleration treatment",
        "Check bankruptcy disallowance and unmatured interest (e.g. § 502(b))",
        "Assess claim amount and recovery impact.",
    ],
    "pik": [
        "Identify PIK toggle and PIK interest terms",
        "Review payment-in-kind capacity and cash vs PIK election",
        "Assess liquidity and covenant impact.",
    ],
    "jcrew_blocker": [
        "Check for J.Crew blocker or anti-dropdown provision restricting IP transfer to unrestricted subs",
        "Review Envision/Chewy precedent and whether blocker exists in this credit agreement",
        "Assess IP/brand/key asset transfer risk if blocker is absent.",
    ],
    "serta_uptier": [
        "Identify if Serta-style non-consensual uptier structure is present or referenced",
        "Review Required Lender threshold and whether majority can subordinate minority",
        "Assess lender-on-lender violence risk and litigation precedent (Serta, Rite Aid).",
    ],
    "incora_wesco_vote_rigging": [
        "Check if Incora/Wesco vote rigging precedent is mentioned or structure is present",
        "Review voting calculation and whether affiliate/sponsor debt is excluded from consent threshold",
        "Assess strategic debt issuance risk and synthetic majority creation.",
    ],
}


def generate_checklist(signals: list[dict[str, Any]]) -> list[str]:
    """
    Build a deduplicated analyst checklist from a list of signals.

    Args:
        signals: List of dicts with at least "type" (str); may include "evidence".

    Returns:
        Ordered list of checklist item strings (no duplicates).
    """
    seen: set[str] = set()
    out = []
    for s in signals:
        stype = (s.get("type") or "").strip().lower()
        if not stype or stype not in SIGNAL_CHECKLISTS:
            continue
        for step in SIGNAL_CHECKLISTS[stype]:
            if step not in seen:
                seen.add(step)
                out.append(step)
    return out

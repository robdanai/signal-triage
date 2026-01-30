"""
Liability Management Exercise (LME) detection in text.
Detects dropdown/guarantee stripping, S-Prime/collateral leakage, uptiering language,
basket_transfer, asset_sale, investment_basket, transfer_to_unrestricted_sub,
structural_subordination, Texas two-step / structural merger, double-dip / triple-dip,
consent solicitation / exchange / tender, equity cure, substantive consolidation / cramdown,
lender voting squeeze (yank-a-bank), forbearance / standstill, crossover / prepack,
make-whole / disallowance, and PIK.
"""

from typing import Any


# Phrases per category (lowercase); substring match in document
LME_PATTERNS = {
    "dropdown": [
        "release of guarantees", "subsidiary guarantee", "restriction on upstream",
        "dividend stopper", "j.crew", "restricted subsidiary", "unrestricted subsidiary",
        "guarantee release", "drop down", "dropdown",
    ],
    "sprime_leakage": [
        "first lien", "second lien", "primed", "priming", "adequate protection",
        "collateral", "security interest", "leakage", "sprime", "s-prime",
    ],
    "uptiering": [
        "uptier", "uptiering", "superpriority", "roll-up", "priming lien",
        "dip", "exit facility", "debtor-in-possession",
    ],
    # Texas two-step / structural merger: divisional merger, two-step, LMT structure
    "texas_two_step": [
        "texas two step", "texas two-step", "two-step", "two step merger",
        "divisional merger", "divisive merger", "liability management transaction",
        "LMT transaction", "split-off", "spin-off", "divisional split",
    ],
    # Double-dip / triple-dip: multiple claims on same economic exposure (empty box, non-guarantor)
    "double_dip_triple_dip": [
        "double dip", "double-dip", "triple dip", "triple-dip",
        "empty box", "non-guarantor subsidiary", "non-guarantor sub",
        "multiple claims on same", "intercompany loan", "double recovery",
    ],
    # Basket / transfer: covenant leakage (asset sale, investment, unrestricted sub transfers)
    "basket_transfer": [
        "asset sale", "asset sale proceeds", "asset sale basket",
        "investment basket", "restricted payment",
        "transfer to unrestricted subsidiary", "sale to unrestricted subsidiary",
        "transfer to unrestricted sub", "proceeds to unrestricted subsidiary",
    ],
    # Asset sale: sale proceeds, asset sale basket (distinct category)
    "asset_sale": [
        "asset sale", "asset sale proceeds", "asset sale basket",
        "sale proceeds", "asset sale covenant",
    ],
    # Investment basket: capacity / usage
    "investment_basket": [
        "investment basket", "investment basket capacity",
        "investment basket usage", "permitted investment basket",
    ],
    # Transfer to unrestricted sub: J.Crew-style leakage
    "transfer_to_unrestricted_sub": [
        "transfer to unrestricted subsidiary", "sale to unrestricted subsidiary",
        "transfer to unrestricted sub", "sale to unrestricted sub",
        "proceeds to unrestricted subsidiary",
    ],
    # Structural subordination: notes subordinated to secured debt
    "structural_subordination": [
        "structural subordination", "structurally subordinated",
        "structurally subordinate", "structural subordination of notes",
        "notes structurally subordinated",
    ],
    # Out-of-court LME: consent solicitation, exchange offer, tender offer
    "consent_solicitation_exchange": [
        "consent solicitation", "consent payment", "exchange offer",
        "tender offer", "solicitation of consents", "amend and extend",
        "amend & extend", "out-of-court restructuring",
    ],
    # Equity cure: covenant cure via equity injection
    "equity_cure": [
        "equity cure", "equity injection", "covenant cure", "equity contribution",
        "cure right", "equity cure right", "cure by equity",
    ],
    # Bankruptcy: substantive consolidation, cramdown
    "substantive_consolidation_cramdown": [
        "substantive consolidation", "substantively consolidated",
        "cramdown", "cram-down", "cram down", "absolute priority",
        "fair and equitable", "plan confirmation",
    ],
    # Lender voting / amendment squeeze: yank-a-bank, required lender, non-consenting
    "lender_voting_squeeze": [
        "yank-a-bank", "yank a bank", "replaceable lender", "required lender",
        "majority lender", "non-consenting lender", "non-consenting",
        "snooze you lose", "snooze-you-lose", "amendment without consent",
        "out-of-the-money lenders",
    ],
    # Forbearance / standstill
    "forbearance_standstill": [
        "forbearance", "forbearance agreement", "standstill", "standstill agreement",
        "forbearance period", "waiver and forbearance",
    ],
    # Crossover / bridge / prepack
    "crossover_prepack": [
        "crossover facility", "crossover financing", "bridge facility",
        "bridge financing", "prepack", "pre-pack", "prepackaged",
        "pre-arranged bankruptcy", "prearranged", "plan support agreement",
    ],
    # Make-whole / claim disallowance
    "make_whole_disallowance": [
        "make-whole", "make whole", "makewhole", "disallowance",
        "claim disallowance", "unmatured interest", "section 502(b)",
    ],
    # Payment-in-kind (distressed indicator)
    "pik": [
        "payment-in-kind", "payment in kind", "PIK interest", "PIK toggle",
        "PIK toggle right", "pay-in-kind", "pay in kind",
    ],
    # Precedent Case Patterns: J.Crew blocker / anti-dropdown
    "jcrew_blocker": [
        "j.crew blocker", "j crew blocker", "anti-dropdown", "ip transfer blocker",
        "envision blocker", "chewy blocker", "blocker on unrestricted",
        "restriction on ip transfer", "ip cannot be transferred to unrestricted",
    ],
    # Precedent: Serta / Rite Aid non-consensual uptier
    "serta_uptier": [
        "serta", "rite aid", "non-consensual uptier", "lender-on-lender violence",
        "majority lender uptier", "non-participating lenders subordinated",
    ],
    # Precedent: Incora / Wesco vote rigging
    "incora_wesco_vote_rigging": [
        "incora", "wesco", "strategic debt issuance", "vote threshold manipulation",
        "artificial lender consent", "synthetic majority", "debt issued to affiliate to manipulate vote",
    ],
}


def detect_lme(text: str) -> list[dict[str, Any]]:
    """
    Detect LME-related language in text.

    Args:
        text: Raw document text.

    Returns:
        List of signals, each with type, label, evidence (snippet), and span (start, end).
    """
    if not text or not text.strip():
        return []

    text_lower = text.lower()
    signals = []

    for signal_type, phrases in LME_PATTERNS.items():
        for phrase in phrases:
            pos = text_lower.find(phrase)
            if pos == -1:
                continue
            # Evidence: extract a short snippet around the match
            start = max(0, pos - 20)
            end = min(len(text), pos + len(phrase) + 20)
            snippet = text[start:end].strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            signals.append({
                "type": signal_type,
                "label": phrase,
                "evidence": snippet,
                "span": (pos, pos + len(phrase)),
            })

    # Deduplicate by (type, label) keeping first occurrence
    seen: set[tuple[str, str]] = set()
    unique = []
    for s in signals:
        key = (s["type"], s["label"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique

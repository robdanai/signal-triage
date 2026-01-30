"""
Trap-Door Mandate: patterns for Structural Leakage.
Maps legal/financial language to basket categories and default signal levels.
"""

import re
from signal_triage.document_intel.schema import SignalLevel

# ----- Section headers (for segmenting) -----
NEGATIVE_COVENANT_HEADERS = [
    r"Article\s+[IVXLC]+[\.\s]*Negative\s+Covenants",
    r"Section\s+\d+\.\d*\s*[\.:]?\s*Negative\s+Covenants",
    r"Negative\s+Covenants",
    r"ARTICLE\s+[IVXLC]+[\.\s]*NEGATIVE\s+COVENANTS",
    r"Restrictive\s+Covenants",
    r"Limitation\s+on\s+.*(?:Dispositions?|Sales?|Investments?)",
]

# ----- Category: Asset Sale Baskets -----
# Dollar limits, sweep (mandatory prepay), collateral
ASSET_SALE_PATTERNS = [
    (r"dispos(e|al|ition)\s+of\s+(?:any\s+)?(?:assets?|property|collateral)", "asset_sale"),
    (r"sale\s+of\s+(?:assets?|property|collateral)", "asset_sale"),
    (r"asset\s+sale\s+basket", "asset_sale"),
    (r"(\$[\d,]+(?:\.\d+)?\s*(?:million|MM|M)?)\s*(?:or\s+)?(?:less|maximum)", "asset_sale"),
    (r"net\s+cash\s+proceeds\s+(?:of\s+)?(?:any\s+)?(?:disposition|sale)", "asset_sale"),
    (r"mandatory\s+(?:prepayment|prepay|sweep)", "asset_sale"),
    (r"100%\s*(?:of\s+)?(?:net\s+)?(?:cash\s+)?proceeds", "asset_sale"),
    (r"sweep\s+(?:of\s+)?(?:proceeds|excess)", "asset_sale"),
    (r"excess\s+cash\s+flow", "asset_sale"),
]

# ----- Category: Unrestricted Subsidiaries (J.Crew / Chewy blockers) -----
UNRESTRICTED_SUBSIDIARY_PATTERNS = [
    (r"unrestricted\s+subsidiary", "unrestricted_subsidiary"),
    (r"investment\s+in\s+(?:an?\s+)?unrestricted", "unrestricted_subsidiary"),
    (r"designat(e|ion)\s+as\s+unrestricted", "unrestricted_subsidiary"),
    (r"restricted\s+subsidiary\s+.*\s+unrestricted", "unrestricted_subsidiary"),
    (r"transfer\s+(?:of\s+)?(?:assets?|property|IP|intellectual\s+property)\s+to\s+(?:an?\s+)?(?:unrestricted|subsidiary)", "unrestricted_subsidiary"),
    (r"basket\s+.*\s+unrestricted", "unrestricted_subsidiary"),
    (r"J\.?\s*Crew|Chewy|dropdown", "unrestricted_subsidiary"),  # structural leakage precedents
]

# ----- Category: Incremental Facilities (Free-and-Clear / Priming) -----
INCREMENTAL_PATTERNS = [
    (r"incremental\s+(?:facility|facilities|debt|amount)", "incremental_facility"),
    (r"free\s+and\s+clear\s+basket", "incremental_facility"),
    (r"priming\s+(?:debt|lien)", "incremental_facility"),
    (r"additional\s+(?:debt|indebtedness)\s+(?:incurred|permitted)", "incremental_facility"),
    (r"incremental\s+equivalent\s+debt", "incremental_facility"),
    (r"amount\s+.*\s+(?:not\s+)?requir(?:e|ing)\s+lender\s+consent", "incremental_facility"),
    (r"(\$[\d,]+(?:\.\d+)?\s*(?:million|MM|M)?)\s*incremental", "incremental_facility"),
    (r"ratio\s+debt\s+capacity|flex\s+basket", "incremental_facility"),
]

# ----- Category: Affiliate Transactions -----
AFFILIATE_PATTERNS = [
    (r"affiliate\s+transaction", "affiliate_transaction"),
    (r"transaction\s+with\s+(?:an?\s+)?affiliate", "affiliate_transaction"),
    (r"management\s+fee(s)?", "affiliate_transaction"),
    (r"dividend\s+recapitalization", "affiliate_transaction"),
    (r"dividend\s+to\s+(?:equity\s+holders?|parent|holdings?)", "affiliate_transaction"),
    (r"upstream\s+(?:dividend|distribution)", "affiliate_transaction"),
    (r"permitted\s+affiliate\s+transaction", "affiliate_transaction"),
    (r"arm\'?s\s+length|arms\s+length", "affiliate_transaction"),
]

# ----- Category: Texas Two-Step / Structural Merger (LME) -----
TEXAS_TWO_STEP_PATTERNS = [
    (r"texas\s+two\s*[- ]?step", "texas_two_step"),
    (r"two\s*[- ]?step\s+(?:merger|restructuring|transaction)", "texas_two_step"),
    (r"divisional\s+merger", "texas_two_step"),
    (r"divisive\s+merger", "texas_two_step"),
    (r"liability\s+management\s+transaction", "texas_two_step"),
    (r"LMT\s+transaction", "texas_two_step"),
    (r"split\s*[- ]?off|spin\s*[- ]?off", "texas_two_step"),
    (r"divisional\s+split", "texas_two_step"),
]

# ----- Category: Double-Dip / Triple-Dip (multi-claim LME) -----
DOUBLE_DIP_TRIPLE_DIP_PATTERNS = [
    (r"double\s*[- ]?dip", "double_dip_triple_dip"),
    (r"triple\s*[- ]?dip", "double_dip_triple_dip"),
    (r"empty\s+box\s+(?:structure|transaction|subsidiary)", "double_dip_triple_dip"),
    (r"non[- ]?guarantor\s+subsidiary", "double_dip_triple_dip"),
    (r"non[- ]?guarantor\s+sub\.?", "double_dip_triple_dip"),
    (r"multiple\s+claims\s+on\s+same\s+(?:collateral|debt|exposure)", "double_dip_triple_dip"),
    (r"double\s+recovery", "double_dip_triple_dip"),
]

# ----- Category: Consent solicitation / Exchange / Tender (out-of-court LME) -----
CONSENT_EXCHANGE_PATTERNS = [
    (r"consent\s+solicitation", "consent_solicitation_exchange"),
    (r"consent\s+payment", "consent_solicitation_exchange"),
    (r"exchange\s+offer", "consent_solicitation_exchange"),
    (r"tender\s+offer", "consent_solicitation_exchange"),
    (r"solicitation\s+of\s+consents", "consent_solicitation_exchange"),
    (r"amend\s+and\s+extend|amend\s*&\s*extend", "consent_solicitation_exchange"),
    (r"out[- ]?of[- ]?court\s+restructuring", "consent_solicitation_exchange"),
]

# ----- Category: Equity cure -----
EQUITY_CURE_PATTERNS = [
    (r"equity\s+cure", "equity_cure"),
    (r"equity\s+injection", "equity_cure"),
    (r"covenant\s+cure", "equity_cure"),
    (r"equity\s+contribution", "equity_cure"),
    (r"cure\s+right", "equity_cure"),
    (r"cure\s+by\s+equity", "equity_cure"),
]

# ----- Category: Substantive consolidation / Cramdown -----
CONSOLIDATION_CRAMDOWN_PATTERNS = [
    (r"substantive\s+consolidation", "substantive_consolidation_cramdown"),
    (r"substantively\s+consolidated", "substantive_consolidation_cramdown"),
    (r"cram\s*[- ]?down", "substantive_consolidation_cramdown"),
    (r"absolute\s+priority", "substantive_consolidation_cramdown"),
    (r"fair\s+and\s+equitable", "substantive_consolidation_cramdown"),
    (r"plan\s+confirmation", "substantive_consolidation_cramdown"),
]

# ----- Category: Lender voting squeeze (yank-a-bank, required lender) -----
LENDER_VOTING_SQUEEZE_PATTERNS = [
    (r"yank[- ]?a[- ]?bank", "lender_voting_squeeze"),
    (r"replaceable\s+lender", "lender_voting_squeeze"),
    (r"required\s+lender", "lender_voting_squeeze"),
    (r"majority\s+lender", "lender_voting_squeeze"),
    (r"non[- ]?consenting\s+lender", "lender_voting_squeeze"),
    (r"snooze\s+you\s+lose|snooze[- ]?you[- ]?lose", "lender_voting_squeeze"),
    (r"amendment\s+without\s+consent", "lender_voting_squeeze"),
    (r"out[- ]?of[- ]?the[- ]?money\s+lenders", "lender_voting_squeeze"),
]

# ----- Category: Forbearance / Standstill -----
FORBEARANCE_STANDSTILL_PATTERNS = [
    (r"\bforbearance\b", "forbearance_standstill"),
    (r"\bstandstill\b", "forbearance_standstill"),
    (r"forbearance\s+agreement", "forbearance_standstill"),
    (r"standstill\s+agreement", "forbearance_standstill"),
    (r"forbearance\s+period", "forbearance_standstill"),
    (r"waiver\s+and\s+forbearance", "forbearance_standstill"),
]

# ----- Category: Crossover / Bridge / Prepack -----
CROSSOVER_PREPACK_PATTERNS = [
    (r"crossover\s+facility", "crossover_prepack"),
    (r"crossover\s+financing", "crossover_prepack"),
    (r"bridge\s+facility", "crossover_prepack"),
    (r"bridge\s+financing", "crossover_prepack"),
    (r"pre[- ]?pack(?:aged)?", "crossover_prepack"),
    (r"pre[- ]?arranged\s+bankruptcy", "crossover_prepack"),
    (r"prearranged", "crossover_prepack"),
    (r"plan\s+support\s+agreement", "crossover_prepack"),
]

# ----- Category: Make-whole / Disallowance -----
MAKE_WHOLE_DISALLOWANCE_PATTERNS = [
    (r"make[- ]?whole", "make_whole_disallowance"),
    (r"makewhole", "make_whole_disallowance"),
    (r"claim\s+disallowance", "make_whole_disallowance"),
    (r"unmatured\s+interest", "make_whole_disallowance"),
    (r"section\s+502\s*\(\s*b\s*\)", "make_whole_disallowance"),
]

# ----- Category: PIK (payment-in-kind) -----
PIK_PATTERNS = [
    (r"payment[- ]?in[- ]?kind", "pik"),
    (r"PIK\s+interest", "pik"),
    (r"PIK\s+toggle", "pik"),
    (r"pay[- ]?in[- ]?kind", "pik"),
]

# ----- Category: EBITDA Add-backs (for covenant forensics) -----
EBITDA_ADDBACK_PATTERNS = [
    (r"run[- ]?rate\s+(?:synergies|savings)", "addback_runrate"),
    (r"anticipated\s+(?:cost\s+)?savings", "addback_anticipated"),
    (r"pro[- ]?forma\s+(?:EBITDA|adjustments?)", "addback_proforma"),
    (r"adjusted\s+EBITDA", "addback_adjusted"),
    (r"one[- ]?time\s+(?:charges?|expenses?)", "addback_onetime"),
    (r"restructuring\s+charges?", "addback_restructuring"),
    (r"stock[- ]?based\s+compensation", "addback_stock_comp"),
    (r"non[- ]?recurring\s+(?:charges?|expenses?)", "addback_nonrecurring"),
]

# ----- Category: Maintenance Covenants (for headroom analysis) -----
MAINTENANCE_COVENANT_PATTERNS = [
    (r"total\s+(?:net\s+)?leverage\s+ratio", "covenant_leverage"),
    (r"first\s+lien\s+leverage", "covenant_first_lien_leverage"),
    (r"secured\s+leverage", "covenant_secured_leverage"),
    (r"fixed\s+charge\s+coverage\s+ratio", "covenant_fccr"),
    (r"interest\s+coverage\s+ratio", "covenant_icr"),
    (r"debt\s+service\s+coverage", "covenant_dscr"),
    (r"(?:shall|must)\s+(?:not\s+)?exceed\s+\d+\.\d+\s*(?:to|:)\s*1\.0", "covenant_threshold"),
    (r"(?:shall|must)\s+(?:be\s+)?(?:at\s+least|greater\s+than)\s+\d+\.\d+\s*(?:to|:)\s*1\.0", "covenant_threshold"),
]

# ----- Category: Incremental Priming Risk (forensic analysis of 50.1% mechanics) -----
PRIMING_MECHANICS_PATTERNS = [
    (r"incremental\s+(?:facility|debt|term\s+loan).*required\s+lenders?", "priming_incremental_required_lender"),
    (r"(?:50|51|majority)\s*%.*(?:amend|modify|consent).*(?:lien|priority|security)", "priming_majority_lien"),
    (r"pari\s+passu.*incremental", "priming_pari_incremental"),
    (r"super[- ]?priority.*(?:without|not\s+requiring).*unanimous", "priming_superpriority_non_unanimous"),
    (r"required\s+lenders?.*(?:may\s+)?(?:amend|modify).*(?:without|not\s+requiring).*unanimous", "priming_required_lender_amendment"),
    (r"incremental.*(?:without|not\s+requiring).*(?:consent\s+of\s+)?(?:all\s+)?lenders", "priming_incremental_no_consent"),
]

# ----- Default signal level by category (can be overridden by language) -----
CATEGORY_DEFAULT_LEVEL = {
    "asset_sale": SignalLevel.MEDIUM,
    "unrestricted_subsidiary": SignalLevel.HIGH,
    "incremental_facility": SignalLevel.MEDIUM,
    "affiliate_transaction": SignalLevel.MEDIUM,
    "texas_two_step": SignalLevel.HIGH,
    "double_dip_triple_dip": SignalLevel.HIGH,
    "consent_solicitation_exchange": SignalLevel.MEDIUM,
    "equity_cure": SignalLevel.MEDIUM,
    "substantive_consolidation_cramdown": SignalLevel.HIGH,
    "lender_voting_squeeze": SignalLevel.HIGH,
    "forbearance_standstill": SignalLevel.MEDIUM,
    "crossover_prepack": SignalLevel.HIGH,
    "make_whole_disallowance": SignalLevel.MEDIUM,
    "pik": SignalLevel.MEDIUM,
    "addback_runrate": SignalLevel.HIGH,
    "addback_anticipated": SignalLevel.HIGH,
    "addback_proforma": SignalLevel.MEDIUM,
    "addback_adjusted": SignalLevel.LOW,
    "addback_onetime": SignalLevel.LOW,
    "addback_restructuring": SignalLevel.LOW,
    "addback_stock_comp": SignalLevel.LOW,
    "addback_nonrecurring": SignalLevel.LOW,
    "covenant_leverage": SignalLevel.MEDIUM,
    "covenant_first_lien_leverage": SignalLevel.MEDIUM,
    "covenant_secured_leverage": SignalLevel.MEDIUM,
    "covenant_fccr": SignalLevel.MEDIUM,
    "covenant_icr": SignalLevel.MEDIUM,
    "covenant_dscr": SignalLevel.MEDIUM,
    "covenant_threshold": SignalLevel.MEDIUM,
    "priming_incremental_required_lender": SignalLevel.HIGH,
    "priming_majority_lien": SignalLevel.HIGH,
    "priming_pari_incremental": SignalLevel.MEDIUM,
    "priming_superpriority_non_unanimous": SignalLevel.HIGH,
    "priming_required_lender_amendment": SignalLevel.HIGH,
    "priming_incremental_no_consent": SignalLevel.HIGH,
}

# ----- Escalators: phrases that push signal to HIGH -----
HIGH_RISK_ESCALATORS = [
    r"without\s+(?:prior\s+)?(?:lender|required)\s+consent",
    r"at\s+the\s+option\s+of\s+the\s+(?:borrower|company)",
    r"sole\s+discretion",
    r"unlimited|uncapped",
    r"in\s+excess\s+of\s+\$[\d,]+(?:\.\d+)?\s*(?:million|MM|M)?",
]

# ----- Double-negative: "shall not ... unless ..." -----
UNLESS_PATTERN = re.compile(
    r"(?:shall\s+not|may\s+not|will\s+not|must\s+not)\s+"
    r"([^.]*?)\s+"
    r"unless\s+([^.]+)",
    re.IGNORECASE | re.DOTALL,
)
# Also: "except ..." and "other than ..."
EXCEPT_PATTERN = re.compile(
    r"(?:shall\s+not|may\s+not)\s+([^.]*?)\s+except\s+(?:to\s+the\s+extent\s+)?([^.]+)",
    re.IGNORECASE | re.DOTALL,
)


def detect_section_header(text: str) -> str | None:
    """Return first matching Negative Covenant section label, else None."""
    for pat in NEGATIVE_COVENANT_HEADERS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None


def find_category_and_snippet(
    text: str, window_before: int = 80, window_after: int = 120
) -> list[tuple[str, str, int]]:
    """
    Scan text for trap-door patterns; return list of (category, snippet, start_pos).
    """
    results: list[tuple[str, str, int]] = []
    text_lower = text.lower()
    combined: list[tuple[str, str]] = (
        ASSET_SALE_PATTERNS
        + UNRESTRICTED_SUBSIDIARY_PATTERNS
        + INCREMENTAL_PATTERNS
        + AFFILIATE_PATTERNS
        + TEXAS_TWO_STEP_PATTERNS
        + DOUBLE_DIP_TRIPLE_DIP_PATTERNS
        + CONSENT_EXCHANGE_PATTERNS
        + EQUITY_CURE_PATTERNS
        + CONSOLIDATION_CRAMDOWN_PATTERNS
        + LENDER_VOTING_SQUEEZE_PATTERNS
        + FORBEARANCE_STANDSTILL_PATTERNS
        + CROSSOVER_PREPACK_PATTERNS
        + MAKE_WHOLE_DISALLOWANCE_PATTERNS
        + PIK_PATTERNS
        + EBITDA_ADDBACK_PATTERNS
        + MAINTENANCE_COVENANT_PATTERNS
        + PRIMING_MECHANICS_PATTERNS
    )
    for pattern, category in combined:
        for m in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            start = max(0, m.start() - window_before)
            end = min(len(text), m.end() + window_after)
            snippet = text[start:end].replace("\n", " ").strip()
            snippet = " ".join(snippet.split())
            if len(snippet) > 50:
                results.append((category, snippet, m.start()))
    return results


def clarify_double_negative(snippet: str) -> str | None:
    """
    Apply Double-Negative Rule: if clause says "shall not X unless Y", return what IS permitted.
    """
    for pat, name in [(UNLESS_PATTERN, "unless"), (EXCEPT_PATTERN, "except")]:
        m = pat.search(snippet)
        if m:
            prohibited = m.group(1).strip()
            exception = m.group(2).strip()
            # Truncate long exception
            if len(exception) > 200:
                exception = exception[:197] + "..."
            return f"Permitted when: {exception}"
    return None


def resolve_signal_level(category: str, snippet: str) -> SignalLevel:
    """Default level for category; escalate to HIGH if escalator phrase found."""
    level = CATEGORY_DEFAULT_LEVEL.get(category, SignalLevel.MEDIUM)
    snippet_lower = snippet.lower()
    for esc in HIGH_RISK_ESCALATORS:
        if re.search(esc, snippet_lower):
            return SignalLevel.HIGH
    return level


def extract_dollar_limit(snippet: str) -> str | None:
    """Heuristic: pull $ amount or percentage from snippet."""
    m = re.search(r"\$[\d,]+(?:\.\d+)?\s*(?:million|MM|M|%)?", snippet)
    if m:
        return m.group(0).strip()
    m = re.search(r"\d+(?:\.\d+)?\s*%\s+of\s+[^\s,]+(?:\s+[^\s,]+)?", snippet, re.IGNORECASE)
    if m:
        return m.group(0).strip()
    return None


def extract_sweep_language(snippet: str) -> str | None:
    """Heuristic: mandatory prepay / sweep of proceeds."""
    if re.search(r"100%\s*(?:of\s+)?(?:net\s+)?(?:cash\s+)?proceeds", snippet, re.IGNORECASE):
        return "100% of net cash proceeds (sweep)"
    if re.search(r"mandatory\s+(?:prepay|sweep)", snippet, re.IGNORECASE):
        return "Mandatory prepayment/sweep"
    if re.search(r"excess\s+cash\s+flow", snippet, re.IGNORECASE):
        return "Excess cash flow sweep"
    return None


def analyze_priming_risk(baskets: list, amendment_snippets: list[str]) -> dict:
    """
    Forensic analysis: assess incremental facility priming risk.

    Incremental priming risk is HIGH when:
    1. Incremental facility basket exists (or is uncapped / large), AND
    2. Amendment provisions allow Required Lenders (>50%) to amend lien priority or
       issue superpriority debt without unanimous consent.

    Args:
        baskets: List of ExtractedBasket or dict with "category", "dollar_limit", "signal_level".
        amendment_snippets: List of text snippets from amendment / consent sections.

    Returns:
        Dict with priming_risk_level ("high" / "medium" / "low"), incremental_basket_present (bool),
        majority_can_prime (bool), consent_threshold (str), risk_note (str).
    """
    # Check for incremental facility basket
    incremental_basket_present = False
    incremental_basket_limit = None
    for b in baskets:
        cat = b.get("category", "") if isinstance(b, dict) else getattr(b, "category", "")
        if cat == "incremental_facility":
            incremental_basket_present = True
            lim = b.get("dollar_limit", None) if isinstance(b, dict) else getattr(b, "dollar_limit", None)
            if lim:
                incremental_basket_limit = lim
            break

    # Check amendment provisions for majority / Required Lender language
    majority_can_prime = False
    consent_threshold = "Unknown"
    for snippet in amendment_snippets:
        if re.search(
            r"required\s+lenders?.*(?:may\s+)?(?:amend|modify|consent).*(?:lien|priority|incremental)",
            snippet,
            re.IGNORECASE,
        ):
            majority_can_prime = True
            consent_threshold = "Required Lenders (>50%)"
            break
        if re.search(
            r"(?:50|51|majority)\s*%.*(?:amend|modify|consent).*(?:lien|priority|security)",
            snippet,
            re.IGNORECASE,
        ):
            majority_can_prime = True
            consent_threshold = "Majority (>50%)"
            break
        if re.search(
            r"super[- ]?priority.*(?:without|not\s+requiring).*unanimous",
            snippet,
            re.IGNORECASE,
        ):
            majority_can_prime = True
            consent_threshold = "Non-unanimous (superpriority allowed)"
            break

    # Risk assessment
    if incremental_basket_present and majority_can_prime:
        risk_level = "high"
        risk_note = f"Incremental facility basket present (limit: {incremental_basket_limit or 'uncapped'}); {consent_threshold} can issue superpriority debt and prime minority lenders without unanimous consent (Serta-style risk)."
    elif incremental_basket_present:
        risk_level = "medium"
        risk_note = f"Incremental facility basket present (limit: {incremental_basket_limit or 'uncapped'}); consent threshold for priming not clearly identified as majority-only."
    elif majority_can_prime:
        risk_level = "medium"
        risk_note = f"{consent_threshold} can amend priority; no explicit incremental basket detected but amendment risk exists."
    else:
        risk_level = "low"
        risk_note = "No incremental facility basket or majority-can-prime language detected."

    return {
        "priming_risk_level": risk_level,
        "incremental_basket_present": incremental_basket_present,
        "incremental_basket_limit": incremental_basket_limit,
        "majority_can_prime": majority_can_prime,
        "consent_threshold": consent_threshold,
        "risk_note": risk_note,
    }

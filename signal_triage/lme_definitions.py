"""
Structured definitions for LME and distress signal categories.
Used by CLI, reporter, and checklist to show "what this means" when a signal fires.
See docs/LME_CATEGORIES.md for full in-depth definitions and rationale.
"""

from dataclasses import dataclass
from typing import Optional

# Severity: how material the risk is for credit/recovery (for triage and reporting)
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

# Market tier: Institutional Restructuring Desk classification (Tight/Market/Toxic)
# - TIGHT: Borrower-friendly but within market (e.g. large baskets, PIK toggle)
# - MARKET: Standard/balanced (e.g. typical asset sale sweep, equity cure with cap)
# - TOXIC: Lender predatory or covenant-light (e.g. yank-a-bank, no make-whole, vote rigging)
MARKET_TIER_TIGHT = "tight"
MARKET_TIER_MARKET = "market"
MARKET_TIER_TOXIC = "toxic"


@dataclass(frozen=True)
class CategoryDefinition:
    """Single category: display name, short definition, rationale, severity, market tier."""

    id: str
    display_name: str
    definition: str
    rationale: str
    severity: str
    market_tier: str  # "tight" / "market" / "toxic"
    related_ids: tuple[str, ...] = ()


# All LME and related signal categories with in-depth definitions.
# Keys must match LME_PATTERNS keys in lme_parser.py and signal ids in signals_config.json.
LME_DEFINITIONS: dict[str, CategoryDefinition] = {
    "dropdown": CategoryDefinition(
        id="dropdown",
        display_name="Dropdown / guarantee release",
        definition="Transfer of valuable assets (e.g. IP, brand) from guarantor subsidiaries into unrestricted subsidiaries, or release of subsidiary guarantees. Value can then be pledged to new debt without sharing with existing lenders.",
        rationale="Reduces collateral and guarantee coverage; precedent (J.Crew, Chewy) established material leakage risk.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TIGHT,  # Tight when enabled; toxic when abused (J.Crew)
        related_ids=("transfer_to_unrestricted_sub", "basket_transfer", "sprime_leakage"),
    ),
    "sprime_leakage": CategoryDefinition(
        id="sprime_leakage",
        display_name="S-Prime / collateral leakage",
        definition="Second-lien or junior debt primed ahead of existing secured creditors on the same collateral, or any covenant/structural feature that allows value to leave the secured group (e.g. incremental debt, asset transfers).",
        rationale="First-lien recovery depends on collateral coverage and lien priority; priming or leakage dilutes recovery.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TIGHT,  # Tight if incremental baskets are capped; toxic if uncapped/abused
        related_ids=("uptiering", "dropdown"),
    ),
    "uptiering": CategoryDefinition(
        id="uptiering",
        display_name="Uptiering",
        definition="Amendment or exchange where participating lenders consent to new debt ranking above existing debt (superpriority, priming lien, roll-up). Non-participating lenders are left junior without consent.",
        rationale="Non-participating lenders are structurally subordinated; recovery drops. Litigation risk (e.g. Serta) is high.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic: lender-on-lender violence
        related_ids=("sprime_leakage", "lender_voting_squeeze", "crossover_prepack"),
    ),
    "texas_two_step": CategoryDefinition(
        id="texas_two_step",
        display_name="Texas two-step / structural merger",
        definition="Restructuring using a divisional or divisive merger to separate liabilities from operating assets (e.g. mass tort in one entity, ops in another). More generally, two-step or LMT structures that reshape entities to change which assets back which creditors.",
        rationale="Creditors of the operating company may find claims tied to an entity separated from valuable operations.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic: structural creditor evasion
        related_ids=("substantive_consolidation_cramdown", "crossover_prepack"),
    ),
    "double_dip_triple_dip": CategoryDefinition(
        id="double_dip_triple_dip",
        display_name="Double-dip / triple-dip",
        definition="Structure creating multiple claims on the same economic exposure: e.g. loan to non-guarantor (empty-box) sub, intercompany loan to guarantor, and parent guarantee. Same value supports two or three claims at different levels.",
        rationale="Existing lenders share collateral with new claims; recovery diluted; non-participating lenders disadvantaged.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic: dilution without consent
        related_ids=("uptiering", "consent_solicitation_exchange", "structural_subordination"),
    ),
    "basket_transfer": CategoryDefinition(
        id="basket_transfer",
        display_name="Basket / transfer",
        definition="Use of covenant baskets (asset sale, investment, restricted payment) to move value—especially to unrestricted subsidiaries—so proceeds or assets leave the secured group. Mechanical path for many dropdowns.",
        rationale="Baskets define how much leakage is permitted; large or uncapped baskets create material leakage risk.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_MARKET,  # Market if balanced; tight if large
        related_ids=("asset_sale", "investment_basket", "transfer_to_unrestricted_sub", "dropdown"),
    ),
    "asset_sale": CategoryDefinition(
        id="asset_sale",
        display_name="Asset sale",
        definition="Covenant and document language governing dispositions: permitted baskets, mandatory prepayment (sweep) of proceeds, and use of proceeds (reinvestment, paydown, or leakage to unrestricted subs).",
        rationale="Asset sale proceeds are a key paydown source; weak sweep or broad leakage baskets reduce recovery.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_MARKET,  # Market for 100% sweep; tight for <100%
        related_ids=("basket_transfer", "transfer_to_unrestricted_sub"),
    ),
    "investment_basket": CategoryDefinition(
        id="investment_basket",
        display_name="Investment basket",
        definition="Covenant exception permitting investments (including in unrestricted subsidiaries) up to a dollar cap or formula. Capacity and usage determine how much value can move outside the secured group.",
        rationale="Investments in unrestricted subs or non-collateral assets transfer value out of the secured group.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_MARKET,  # Market if capped; tight if large
        related_ids=("basket_transfer", "transfer_to_unrestricted_sub", "dropdown"),
    ),
    "transfer_to_unrestricted_sub": CategoryDefinition(
        id="transfer_to_unrestricted_sub",
        display_name="Transfer to unrestricted subsidiary",
        definition="Explicit transfer or sale of assets or proceeds to an unrestricted subsidiary. Operational step in a J.Crew-style move: value is moved into an entity that can pledge to new lenders.",
        rationale="Directly reduces collateral and guarantee coverage for existing lenders.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TIGHT,  # Tight when enabled; toxic when abused
        related_ids=("dropdown", "basket_transfer", "asset_sale", "investment_basket"),
    ),
    "structural_subordination": CategoryDefinition(
        id="structural_subordination",
        display_name="Structural subordination",
        definition="Notes or other claims rank behind others by structure, not contract: e.g. notes at holdco with no assets other than equity in opcos that have their own secured debt. In default, opco assets go to opco creditors first.",
        rationale="Noteholders recover only after secured and subsidiary-level debt; recovery more volatile and typically lower.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_MARKET,  # Market: standard for unsecured notes
        related_ids=("sprime_leakage", "uptiering", "double_dip_triple_dip"),
    ),
    "consent_solicitation_exchange": CategoryDefinition(
        id="consent_solicitation_exchange",
        display_name="Consent solicitation / exchange / tender",
        definition="Out-of-court LME tools: consent solicitation (amendments for consent payment), exchange offer (new debt for old), tender offer (cash repurchase), amend-and-extend. Change economics and priority without bankruptcy.",
        rationale="Non-participating holders may be left with worse terms or subordinated claims; consent thresholds drive litigation risk.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_MARKET,  # Market: standard restructuring tool
        related_ids=("uptiering", "lender_voting_squeeze", "forbearance_standstill"),
    ),
    "equity_cure": CategoryDefinition(
        id="equity_cure",
        display_name="Equity cure",
        definition="Right for borrower or sponsor to inject equity (or equity-like contribution) to cure a covenant breach and avoid default. Often limited by frequency and dollar cap.",
        rationale="Extends runway but overuse signals covenant pressure; uncapped cures can mask deterioration.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_MARKET,  # Market if capped (2x in life); tight if uncapped
        related_ids=("liquidity_covenant", "forbearance_standstill"),
    ),
    "substantive_consolidation_cramdown": CategoryDefinition(
        id="substantive_consolidation_cramdown",
        display_name="Substantive consolidation / cramdown",
        definition="Substantive consolidation: merging related entities' assets and liabilities in bankruptcy. Cramdown: confirming a Ch. 11 plan over objection, subject to absolute priority and fair and equitable. Plan confirmation binds all parties.",
        rationale="Consolidation can reorder recovery; cramdown determines whether holdouts are bound and how value is allocated.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_MARKET,  # Market: standard Ch. 11 mechanism
        related_ids=("texas_two_step", "crossover_prepack", "make_whole_disallowance"),
    ),
    "lender_voting_squeeze": CategoryDefinition(
        id="lender_voting_squeeze",
        display_name="Lender voting squeeze",
        definition="Document mechanics allowing majority or required lenders to amend terms without consent of non-consenting or out-of-the-money lenders. Yank-a-bank (replace lender to reach threshold), snooze-you-lose (deem consent).",
        rationale="Minority or holdout lenders can be structurally subordinated or diluted without consent.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic: enables non-consensual subordination
        related_ids=("uptiering", "consent_solicitation_exchange"),
    ),
    "forbearance_standstill": CategoryDefinition(
        id="forbearance_standstill",
        display_name="Forbearance / standstill",
        definition="Forbearance: lenders agree not to exercise remedies (e.g. acceleration) for a period despite default. Standstill: agreement to refrain from enforcing or suing for a defined period. Used to buy time for restructuring or sale.",
        rationale="Indicates existing or imminent default and workout mode; length and scope affect runway.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_MARKET,  # Market: standard workout tool
        related_ids=("potential_default", "liquidity_covenant", "crossover_prepack"),
    ),
    "crossover_prepack": CategoryDefinition(
        id="crossover_prepack",
        display_name="Crossover / bridge / prepack",
        definition="Crossover facility: financing intended to cross from out-of-court into Ch. 11 (e.g. roll into DIP). Bridge facility: short-term financing to bankruptcy or refinancing. Prepack: plan agreed before filing. Plan support agreement: creditors agree to support a plan.",
        rationale="Indicates contemplated or agreed bankruptcy path; affects who funds in Ch. 11 and recovery for consenting vs non-consenting.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_MARKET,  # Market: standard Ch. 11 financing
        related_ids=("uptiering", "substantive_consolidation_cramdown", "forbearance_standstill"),
    ),
    "make_whole_disallowance": CategoryDefinition(
        id="make_whole_disallowance",
        display_name="Make-whole / disallowance",
        definition="Make-whole: premium on early redemption or acceleration. In bankruptcy, whether it is allowed as a claim. Disallowance: § 502(b) and case law limit unmatured interest and sometimes make-whole; claim disallowance reduces recovery.",
        rationale="Make-whole can be a large part of claim; disallowance (e.g. Townsend) can significantly reduce recovery.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic when disallowed (creditor harm)
        related_ids=("substantive_consolidation_cramdown", "potential_default"),
    ),
    "pik": CategoryDefinition(
        id="pik",
        display_name="Payment-in-kind (PIK)",
        definition="Interest paid in kind (added to principal or in additional notes) rather than in cash. PIK toggle: borrower's right to elect PIK instead of cash interest, often when covenant headroom is tight.",
        rationale="PIK and PIK toggle are common in stressed structures; election signals liquidity or covenant pressure and increases leverage.",
        severity=SEVERITY_MEDIUM,
        market_tier=MARKET_TIER_TIGHT,  # Tight: borrower-friendly distress indicator
        related_ids=("liquidity_covenant", "debt_maturity_refinancing", "equity_cure"),
    ),
    "jcrew_blocker": CategoryDefinition(
        id="jcrew_blocker",
        display_name="J.Crew blocker / anti-dropdown",
        definition="Covenant provision restricting transfer of IP or key assets to unrestricted subsidiaries. Named after J.Crew (2017) where absence of such blocker allowed $250M IP dropdown. Envision, Chewy, and others had similar structures; the presence of a blocker protects lenders from value leakage.",
        rationale="Blocker protects lenders from dropdown / guarantee stripping; absence is a critical vulnerability.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_MARKET,  # Market when present; toxic when absent
        related_ids=("dropdown", "transfer_to_unrestricted_sub", "basket_transfer"),
    ),
    "serta_uptier": CategoryDefinition(
        id="serta_uptier",
        display_name="Serta / Rite Aid uptier (non-consensual)",
        definition="Non-consensual uptier where majority lenders (>50%) amend credit agreement to issue new super-priority debt, subordinating minority lenders without their consent. Named after Serta Simmons (2020) and Rite Aid (2020). Often relies on 'Required Lenders' amendment threshold and roll-up of existing debt into new senior facility.",
        rationale="Minority lenders are structurally subordinated; recovery drops; 'lender-on-lender violence' and litigation risk.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic: precedent for non-consensual subordination
        related_ids=("uptiering", "lender_voting_squeeze", "sprime_leakage"),
    ),
    "incora_wesco_vote_rigging": CategoryDefinition(
        id="incora_wesco_vote_rigging",
        display_name="Incora / Wesco vote rigging",
        definition="Strategic debt issuance to affiliates or friendly parties to manipulate voting thresholds and achieve 'synthetic majority' for amendments. Named after Incora (Wesco Aircraft, 2020) where issuer issued debt to sponsor to reach >50% consent threshold. Exploit: if voting calculation does not exclude affiliate/sponsor debt, issuer can artificially create consent.",
        rationale="Non-participating lenders are forced into amendments or subordination via vote manipulation; undermines creditor protections.",
        severity=SEVERITY_HIGH,
        market_tier=MARKET_TIER_TOXIC,  # Toxic: vote manipulation
        related_ids=("lender_voting_squeeze", "uptiering", "consent_solicitation_exchange"),
    ),
}


def get_definition(category_id: str) -> Optional[CategoryDefinition]:
    """Return the definition for a category id, or None if unknown."""
    return LME_DEFINITIONS.get(category_id.strip().lower())


def get_all_category_ids() -> list[str]:
    """Return all defined category ids in a stable order."""
    return sorted(LME_DEFINITIONS.keys())

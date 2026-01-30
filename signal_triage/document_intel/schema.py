"""
Structured output for the Distressed Librarian.
JSON-serializable for Quant Agent / Recovery Waterfall integration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SignalLevel(str, Enum):
    """Risk tier for triage and Quant Agent."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ExtractedBasket:
    """
    A single extracted basket or covenant clause with citation and clarification.
    Every basket must include Section Number and Page Number from source when available.
    """

    category: str  # asset_sale | unrestricted_subsidiary | incremental_facility | affiliate_transaction
    section_number: str | None  # e.g. "7.05", "Article VII"
    page_number: int | None  # from source PDF
    evidence_snippet: str  # quoted text
    signal_level: SignalLevel
    permitted_clarification: str | None  # Double-negative rule: what IS permitted
    dollar_limit: str | None  # e.g. "$10,000,000", "10% of Consolidated EBITDA"
    sweep_requirement: str | None  # for asset sales: mandatory prepay / sweep
    raw_section_label: str | None = None  # full heading if known

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "section_number": self.section_number,
            "page_number": self.page_number,
            "evidence_snippet": self.evidence_snippet,
            "signal_level": self.signal_level.value,
            "permitted_clarification": self.permitted_clarification,
            "dollar_limit": self.dollar_limit,
            "sweep_requirement": self.sweep_requirement,
            "raw_section_label": self.raw_section_label,
        }


@dataclass
class ExtractionResult:
    """Full output for one document: segments + extracted baskets + priming risk."""

    source_path: str | None = None
    segments: list[dict[str, Any]] = field(default_factory=list)  # section_label, start, end, page
    baskets: list[ExtractedBasket] = field(default_factory=list)
    priming_risk: dict[str, Any] | None = None  # NEW: from analyze_priming_risk()
    metadata: dict[str, Any] = field(default_factory=dict)

    def collateral_leakage_flags(self) -> list[dict[str, Any]]:
        """
        Baskets that represent material leakage risk for the Quant: HIGH (or MEDIUM) with dollar_limit,
        or structural LME categories (unrestricted_subsidiary, texas_two_step, double_dip_triple_dip).
        Emitted in JSON so Quant can apply LME-adjusted collateral in the waterfall.
        """
        structural_leakage_categories = {
            "unrestricted_subsidiary", "texas_two_step", "double_dip_triple_dip",
            "substantive_consolidation_cramdown", "crossover_prepack",
        }
        out = []
        for b in self.baskets:
            if b.signal_level in (SignalLevel.HIGH, SignalLevel.MEDIUM) and (
                b.dollar_limit or b.category in structural_leakage_categories
            ):
                out.append({
                    "category": b.category,
                    "section_number": b.section_number,
                    "page_number": b.page_number,
                    "dollar_limit": b.dollar_limit,
                    "signal_level": b.signal_level.value,
                    "evidence_snippet": (b.evidence_snippet or "")[:200],
                })
        return out

    def to_dict(self) -> dict[str, Any]:
        out = {
            "source_path": self.source_path,
            "segments": self.segments,
            "baskets": [b.to_dict() for b in self.baskets],
            "collateral_leakage_flags": self.collateral_leakage_flags(),
            "metadata": self.metadata,
        }
        if self.priming_risk is not None:
            out["priming_risk"] = self.priming_risk
        return out

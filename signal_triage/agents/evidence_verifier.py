"""
Evidence Verifier agent: ensures every signal has a cited snippet.

Checks that each signal/basket includes non-empty evidence text and, when applicable,
section or page provenance. Used after extraction or scoring to validate analyst-facing outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from signal_triage.document_intel.schema import ExtractedBasket, ExtractionResult


@dataclass
class VerificationItem:
    """Result of verifying a single signal/basket."""

    index: int
    verified: bool
    reason: str  # e.g. "has evidence and section" or "missing evidence_snippet"
    evidence_preview: str  # first N chars of evidence for reporting


@dataclass
class VerificationResult:
    """Result of running the Evidence Verifier on a set of signals."""

    all_verified: bool
    total: int
    verified_count: int
    items: list[VerificationItem] = field(default_factory=list)
    missing_indices: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_verified": self.all_verified,
            "total": self.total,
            "verified_count": self.verified_count,
            "missing_indices": self.missing_indices,
            "items": [
                {
                    "index": i.index,
                    "verified": i.verified,
                    "reason": i.reason,
                    "evidence_preview": i.evidence_preview,
                }
                for i in self.items
            ],
        }


def _evidence_from_basket(basket: ExtractedBasket) -> str:
    """Return evidence text from an ExtractedBasket."""
    return (basket.evidence_snippet or "").strip()


def _evidence_from_signal_dict(s: dict[str, Any]) -> str:
    """Return evidence text from a generic signal dict (evidence_snippet or evidence)."""
    return (s.get("evidence_snippet") or s.get("evidence") or "").strip()


def verify_basket(basket: ExtractedBasket, index: int, require_section_or_page: bool = False) -> VerificationItem:
    """
    Verify a single ExtractedBasket has a cited snippet.

    Args:
        basket: One extracted basket from document_intel.
        index: Zero-based index for reporting.
        require_section_or_page: If True, also require section_number or page_number for PDF-derived docs.

    Returns:
        VerificationItem with verified flag and reason.
    """
    evidence = _evidence_from_basket(basket)
    if not evidence:
        return VerificationItem(
            index=index,
            verified=False,
            reason="missing evidence_snippet",
            evidence_preview="",
        )
    if require_section_or_page and basket.section_number is None and basket.page_number is None:
        return VerificationItem(
            index=index,
            verified=False,
            reason="evidence present but missing section_number and page_number (provenance)",
            evidence_preview=evidence[:120] + ("..." if len(evidence) > 120 else ""),
        )
    has_sec = basket.section_number is not None
    has_page = basket.page_number is not None
    reason = "has evidence" + (" and section" if has_sec else "") + (" and page" if has_page else "")
    return VerificationItem(
        index=index,
        verified=True,
        reason=reason,
        evidence_preview=evidence[:120] + ("..." if len(evidence) > 120 else ""),
    )


def verify_baskets(
    baskets: list[ExtractedBasket],
    *,
    require_section_or_page: bool = False,
) -> VerificationResult:
    """
    Verify that every ExtractedBasket has a cited snippet.

    Args:
        baskets: List of extracted baskets (e.g. from ExtractionResult.baskets).
        require_section_or_page: If True, also require section_number or page_number.

    Returns:
        VerificationResult with per-item results and summary.
    """
    items: list[VerificationItem] = []
    missing_indices: list[int] = []
    for i, b in enumerate(baskets):
        vi = verify_basket(b, i, require_section_or_page=require_section_or_page)
        items.append(vi)
        if not vi.verified:
            missing_indices.append(i)
    verified_count = len(baskets) - len(missing_indices)
    return VerificationResult(
        all_verified=len(missing_indices) == 0,
        total=len(baskets),
        verified_count=verified_count,
        items=items,
        missing_indices=missing_indices,
    )


def verify_extraction(
    extraction: ExtractionResult,
    *,
    require_section_or_page: bool = False,
) -> VerificationResult:
    """
    Verify all baskets in an ExtractionResult have citations.

    Args:
        extraction: Full extraction result from document_intel.
        require_section_or_page: If True, require section or page for each basket.

    Returns:
        VerificationResult for extraction.baskets.
    """
    return verify_baskets(
        extraction.baskets,
        require_section_or_page=require_section_or_page,
    )


def verify_signal_dict(s: dict[str, Any], index: int) -> VerificationItem:
    """
    Verify a single signal dict (e.g. from analyzer or signals_io) has evidence.

    Expects keys 'evidence_snippet' or 'evidence'. Section/page are optional.
    """
    evidence = _evidence_from_signal_dict(s)
    if not evidence:
        return VerificationItem(
            index=index,
            verified=False,
            reason="missing evidence_snippet / evidence",
            evidence_preview="",
        )
    return VerificationItem(
        index=index,
        verified=True,
        reason="has evidence",
        evidence_preview=evidence[:120] + ("..." if len(evidence) > 120 else ""),
    )


def verify_signals(signals: list[dict[str, Any]]) -> VerificationResult:
    """
    Verify that every signal dict has a cited snippet (evidence_snippet or evidence).

    Use for analyzer-style signals (lme_signals, covenant_signals) or trap_doors from signals_io.

    Args:
        signals: List of dicts with at least 'evidence_snippet' or 'evidence'.

    Returns:
        VerificationResult with per-item results and summary.
    """
    items: list[VerificationItem] = []
    missing_indices: list[int] = []
    for i, s in enumerate(signals):
        vi = verify_signal_dict(s, i)
        items.append(vi)
        if not vi.verified:
            missing_indices.append(i)
    verified_count = len(signals) - len(missing_indices)
    return VerificationResult(
        all_verified=len(missing_indices) == 0,
        total=len(signals),
        verified_count=verified_count,
        items=items,
        missing_indices=missing_indices,
    )


def run_evidence_verifier(
    baskets: list[ExtractedBasket] | None = None,
    extraction: ExtractionResult | None = None,
    signals: list[dict[str, Any]] | None = None,
    *,
    require_section_or_page: bool = False,
) -> VerificationResult:
    """
    Run the Evidence Verifier on baskets, an extraction result, or generic signal dicts.

    Exactly one of baskets, extraction, or signals must be provided.

    Args:
        baskets: Optional list of ExtractedBasket to verify.
        extraction: Optional ExtractionResult; verifies extraction.baskets.
        signals: Optional list of signal dicts (evidence_snippet or evidence).
        require_section_or_page: When verifying baskets, require section or page provenance.

    Returns:
        VerificationResult with all_verified, counts, and per-item details.

    Raises:
        ValueError: If none or more than one of baskets/extraction/signals is provided.
    """
    if sum([baskets is not None, extraction is not None, signals is not None]) != 1:
        raise ValueError("Exactly one of baskets, extraction, or signals must be provided.")
    if baskets is not None:
        return verify_baskets(baskets, require_section_or_page=require_section_or_page)
    if extraction is not None:
        return verify_extraction(extraction, require_section_or_page=require_section_or_page)
    return verify_signals(signals or [])

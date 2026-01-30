"""
Tests for Evidence Verifier agent: ensures every signal has a cited snippet.
"""

import pytest

from signal_triage.document_intel.schema import ExtractedBasket, ExtractionResult, SignalLevel
from signal_triage.agents.evidence_verifier import (
    VerificationItem,
    VerificationResult,
    run_evidence_verifier,
    verify_basket,
    verify_baskets,
    verify_extraction,
    verify_signal_dict,
    verify_signals,
)


def _basket(evidence_snippet: str, section_number: str | None = None, page_number: int | None = None) -> ExtractedBasket:
    return ExtractedBasket(
        category="asset_sale",
        section_number=section_number,
        page_number=page_number,
        evidence_snippet=evidence_snippet,
        signal_level=SignalLevel.MEDIUM,
        permitted_clarification=None,
        dollar_limit=None,
        sweep_requirement=None,
        raw_section_label=None,
    )


def test_verify_basket_has_evidence():
    b = _basket("Disposition of assets up to $5 million.", section_number="7.05", page_number=12)
    vi = verify_basket(b, 0)
    assert vi.verified is True
    assert "evidence" in vi.reason.lower()
    assert vi.evidence_preview


def test_verify_basket_missing_evidence():
    b = _basket("")
    vi = verify_basket(b, 0)
    assert vi.verified is False
    assert "missing" in vi.reason.lower()
    assert vi.evidence_preview == ""


def test_verify_basket_whitespace_only_evidence():
    b = _basket("   \n  ")
    vi = verify_basket(b, 0)
    assert vi.verified is False


def test_verify_basket_require_section_or_page():
    b = _basket("Some text.", section_number=None, page_number=None)
    vi = verify_basket(b, 0, require_section_or_page=True)
    assert vi.verified is False
    assert "provenance" in vi.reason.lower() or "section" in vi.reason.lower()

    b_with_sec = _basket("Some text.", section_number="7.05", page_number=None)
    vi2 = verify_basket(b_with_sec, 0, require_section_or_page=True)
    assert vi2.verified is True

    b_with_page = _basket("Some text.", section_number=None, page_number=5)
    vi3 = verify_basket(b_with_page, 0, require_section_or_page=True)
    assert vi3.verified is True


def test_verify_baskets_all_verified():
    baskets = [
        _basket("Snippet A", section_number="7.01"),
        _basket("Snippet B", page_number=3),
    ]
    result = verify_baskets(baskets)
    assert isinstance(result, VerificationResult)
    assert result.all_verified is True
    assert result.total == 2
    assert result.verified_count == 2
    assert result.missing_indices == []
    assert len(result.items) == 2
    assert all(i.verified for i in result.items)


def test_verify_baskets_some_missing():
    baskets = [
        _basket("Snippet A"),
        _basket(""),
        _basket("Snippet C"),
    ]
    result = verify_baskets(baskets)
    assert result.all_verified is False
    assert result.total == 3
    assert result.verified_count == 2
    assert result.missing_indices == [1]
    assert result.items[1].verified is False


def test_verify_extraction():
    extraction = ExtractionResult(
        source_path="/tmp/doc.txt",
        segments=[],
        baskets=[
            _basket("Evidence here.", section_number="8.01"),
        ],
        metadata={},
    )
    result = verify_extraction(extraction)
    assert result.all_verified is True
    assert result.total == 1


def test_verify_signal_dict_has_evidence():
    s = {"type": "covenant_risk", "evidence": "covenant breach language"}
    vi = verify_signal_dict(s, 0)
    assert vi.verified is True
    assert "evidence" in vi.reason.lower()


def test_verify_signal_dict_evidence_snippet_key():
    s = {"type": "trap_door", "evidence_snippet": "disposition of assets"}
    vi = verify_signal_dict(s, 0)
    assert vi.verified is True


def test_verify_signal_dict_missing_evidence():
    s = {"type": "covenant_risk"}
    vi = verify_signal_dict(s, 0)
    assert vi.verified is False
    assert vi.evidence_preview == ""


def test_verify_signals():
    signals = [
        {"type": "a", "evidence": "text one"},
        {"type": "b", "evidence_snippet": "text two"},
        {"type": "c"},
    ]
    result = verify_signals(signals)
    assert result.all_verified is False
    assert result.total == 3
    assert result.verified_count == 2
    assert result.missing_indices == [2]


def test_run_evidence_verifier_with_baskets():
    baskets = [_basket("Cite me.")]
    result = run_evidence_verifier(baskets=baskets)
    assert result.all_verified is True
    assert result.total == 1


def test_run_evidence_verifier_with_extraction():
    extraction = ExtractionResult(source_path=None, segments=[], baskets=[_basket("Snippet.")], metadata={})
    result = run_evidence_verifier(extraction=extraction)
    assert result.all_verified is True


def test_run_evidence_verifier_with_signals():
    result = run_evidence_verifier(signals=[{"evidence": "ok"}])
    assert result.all_verified is True


def test_run_evidence_verifier_requires_exactly_one():
    with pytest.raises(ValueError, match="Exactly one"):
        run_evidence_verifier()
    with pytest.raises(ValueError, match="Exactly one"):
        run_evidence_verifier(baskets=[_basket("x")], extraction=ExtractionResult(segments=[], baskets=[]))


def test_verification_result_to_dict():
    result = VerificationResult(
        all_verified=True,
        total=1,
        verified_count=1,
        items=[
            VerificationItem(index=0, verified=True, reason="has evidence", evidence_preview="abc"),
        ],
        missing_indices=[],
    )
    d = result.to_dict()
    assert d["all_verified"] is True
    assert d["total"] == 1
    assert d["verified_count"] == 1
    assert len(d["items"]) == 1
    assert d["items"][0]["index"] == 0
    assert d["items"][0]["verified"] is True
    assert d["items"][0]["evidence_preview"] == "abc"

"""
Tests for Distressed Librarian (document_intel): Negative Covenants and Baskets extraction.
"""

import json
import pytest
from pathlib import Path

from signal_triage.document_intel import (
    ExtractedBasket,
    ExtractionResult,
    SignalLevel,
    extract_baskets_and_covenants,
)
from signal_triage.document_intel.patterns import (
    clarify_double_negative,
    find_category_and_snippet,
    resolve_signal_level,
)


def test_extract_from_text():
    text = """
    Article VII: Negative Covenants.
    The Company shall not make any Disposition of any assets unless the aggregate
    fair market value does not exceed $10,000,000. Net cash proceeds in excess of
    $1,000,000 shall trigger mandatory prepayment (sweep).
    The Company shall not invest in any Unrestricted Subsidiary without consent.
    """
    result = extract_baskets_and_covenants(text=text)
    assert isinstance(result, ExtractionResult)
    assert result.source_path is None
    assert len(result.baskets) >= 1
    cats = {b.category for b in result.baskets}
    assert "asset_sale" in cats or "unrestricted_subsidiary" in cats
    for b in result.baskets:
        assert b.evidence_snippet
        assert b.signal_level in (SignalLevel.LOW, SignalLevel.MEDIUM, SignalLevel.HIGH)


def test_citation_fields():
    text = "Asset Sale basket: disposition of assets up to $5 million. 100% of net cash proceeds sweep."
    result = extract_baskets_and_covenants(text=text)
    assert len(result.baskets) >= 1
    for b in result.baskets:
        assert b.evidence_snippet
        assert b.category in ("asset_sale", "unrestricted_subsidiary", "incremental_facility", "affiliate_transaction")


def test_double_negative_clarification():
    snippet = "The Company shall not sell any assets unless the Required Lenders have given consent."
    permitted = clarify_double_negative(snippet)
    assert permitted is not None
    assert "Permitted" in permitted
    assert "consent" in permitted.lower()


def test_signal_level_resolution():
    assert resolve_signal_level("unrestricted_subsidiary", "transfer to unrestricted subsidiary") == SignalLevel.HIGH
    assert resolve_signal_level("asset_sale", "disposition of assets $5M") in (SignalLevel.MEDIUM, SignalLevel.HIGH)


def test_json_output():
    text = "Incremental Facilities: the Company may incur additional debt in the Free and Clear Basket of $50 million."
    result = extract_baskets_and_covenants(text=text)
    out = result.to_dict()
    assert "baskets" in out
    assert "segments" in out
    parsed = json.loads(json.dumps(out))
    assert parsed["baskets"] == out["baskets"]


def test_extract_from_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text(
        "Section 7.05. Negative Covenants. Limitation on Dispositions. "
        "The Company shall not make any Disposition of assets except to the extent permitted under the basket."
    )
    result = extract_baskets_and_covenants(path=f)
    assert result.source_path is not None
    assert len(result.segments) >= 1

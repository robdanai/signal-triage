"""
Distressed Librarian: extract Negative Covenants and Baskets from ingested documents.
Every extracted basket includes Section Number and Page Number when available.

Enhanced with forensic table extraction, EBITDA normalizer, and LME risk scoring.
"""

from pathlib import Path

from signal_triage.document_intel.schema import (
    ExtractedBasket,
    ExtractionResult,
    SignalLevel,
)
from signal_triage.document_intel.patterns import (
    find_category_and_snippet,
    clarify_double_negative,
    resolve_signal_level,
    extract_dollar_limit,
    extract_sweep_language,
    analyze_priming_risk,
)
from signal_triage.basket_stacking import analyze_basket_interactions
from signal_triage.document_intel.segmenter import segment_text, section_number_from_label
from signal_triage.ingest.reader import read_document, DocumentChunk, full_text

# Import enhanced forensic parser
try:
    from signal_triage.document_intel.enhanced_parser import (
        extract_forensic_data,
        EnhancedExtractionResult,
    )
    ENHANCED_PARSER_AVAILABLE = True
except ImportError:
    ENHANCED_PARSER_AVAILABLE = False


def _page_for_char_offset(chunks: list[DocumentChunk], char_offset: int) -> int | None:
    """Return 1-based page number for character offset (PDF chunks)."""
    cumulative = 0
    for c in chunks:
        if cumulative <= char_offset < cumulative + len(c.content):
            return c.page_number
        cumulative += len(c.content)
    return chunks[-1].page_number if chunks else None


def _section_for_char_offset(
    segments: list[dict], char_offset: int
) -> tuple[str | None, str | None]:
    """Return (section_number, section_label) for char offset."""
    for seg in segments:
        if seg["start"] <= char_offset < seg["end"]:
            label = seg.get("section_label")
            return (section_number_from_label(label) if label else None, label)
    return (None, None)


def extract_baskets_and_covenants(
    path: str | Path | None = None,
    chunks: list[DocumentChunk] | None = None,
    text: str | None = None,
) -> ExtractionResult:
    """
    Ingest document (or use provided chunks/text), segment, and extract baskets/covenants.

    Either:
      - path: path to .txt or .pdf
      - chunks: pre-ingested DocumentChunk list (e.g. from Author Agent)
      - text: raw full text (no page numbers)

    Returns ExtractionResult with segments and baskets; every basket has citation
    (section_number, page_number when available) and permitted_clarification when
    double-negative language is detected.
    """
    if path is not None:
        chunks = read_document(path)
        source_path = str(Path(path).resolve())
    elif chunks:
        source_path = None
    else:
        if not text:
            return ExtractionResult(source_path=None, segments=[], baskets=[])
        chunks = [
            DocumentChunk(content=text, page_number=None, section_label=None, start_char=0, end_char=len(text))
        ]
        source_path = None

    full = full_text(chunks)
    # Build char -> page map for PDF
    page_by_char: list[tuple[int, int]] = []
    cum = 0
    for c in chunks:
        if c.page_number is not None:
            page_by_char.append((cum, c.page_number))
        cum += len(c.content)

    segments = segment_text(full, page_by_char if page_by_char else None)

    # Find all category/snippet hits
    hits = find_category_and_snippet(full)
    seen_snippets: set[str] = set()
    baskets: list[ExtractedBasket] = []

    for category, snippet, start_pos in hits:
        # Dedupe by normalized snippet
        key = snippet[:200].strip()
        if key in seen_snippets:
            continue
        seen_snippets.add(key)

        page = _page_for_char_offset(chunks, start_pos)
        sec_num, sec_label = _section_for_char_offset(segments, start_pos)
        permitted = clarify_double_negative(snippet)
        level = resolve_signal_level(category, snippet)
        dollar = extract_dollar_limit(snippet) if category in ("asset_sale", "incremental_facility") else None
        sweep = extract_sweep_language(snippet) if category == "asset_sale" else None

        baskets.append(
            ExtractedBasket(
                category=category,
                section_number=sec_num,
                page_number=page,
                evidence_snippet=snippet,
                signal_level=level,
                permitted_clarification=permitted,
                dollar_limit=dollar,
                sweep_requirement=sweep,
                raw_section_label=sec_label,
            )
        )

    # Forensic: Analyze priming risk (incremental facility + amendment provisions)
    # Extract amendment-related snippets for priming risk analysis
    amendment_snippets = [
        b.evidence_snippet for b in baskets
        if "amend" in b.evidence_snippet.lower() or "required lender" in b.evidence_snippet.lower()
    ]
    priming_risk_result = analyze_priming_risk(baskets, amendment_snippets)
    
    # Forensic: Analyze basket stacking (multi-step leakage paths)
    basket_dicts = [b.to_dict() for b in baskets]
    stacking_result = analyze_basket_interactions(basket_dicts)
    
    return ExtractionResult(
        source_path=source_path,
        segments=segments,
        baskets=baskets,
        priming_risk=priming_risk_result,
        metadata={
            "total_chunks": len(chunks),
            "total_segments": len(segments),
            "basket_stacking": stacking_result,  # NEW: forensic stacking analysis
        },
    )


def extract_baskets_and_covenants_enhanced(
    path: str | Path | None = None,
    chunks: list[DocumentChunk] | None = None,
    text: str | None = None,
) -> tuple[ExtractionResult, EnhancedExtractionResult | None]:
    """
    Enhanced extraction combining standard covenant extraction with forensic table parsing.
    
    Returns:
        - ExtractionResult: Standard covenant/basket extraction
        - EnhancedExtractionResult: Forensic data (capital structure, EBITDA, LME risks)
    """
    # Run standard extraction
    standard_result = extract_baskets_and_covenants(path=path, chunks=chunks, text=text)
    
    # Run enhanced forensic extraction if available
    enhanced_result = None
    if ENHANCED_PARSER_AVAILABLE and path is not None:
        try:
            # Build page_by_char mapping
            if chunks:
                page_by_char: list[tuple[int, int]] = []
                cum = 0
                for c in chunks:
                    if c.page_number is not None:
                        page_by_char.append((cum, c.page_number))
                    cum += len(c.content)
            else:
                page_by_char = None
            
            # Extract forensic data
            enhanced_result = extract_forensic_data(
                path=path,
                text=text or (full_text(chunks) if chunks else None),
                page_by_char=page_by_char,
            )
            
            # Integrate enhanced results into standard metadata
            standard_result.metadata["forensic_extraction"] = {
                "debt_tranches_found": len(enhanced_result.debt_tranches),
                "ebitda_risk_score": enhanced_result.ebitda_definition.addback_risk_score if enhanced_result.ebitda_definition else None,
                "lme_risks_count": len(enhanced_result.lme_risks),
                "highest_lme_risk": max([r.leakage_risk_score for r in enhanced_result.lme_risks], default=0.0),
            }
            
        except Exception as e:
            # Don't fail on enhanced extraction errors
            standard_result.metadata["forensic_extraction_error"] = str(e)
    
    return standard_result, enhanced_result

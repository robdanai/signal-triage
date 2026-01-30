"""
Segment long documents into relevant sections (e.g. Article VII: Negative Covenants).
Assigns section labels to text ranges for citation.
"""

import re

from signal_triage.document_intel.patterns import NEGATIVE_COVENANT_HEADERS

# Broader article/section headers for context
ARTICLE_SECTION_PATTERNS = [
    (r"Article\s+([IVXLC]+|\d+)[\.\s]*([^\n]{5,80})", "Article"),
    (r"Section\s+(\d+\.\d*(?:\.\d+)?)[\.\s]*([^\n]{5,80})", "Section"),
    (r"ARTICLE\s+([IVXLC]+|\d+)[\.\s]*([^\n]{5,80})", "Article"),
]


def find_section_matches(text: str) -> list[tuple[int, str, str]]:
    """
    Find all section/article headers in text.
    Returns list of (start_pos, section_id, full_label).
    """
    results: list[tuple[int, str, str]] = []
    for pattern in NEGATIVE_COVENANT_HEADERS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            label = m.group(0).strip()
            results.append((m.start(), "negative_covenants", label))
    for pat, kind in ARTICLE_SECTION_PATTERNS:
        for m in re.finditer(pat, text):
            num = m.group(1).strip()
            title = (m.group(2) if m.lastindex >= 2 else "").strip()
            full = f"{kind} {num}" + (f": {title}" if title else "")
            results.append((m.start(), f"{kind}_{num}", full))
    results.sort(key=lambda x: x[0])
    return results


def segment_text(
    text: str, page_by_char: list[tuple[int, int]] | None = None
) -> list[dict]:
    """
    Break text into segments with section labels.
    page_by_char: optional list of (char_start, page_number) for citation.
    Returns list of {section_label, start, end, page_number}.
    """
    matches = find_section_matches(text)
    segments: list[dict] = []
    for i, (start, sec_id, label) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        page = None
        if page_by_char:
            for char_start, p in page_by_char:
                if start >= char_start:
                    page = p
                else:
                    break
        segments.append({
            "section_label": label,
            "section_id": sec_id,
            "start": start,
            "end": end,
            "page_number": page,
        })
    if not segments:
        page_num = page_by_char[0][1] if page_by_char and len(page_by_char) > 0 else None
        segments.append({
            "section_label": "Full Document",
            "section_id": "full",
            "start": 0,
            "end": len(text),
            "page_number": page_num,
        })
    return segments


def section_number_from_label(label: str) -> str | None:
    """Extract section number (e.g. 7.05, Article VII) from label."""
    m = re.search(r"Section\s+(\d+\.\d*(?:\.\d+)?)", label, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"Article\s+([IVXLC]+|\d+)", label, re.IGNORECASE)
    if m:
        return f"Article {m.group(1)}"
    return None

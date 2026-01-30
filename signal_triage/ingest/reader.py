"""
Document reader: text and PDF ingestion with page numbers for citation.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocumentChunk:
    """A segment of document text with provenance for citation."""
    content: str
    page_number: int | None = None  # 1-based; None for plain text
    section_label: str | None = None  # e.g. "Article VII: Negative Covenants"
    start_char: int = 0
    end_char: int = 0

    def citation(self) -> str:
        """Human-readable citation (Section and/or Page)."""
        parts = []
        if self.section_label:
            parts.append(self.section_label)
        if self.page_number is not None:
            parts.append(f"Page {self.page_number}")
        return "; ".join(parts) if parts else "Source"


def _read_text_file(path: Path) -> list[DocumentChunk]:
    """Read a .txt file as a single chunk (no page numbers)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return [
        DocumentChunk(
            content=text,
            page_number=None,
            section_label=None,
            start_char=0,
            end_char=len(text),
        )
    ]


def _read_pdf_file(path: Path) -> list[DocumentChunk]:
    """Read a .pdf file page by page for citation."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "PDF support requires pypdf. Install with: pip install pypdf"
        ) from None

    reader = PdfReader(str(path))
    chunks: list[DocumentChunk] = []
    start = 0
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        end = start + len(text)
        chunks.append(
            DocumentChunk(
                content=text,
                page_number=i,
                section_label=None,
                start_char=start,
                end_char=end,
            )
        )
        start = end
    return chunks


def read_document(path: str | Path) -> list[DocumentChunk]:
    """
    Ingest a document (text or PDF) and return chunks with page numbers where available.

    Args:
        path: Path to .txt or .pdf file.

    Returns:
        List of DocumentChunk (one per page for PDF, one for .txt).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    suffix = (p.suffix or "").lower()
    if suffix == ".txt":
        return _read_text_file(p)
    if suffix == ".pdf":
        return _read_pdf_file(p)
    raise ValueError(f"Unsupported format: {suffix}. Use .txt or .pdf.")


def full_text(chunks: list[DocumentChunk]) -> str:
    """Concatenate all chunk content (preserves order)."""
    return "".join(c.content for c in chunks)

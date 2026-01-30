"""
Ingest module: read text and PDF documents with page/section metadata.
Unified pipeline for .txt and .pdf (Credit Agreements, Indentures, 10-Ks).
"""

from signal_triage.ingest.reader import read_document, DocumentChunk

__all__ = ["read_document", "DocumentChunk"]

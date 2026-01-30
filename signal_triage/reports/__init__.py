"""
Reporting: document-level and portfolio-level report structures.
Report-per-document format: score, tier, top_signals, evidence_snippets, provenance.
"""

from signal_triage.reports.document_report import (
    DOCUMENT_REPORT_FIELDS,
    DocumentReportCore,
    Provenance,
    TopSignal,
    build_document_report,
    build_error_report,
)

__all__ = [
    "DOCUMENT_REPORT_FIELDS",
    "DocumentReportCore",
    "Provenance",
    "TopSignal",
    "build_document_report",
    "build_error_report",
]

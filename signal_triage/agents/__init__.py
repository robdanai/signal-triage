"""
Agent modules for Signal Triage.
Batch Portfolio: ranks businesses and produces top-risk list.
Benchmarker: market context, precedent transactions, recovery variance for Quant/Auditor/Author.
Summary & Risk Narrative: short restructuring-style overview and tier for analyst-facing output.
Evidence Verifier: ensures every signal has a cited snippet.
"""

from signal_triage.agents.batch_portfolio import run_batch_portfolio
from signal_triage.agents.benchmarker import run_benchmarker
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
from signal_triage.agents.signal_extractor import extract_signals, run_signal_extractor
from signal_triage.agents.summary_narrative import run_summary_narrative

__all__ = [
    "run_batch_portfolio",
    "run_benchmarker",
    "compare_two",
    "run_comparator",
    "run_evidence_verifier",
    "extract_signals",
    "run_signal_extractor",
    "run_summary_narrative",
    "VerificationItem",
    "VerificationResult",
    "verify_basket",
    "verify_baskets",
    "verify_extraction",
    "verify_signal_dict",
    "verify_signals",
]

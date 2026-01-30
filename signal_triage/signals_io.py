"""
Signals handoff: Librarian writes signals.json; Quant reads it for the waterfall.
Contains trap doors (covenant baskets), LME signals, and optional capital structure.
Versioned schema (schema_version) for reproducibility.
"""

import json
import warnings
from pathlib import Path
from typing import Any

from signal_triage.config_schema import (
    DEFAULT_SIGNALS_JSON_SCHEMA_VERSION,
    SUPPORTED_SIGNALS_JSON_VERSIONS,
)
from signal_triage.document_intel.extractor import extract_baskets_and_covenants
from signal_triage.analyzer import analyze_text
from signal_triage.ingest.reader import read_document, full_text, DocumentChunk


# Default capital structure skeleton when document does not specify one (Quant placeholder).
DEFAULT_CAPITAL_STRUCTURE = {
    "tranches": [
        {"name": "Senior Secured", "claim": 300},
        {"name": "Mezz", "claim": 150},
        {"name": "Unsecured", "claim": 100},
    ],
    "default_ev": 350,
}


def scan_document_and_write_signals(
    file_path: str | Path,
    signals_path: str | Path = "signals.json",
    include_default_capital_structure: bool = True,
) -> dict[str, Any]:
    """
    Librarian: Ingest document, extract Trap Doors and LME signals, write signals.json.

    Args:
        file_path: Path to .txt or .pdf to scan.
        signals_path: Where to write signals.json.
        include_default_capital_structure: If True, add skeleton tranches/default_ev when none parsed.

    Returns:
        The payload that was written (for tests/callers).
    """
    path = Path(file_path)
    chunks = read_document(path)
    extraction = extract_baskets_and_covenants(chunks=chunks)
    text = full_text(chunks)
    analysis = analyze_text(text)

    trap_doors = [b.to_dict() for b in extraction.baskets]
    lme_signals = analysis.get("lme_signals") or []
    collateral_leakage_flags = extraction.collateral_leakage_flags

    capital_structure = None
    if include_default_capital_structure:
        capital_structure = DEFAULT_CAPITAL_STRUCTURE.copy()

    payload = {
        "schema_version": DEFAULT_SIGNALS_JSON_SCHEMA_VERSION,
        "source_file": str(path.resolve()),
        "trap_doors": trap_doors,
        "lme_signals": lme_signals,
        "collateral_leakage_flags": collateral_leakage_flags,
        "capital_structure": capital_structure,
        "metadata": {
            "trap_door_count": len(trap_doors),
            "lme_count": len(lme_signals),
            "collateral_leakage_count": len(collateral_leakage_flags),
            **extraction.metadata,
        },
    }

    out = Path(signals_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


def write_signals_from_chunks(
    chunks: list[DocumentChunk],
    signals_path: str | Path = "signals.json",
    *,
    source_file: str | None = None,
    include_default_capital_structure: bool = True,
) -> dict[str, Any]:
    """
    Librarian: Write signals.json from pre-ingested chunks (e.g. from URL/EDGAR).

    Args:
        chunks: DocumentChunk list from ingest_url or ingest_edgar_filing.
        signals_path: Where to write signals.json.
        source_file: Optional source label (URL or EDGAR:accession) for provenance.
        include_default_capital_structure: If True, add skeleton tranches/default_ev when none parsed.

    Returns:
        The payload that was written.
    """
    extraction = extract_baskets_and_covenants(chunks=chunks)
    text = full_text(chunks)
    analysis = analyze_text(text)

    trap_doors = [b.to_dict() for b in extraction.baskets]
    lme_signals = analysis.get("lme_signals") or []
    collateral_leakage_flags = extraction.collateral_leakage_flags

    capital_structure = None
    if include_default_capital_structure:
        capital_structure = DEFAULT_CAPITAL_STRUCTURE.copy()

    payload = {
        "schema_version": DEFAULT_SIGNALS_JSON_SCHEMA_VERSION,
        "source_file": source_file or "(chunks)",
        "trap_doors": trap_doors,
        "lme_signals": lme_signals,
        "collateral_leakage_flags": collateral_leakage_flags,
        "capital_structure": capital_structure,
        "metadata": {
            "trap_door_count": len(trap_doors),
            "lme_count": len(lme_signals),
            "collateral_leakage_count": len(collateral_leakage_flags),
            **extraction.metadata,
        },
    }

    out = Path(signals_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return payload


def read_signals(signals_path: str | Path) -> dict[str, Any]:
    """
    Quant: Read signals.json. Raises FileNotFoundError if missing.
    Validates schema_version for reproducibility; warns on unsupported version.
    """
    with open(signals_path, encoding="utf-8") as f:
        data = json.load(f)
    schema_version = data.get("schema_version") or data.get("version")
    if schema_version is not None and str(schema_version) not in SUPPORTED_SIGNALS_JSON_VERSIONS:
        warnings.warn(
            f"signals.json schema_version={schema_version!r} is not in supported "
            f"{SUPPORTED_SIGNALS_JSON_VERSIONS}; results may not be reproducible.",
            UserWarning,
            stacklevel=2,
        )
    return data

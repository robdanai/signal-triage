"""
Distressed Librarian (Document Intelligence).
Extract Negative Covenants and Baskets that define restructuring boundaries.

Enhanced with forensic table extraction, EBITDA normalizer, and LME risk scoring.
"""

from signal_triage.document_intel.schema import (
    ExtractedBasket,
    ExtractionResult,
    SignalLevel,
)
from signal_triage.document_intel.extractor import (
    extract_baskets_and_covenants,
    extract_baskets_and_covenants_enhanced,
)

# Export enhanced parser components (optional import)
try:
    from signal_triage.document_intel.enhanced_parser import (
        extract_forensic_data,
        EnhancedExtractionResult,
        DebtTranche,
        EBITDADefinition,
        LMELeakageRisk,
    )
    ENHANCED_PARSER_AVAILABLE = True
except ImportError:
    ENHANCED_PARSER_AVAILABLE = False
    extract_forensic_data = None
    EnhancedExtractionResult = None
    DebtTranche = None
    EBITDADefinition = None
    LMELeakageRisk = None

__all__ = [
    "ExtractedBasket",
    "ExtractionResult",
    "SignalLevel",
    "extract_baskets_and_covenants",
    "extract_baskets_and_covenants_enhanced",
    "extract_forensic_data",
    "EnhancedExtractionResult",
    "DebtTranche",
    "EBITDADefinition",
    "LMELeakageRisk",
    "ENHANCED_PARSER_AVAILABLE",
]

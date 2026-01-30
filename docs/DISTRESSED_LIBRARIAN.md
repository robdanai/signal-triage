# Distressed Librarian (Document Intelligence)

**Role:** Ingest legal and financial documents (Credit Agreements, Indentures, 10-Ks) and extract **Negative Covenants** and **Baskets** that define the boundaries of a restructuring.

## The "Trap Door" Mandate

The module is focused on **Structural Leakage**. It scans every document for:

| Category | Description |
|----------|-------------|
| **Asset Sale Baskets** | Dollar limits and "sweep" requirements for selling collateral; net cash proceeds application. |
| **Investments in Unrestricted Subsidiaries** | "J.Crew" / "Chewy" blockers: language that prevents moving valuable IP or assets into entities beyond lenders' reach. |
| **Incremental Facilities (Free-and-Clear Baskets)** | How much "Priming Debt" the company can issue without lender consent. |
| **Affiliate Transactions** | Language allowing value transfer to equity holders via management fees or dividend recapitalizations. |

## Extraction Protocol

1. **Segment** – Break long documents into relevant sections (e.g. "Article VII: Negative Covenants").
2. **Tag & Triage** – Map each extracted clause to a **Signal Level**: Low / Medium / High Risk.
3. **JSON Output** – Structured data for the Quant Agent and Recovery Waterfall.

## Verification

- **Cite the Source** – Every extracted basket includes **Section Number** and **Page Number** from the source PDF when available.
- **Double-Negative Rule** – When a clause says "The company shall not … unless …", the output clarifies **exactly what is permitted** (`permitted_clarification`).

## Usage

### CLI

```bash
# Extract Negative Covenants and Baskets from a file (text or PDF)
python -m signal_triage.cli path/to/document.pdf --librarian --json

# Or with the entry point
signal-triage path/to/credit_agreement.txt --librarian --json
```

### Python

```python
from signal_triage.document_intel import extract_baskets_and_covenants

# From file path (.txt or .pdf)
result = extract_baskets_and_covenants(path="agreement.pdf")
print(result.to_dict())

# From pre-ingested chunks (e.g. from Author Agent)
from signal_triage.ingest import read_document
chunks = read_document("agreement.pdf")
result = extract_baskets_and_covenants(chunks=chunks)

# From raw text (no page numbers)
result = extract_baskets_and_covenants(text="...")
```

### JSON Output Shape (for Quant Agent)

```json
{
  "source_path": "/path/to/doc.pdf",
  "segments": [
    { "section_label": "Article VII: Negative Covenants", "section_id": "negative_covenants", "start": 0, "end": 5000, "page_number": 42 }
  ],
  "baskets": [
    {
      "category": "asset_sale",
      "section_number": "7.05",
      "page_number": 43,
      "evidence_snippet": "...",
      "signal_level": "medium",
      "permitted_clarification": "Permitted when: aggregate value does not exceed $10,000,000",
      "dollar_limit": "$10,000,000",
      "sweep_requirement": "100% of net cash proceeds (sweep)"
    }
  ],
  "metadata": { "total_chunks": 150, "total_segments": 12 }
}
```

## Dependencies

- **pypdf** – For PDF ingestion and page-number citation. Install with: `pip install pypdf`

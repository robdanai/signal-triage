# Common Development Tasks for AI Agents

This guide provides step-by-step instructions for common development tasks in Signal Triage.

---

## Adding a New Signal Type

### 1. Update Signal Configuration

**File:** `signals_config.json`

```json
{
  "signals": {
    "new_signal_type": {
      "display_name": "New Signal Type",
      "category": "covenant|lme|structural|financial",
      "weight": 1.5,
      "severity": "low|medium|high",
      "description": "Brief description of what this signal detects"
    }
  }
}
```

### 2. Add Extraction Logic

**File:** `signal_triage/agents/signal_extractor.py`

```python
def extract_new_signal_type(text: str, document_chunks: List[DocumentChunk]) -> List[Signal]:
    """
    Extract new signal type from document.
    
    Args:
        text: Full document text
        document_chunks: Document chunks with page numbers
        
    Returns:
        List of Signal objects with provenance
    """
    signals = []
    # Detection logic here
    for match in pattern.finditer(text):
        signal = Signal(
            type="new_signal_type",
            severity="medium",
            evidence=match.group(0),
            page=get_page_number(match.start(), document_chunks),
            section=extract_section_reference(match.group(0))
        )
        signals.append(signal)
    return signals
```

### 3. Add Tests

**File:** `tests/test_signal_extractor.py`

```python
def test_new_signal_type_detection():
    """Test new signal type is detected correctly."""
    text = "Sample text containing new signal indicator..."
    chunks = create_test_chunks(text)
    
    signals = extract_new_signal_type(text, chunks)
    
    assert len(signals) == 1
    assert signals[0].type == "new_signal_type"
    assert signals[0].severity == "medium"
    assert signals[0].page is not None
```

### 4. Run Validation

```bash
# Run new test
pytest tests/test_signal_extractor.py::test_new_signal_type_detection -v

# Run full validation suite
pytest tests/test_validation.py -v

# Test against benchmark corpus
python -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline
```

---

## Adding a New Covenant Type

### 1. Update Schema

**File:** `signal_triage/document_intel/schema.py`

```python
@dataclass
class NewCovenantType:
    """New covenant type definition."""
    covenant_name: str
    limit_value: Decimal
    current_value: Optional[Decimal] = None
    headroom_percentage: Optional[float] = None
    section: Optional[str] = None
    page: Optional[int] = None
    evidence: Optional[str] = None
```

### 2. Add Detection Pattern

**File:** `signal_triage/document_intel/patterns.py`

```python
# New covenant detection pattern
NEW_COVENANT_PATTERN = re.compile(
    r'shall not\s+(?P<action>[^,]+)\s+unless.*?(?P<limit>[\d.]+)',
    re.IGNORECASE
)

def detect_new_covenant(text: str) -> List[NewCovenantType]:
    """Detect new covenant type from text."""
    matches = NEW_COVENANT_PATTERN.finditer(text)
    covenants = []
    for match in matches:
        covenant = NewCovenantType(
            covenant_name=match.group('action'),
            limit_value=Decimal(match.group('limit')),
            evidence=match.group(0)
        )
        covenants.append(covenant)
    return covenants
```

### 3. Integrate with Librarian

**File:** `signal_triage/document_intel/extractor.py`

```python
def extract_covenants(chunks: List[DocumentChunk]) -> ExtractionResult:
    """Extract all covenant types including new type."""
    # ... existing covenant extraction ...
    
    # Add new covenant extraction
    new_covenants = detect_new_covenant(full_text)
    result.new_covenants = new_covenants
    
    return result
```

### 4. Update Tests

```bash
# Add test in tests/test_librarian.py
pytest tests/test_librarian.py -v

# Test with enhanced parser
python demo_enhanced_parser.py
```

---

## Adding a New LME Category

### 1. Update LME Definitions

**File:** `signal_triage/lme_definitions.py`

```python
LME_DEFINITIONS = {
    "new_lme_tactic": {
        "id": "new_lme_tactic",
        "display_name": "New LME Tactic",
        "category": "structural",  # structural, out_of_court, bankruptcy, precedent
        "definition": "What this tactic does and how it affects lenders.",
        "rationale": "Why companies use this tactic.",
        "severity": "high",  # low, medium, high
        "market_tier": "Toxic",  # Tight, Market, Toxic
        "precedents": ["Company X 2024", "Company Y 2025"],
        "detection_keywords": ["keyword1", "keyword2"]
    }
}
```

### 2. Add Detection Logic

**File:** `signal_triage/lme_parser.py`

```python
def detect_new_lme_tactic(text: str) -> List[LMESignal]:
    """Detect new LME tactic from document."""
    signals = []
    definition = get_definition("new_lme_tactic")
    
    # Pattern matching logic
    for keyword in definition["detection_keywords"]:
        if keyword.lower() in text.lower():
            signal = LMESignal(
                lme_type="new_lme_tactic",
                severity=definition["severity"],
                evidence=extract_evidence_context(text, keyword),
                definition=definition
            )
            signals.append(signal)
    
    return signals
```

### 3. Update Documentation

**File:** `docs/LME_CATEGORIES.md`

Add comprehensive section:
- What is this tactic?
- How does it work?
- Why is it risky for lenders?
- Precedent cases
- Detection approach

### 4. Test

```bash
# Test LME detection
pytest tests/test_lme_parser.py -v

# Test against known documents
python -m signal_triage.cli examples/jcrew/jcrew_credit_agreement.txt --librarian --json
```

---

## Debugging the Pipeline

### Enable Debug Logging

**PowerShell:**
```powershell
$env:LOG_LEVEL = "DEBUG"
python -m signal_triage.cli <file> --pipeline
```

**Bash:**
```bash
export LOG_LEVEL=DEBUG
python -m signal_triage.cli <file> --pipeline
```

### Run Individual Agents

```bash
# Test Author (ingestion)
python -m signal_triage.cli <file> --author --json

# Test Librarian (covenant extraction)
python -m signal_triage.cli <file> --librarian --json

# Test Quant (waterfall)
python -m signal_triage.cli <file> --waterfall --ev 150 --tranches "Senior:100,Mezz:50"

# Test Benchmarker
python -m signal_triage.cli <file> --benchmark --industry Retail --geography US

# Test full pipeline with verbose output
python -m signal_triage.cli <file> --pipeline --verbose
```

### Check Specific Agent Output

```python
# Python REPL debugging
from signal_triage.document_intel.extractor import extract_baskets_and_covenants
from signal_triage.ingest.reader import read_document

chunks = read_document("path/to/file.pdf")
result = extract_baskets_and_covenants(chunks)

print(f"Baskets found: {len(result.baskets)}")
print(f"Signals found: {len(result.signals)}")
print(f"Leakage flags: {result.collateral_leakage_flags}")
```

### Inspect Audit Trail

```bash
# Run with audit trail output
python -m signal_triage.cli <file> --pipeline --json > output.json

# Extract audit trail
python -c "import json; data=json.load(open('output.json')); print(json.dumps(data['audit_trail'], indent=2))"
```

---

## Working with Live APIs

### Configure SEC EDGAR Access

```bash
# Set User-Agent (REQUIRED by SEC)
export SEC_USER_AGENT="YourCompany/1.0 (contact@example.com)"

# Enable live data
export BENCHMARKER_USE_LIVE="1"
export BENCHMARKER_DATA_SOURCE="edgar"

# Test EDGAR integration
python demo_live_data.py
```

### Test Market Data APIs

```bash
# Set API keys
export ALPHA_VANTAGE_API_KEY="your-key"
export IEX_CLOUD_API_KEY="your-key"

# Test live market data
pytest tests/test_market_data_live.py -v

# Test API integration
python test_api_integration.py
```

### Handle Rate Limiting

```python
# Built-in rate limiter in signal_triage/api/sec_edgar.py
from signal_triage.api.sec_edgar import SECEdgarClient

client = SECEdgarClient(
    user_agent="YourCompany/1.0 (contact@example.com)",
    rate_limit=10  # Max 10 requests/second
)

# Client automatically handles rate limiting and retries
filings = client.get_company_filings(ticker="ABC", form_type="8-K")
```

---

## Running Tests

### Basic Test Commands

```bash
# All tests
pytest

# Specific test file
pytest tests/test_librarian.py -v

# Specific test function
pytest tests/test_librarian.py::test_basket_extraction -v

# Tests matching pattern
pytest -k "test_waterfall" -v

# Show print statements
pytest tests/test_validation.py -v -s
```

### Coverage Report

```bash
# Generate coverage report
pytest --cov=signal_triage --cov-report=html

# Open report
# Windows: start htmlcov/index.html
# Mac: open htmlcov/index.html
```

### Agent-Specific Test Suites

```bash
# Librarian (covenant extraction, LME detection)
pytest tests/test_librarian.py tests/test_enhanced_parser.py tests/test_lme_parser.py -v

# Quant (waterfall, APR, fulcrum)
pytest tests/test_recovery_engine.py tests/test_waterfall.py -v

# Benchmarker (market data, precedents)
pytest tests/test_benchmarker.py tests/test_market_data_client.py -v

# Auditor (stress-test, validation)
pytest tests/test_auditor.py tests/test_validation.py -v

# Full pipeline integration
pytest tests/test_pipeline.py -v
```

---

## Docker Development

### Build and Run Locally

```bash
# Build image
docker build -t signal-triage:latest .

# Run API server
docker run -p 8000:8000 signal-triage:latest

# Run with environment variables
docker run -p 8000:8000 \
  -e SEC_USER_AGENT="YourCompany/1.0 (contact@example.com)" \
  -e BENCHMARKER_USE_LIVE="1" \
  signal-triage:latest
```

### Full Stack with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Access Services

- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- PostgreSQL: localhost:5432 (user: signal_triage, db: signal_triage)
- Redis: localhost:6379

---

## Updating Documentation

### After Adding a Feature

1. **Update ROADMAP.md:**
   - Strike through completed todo items
   - Update phase status
   - Add new todos if feature exposes new work

2. **Update ORCHESTRATION.md:**
   - Update "Current Implementation" table if CLI commands changed
   - Update handoff descriptions if agent interfaces changed

3. **Update agent mandate:**
   - Update `.cursor/agents/<agent-name>.md` if responsibilities changed
   - Document new owned files or code paths

4. **Update user-facing docs:**
   - Add usage examples to README.md if public-facing feature
   - Update relevant guides in `docs/` folder

### Documentation Standards

- **Code comments:** Explain "why" not "what"
- **Docstrings:** Google style, include Args, Returns, Raises
- **Examples:** Include working code snippets
- **Links:** Use relative paths for internal links

---

## Common Error Resolution

### "No module named 'signal_triage'"

```bash
# Install in development mode
pip install -e .

# Or use python -m to run from project root
python -m signal_triage.cli <file>
```

### "Decimal precision error in waterfall"

Check for float usage:
```python
# WRONG
recovery = 150000000.0 / 200000000.0

# CORRECT
from decimal import Decimal
recovery = Decimal("150000000") / Decimal("200000000")
```

### "SEC EDGAR 403 Forbidden"

```bash
# Set User-Agent (required by SEC)
export SEC_USER_AGENT="YourCompany/1.0 (your.email@example.com)"
```

### "Critical Variance unresolved - Report not published"

```bash
# Option 1: Fix the variance in Auditor
# Option 2: Skip gate for draft
python -m signal_triage.cli <file> --pipeline --no-audit-gate
```

### "Collateral leakage not reflected in waterfall"

Ensure Quant receives leakage flags:
```python
# In recovery_engine.py
if extraction_result.collateral_leakage_flags:
    adjusted_collateral = base_collateral - calculate_leakage(flags)
    # Recalculate with adjusted value
```

---

## Performance Optimization

### Profile Pipeline Execution

```bash
# Time each agent
python -m cProfile -s cumtime signal_triage/cli.py <file> --pipeline

# Memory profiling
python -m memory_profiler signal_triage/cli.py <file> --pipeline
```

### Cache API Responses

```python
# Redis caching (automatic when Redis available)
# Set TTLs in environment
export API_CACHE_TTL="3600"  # 1 hour
export FILING_CACHE_TTL="86400"  # 24 hours
```

### Batch Processing Optimization

```bash
# Process multiple files efficiently
python -m signal_triage.cli --pipeline --batch folder/ --workers 4
```

---

## Quick Reference

### Most Common Commands

```bash
# 1. Full pipeline (single file)
python -m signal_triage.cli <file> --pipeline

# 2. Batch processing
python -m signal_triage.cli --pipeline --batch <folder>

# 3. Run tests
pytest tests/test_validation.py -v

# 4. Start API server
python run_api_server.py

# 5. Individual agent
python -m signal_triage.cli <file> --librarian --json
```

### File Locations

- **Agent definitions:** `.cursor/agents/<agent-name>.md`
- **Tests:** `tests/test_<agent-name>.py`
- **Fixtures:** `tests/fixtures/`
- **Examples:** `examples/<company>/`
- **Docs:** `docs/<topic>.md`

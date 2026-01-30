# Signal Triage - Agent Context for LLMs

## What This Codebase Does

Signal Triage is an **institutional-grade forensic decision engine** for distressed investing. It analyzes credit agreements, indentures, 10-Ks, and restructuring documents to provide forensic-level distress assessment and recovery modeling.

**Core Function:** Detect "trap doors" in credit agreements that allow value to leak from lenders, model recovery waterfalls under bankruptcy scenarios, and generate auditable analyst reports with full source traceability.

---

## Key Concepts for AI Agents

### Domain-Specific Terms

| Term | Definition | Why It Matters |
|------|------------|----------------|
| **LME** | Liability Management Exercise - debt restructuring tactics that favor certain creditors over others | 21 categories detected; high-risk structural changes |
| **Waterfall** | Priority-based debt recovery calculation under bankruptcy | Determines which debt tranches get value and in what order |
| **Baskets** | Covenant carve-outs that allow companies to take actions otherwise restricted | Limit lender protections; enable value leakage |
| **Fulcrum Security** | The debt tranche that converts to equity ownership in bankruptcy | The "break-even" point where value stops |
| **APR** | Absolute Priority Rule - senior debt must be paid 100% before junior gets anything | Violation detection is critical for fairness |
| **Critical Variance** | Material discrepancy between model predictions and market precedents | Requires reconciliation before report publication |
| **Collateral Leakage** | Structural mechanisms that move value out of lender reach | J.Crew dropdown, Serta uptier, unrestricted subsidiary transfers |

### Financial Math Requirements

- **Decimal Precision:** All financial calculations MUST use `decimal.Decimal` (never `float`)
- **APR Enforcement:** No value to junior tranches until senior is 100% recovered
- **LME Adjustments:** When Librarian flags collateral leakage, Quant must reduce available collateral value
- **Provenance:** Every number must be traceable to source (document page/section, API with date)

---

## Architecture Overview

### Multi-Agent System

7 specialized agents work in sequence to build a complete analysis:

```
Document → Author → Librarian → Quant ← Benchmarker → Auditor → Comparator → Reporter
           (ingest)  (extract)  (model)   (validate)   (test)   (compare)  (publish)
```

**Key Principle:** Each agent has clear inputs/outputs and hands off to the next. No agent skips its predecessor's work.

### Agent Responsibilities

| Agent | Primary Responsibility | Key Output |
|-------|------------------------|------------|
| **Author** | Document ingestion, API integration | Document chunks with page numbers |
| **Librarian** | Covenant extraction, LME detection | Baskets, covenants, leakage flags |
| **Quant** | Recovery modeling, waterfall | Recovery percentages, fulcrum |
| **Benchmarker** | Market validation, precedents | Market multiples, Critical Variance flags |
| **Auditor** | Stress-testing, validation | Pass/fail, audit trail |
| **Comparator** | Prior vs current, peer analysis | Score deltas, material changes |
| **Reporter** | Final analyst report | Auditable report with provenance |

---

## Code Organization

### Primary Modules

```
signal_triage/
├── ingest/              # Author: PDF/text/web ingestion
│   ├── reader.py        # DocumentChunk generation
│   └── web.py           # URL fetch, SEC EDGAR integration
├── document_intel/      # Librarian: Covenant extraction
│   ├── extractor.py     # Main extraction logic
│   ├── enhanced_parser.py  # Forensic table extraction, EBITDA normalization
│   ├── schema.py        # Data models (Basket, Covenant, Signal)
│   └── patterns.py      # Regex patterns for covenant detection
├── recovery_engine.py   # Quant: Waterfall modeling
├── agents/              # Benchmarker, Auditor, Comparator
│   ├── benchmarker.py
│   ├── auditor.py
│   └── comparator.py
├── reports/             # Reporter: Final output
│   └── document_report.py
├── api/                 # External data APIs
│   ├── sec_edgar.py     # SEC EDGAR filings
│   └── market_pricing.py
├── cli.py               # Command-line interface
└── pipeline.py          # Full pipeline orchestration
```

### Configuration Files

- `signals_config.json` - Signal definitions, weights, thresholds
- `.env` / `.env.cloud` - Environment variables, API keys
- `tests/fixtures/benchmark_corpus/` - Test documents for validation

---

## Testing Philosophy

### Test Coverage

- **120+ tests** covering all agents, edge cases, API integrations
- **Benchmark corpus:** `tests/fixtures/benchmark_corpus/` with known-good documents
- **Validation suite:** `tests/fixtures/validation_suite/` with targeted scenarios
- **Live API tests:** `tests/test_integration_live_apis.py` (requires API keys)

### Running Tests

```bash
# All tests
pytest

# Agent-specific
pytest tests/test_librarian.py -v
pytest tests/test_auditor.py -v

# Validation suite
pytest tests/test_validation.py -v

# Live API integration (requires keys)
pytest tests/test_market_data_live.py -v
```

### Test Patterns

- **Decimal precision tests:** Ensure no float drift in financial math
- **APR violation tests:** Verify junior tranches don't get value when senior < 100%
- **LME detection tests:** Validate all 21 LME categories are detected
- **Provenance tests:** Confirm all outputs include source attribution

---

## Code Style & Standards

### Formatting

- **Black:** Line length 88, auto-format on save
- **isort:** Import ordering
- **flake8:** Linting (max line length 100, ignore E203/W503)

### Type Hints

- **Required** for all public APIs and agent methods
- **Optional** for internal helper functions
- Use `typing` module: `List`, `Dict`, `Optional`, `Union`, `Tuple`

### Documentation

- **Docstrings:** All public functions must have docstrings (Google style)
- **Comments:** Explain "why" not "what"; focus on business logic
- **Agent mandates:** See `.cursor/agents/<agent-name>.md` for role-specific requirements

### Error Handling

- **Graceful degradation:** Analysis proceeds with warnings when non-critical data missing
- **Explicit validation:** Use `evidence_verifier.py` to validate assumptions
- **Logging:** Use `logging` module (DEBUG for detailed, INFO for key milestones, WARNING for issues)

---

## Domain-Specific Patterns

### LME Detection

21 categories across 4 groups:

1. **Structural/Collateral:** Dropdown, S-Prime, uptiering, Texas two-step, double-dip, basket transfers, asset sale, investment basket, transfer to unrestricted sub, structural subordination
2. **Out-of-Court:** Consent solicitation, equity cure, lender voting squeeze, forbearance
3. **Bankruptcy:** Substantive consolidation, cramdown, crossover/prepack, make-whole/disallowance, PIK
4. **Precedents:** J.Crew blocker, Serta uptier, Incora/Wesco vote rigging

**Detection Files:**
- `signal_triage/lme_parser.py` - Main LME detection logic
- `signal_triage/lme_definitions.py` - Category definitions with severity and rationale
- `signal_triage/document_intel/enhanced_parser.py` - Forensic LME risk scoring

### Covenant Forensics

**EBITDA Normalization:**
- **High Risk:** Run-rate synergies, anticipated cost savings (future benefits not realized)
- **Medium Risk:** Pro-forma adjustments (as-if scenarios)
- **Low Risk:** Non-cash charges (legitimate add-backs like stock comp)

**Leverage Headroom:**
```
Headroom % = ((Covenant Limit - Actual Ratio) / Covenant Limit) * 100
Critical Distress = Headroom < 15%
```

### Recovery Waterfall

**Absolute Priority Rule:**
```python
# CORRECT: Senior fully recovered before junior gets anything
if senior_recovery < Decimal("1.0"):
    junior_recovery = Decimal("0")
    
# WRONG: Never allocate to junior if senior < 100%
```

**LME Adjustments:**
```python
# When Librarian flags collateral leakage
if collateral_leakage_flags:
    adjusted_collateral = base_collateral - leakage_amount
    # Recalculate waterfall with reduced collateral
```

---

## Common Pitfalls for AI Agents

### ❌ Don't Do This

1. **Float math for currency:** `recovery = 150000000.0 / 200000000.0`  
   ✅ **Do this:** `recovery = Decimal("150000000") / Decimal("200000000")`

2. **Skip provenance:** `signal = {"type": "dropdown", "severity": "high"}`  
   ✅ **Do this:** `signal = {"type": "dropdown", "severity": "high", "section": "7.02", "page": 45}`

3. **Violate APR:** `if value_remaining > 0: allocate_to_junior(value_remaining)`  
   ✅ **Do this:** `if senior_recovery >= Decimal("1.0") and value_remaining > 0: ...`

4. **Hardcode thresholds:** `if leverage > 6.0: return "high_risk"`  
   ✅ **Do this:** `if leverage > settings.leverage_threshold: return "high_risk"`

5. **Ignore Critical Variance:** Ship report when model predicts 90% recovery but market shows 30%  
   ✅ **Do this:** Auditor must reconcile or flag before Reporter publishes

---

## External Dependencies

### Required APIs (for live data)

- **SEC EDGAR:** Free, requires `SEC_USER_AGENT` with email (mandatory)
- **Alpha Vantage:** Stock prices (free tier available, API key required)
- **IEX Cloud:** Market data (free tier available, API key required)
- **FRED:** Treasury yields (free, no key required)

### Optional Commercial APIs

- **9fin:** Precedent transactions, restructuring intelligence
- **Bloomberg:** Market data, credit ratings
- **FactSet:** Financial data, comparables

### Rate Limiting & Caching

- **SEC EDGAR:** 10 requests/second max (enforced by client)
- **Caching:** Redis for API responses (TTL: 1 hour for market data, 24 hours for filings)
- **Circuit breaker:** Auto-disable failing APIs after 5 consecutive errors

---

## Key Files for Cloud Agents

### Agent Discovery
- `AGENTS.md` - Human-readable agent guide
- `.github/agent-registry.json` - Machine-readable agent manifest
- `.cursor/agents/<agent-name>.md` - Detailed agent mandates

### Development Guides
- `.github/agent-context/common-tasks.md` - Task templates
- `docs/AGENT_PROTOCOL.md` - Communication format
- `docs/ROADMAP.md` - Project roadmap and phase status

### Infrastructure
- `INFRASTRUCTURE_SUMMARY.md` - Complete infrastructure overview
- `docker-compose.yml` - Multi-service orchestration
- `.github/workflows/ci.yml` - CI/CD pipeline

---

## Quick Reference Commands

```bash
# Full pipeline (single document)
python -m signal_triage.cli <file> --pipeline

# Batch processing
python -m signal_triage.cli --pipeline --batch <folder>

# Individual agent execution
python -m signal_triage.cli <file> --librarian --json
python -m signal_triage.cli <file> --waterfall --ev 150

# API server
python run_api_server.py

# Dashboard
streamlit run signal_triage/ui/dashboard.py

# Tests
pytest tests/test_validation.py -v
```

---

## Support Resources

- **Documentation:** `docs/` folder (44 markdown files)
- **Examples:** `examples/` folder (J.Crew, Serta, Hertz case studies)
- **Issue Tracker:** GitHub Issues (when repo is public)
- **API Docs:** http://localhost:8000/docs (when server running)

# AI Agent Integration Guide

## Overview

Signal Triage uses a **7-agent orchestration system** for forensic distressed debt analysis. Each agent has specialized responsibilities and operates as part of an integrated pipeline.

**Architecture:** Multi-agent system with defined handoffs, source attribution, and audit trails. One-command pipeline execution from document ingestion to final analyst report.

---

## Agent Roles & Entry Points

| Agent | CLI Command | API Endpoint | Purpose | Primary Files |
|-------|-------------|--------------|---------|---------------|
| **Author** | `python -m signal_triage.cli <file> --author` | `/api/v1/agent/author/execute` | Document ingestion, API integrations, versioned configs | `signal_triage/ingest/` |
| **Librarian** | `python -m signal_triage.cli <file> --librarian` | `/api/v1/agent/librarian/execute` | Covenant extraction, LME detection, collateral leakage flags | `signal_triage/document_intel/` |
| **Quant** | `python -m signal_triage.cli <file> --waterfall` | `/api/v1/agent/quant/execute` | Recovery waterfall, fulcrum identification, APR enforcement | `signal_triage/recovery_engine.py` |
| **Benchmarker** | `python -m signal_triage.cli <file> --benchmark` | `/api/v1/agent/benchmarker/execute` | Market context, precedent transactions, Critical Variance detection | `signal_triage/agents/benchmarker.py` |
| **Auditor** | `python -m signal_triage.cli <file> --audit` | `/api/v1/agent/auditor/execute` | Stress-testing, validation, audit trail, publish gate | `signal_triage/agents/auditor.py` |
| **Comparator** | `python -m signal_triage.cli <file> --compare` | `/api/v1/agent/comparator/execute` | Prior vs current, peer comparison, delta analysis | `signal_triage/agents/comparator.py` |
| **Reporter** | `python -m signal_triage.cli <file> --report` | `/api/v1/agent/reporter/execute` | Final analyst report, portfolio summary, narrative | `signal_triage/reports/document_report.py` |

---

## Full Pipeline Execution

### Single Document
```bash
python -m signal_triage.cli path/to/document.pdf --pipeline
```

### Batch Processing
```bash
python -m signal_triage.cli --pipeline --batch path/to/folder
python -m signal_triage.cli --pipeline --batch path/to/folder --recursive
```

### Optional Filters
```bash
# Filter by industry and geography for Benchmarker
python -m signal_triage.cli <file> --pipeline --industry Retail --geography US

# Skip Auditor gate (draft mode)
python -m signal_triage.cli <file> --pipeline --no-audit-gate
```

**Exit Codes:**
- `0` - Report published (Auditor passed or gate not required)
- `1` - Report not published (Auditor gate failed, Critical Variance unresolved)

---

## Agent Orchestration Flow

```
Author → Librarian → Quant ← Benchmarker → Auditor → Comparator → Reporter
  ↓          ↓         ↓           ↓            ↓          ↓          ↓
Chunks   Covenants  Waterfall   Market      Stress-   Deltas    Final
         + LME      + Fulcrum   Context     Test               Report
         Flags                  
```

**Handoffs:**
1. **Author → Librarian:** Document chunks with provenance (page numbers, source)
2. **Librarian → Quant:** Baskets, covenant limits, LME/collateral leakage flags
3. **Quant → Auditor:** Recovery model, fulcrum, situational summary
4. **Benchmarker → Quant:** Market multiples (EV driver)
5. **Benchmarker → Auditor:** Precedent recovery rates, Critical Variance flags
6. **Auditor → Reporter:** Pass/fail status, audit trail
7. **Comparator → Reporter:** Prior/peer deltas, material-change narrative
8. **Reporter → Analyst:** Single auditable report with traceability

---

## REST API Integration (Cloud Agents)

### Start API Server
```bash
# Development mode
python run_api_server.py

# Production mode (4 workers)
python run_api_server.py --production
```

### API Documentation
- **Interactive Swagger UI:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Comprehensive Guide:** [docs/API_GUIDE.md](docs/API_GUIDE.md)

### Example: Submit Analysis via API
```python
import requests

# Submit document for analysis
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "document_url": "https://example.com/filing.pdf",
        "ticker": "ABC",
        "analysis_type": "full"
    }
)

job_id = response.json()["job_id"]

# Poll for completion
status = requests.get(f"http://localhost:8000/jobs/{job_id}").json()
```

### Agent-Specific Endpoints
```bash
# Execute individual agent
POST /api/v1/agent/{agent_name}/execute
  Body: {"document_path": "...", "options": {...}}

# Get agent status
GET /api/v1/agent/{agent_name}/status

# Execute full pipeline
POST /api/v1/pipeline/execute
  Body: {"document_path": "...", "options": {...}}
```

---

## Architecture Documentation

### Detailed Agent Documentation
- **Agent Definitions:** `.cursor/agents/<agent-name>.md` (local development)
- **Orchestration Plan:** `.cursor/agents/ORCHESTRATION.md`
- **Project Roadmap:** `docs/ROADMAP.md`
- **Agent Protocol:** `docs/AGENT_PROTOCOL.md` (communication format)

### Cloud Agent Context
- **Project Overview:** `.github/agent-context/project-overview.md`
- **Common Tasks:** `.github/agent-context/common-tasks.md`
- **Agent Registry:** `.github/agent-registry.json` (machine-readable)

### Key Capabilities
- **LME Detection:** 21 categories (dropdown, S-Prime, uptiering, J.Crew blockers, Serta uptier, etc.)
- **Covenant Forensics:** EBITDA normalization, leverage/FCCR headroom, critical distress (<15%)
- **Recovery Waterfall:** Decimal-precision, APR enforcement, fulcrum identification
- **Chapter 11 Modeling:** Liquidation value, adequate protection, feasibility analysis
- **Market Validation:** Live SEC EDGAR data, precedent transactions, Critical Variance detection

---

## Development Quick Start

### Run Full Pipeline (Test)
```bash
python -m signal_triage.cli tests/fixtures/benchmark_corpus/low_distress.txt --pipeline
```

### Run Tests
```bash
# All tests (120+ tests)
pytest

# Agent-specific tests
pytest tests/test_librarian.py -v
pytest tests/test_auditor.py -v

# Validation suite
pytest tests/test_validation.py -v
```

### Docker Deployment
```bash
# Start all services (PostgreSQL, Redis, API, Dashboard)
docker-compose up -d

# Access services
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8501
```

---

## Configuration & Environment

### Required Environment Variables
```bash
# SEC EDGAR (required for live market data)
SEC_USER_AGENT="YourCompany/1.0 (contact@example.com)"

# Feature Flags
BENCHMARKER_USE_LIVE="1"
BENCHMARKER_DATA_SOURCE="edgar"

# API Keys (optional, for premium data)
ALPHA_VANTAGE_API_KEY="your-key"
IEX_CLOUD_API_KEY="your-key"
```

### Configuration Files
- **Signals Config:** `signals_config.json` - Signal definitions and weights
- **Benchmark Corpus:** `tests/fixtures/benchmark_corpus/` - Test documents
- **Environment Template:** `.env.example` (local), `.env.cloud.example` (cloud)

---

## Key Principles for Cloud Agents

1. **Source Attribution:** Every signal, covenant, and recovery assumption must be traceable to source (document, page, section, API)
2. **Versioned Configs:** Config versions captured in audit trail for reproducibility
3. **Decimal Precision:** All financial calculations use `decimal.Decimal` (no float drift)
4. **Absolute Priority Rule:** No value to junior tranches until senior fully recovered
5. **Auditor Gate:** Final reports only published when Auditor validates (or `--no-audit-gate` used)
6. **Critical Variance:** Discrepancies between model and market precedents must be reconciled
7. **Provenance:** Document chunks include page numbers; API data includes source and date

---

## Support & Documentation

- **Setup Guide:** [SETUP_INFRASTRUCTURE.md](SETUP_INFRASTRUCTURE.md)
- **Quick Start:** [QUICK_START.md](QUICK_START.md)
- **API Guide:** [docs/API_GUIDE.md](docs/API_GUIDE.md)
- **Forensic Capabilities:** [docs/FORENSIC_ENHANCEMENTS.md](docs/FORENSIC_ENHANCEMENTS.md)
- **LME Categories:** [docs/LME_CATEGORIES.md](docs/LME_CATEGORIES.md)
- **UI Guide:** [docs/UI_REDESIGN_AND_VALIDATION.md](docs/UI_REDESIGN_AND_VALIDATION.md)

---

## Cloud Deployment

Signal Triage is production-ready with:
- **Docker/Docker Compose:** Multi-service orchestration (API, Dashboard, PostgreSQL, Redis)
- **CI/CD:** GitHub Actions (lint, test, security scan, Docker build/push)
- **Monitoring:** Health checks, logging, error tracking ready
- **Rate Limiting:** Built-in for external APIs (SEC EDGAR, market data)
- **Caching:** Redis for API responses and market data

See [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md) for complete infrastructure details.

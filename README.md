# Signal Triage — Forensic Restructuring Desk

**Institutional-grade forensic decision engine for distressed investing.**

A comprehensive CLI and dashboard tool for analyzing credit agreements, 10-Ks, and restructuring documents with forensic-level LME detection, covenant headroom analysis, APR enforcement, and Ch. 11 feasibility modeling.

## ⚡ **QUICK START** (One Command)

```powershell
# Windows - Double-click or run:
START_APP.bat

# Mac/Linux:
chmod +x START_APP.sh && ./START_APP.sh
```

**Then open:** http://localhost:8501

**See:** [QUICK_START.md](QUICK_START.md) for detailed setup and troubleshooting.

---

## 🚀 NEW: Live Market Data Integration (Workstream 1)

**Transform from demo to production with live SEC EDGAR data!**

Signal Triage now supports live market data from SEC EDGAR, FRED, Alpha Vantage, IEX Cloud, and commercial sources (9fin, Bloomberg, etc.). Replace all stub data with real-time market intelligence.

### Quick Setup (2 Minutes):
```powershell
# Set your email (required by SEC)
$env:SEC_USER_AGENT = "YourCompany/1.0 (your.email@example.com)"

# Enable live data
$env:BENCHMARKER_USE_LIVE = "1"
$env:BENCHMARKER_DATA_SOURCE = "edgar"

# Verify setup
py demo_live_data.py
```

**What You Get:**
- ✅ Live 8-K filings (comparables, distress events)
- ✅ Company financials (revenue, debt, EBITDA from SEC XBRL)
- ✅ Treasury yields (credit spread calculations)
- ✅ Real-time stock prices
- ✅ Production-grade infrastructure (rate limiting, caching, retries)

**Documentation:**
- 📘 [Workstream 1 Setup Guide](docs/WORKSTREAM_1_SETUP.md) - Complete configuration guide
- ✅ [Completion Report](WORKSTREAM_1_COMPLETE.md) - What was built and why
- 🎯 [API Status](WORKSTREAM_1_COMPLETE.md#api-status-matrix) - Which APIs are ready

---

## 🆕 Professional UI & Validation Layer (v2.0)

**NEW:** Signal Triage now features a **Bloomberg-terminal style interface** with comprehensive **validation and sanity checks** for institutional use.

### Key Features:
- **Dark Theme:** Professional, high-density dashboard optimized for senior partner presentations
- **Interactive EBITDA Multiple Slider:** Real-time fulcrum migration as you adjust valuation multiples
- **Validation Layer:** Comprehensive sanity checks (recovery ≤ EV, APR violations, data integrity)
- **Data Quality Flags:** Explicit marking of HARD_DATA vs INFERRED assumptions
- **Zero-Casualty Interface:** All emojis and casual language removed
- **Graceful Degradation:** Analysis proceeds with warnings; missing data explicitly flagged

### Quick Start (Dashboard):
```bash
streamlit run signal_triage/ui/dashboard.py
```

### Quick Start (API Server):
```bash
# Start comprehensive REST API server
python run_api_server.py

# Access interactive docs
# http://localhost:8000/docs

# Run comprehensive tests
python test_api_comprehensive.py
```

**Documentation:**
- 📘 [UI Redesign & Validation Guide](docs/UI_REDESIGN_AND_VALIDATION.md) (comprehensive 500+ line guide)
- 🎨 [UI Quick Reference](docs/UI_QUICK_REFERENCE.md) (color palette, badges, components)
- 🚀 [API Guide](docs/API_GUIDE.md) (REST API reference & Python client)
- ⚡ [API Comprehensive Features](docs/API_COMPREHENSIVE_FEATURES.md) (advanced features & forensics)
- 📋 [Implementation Summary](IMPLEMENTATION_SUMMARY.md) (what was built)

**Demo:**
```bash
py demo_validation.py  # Run validation demos (no pytest required)
python test_api_integration.py  # Test API integration
```

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access services
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8501
```

### Option 2: Local Installation

1. Make sure you have Python 3.10 or higher installed
2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

**New to the project?** See [SETUP_INFRASTRUCTURE.md](SETUP_INFRASTRUCTURE.md) for complete setup guide.

## Usage

### CLI Usage

#### Basic usage
```bash
python main.py path/to/your/file.txt
```

#### With verbose output
```bash
python main.py path/to/your/file.txt --verbose
```

#### Analyst checklist only
```bash
python main.py path/to/your/file.txt --checklist-only
```

#### Recovery waterfall (EV and tranches)
```bash
python main.py --waterfall --ev 150 --tranches "Senior:100,Mezz:100,Unsecured:50"
```

#### After installation
Once installed, you can also run:
```bash
signal-triage path/to/your/file.txt
```

### API Usage

#### Start the server
```bash
# Development mode (auto-reload)
python run_api_server.py

# Production mode (4 workers)
python run_api_server.py --production
```

#### Submit analysis (Python)
```python
import requests

# Submit document URL for analysis
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
import time
while True:
    status = requests.get(f"http://localhost:8000/jobs/{job_id}").json()
    if status["status"] == "completed":
        # Get analysis results
        analysis = requests.get(
            f"http://localhost:8000/analyses/{status['analysis_id']}"
        ).json()
        print(f"Distress Score: {analysis['distress_score']}")
        break
    time.sleep(2)
```

#### API Documentation
- Interactive Swagger UI: http://localhost:8000/docs
- Complete guide: [docs/API_GUIDE.md](docs/API_GUIDE.md)

## How it works

### **Forensic Analysis (Not Just Keyword Matching)**

- **LME Vulnerability Audit:** Detects 21 categories of liability management exercises including precedent cases (J.Crew, Serta, Incora). Analyzes trap doors, dropdown risk, priming mechanics, vote rigging, and double-dip structures.
- **Covenant Headroom:** Strips aggressive EBITDA add-backs (run-rate synergies, anticipated savings) with credibility haircuts; calculates leverage and FCCR headroom; flags critical distress when headroom < 15%.
- **Recovery Waterfall:** Decimal-precision waterfall with Pari Passu, fulcrum identification, LME-adjusted EV, and **APR violation detection** (flags when junior gets value while senior < 100%).
- **Ch. 11 Feasibility:** Models going concern vs liquidation value; calculates adequate protection requirements; assesses reorganization viability.
- **Priming Risk:** Analyzes incremental facility baskets + amendment provisions to detect if 50.1% Required Lenders can prime minority (Serta-style risk).
- **Double-Dip Tracing:** Identifies multiple claims on same economic exposure (empty box, non-guarantor structures).

## Forensic capabilities and documentation

### **LME Categories (21 Total)**
**Structural/Collateral:** dropdown, S-Prime, uptiering, Texas two-step, double-dip/triple-dip, basket/transfer, asset sale, investment basket, transfer to unrestricted sub, structural subordination.  
**Out-of-Court:** consent solicitation/exchange, equity cure, lender voting squeeze, forbearance/standstill.  
**Bankruptcy:** substantive consolidation/cramdown, crossover/prepack, make-whole/disallowance, PIK.  
**Precedents:** J.Crew blocker, Serta uptier, Incora/Wesco vote rigging.

### **Forensic Modules**
- **`covenant_forensics.py`** — EBITDA normalization, leverage/FCCR headroom, critical distress (<15%)
- **`chapter11_modeling.py`** — Liquidation value, adequate protection, Ch. 11 feasibility
- **`recovery_engine.py`** — Waterfall + APR violations + double-dip tracing
- **`lme_definitions.py`** — Programmatic definitions (`get_definition(id)`), market tier (Tight/Market/Toxic)

### **Documentation**
- **`docs/LME_CATEGORIES.md`** — In-depth definitions for all 21 categories (what, why, severity, precedents)
- **`docs/FORENSIC_ENHANCEMENTS.md`** — Implementation summary with usage examples
- **`docs/CURRENT_CAPABILITIES.md`** — Production status and comprehensive capability matrix

### **Dashboard**
```bash
streamlit run signal_triage/ui/dashboard.py
```
Bloomberg-style interface: score card, LME flags with definitions, waterfall with APR violations, covenant headroom gauge, Ch. 11 feasibility.

## Project Structure

- `signal_triage/` - Main package
  - `analyzer.py` - Core analysis and distress score
  - `cli.py` - Command-line interface
  - `lme_parser.py` - LME (dropdown, S-Prime, uptiering, Texas two-step, double-dip, etc.) detection
  - `lme_definitions.py` - Structured category definitions (display name, definition, rationale, severity)
  - `recovery_engine.py` - Recovery waterfall and fulcrum
  - `checklist.py` - Analyst checklist from signals
- `docs/` - Documentation (including **LME_CATEGORIES.md** for in-depth signal definitions)
- `tests/` - Unit tests
- `main.py` - Entry point
- `setup.py`, `requirements.txt`, `README.md`

## Development

Run tests:
```bash
python -m unittest discover -s tests -v
```

---

## 🤖 AI Agent Integration

Signal Triage uses a **7-agent orchestration system** designed for both local and cloud-based AI agents. Each agent has specialized responsibilities and operates as part of an integrated pipeline.

### Agent Architecture

```
Author → Librarian → Quant ← Benchmarker → Auditor → Comparator → Reporter
  ↓          ↓         ↓           ↓            ↓          ↓          ↓
Ingest   Extract   Waterfall   Market      Validate   Compare    Publish
         Covenants  + Fulcrum   Context                           Report
```

### Quick Reference

| Agent | Purpose | CLI Command | API Endpoint |
|-------|---------|-------------|--------------|
| **Author** | Document ingestion, API integration | `--author` | `/api/v1/agent/author/execute` |
| **Librarian** | Covenant extraction, LME detection | `--librarian` | `/api/v1/agent/librarian/execute` |
| **Quant** | Recovery waterfall, fulcrum | `--waterfall` | `/api/v1/agent/quant/execute` |
| **Benchmarker** | Market context, precedents | `--benchmark` | `/api/v1/agent/benchmarker/execute` |
| **Auditor** | Stress-testing, validation | `--audit` | `/api/v1/agent/auditor/execute` |
| **Comparator** | Prior vs current, peer analysis | `--compare` | `/api/v1/agent/comparator/execute` |
| **Reporter** | Final analyst report | `--report` | `/api/v1/agent/reporter/execute` |

### Full Pipeline Execution

```bash
# Single document
python -m signal_triage.cli <file> --pipeline

# Batch processing
python -m signal_triage.cli --pipeline --batch <folder>
```

### Agent Documentation

- **Agent Integration Guide:** [AGENTS.md](AGENTS.md) - Complete guide for AI agents
- **Agent Registry:** [.github/agent-registry.json](.github/agent-registry.json) - Machine-readable agent manifest
- **Agent Protocol:** [docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md) - Communication format
- **Project Overview:** [.github/agent-context/project-overview.md](.github/agent-context/project-overview.md) - LLM context
- **Common Tasks:** [.github/agent-context/common-tasks.md](.github/agent-context/common-tasks.md) - Development templates

### Cloud Agent Support

Signal Triage is optimized for cloud-based AI agents (GitHub Copilot Workspace, OpenAI Assistants, Anthropic Claude Code, Replit Agent, etc.):

✅ **Agent Discovery:** Machine-readable registry with agent capabilities  
✅ **REST API:** Full OpenAPI/Swagger documentation at `/docs`  
✅ **Standardized Protocol:** JSON-based request/response format  
✅ **Source Attribution:** All outputs include provenance (page, section, API source)  
✅ **Versioned Configs:** Reproducible analysis with audit trails  
✅ **Cloud Deployment:** Docker, Render, Fly.io configurations included

### API Integration Example

```python
import requests

# Execute Librarian agent
response = requests.post(
    "http://localhost:8000/api/v1/agent/librarian/execute",
    json={
        "agent": "librarian",
        "task": "extract_covenants",
        "input": {
            "document_path": "path/to/document.pdf"
        }
    }
)

result = response.json()
print(f"Covenants found: {len(result['output']['covenants'])}")
print(f"LME flags: {len(result['output']['collateral_leakage_flags'])}")
```

### Key Principles

1. **Source Attribution:** Every signal, covenant, and recovery assumption is traceable
2. **Decimal Precision:** All financial calculations use `decimal.Decimal`
3. **Absolute Priority Rule:** No value to junior tranches until senior fully recovered
4. **Auditor Gate:** Final reports only published when validated
5. **Critical Variance:** Model vs market discrepancies must be reconciled

### Cloud Deployment

```bash
# Render.com
# Uses render.yaml - configure secrets in dashboard

# Fly.io
fly launch  # First time
fly deploy  # Updates

# Docker (any cloud)
docker build -t signal-triage .
docker run -p 8000:8000 signal-triage
```

**See:** [INFRASTRUCTURE_SUMMARY.md](INFRASTRUCTURE_SUMMARY.md) for complete deployment guide

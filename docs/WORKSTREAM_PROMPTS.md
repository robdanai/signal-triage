# Signal Triage: Parallel Workstream Prompts

**Purpose:** These prompts allow multiple Cursor instances to work on different parts of the codebase simultaneously without conflicts.

**Date Created:** 2026-01-29

---

## 🎯 Workstream 1: Live Market Data Integration

**Status:** 🔄 **HIGHEST PRIORITY**  
**Files:** `signal_triage/agents/benchmarker.py`, `signal_triage/agents/market_data_live.py`  
**No Conflicts With:** Workstreams 2, 3, 4

### Prompt for Cursor Agent:

```
I need you to complete the live market data integration for the Benchmarker agent in Signal Triage. 

CONTEXT:
- The project is a production-ready distressed debt analysis tool
- Benchmarker currently uses stubs for recovery rates and market data
- We have fully implemented: SEC EDGAR, FRED, Alpha Vantage, IEX Cloud
- We have stub interfaces for: 9fin, Bloomberg, Reorg, Debtwire

YOUR MISSION:
1. Review `signal_triage/agents/benchmarker.py` and identify all stub/hardcoded data
2. Replace stubs with live data calls from `market_data_live.py`
3. Wire SEC EDGAR company financials into benchmarking logic
4. Add fallback logic: live data → cached data → stubs (graceful degradation)
5. Update `get_recovery_rates_by_industry()` to use SEC EDGAR 8-K precedents
6. Ensure all functions return proper source attribution in results
7. Add integration tests in `tests/test_benchmarker.py` for live data paths
8. Update `docs/LIVE_DATA_SETUP.md` with any new environment variables

CONSTRAINTS:
- Do NOT modify: pipeline.py, cli.py, fastapi_app/ (other workstreams)
- Do NOT modify: enhanced_parser.py, document_intel/* (workstream 3)
- Maintain backward compatibility with existing stub behavior
- Use environment variable checks: if BENCHMARKER_USE_LIVE is set, use live data
- All live data calls must be wrapped in try/except with fallback to stubs

SUCCESS CRITERIA:
- Benchmarker uses live SEC EDGAR data when BENCHMARKER_USE_LIVE=1
- All Critical Variance flags cite real data sources
- Tests pass with and without live API keys
- No breaking changes to existing pipeline

FILES YOU'LL MODIFY:
- signal_triage/agents/benchmarker.py (primary)
- signal_triage/agents/market_data_live.py (enhancements)
- tests/test_benchmarker.py (add live data tests)
- docs/LIVE_DATA_SETUP.md (update if needed)

START BY:
1. Reading benchmarker.py to identify all stub data
2. Reading market_data_live.py to understand available APIs
3. Creating a plan for replacing stubs systematically
```

---

## 🌐 Workstream 2: FastAPI Pipeline Integration

**Status:** 🔄 **HIGH PRIORITY**  
**Files:** `signal_triage/fastapi_app/main.py`, `run_api_server.py`  
**No Conflicts With:** Workstreams 1, 3, 4

### Prompt for Cursor Agent:

```
I need you to connect the FastAPI application to the actual Signal Triage analysis pipeline.

CONTEXT:
- FastAPI skeleton exists in `signal_triage/fastapi_app/main.py`
- Database models, infrastructure (rate limiter, cache, circuit breaker) are complete
- Line 352 in main.py has TODO: "Call actual analysis pipeline"
- Current behavior: creates stub analysis with dummy results
- Core pipeline is in `signal_triage/pipeline.py` (run_pipeline, run_pipeline_batch)

YOUR MISSION:
1. Wire `process_analysis_job()` to call the actual pipeline
2. Handle file uploads: save to temp file, pass to pipeline, return results
3. Handle URL ingestion: use `ingest/web.py` for document fetching
4. Store full analysis results (signals, LME flags, covenant headroom, waterfall) in Analysis table
5. Add proper error handling and job status updates (PENDING → RUNNING → COMPLETED/FAILED)
6. Implement webhook delivery with actual analysis data
7. Add endpoint: GET /analyses/{id}/report for full auditable report
8. Write integration tests in `tests/test_fastapi_integration.py`

CONSTRAINTS:
- Do NOT modify: benchmarker.py, market_data_live.py (workstream 1)
- Do NOT modify: enhanced_parser.py (workstream 3)
- Do NOT modify: core pipeline logic in pipeline.py (only import and call)
- Maintain existing API schema (don't break existing endpoints)
- Ensure backward compatibility with database models

SUCCESS CRITERIA:
- POST /analyze → runs actual pipeline → returns real results
- Job status accurately reflects pipeline progress
- Analysis results stored in database include full signals JSON
- Webhook delivers actual analysis data (not stubs)
- Tests demonstrate end-to-end workflow

FILES YOU'LL MODIFY:
- signal_triage/fastapi_app/main.py (primary - remove TODO, add pipeline integration)
- run_api_server.py (ensure proper startup script)
- tests/test_fastapi_integration.py (create new file)
- docs/API_INFRASTRUCTURE.md (update with actual usage examples)

START BY:
1. Reading pipeline.py to understand run_pipeline() inputs/outputs
2. Reading main.py process_analysis_job() to see current stub logic
3. Creating a plan for seamless integration with proper error handling
```

---

## 🔬 Workstream 3: Enhanced Parser Integration & Validation

**Status:** 🔄 **MEDIUM PRIORITY**  
**Files:** `signal_triage/document_intel/enhanced_parser.py`, integration with `pipeline.py`  
**No Conflicts With:** Workstreams 1, 2, 4

### Prompt for Cursor Agent:

```
I need you to validate and fully integrate the Enhanced Parser into the main pipeline.

CONTEXT:
- Enhanced parser implemented in Jan 2026 (`document_intel/enhanced_parser.py`)
- Features: capital structure table extraction, EBITDA normalization, LME risk scoring
- Tests exist in `tests/test_enhanced_parser.py` and pass
- ROADMAP says "handoff to Quant complete" but unclear if fully wired into pipeline
- Core pipeline in `signal_triage/pipeline.py` and CLI in `signal_triage/cli.py`

YOUR MISSION:
1. Verify enhanced parser is properly wired into the pipeline flow
2. Check if `run_pipeline()` uses enhanced_parser or standard extractor
3. Ensure CLI flags (`--librarian`, `--from-signals`) use enhanced extraction
4. Add integration test: real PDF → enhanced parser → waterfall with LME adjustments
5. Validate capital structure table extraction on sample credit agreements
6. Test EBITDA normalization with real 10-K add-back language
7. Create demo script: `demo_enhanced_parser_realworld.py` with 3 real-world examples
8. Document any edge cases or limitations discovered during testing

CONSTRAINTS:
- Do NOT modify: benchmarker.py (workstream 1)
- Do NOT modify: fastapi_app/ (workstream 2)
- Maintain backward compatibility (enhanced parser should be opt-in or default)
- Do NOT break existing pipeline tests

SUCCESS CRITERIA:
- Enhanced parser runs by default in pipeline (or via clear CLI flag)
- Capital structure tables extracted accurately from real PDFs
- EBITDA add-backs flagged with risk scores (0-10 scale)
- LME leakage risk scores flow into waterfall EV adjustments
- Demo script shows 3 compelling real-world examples
- Documentation updated with any discovered edge cases

FILES YOU'LL MODIFY:
- signal_triage/pipeline.py (verify/enhance integration)
- signal_triage/cli.py (add/verify enhanced parser flags)
- demo_enhanced_parser_realworld.py (create new comprehensive demo)
- tests/test_pipeline_enhanced_parser.py (create integration test)
- docs/ENHANCED_PARSER.md (update with real-world validation results)

START BY:
1. Reading enhanced_parser.py to understand its API
2. Tracing pipeline.py to see where extraction happens
3. Running existing tests to ensure baseline works
4. Creating a test plan for real-world validation
```

---

## 📚 Workstream 4: Examples, Case Studies & User Experience

**Status:** 🔄 **MEDIUM PRIORITY**  
**Files:** `examples/` (new directory), `docs/CASE_STUDIES.md` (new), README updates  
**No Conflicts With:** Workstreams 1, 2, 3

### Prompt for Cursor Agent:

```
I need you to create compelling real-world examples and improve user onboarding experience.

CONTEXT:
- Signal Triage is production-ready but lacks real-world demonstration
- Documentation is technical but missing "show don't tell" examples
- Target users: institutional restructuring desks (PJT, Houlihan, Lazard, Moelis)
- Famous cases: J.Crew (2017), Serta (2020), Hertz (2020), Incora (2020)

YOUR MISSION:
1. Create `examples/` directory with 3-5 real-world case studies
2. For each case: input document → analysis command → output interpretation
3. Write `docs/CASE_STUDIES.md` with narrative explanations
4. Create `examples/quickstart.py` - 5-minute getting started script
5. Add `examples/jupyter_notebook_demo.ipynb` for interactive exploration
6. Update main README.md with compelling "Why Signal Triage?" section
7. Create `CONTRIBUTING.md` for open-source contributors
8. Add `examples/docker-compose.yml` for one-command local setup

CONSTRAINTS:
- Do NOT modify: any code in signal_triage/ (read-only for you)
- Do NOT modify: existing docs (only add new case studies doc)
- Use publicly available documents (SEC filings, court documents)
- Cite sources properly to avoid legal issues

SUCCESS CRITERIA:
- 3+ real-world case studies with actual analysis runs
- Quickstart script gets user to first results in < 5 minutes
- Jupyter notebook is interactive and educational
- README.md has compelling opening that sells the value prop
- Docker setup works on Windows, Mac, Linux

FILES YOU'LL CREATE:
- examples/quickstart.py
- examples/case_studies/jcrew_analysis.py
- examples/case_studies/serta_analysis.py
- examples/case_studies/hertz_analysis.py
- examples/jupyter_notebook_demo.ipynb
- examples/docker-compose.yml
- examples/README.md
- docs/CASE_STUDIES.md
- CONTRIBUTING.md

START BY:
1. Reading existing documentation to understand capabilities
2. Researching public documents from J.Crew, Serta, Hertz cases
3. Creating outline for case studies
4. Running pipeline on sample documents to ensure examples are realistic
```

---

## 🚀 How to Use These Workstreams

### **Option 1: Sequential Execution (Recommended for Solo Work)**
Run workstreams in priority order:
1. Workstream 1 (Live Data) - highest user value
2. Workstream 2 (API Integration) - enables scalability  
3. Workstream 3 (Enhanced Parser) - quality validation
4. Workstream 4 (Examples) - user experience polish

### **Option 2: Parallel Execution (Multiple Cursor Instances)**
Open 4 separate Cursor windows:
- Window A: Workstream 1 (focus on `agents/benchmarker.py`)
- Window B: Workstream 2 (focus on `fastapi_app/main.py`)
- Window C: Workstream 3 (focus on `document_intel/enhanced_parser.py`)
- Window D: Workstream 4 (focus on `examples/` directory)

**No conflicts** because each workstream touches different files.

### **After Completion**
Run full test suite to ensure no integration issues:
```bash
python -m pytest tests/ -v
```

Then update `docs/ROADMAP.md` and `docs/STATUS_SUMMARY.md` with progress.

---

## 📊 Progress Tracking

| Workstream | Status | Assigned To | Completion Date | Notes |
|------------|--------|-------------|-----------------|-------|
| 1. Live Market Data | 🔄 Not Started | | | High priority |
| 2. FastAPI Integration | 🔄 Not Started | | | High priority |
| 3. Enhanced Parser | 🔄 Not Started | | | Medium priority |
| 4. Examples & UX | 🔄 Not Started | | | Medium priority |

---

## 🎯 Success Metrics

After all workstreams complete:
- ✅ Benchmarker uses live SEC EDGAR data (no stubs)
- ✅ API server runs actual pipeline (not dummy results)
- ✅ Enhanced parser validated on 10+ real credit agreements
- ✅ 3+ case studies with real-world examples
- ✅ All 150+ tests passing
- ✅ User can go from install to first analysis in < 5 minutes

---

**Last Updated:** 2026-01-29  
**Next Review:** After each workstream completes

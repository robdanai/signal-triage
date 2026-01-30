# Signal Triage Roadmap

Single source of truth for phase progress, orchestration, and high-level todo.

**Iterative refresh:** When the codebase or pipeline changes, update this file (phase status, todo, Done) and keep **`.cursor/agents/ORCHESTRATION.md`** (Current Implementation) and **`.cursor/agents/README.md`** aligned so plans match reality.

---

## Ambitious Goal (Vision)

**One-command production pipeline:** Ingest document(s) → extract covenants → run recovery waterfall → validate against market → stress-test → compare (prior/peers) → emit a single, auditable analyst report. Every step is versioned and reproducible so any run can be re-verified by the Auditor.

---

## Vision → Todo Alignment (Big Picture)

Todos should map directly to this pipeline. Each step of the vision implies what’s “done” vs “next.”

| Vision step | What “done” looks like | What “next” (todo) is |
|-------------|------------------------|------------------------|
| **1. Ingest** | PDF/txt with provenance; one CLI; versioned configs; web/EDGAR ingestion. | None; web/EDGAR implemented in `ingest/web.py`. |
| **2. Extract covenants** | Librarian wired to CLI and recovery; LME/collateral flags; section/page in JSON. | None; handoff to Quant complete. |
| **3. Run recovery waterfall** | Waterfall, fulcrum, EV sensitivity, LME-adjusted EV, Decimal, situational summary; tornado drivers (EV, collateral). | None. |
| **4. Validate against market** | Benchmarker in pipeline; multiples, precedent recovery, Critical Variance flags; source citation. | **Benchmarker:** Replace stubs with live APIs (EDGAR, 9fin, etc.) so “validate against market” uses real market data. |
| **5. Stress-test** | Auditor runs in pipeline; APR, precision, Critical Variance reconciliation; audit trail; gate for report. | None. |
| **6. Compare (prior/peers)** | Prior vs current in batch (2+ docs); score/tier deltas, material-change narrative in report. | **Comparator (Phase 5):** Vs peers / vs baseline when external or peer data exists. |
| **7. Emit auditable report** | Single report per doc and batch; aggregates all agents; published only when Auditor passes (when gate required). | None. |
| **Versioned & reproducible** | Config versions and document sources in audit trail; pipeline tests; improvement checklist. | **Phase 6:** Broader test coverage and any run manifest / repro script if needed. |

**Principle:** A todo is vision-aligned if it closes a gap in one of the seven pipeline steps or in “versioned & reproducible.” If a todo doesn’t map to the pipeline or reproducibility, drop it or reframe it.

---

## Subagent Orchestration (Run in Tandem)

To achieve the goal above, the parent Agent should delegate **objectives** to subagents in this order. Each subagent owns its objective; handoffs follow the flow below.

| Order | Subagent | Objective |
| ----- | -------- | --------- |
| 1 | **Author** | Single CLI entry point and versioned configs so the full pipeline can be invoked with one command; DocumentChunk ingestion with provenance for PDF/txt (and design or stub for web/URL when Phase 5 is active). |
| 2 | **Librarian** | Covenant/basket extraction wired to CLI and recovery path; LME/collateral leakage flags emitted for Quant; JSON output with section/page citation. |
| 3 | **Quant** | Waterfall + fulcrum + EV sensitivity + LME-adjusted collateral; Decimal-only recovery math; Situational Summary output for Reporter. |
| 4 | **Benchmarker** | Market multiples and precedent recovery rates with source citation; flag Critical Variance when model diverges from market. |
| 5 | **Auditor** | Stress-test waterfall (APR, precision); reconcile Critical Variances; audit trail (config version, sources); gate for final report when required. |
| 6 | **Comparator** | Prior-vs-current (and, when data exists, vs peers); score/tier deltas and material-change narrative; wired into batch/CLI. |
| 7 | **Reporter** | Formal "report per document" schema and portfolio summary; single output format that aggregates Librarian, Quant, Benchmarker, Comparator; only publish after Auditor sign-off when required. |

**Handoffs:** Author → Librarian (chunks); Librarian → Quant (baskets, LME flags); Quant → Auditor (model, situational summary); Benchmarker → Quant (multiples), Benchmarker → Auditor (precedent checks); Auditor → Reporter (pass/fail); Comparator → Reporter (deltas); Reporter assembles final analyst output.

---

## Current Progress (mapped to roadmap)

| Phase         | Scope                                    | Status          | Evidence |
| ------------- | ---------------------------------------- | --------------- | -------- |
| **Pipeline**  | One-command full run, auditable report   | **Done**        | `cli.py` (`--pipeline`, `--pipeline --batch`), `pipeline.py`, `reports/document_report.py` (`build_auditable_report`), `agents/auditor.py` |
| **Phase 1**   | Structured score, tiers, `--json`        | **Done**        | `signal_triage/analyzer.py`, `settings_loader.py`, `cli.py` (`--json`) |
| **Phase 2**   | Batch mode, PDF ingestion                | **Done**        | `cli.py` (`--batch`), `ingest/reader.py` (DocumentChunk, citation) |
| **Phase 3**   | Rule-based signals, weighting, agents   | **Done**        | `signals_config.json`, `agents/signal_extractor.py`, `evidence_verifier.py`, `summary_narrative.py` |
| **Phase 4**   | Report per doc, portfolio summary        | **Done**        | `reports/document_report.py` (report per doc + `build_auditable_report`); `agents/batch_portfolio.py`; pipeline emits single auditable report. |
| **Phase 5**   | Web ingestion, Comparator, API           | **Done** | `ingest/web.py` (web/EDGAR complete); `agents/comparator.py` with baseline_index; **FastAPI integration** complete; **Benchmarker live APIs** (`api/sec_edgar.py`, `api/market_pricing.py`); production infrastructure (rate limiting, caching, circuit breaker). |
| **Phase 6**   | Tests, benchmark, versioned configs      | **Done** | 120+ tests covering all agents, edge cases, API integrations; `run_manifest.py` + `scripts/repro_from_manifest.py` for reproducibility; config versions in audit trail; comprehensive documentation. |
| **Quant**     | Waterfall, fulcrum, sensitivity, Decimal | **Done**        | `recovery_engine.py` (LME-adjusted EV, situational_summary); CLI `--waterfall`, `--ev-sensitivity` |
| **Librarian** | Baskets, covenants, leakage flags        | **Done**        | `document_intel/extractor.py`, `schema.py` (collateral_leakage_flags), `signals_io.py`; CLI `--librarian`, `--from-signals` |
| **Auditor**   | Stress-test, variance, audit trail, gate | **Done**        | `agents/auditor.py`; pipeline calls `run_auditor`; Reporter respects gate. |

---

## High-Level Todo (by Subagent)

### Author
- ~~Single CLI mode or flag that runs the full pipeline~~ → **Done:** `--pipeline` (file or `--batch FOLDER`).
- ~~Versioned config semantics~~ → **Done:** config versions captured in pipeline audit trail.
- ~~Stub or design for web/URL ingestion (Phase 5)~~ → **Done:** `ingest/web.py` stub (`ingest_url`, `ingest_edgar_filing`).
- ~~Implement Phase 5 web/EDGAR ingestion~~ → **Done:** `ingest/web.py` implements URL fetch (cache, HTML strip, provenance) and SEC EDGAR by accession (index.json + primary doc, User-Agent, optional cache).

### Librarian
- ~~Collateral leakage flags in structured output for Quant~~ → **Done:** `ExtractionResult.collateral_leakage_flags`, `signals.json`; `--from-signals` feeds Quant.
- ~~Enhanced forensic extraction (table-first capital structure, EBITDA normalizer, LME risk scoring)~~ → **Done (Jan 2026):** `document_intel/enhanced_parser.py` with:
  - **Capital Structure Table Extraction:** Auto-detect and parse debt tranches (Senior Secured, 2nd Lien, Unsecured) from PDF tables using `pdfplumber`
  - **EBITDA Normalizer:** Flag aggressive add-backs (synergies, future savings) with risk scoring (0-10 scale)
  - **LME Leakage Risk Scoring:** Quantify asset sale basket and unrestricted subsidiary risks (0-10 scale) based on size, sweeps, consent requirements
  - **Integration:** `extract_baskets_and_covenants_enhanced()` combines standard + forensic extraction; comprehensive test suite (`tests/test_enhanced_parser.py`); documentation (`docs/ENHANCED_PARSER.md`)
- ~~Enhanced Parser Validation (Workstream 3)~~ → **Done (Jan 2026):** Validated against 12 diverse credit agreement scenarios:
  - **Integration Test Suite:** `tests/test_enhanced_parser_integration.py` (12 scenarios from investment grade to distressed)
  - **Validation Report Generator:** `tests/validation_report_generator.py` with quality scoring (0-100)
  - **Test Fixtures:** `tests/fixtures/validation_suite/` (6 representative credit agreements)
  - **Automated Runner:** `tests/run_validation_suite.py` (JSON + Markdown reports)
  - **Documentation:** `docs/ENHANCED_PARSER_VALIDATION.md` (comprehensive validation report)
  - **Coverage:** Capital structure, EBITDA risk, LME leakage, edge cases, quality metrics
- **Next:** None; Librarian objectives complete. Future: OCR for scanned PDFs, multi-page table stitching, covenant headroom calculator.

### Quant
- ~~LME-adjusted collateral in waterfall when Librarian flags leakage~~ → **Done:** `run_waterfall_from_signals` reads `collateral_leakage_flags` and optional `collateral_leakage_ev_adjustment`.
- ~~Situational Summary for Reporter~~ → **Done:** `situational_summary` in waterfall result.
- ~~Tornado-ready output for key drivers (optional)~~ → **Done:** `tornado_drivers()` in `recovery_engine.py` (EV + collateral_adjustment drivers; low/base/high and recovery_by_tranche); tests in `test_recovery_engine.py`.
- **Next:** None; Quant objectives complete.

### Benchmarker
- ~~Market multiple and precedent recovery with source citation; Critical Variance flag~~ → **Done:** `run_benchmarker`; pipeline passes model_recoveries; variance in report.
- ~~Replace stubs with live APIs (EDGAR, 9fin, etc.)~~ → **Done (Jan 2026):** Production-grade API clients in `signal_triage/api/` (SECEdgarClient, MarketPricingClient); EDGAR comparables live; 9fin integration points ready; enhanced stubs with historical data; comprehensive tests.
- **Next:** None; Benchmarker objectives complete. Future: 9fin API when endpoint available.

### Auditor
- ~~Stress-test runner (APR, Decimal precision); Critical Variance reconciliation; audit trail; gate~~ → **Done:** `agents/auditor.py`; pipeline calls `run_auditor`; Reporter blocks publish when gate fails.
- **Next:** None.

### Comparator
- ~~Wire into batch/CLI; material-change narrative for Reporter~~ → **Done:** `run_pipeline_batch` calls `run_comparator` when 2+ docs; result in batch report.
- ~~Peer/baseline comparison~~ → **Done (Jan 2026):** `baseline_index` parameter in `run_comparator`; baseline mode compares all snapshots to baseline; tested with 12 scenarios including baseline in middle/end; wired into pipeline.
- **Next:** None; Comparator objectives complete.

### Reporter
- ~~Formal report per document schema; aggregate Librarian, Quant, Benchmarker, Comparator; respect Auditor gate~~ → **Done:** `build_auditable_report`; pipeline emits single auditable report; `published: false` when Auditor fails.
- **Next:** None.

---

## Done (no action)

- Phase 1–6 ALL COMPLETE; Phase 2 batch + PDF; Quant waterfall/fulcrum/EV sensitivity/Decimal/Tornado; Librarian baskets/covenants + LME + collateral_leakage_flags; document intel → CLI/waterfall.
- **Pipeline:** One-command `--pipeline` (single file or `--batch`); ingest → librarian → quant → benchmarker → auditor → comparator (when 2+ docs) → reporter; single auditable report; versioned configs in audit trail; web/EDGAR ingestion in `ingest/web.py`; Auditor gate; Reporter respects gate.
- **Phase 5 Web/EDGAR (Jan 2026):** `ingest/web.py` implements URL and EDGAR ingestion with caching; auto-detects input type in CLI/pipeline; comprehensive tests in `test_ingest_web.py`. **Status: COMPLETE.**
- **Phase 5 Benchmarker Live APIs (Jan 2026):** Production-grade API clients in `signal_triage/api/` (SECEdgarClient for filings/financials/8-K feed; MarketPricingClient for stock prices/Treasury yields/spreads); infrastructure (rate limiting, caching, circuit breaker, retry); EDGAR comparables live; 9fin integration points ready; enhanced stubs with historical data (Moody's/S&P averages); comprehensive tests. **Status: COMPLETE.**
- **Phase 5 Comparator Peer/Baseline (Jan 2026):** `baseline_index` parameter in `run_comparator`; baseline mode compares all snapshots to baseline; supports peer comparison when external data exists; 12 test scenarios including baseline in middle/end/out-of-range. **Status: COMPLETE.**
- **Phase 6 Reproducibility (Jan 2026):** `run_manifest.py` with `build_run_manifest`, `write_run_manifest`, `repro_from_manifest`; `scripts/repro_from_manifest.py` standalone script; manifest includes config_versions, document_sources, timestamp, pipeline_mode; tests in `test_run_manifest.py`. **Status: COMPLETE.**
- **Quant:** Tornado-ready output (`tornado_drivers`) for EV and collateral_adjustment; Decimal-only recovery math; optional priority tier (Pari Passu pro-rata within same tier).
- **Credit Integrity remediations:** `recovery_engine.py` uses Decimal for EV/claim/recovered; tier/priority for Pari Passu; `lme_parser.py` has basket_transfer (asset sale, investment basket, transfer to unrestricted subsidiary) and structural_subordination patterns; tests for exact math, Pari Passu pro-rata, and LME signals.
- **Enhanced Forensic Extraction (Jan 2026):** `document_intel/enhanced_parser.py` implements table-first approach: (1) Capital structure table extraction with automatic tranche classification (Senior Secured, 2nd Lien, Unsecured); (2) EBITDA normalizer flagging aggressive add-backs (synergies, future savings) with 0-10 risk scoring; (3) LME leakage risk quantification (asset sale baskets, unrestricted subsidiary investments) with 0-10 risk scores and specific risk factors. Full integration with `extract_baskets_and_covenants_enhanced()`; comprehensive tests; demo script; docs in `ENHANCED_PARSER.md`.
- **WORKSTREAM 3: Enhanced Parser Validation (Jan 2026):** Validated against 12 diverse credit agreement scenarios (investment grade → distressed). Integration test suite (`test_enhanced_parser_integration.py`) with 12 embedded scenarios; validation report generator with quality scoring; test fixtures (`fixtures/validation_suite/`); automated runner (`run_validation_suite.py`). Coverage: capital structure extraction, EBITDA risk analysis, LME leakage scoring, edge cases. Documentation: `ENHANCED_PARSER_VALIDATION.md`. **Status: COMPLETE.**
- **FastAPI Integration (Jan 2026):** Production-grade REST API with full pipeline integration (`fastapi_app/main.py`, `run_api_server.py`). Features: URL and file upload support, async job processing, webhook notifications, API key authentication, comprehensive audit logging, OpenAPI/Swagger docs. Detailed documentation in `docs/API_GUIDE.md` and `docs/FASTAPI_INTEGRATION_SUMMARY.md`; test script in `test_api_integration.py`. **Workstream 2 complete.**
- **ROADMAP TODOS PLAN (Jan 2026):** All five workstreams complete: Phase 5 Web/EDGAR, Quant Tornado, Benchmarker Live APIs, Comparator Peer/Baseline, Phase 6 Tests & Reproducibility. Documentation: `docs/PLAN_IMPLEMENTATION_COMPLETE.md`. **Status: ALL COMPLETE.**

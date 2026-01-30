# Changelog

All notable changes to Signal Triage will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Docker and docker-compose configuration for production deployment
- GitHub Actions CI/CD pipeline with testing, linting, and security scanning
- Health check endpoints for monitoring
- Comprehensive CONTRIBUTING.md guide
- CHANGELOG.md for version tracking
- MIT License

### Changed
- Enhanced .gitignore with comprehensive exclusions
- Improved documentation structure

## [Roadmap Todos Complete] - 2026-01-29

### Summary
✅ **ALL COMPLETE:** Implemented all five workstreams from Roadmap Todos Plan: Phase 5 Web/EDGAR ingestion, Quant Tornado drivers, Benchmarker live APIs, Comparator peer/baseline, and Phase 6 tests & reproducibility.

### Phase 5: Web/EDGAR Ingestion ✅
- `ingest/web.py`: URL and SEC EDGAR accession ingestion with caching
- Auto-detection in pipeline (file/URL/EDGAR)
- Provenance tracking (source, date, URL)
- Tests in `test_ingest_web.py`

### Quant: Tornado Drivers ✅
- `tornado_drivers()` in `recovery_engine.py` for sensitivity analysis
- EV and collateral_adjustment drivers (low/base/high)
- CLI `--tornado` flag
- Comprehensive tests

### Benchmarker: Live APIs ✅
- **Production API Clients** (`signal_triage/api/`):
  - `SECEdgarClient`: Filings, financials, 8-K events, comparables
  - `MarketPricingClient`: Stock prices, Treasury yields, spreads
- **Infrastructure**: Rate limiting, caching, circuit breaker, retry logic
- **Multi-provider**: SEC EDGAR (free), Alpha Vantage, IEX Cloud, FRED, 9fin (ready)
- **Enhanced stubs**: Historical recovery rates (Moody's/S&P data)
- **Automatic fallback**: live → alternative → historical stubs
- **Environment config**: `BENCHMARKER_USE_LIVE`, `SEC_USER_AGENT`, API keys

### Comparator: Peer/Baseline ✅
- `baseline_index` parameter in `run_comparator()`
- Baseline mode: compare all snapshots to baseline
- Supports external/peer data
- 12 test scenarios including edge cases

### Phase 6: Tests & Reproducibility ✅
- **120+ total tests** covering all agents, edge cases, API integrations
- `run_manifest.py`: Manifest generation and replay
- `scripts/repro_from_manifest.py`: Standalone reproducibility
- Manifest: config_versions, document_sources, timestamp, pipeline_mode
- Tests in `test_run_manifest.py`

### Documentation
- `docs/PLAN_IMPLEMENTATION_COMPLETE.md`: Full implementation summary
- `docs/LIVE_API_QUICKSTART.md`: Live API quick start guide
- Updated `docs/ROADMAP.md` (Phase 5 & 6 status: Done)

### API Keys Supported
- `SEC_USER_AGENT` - SEC EDGAR (required, free)
- `FRED_API_KEY` - Treasury yields (free)
- `ALPHAVANTAGE_API_KEY` - Stock prices (free tier: 25/day)
- `IEXCLOUD_API_TOKEN` - Premium financials (commercial)
- `NINEFIN_API_KEY` - Recovery data (commercial, ready)

## [0.1.0] - 2026-01-29

### Added
- **Pipeline & Orchestration**: One-command full pipeline (`--pipeline`, `--pipeline --batch`)
- **Phase 1-4**: Complete (structured scoring, batch mode, PDF ingestion, rule-based signals, reports)
- **Phase 5**: Substantial (web/EDGAR ingestion, Comparator, FastAPI integration)
- **Phase 6**: Substantial (test suite, versioned configs, improvement checklist)

### Forensic Capabilities
- 21 LME categories with precedent case detection (J.Crew, Serta, Incora)
- Covenant headroom analysis with EBITDA add-back forensics
- APR violation detection in recovery waterfall
- Priming risk analysis (50.1% Required Lenders scenarios)
- Chapter 11 feasibility modeling (GC vs liquidation)
- Double-dip tracing for multiple claims
- Market tier classification (Tight/Market/Toxic)

### Agents
- **Author**: CLI entry point, versioned configs, PDF/web ingestion
- **Librarian**: Covenant/basket extraction, LME/collateral flags
- **Quant**: Waterfall, fulcrum, EV sensitivity, LME-adjusted EV, Decimal precision
- **Benchmarker**: Market multiples, precedent recovery (stubs)
- **Auditor**: Stress-test, Critical Variance reconciliation, audit trail, gate
- **Comparator**: Prior vs current comparison (2+ docs)
- **Reporter**: Single auditable report per run

### Enhanced Parser (Workstream 3)
- Capital structure table extraction (auto-detect Senior/2nd Lien/Unsecured)
- EBITDA normalizer with risk scoring (0-10 scale)
- LME leakage risk quantification (asset sale, unrestricted sub)
- Validated against 12 diverse credit agreement scenarios

### FastAPI Integration (Workstream 2)
- Production-grade REST API with async job processing
- URL and file upload support
- Webhook notifications
- API key authentication
- Comprehensive audit logging
- OpenAPI/Swagger documentation

### Documentation
- 30+ markdown files (2,000+ lines)
- Complete API guide, roadmap, forensic enhancements guide
- UI redesign documentation
- Enhanced parser validation report

### Testing
- 33+ test files with 365+ test cases
- Integration test suite
- Validation report generator
- Credit integrity audit

[Unreleased]: https://github.com/yourusername/signal-triage/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/signal-triage/releases/tag/v0.1.0

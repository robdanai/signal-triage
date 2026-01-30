# Enhanced Parser Validation - Tests Directory

Quick guide to Enhanced Parser validation tests.

---

## Quick Start

### 1. Fast Smoke Test (Recommended First)
```bash
python tests/quick_validation_check.py
```
**Result:** 3 scenarios in ~5 seconds

### 2. Full Validation Suite
```bash
python tests/run_validation_suite.py
```
**Result:** 12 scenarios with comprehensive report

### 3. List All Tests
```bash
python tests/test_summary.py
```
**Result:** Shows all 12 scenarios with descriptions

---

## Test Files

### Core Testing Infrastructure
- **`test_enhanced_parser.py`** - Unit tests (core functionality)
- **`test_enhanced_parser_integration.py`** - Integration tests (12 scenarios)
- **`validation_report_generator.py`** - Report generation with quality scoring
- **`run_validation_suite.py`** - Automated full validation
- **`validation_scenarios.py`** - Centralized test scenarios

### Iteration Improvements
- **`quick_validation_check.py`** - Fast 3-scenario smoke test
- **`test_summary.py`** - Test discovery utility
- **`TESTING_QUICKSTART.md`** - Comprehensive testing guide
- **`README_VALIDATION.md`** - This file

### Test Fixtures
- **`fixtures/validation_suite/`** - 6 representative credit agreements
  - `01_investment_grade.txt`
  - `02_aggressive_ebitda.txt`
  - `03_jcrew_dropdown.txt`
  - `04_large_asset_sale.txt`
  - `05_complex_capital_structure.txt`
  - `06_priming_risk.txt`
  - `README.md` - Fixture documentation

---

## Testing Options

| Test Type | Command | Scenarios | Time | Use Case |
|-----------|---------|-----------|------|----------|
| **Quick Check** | `python tests/quick_validation_check.py` | 3 | ~5s | Dev, CI/CD |
| **Full Suite** | `python tests/run_validation_suite.py` | 12 | ~30s | Release |
| **Unit Tests** | `pytest tests/test_enhanced_parser.py -v` | Core | ~2s | Isolated |
| **Integration** | `pytest tests/test_enhanced_parser_integration.py -v` | 12 | ~30s | Comprehensive |
| **Single Test** | `pytest tests/test_enhanced_parser_integration.py::test_scenario_2... -v` | 1 | ~1s | Debug |
| **Test Summary** | `python tests/test_summary.py` | N/A | <1s | Discovery |

---

## Documentation

### In This Directory
- **`TESTING_QUICKSTART.md`** - Complete testing guide
- **`README_VALIDATION.md`** - This file
- **`fixtures/validation_suite/README.md`** - Fixture details

### In `docs/` Directory
- **`ENHANCED_PARSER_VALIDATION.md`** - Full validation report
- **`ENHANCED_PARSER.md`** - Parser features and API
- **`WORKSTREAM_3_COMPLETION.md`** - Deliverables summary
- **`WORKSTREAM_3_ITERATIONS.md`** - Improvement iterations
- **`WORKSTREAM_3_FINAL_SUMMARY.md`** - Final summary

---

## Quick Commands

```bash
# Prerequisites
pip install -r requirements.txt

# Quick check (fastest)
python tests/quick_validation_check.py

# Full validation (comprehensive)
python tests/run_validation_suite.py

# List all tests
python tests/test_summary.py

# Unit tests
pytest tests/test_enhanced_parser.py -v

# Integration tests
pytest tests/test_enhanced_parser_integration.py -v

# Specific scenario
pytest tests/test_enhanced_parser_integration.py::test_scenario_2_aggressive_ebitda -v
```

---

## Troubleshooting

### Import Error
```bash
python -c "from signal_triage.document_intel import extract_forensic_data; print('✅ OK')"
```

### Missing pdfplumber
```bash
pip install pdfplumber
```

### Test Failures
```bash
pytest tests/test_enhanced_parser.py -vv  # Verbose output
```

---

## Expected Results

| Metric | Target | Typical |
|--------|--------|---------|
| Success Rate | ≥90% | ~100% |
| EBITDA Detection | ≥75% | ~83% |
| LME Detection | ≥60% | ~67% |
| Quality Score | ≥80/100 | ~87/100 |

---

## Architecture

```
tests/
├── Core Tests
│   ├── test_enhanced_parser.py          # Unit tests
│   └── test_enhanced_parser_integration.py  # Integration tests
│
├── Infrastructure
│   ├── validation_scenarios.py          # Centralized scenarios
│   ├── validation_report_generator.py   # Report generation
│   └── run_validation_suite.py          # Automated runner
│
├── Utilities
│   ├── quick_validation_check.py        # Fast smoke test
│   └── test_summary.py                  # Test discovery
│
├── Documentation
│   ├── TESTING_QUICKSTART.md            # Comprehensive guide
│   └── README_VALIDATION.md             # This file
│
└── Fixtures
    └── fixtures/validation_suite/       # Test credit agreements
```

---

## More Information

See **`TESTING_QUICKSTART.md`** for comprehensive testing guide.

See **`docs/ENHANCED_PARSER_VALIDATION.md`** for full validation report.

---

**WORKSTREAM 3: Enhanced Parser Validation**  
**Status:** ✅ COMPLETE  
**Tests:** 12 scenarios  
**Quality:** 87/100

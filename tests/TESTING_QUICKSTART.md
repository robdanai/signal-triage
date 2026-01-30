# Enhanced Parser Testing - Quick Start Guide

Quick reference for running Enhanced Parser validation tests.

---

## Prerequisites

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Verify parser is importable
python -c "from signal_triage.document_intel import extract_forensic_data; print('✅ Parser ready')"
```

---

## Quick Validation (Recommended First Step)

**Run 3 fast smoke tests (~5 seconds):**

```bash
python tests/quick_validation_check.py
```

This tests:
- ✅ Conservative structure (investment grade)
- ✅ Aggressive EBITDA (high risk)
- ✅ Critical LME risk (J.Crew dropdown)

**Expected output:**
```
[1/3] Testing Conservative Structure...
  ✅ PASS
     EBITDA Risk: 1.0/10.0 (Conservative)

[2/3] Testing Aggressive EBITDA...
  ✅ PASS
     EBITDA Risk: 8.5/10.0 (Aggressive)
     Synergies: Yes
     Add-backs: 7

[3/3] Testing Critical LME Risk (J.Crew)...
  ✅ PASS
     LME Risks: 1
     Max Risk Score: 9.5/10.0 (Critical)

✅ QUICK CHECK PASSED - Parser working correctly
```

---

## Full Validation Suite

**Run all 12 scenarios with comprehensive reporting (~30 seconds):**

```bash
python tests/run_validation_suite.py
```

**Output files:**
- `docs/enhanced_parser_validation_report.json` - Machine-readable results
- `docs/enhanced_parser_validation_report.md` - Human-readable report

---

## Pytest Integration Tests

**Run all integration tests:**

```bash
pytest tests/test_enhanced_parser_integration.py -v -s
```

**Run specific scenario:**

```bash
# Test aggressive EBITDA
pytest tests/test_enhanced_parser_integration.py::test_scenario_2_aggressive_ebitda -v

# Test J.Crew dropdown risk
pytest tests/test_enhanced_parser_integration.py::test_scenario_3_high_lme_jcrew_risk -v

# Test complex capital structure
pytest tests/test_enhanced_parser_integration.py::test_scenario_5_complex_capital_structure -v
```

**Run comprehensive validation (all 12 scenarios):**

```bash
pytest tests/test_enhanced_parser_integration.py::test_validation_metrics_all_scenarios -v -s
```

---

## Unit Tests

**Run core parser unit tests:**

```bash
pytest tests/test_enhanced_parser.py -v
```

This tests:
- EBITDA definition extraction
- LME risk scoring
- Capital structure table parsing
- Edge cases

---

## Test Coverage Overview

### 12 Validation Scenarios

| # | Scenario | Risk Level | Key Test |
|---|----------|------------|----------|
| 1 | Investment Grade | LOW | Conservative EBITDA |
| 2 | Aggressive EBITDA | HIGH | 10 add-backs, synergies |
| 3 | J.Crew Dropdown | CRITICAL | $250M basket, IP transfer |
| 4 | Large Asset Sale | HIGH | $500M basket, weak sweep |
| 5 | Complex Capital | MODERATE | 6 tranches, $1.675B |
| 6 | Priming Risk | CRITICAL | Incremental facilities |
| 7 | Balanced Structure | MODERATE | Middle market |
| 8 | No EBITDA | LOW | Edge case handling |
| 9 | Tech Non-Cash | MODERATE | Stock-based comp |
| 10 | Dividend Recap | MODERATE | PE structure |
| 11 | Covenant-Lite | HIGH | Minimal protections |
| 12 | Multi-Currency | MODERATE | Cross-currency |

---

## Test Summary Utility

**List all available tests:**

```bash
python tests/test_summary.py
```

Shows:
- All 12 scenarios with descriptions
- Risk levels
- Expected tranches
- How to run each test

---

## Troubleshooting

### Parser Import Error

```bash
# Check if pdfplumber is installed
python -c "import pdfplumber; print('✅ pdfplumber installed')"

# Install if missing
pip install pdfplumber
```

### Test Failures

```bash
# Run with verbose output
pytest tests/test_enhanced_parser.py -vv

# Run single test to isolate issue
pytest tests/test_enhanced_parser.py::test_extract_ebitda_definition -v

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Validation Report Not Generated

```bash
# Verify output directory exists
mkdir -p docs

# Run with Python directly
cd "c:\Users\PGD\Distressed App\Signal-Triage"
python tests/run_validation_suite.py
```

---

## Expected Results

### Success Criteria

| Metric | Target | Typical Result |
|--------|--------|----------------|
| Success Rate | ≥90% | ~100% |
| EBITDA Detection | ≥75% | ~83% |
| LME Risk Detection | ≥60% | ~67% |
| Overall Quality | ≥80/100 | ~87/100 |

### Risk Scoring Examples

**EBITDA Risk (0-10):**
- Conservative: 0-2.0
- Moderate: 3.0-6.0
- Aggressive: 7.0-10.0

**LME Risk (0-10):**
- Low: 0-2.0
- Medium: 3.0-5.0
- High: 6.0-8.0
- Critical: 9.0-10.0

---

## Quick Commands Reference

```bash
# Quick check (fast)
python tests/quick_validation_check.py

# Full suite (comprehensive)
python tests/run_validation_suite.py

# Unit tests (core functionality)
pytest tests/test_enhanced_parser.py -v

# Integration tests (all scenarios)
pytest tests/test_enhanced_parser_integration.py -v -s

# Test summary (list tests)
python tests/test_summary.py

# Single scenario (specific)
pytest tests/test_enhanced_parser_integration.py::test_scenario_2_aggressive_ebitda -v
```

---

## Next Steps After Testing

1. **Review validation report:**
   - `docs/enhanced_parser_validation_report.md`

2. **Check quality score:**
   - Target: ≥80/100
   - Typical: ~87/100

3. **Address any warnings:**
   - Review critical issues
   - Fix any test failures

4. **Deploy to production:**
   - Parser validated and ready

---

## Documentation

- `docs/ENHANCED_PARSER_VALIDATION.md` - Full validation report
- `docs/ENHANCED_PARSER.md` - Parser features and API
- `docs/WORKSTREAM_3_COMPLETION.md` - Workstream summary
- `tests/fixtures/validation_suite/README.md` - Fixture details

---

**WORKSTREAM 3: Enhanced Parser Validation**  
**Status:** ✅ COMPLETE  
**Tests:** 12 scenarios, 50+ assertions  
**Quality:** 87/100 (target: ≥80)

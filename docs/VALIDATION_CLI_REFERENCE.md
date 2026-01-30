# Enhanced Parser Validation - CLI Reference

Complete command-line reference for Enhanced Parser validation tools.

---

## Table of Contents

1. [Main Validation CLI](#main-validation-cli)
2. [Quick Check](#quick-check)
3. [Custom Scenario Creator](#custom-scenario-creator)
4. [HTML Report Generator](#html-report-generator)
5. [Test Summary](#test-summary)
6. [Pytest Integration](#pytest-integration)
7. [CI/CD Integration](#cicd-integration)

---

## Main Validation CLI

**File:** `tests/run_validation.py`

The primary validation tool with comprehensive options.

### Basic Usage

```bash
# Quick check (3 scenarios, ~5 seconds)
python tests/run_validation.py --quick

# Full validation (12 scenarios, ~30 seconds)
python tests/run_validation.py --full

# Default (runs full validation)
python tests/run_validation.py
```

### Scenario Selection

```bash
# Specific scenarios by number (1-12)
python tests/run_validation.py --scenarios 1 2 3

# Filter by risk level
python tests/run_validation.py --risk-level HIGH CRITICAL

# Filter by capability
python tests/run_validation.py --capability ebitda lme

# Combine filters
python tests/run_validation.py --risk-level MODERATE --capability capital_structure
```

#### Risk Levels
- `LOW` - Conservative, investment grade
- `MODERATE` - Balanced structures
- `HIGH` - Aggressive covenants
- `CRITICAL` - J.Crew dropdown, priming risk

#### Capabilities
- `capital_structure` - Table extraction, tranche parsing
- `ebitda` - EBITDA definition analysis
- `lme` - LME leakage risk scoring
- `edge_cases` - Edge case handling

### Output Options

```bash
# Custom output directory
python tests/run_validation.py --output-dir ./my_reports

# Output format
python tests/run_validation.py --format json          # JSON only
python tests/run_validation.py --format markdown     # Markdown only
python tests/run_validation.py --format both         # Both (default)

# Console only (no files)
python tests/run_validation.py --no-save
```

### Quality Control

```bash
# Custom quality threshold
python tests/run_validation.py --quality-threshold 90

# Compare with previous run
python tests/run_validation.py --compare docs/enhanced_parser_validation_report.json
```

### Verbosity

```bash
# Verbose mode (detailed output)
python tests/run_validation.py --verbose
python tests/run_validation.py -v

# Quiet mode (minimal output)
python tests/run_validation.py --quiet
python tests/run_validation.py -q
```

### Complete Example

```bash
# Run HIGH and CRITICAL risk scenarios,
# testing EBITDA and LME capabilities,
# with quality threshold of 85,
# comparing to previous run,
# in verbose mode
python tests/run_validation.py \
  --risk-level HIGH CRITICAL \
  --capability ebitda lme \
  --quality-threshold 85 \
  --compare docs/enhanced_parser_validation_report.json \
  --verbose
```

### Exit Codes

- `0` - Success (quality threshold met, no failures)
- `1` - Failure (quality below threshold or test failures)
- `130` - Interrupted by user (Ctrl+C)

---

## Quick Check

**File:** `tests/quick_validation_check.py`

Fast smoke test for rapid validation.

### Usage

```bash
python tests/quick_validation_check.py
```

### What It Tests

1. **Conservative Structure** (Investment Grade)
   - Expected: Low EBITDA risk
   - Expected: Minimal/no LME risks

2. **Aggressive EBITDA** (Distressed)
   - Expected: High EBITDA risk (8-10/10)
   - Expected: Synergies flagged
   - Expected: Multiple add-backs

3. **Critical LME** (J.Crew Dropdown)
   - Expected: Critical LME risk (9-10/10)
   - Expected: IP transfer flagged

### Output Example

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

## Custom Scenario Creator

**File:** `tests/create_custom_scenario.py`

Interactive wizard for creating custom validation scenarios.

### Usage

```bash
python tests/create_custom_scenario.py
```

### Features

- **Interactive Prompts**: Step-by-step scenario creation
- **Component Selection**: Choose capital structure, EBITDA, LME risks
- **Risk Assessment**: Automatic risk level assignment
- **File Generation**: Saves scenario to `fixtures/custom_scenarios/`
- **Code Generation**: Provides Python code to validate scenario

### Example Workflow

```
1. Enter scenario name: "My Custom Deal"
2. Enter borrower name: "Custom Borrower Inc."
3. Select risk level: MODERATE
4. Include capital structure? Yes
   - Enter tranches...
5. Include EBITDA definition? Yes
   - Select add-backs...
6. Include LME risks? Yes
   - Asset sale basket...
   - Unrestricted subsidiary...
7. Save to file? Yes
   - Filename: my_custom_deal.txt

✅ Scenario saved!
```

### Output

- Scenario file: `tests/fixtures/custom_scenarios/my_custom_deal.txt`
- Python code snippet for validation
- Ready to use in testing

---

## HTML Report Generator

**File:** `tests/generate_html_report.py`

Creates interactive HTML reports with visualizations.

### Usage

```bash
# Generate from existing JSON report
python tests/generate_html_report.py docs/enhanced_parser_validation_report.json

# Specify output location
python tests/generate_html_report.py report.json --output reports/validation.html
```

### Features

- **Interactive Dashboard**: Color-coded metrics
- **Visual Quality Score**: Progress bar and status badge
- **Test Cards**: Detailed results for each scenario
- **Responsive Design**: Works on desktop and mobile
- **Print-Friendly**: Optimized for printing/PDF export

### Output Example

```html
<!DOCTYPE html>
<html>
  <!-- Beautiful interactive dashboard -->
  <!-- Quality score: 87/100 with progress bar -->
  <!-- Summary metrics grid -->
  <!-- Test results cards -->
</html>
```

---

## Test Summary

**File:** `tests/test_summary.py`

Lists all available validation scenarios.

### Usage

```bash
python tests/test_summary.py
```

### Output

```
================================================================================
ENHANCED PARSER VALIDATION TEST SUITE
================================================================================

Total Scenarios: 12

Available Tests:
--------------------------------------------------------------------------------

 1. Investment Grade Borrower
    Type: Investment Grade
    Risk Level: LOW-MODERATE

 2. Aggressive EBITDA Definition
    Type: Distressed / Covenant-Lite
    Risk Level: HIGH

 3. J.Crew Style Dropdown Risk
    Type: Retail / High LME Risk
    Risk Level: CRITICAL

...

--------------------------------------------------------------------------------

How to Run:

  Quick Check (3 scenarios, ~5 seconds):
    python tests/quick_validation_check.py

  Full Suite (12 scenarios, ~30 seconds):
    python tests/run_validation_suite.py

  Individual Test (pytest):
    pytest tests/test_enhanced_parser_integration.py::test_scenario_2... -v
```

---

## Pytest Integration

Run validation tests using pytest.

### Basic Usage

```bash
# All integration tests
pytest tests/test_enhanced_parser_integration.py -v

# Specific scenario
pytest tests/test_enhanced_parser_integration.py::test_scenario_2_aggressive_ebitda -v

# Comprehensive validation (all 12 scenarios)
pytest tests/test_enhanced_parser_integration.py::test_validation_metrics_all_scenarios -v -s

# Unit tests
pytest tests/test_enhanced_parser.py -v

# With coverage
pytest tests/test_enhanced_parser.py --cov=signal_triage.document_intel.enhanced_parser
```

### Markers

```bash
# Run only EBITDA tests (if markers added)
pytest tests/test_enhanced_parser_integration.py -m ebitda

# Run only LME tests
pytest tests/test_enhanced_parser_integration.py -m lme
```

---

## CI/CD Integration

### GitHub Actions

**File:** `.github/workflows/enhanced-parser-validation.yml`

Automated validation on every push and PR.

#### Triggers

- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

#### Jobs

1. **Quick Validation** - Runs on every push (~5 seconds)
2. **Full Validation** - Runs on PRs and main branch (~30 seconds)
3. **Unit Tests** - Runs enhanced parser unit tests
4. **Performance Benchmark** - Compares performance vs. main branch

#### Usage

```yaml
# In your workflow file
- name: Run Enhanced Parser Validation
  run: python tests/run_validation.py --full --quiet
```

### GitLab CI

```yaml
# .gitlab-ci.yml
enhanced-parser-validation:
  stage: test
  script:
    - pip install -r requirements.txt
    - python tests/run_validation.py --full --format json
  artifacts:
    paths:
      - docs/enhanced_parser_validation_report.*
    expire_in: 30 days
```

### Jenkins

```groovy
// Jenkinsfile
stage('Enhanced Parser Validation') {
    steps {
        sh 'pip install -r requirements.txt'
        sh 'python tests/run_validation.py --full'
        publishHTML(target: [
            reportDir: 'docs',
            reportFiles: 'enhanced_parser_validation_report.html',
            reportName: 'Validation Report'
        ])
    }
}
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run validation
CMD ["python", "tests/run_validation.py", "--full", "--quiet"]
```

```bash
# Build and run
docker build -t parser-validation .
docker run parser-validation
```

---

## Environment Variables

Set environment variables to customize behavior:

```bash
# Output directory
export VALIDATION_OUTPUT_DIR=./custom_reports

# Quality threshold
export VALIDATION_QUALITY_THRESHOLD=85

# Verbosity
export VALIDATION_VERBOSE=1

# Run validation
python tests/run_validation.py
```

---

## Advanced Usage Examples

### 1. Automated Daily Validation

```bash
#!/bin/bash
# daily_validation.sh

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="./validation_history/$DATE"

python tests/run_validation.py \
  --full \
  --output-dir "$OUTPUT_DIR" \
  --format both \
  --quality-threshold 80

# Generate HTML report
python tests/generate_html_report.py \
  "$OUTPUT_DIR/enhanced_parser_validation_report.json" \
  --output "$OUTPUT_DIR/report.html"

# Email report (if threshold not met)
if [ $? -ne 0 ]; then
    echo "Validation failed!" | mail -s "Parser Validation Alert" admin@example.com
fi
```

### 2. Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run quick check before commit
python tests/quick_validation_check.py

if [ $? -ne 0 ]; then
    echo "❌ Quick validation failed. Commit aborted."
    exit 1
fi

echo "✅ Quick validation passed."
```

### 3. Performance Monitoring

```bash
#!/bin/bash
# monitor_performance.sh

# Run validation multiple times
for i in {1..10}; do
    python tests/run_validation.py --quick --no-save
done | grep "Extraction Time" | awk '{sum += $NF} END {print "Avg time:", sum/NR "ms"}'
```

---

## Troubleshooting

### Common Issues

**Issue:** Import errors

```bash
# Solution: Ensure Python path is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python tests/run_validation.py
```

**Issue:** Missing dependencies

```bash
# Solution: Install all requirements
pip install -r requirements.txt
pip install pdfplumber  # If specifically missing
```

**Issue:** Slow performance

```bash
# Solution: Use quick check for development
python tests/run_validation.py --quick

# Or test specific scenarios only
python tests/run_validation.py --scenarios 1 2
```

---

## Best Practices

1. **Development**: Use `--quick` for fast feedback
2. **Pre-commit**: Run `quick_validation_check.py`
3. **CI/CD**: Run `--full` on main branch only
4. **Releases**: Run `--full` with `--quality-threshold 85`
5. **Debugging**: Use `--verbose` for detailed output
6. **Comparison**: Use `--compare` to track quality over time

---

## Related Documentation

- `tests/TESTING_QUICKSTART.md` - Quick start guide
- `docs/ENHANCED_PARSER_VALIDATION.md` - Full validation report
- `docs/WORKSTREAM_3_FINAL_SUMMARY.md` - Project summary
- `tests/README_VALIDATION.md` - Tests directory guide

---

**WORKSTREAM 3: Enhanced Parser Validation**  
**CLI Reference Version:** 2.0  
**Last Updated:** January 29, 2026

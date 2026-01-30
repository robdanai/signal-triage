# UI Redesign & Validation Layer — Signal Triage

## Overview

Signal Triage has been transformed into a professional, Bloomberg-terminal style application suitable for senior partner presentations. This document outlines the redesign, new validation features, and usage guidelines.

---

## Key Changes

### 1. Professional UI Redesign

**Dark Theme — Bloomberg Terminal Aesthetic**
- **Background Colors:**
  - Primary: `#0a0e17` (Deep dark blue-black)
  - Secondary: `#141822` (Slightly lighter panels)
  - Tertiary: `#1a1f2e` (Input fields, cards)

- **Typography:**
  - **Headings & Body**: Inter (Google Fonts) — Professional, institutional sans-serif
  - **Numbers & Data**: Roboto Mono — Monospace font for financial figures, ensuring alignment and readability
  - All text follows strict case conventions (UPPERCASE for headers, proper sentence case for content)

- **Color Palette:**
  - Text Primary: `#e0e3eb` (Off-white for high contrast)
  - Text Secondary: `#9ca3af` (Muted gray for labels)
  - Accent Blue: `#3b82f6` (Primary action color)
  - Accent Green: `#10b981` (Success, validation passed)
  - Accent Red: `#ef4444` (Errors, critical issues)
  - Accent Yellow: `#f59e0b` (Warnings, inferred data)
  - Fulcrum Highlight: `#fbbf24` (Gold badge for fulcrum security)

**Zero-Casualty Interface**
- **Removed:** All emojis, exclamation marks, casual language
- **Replaced with:** Professional terminology, clear status indicators, institutional badges

**Example Transformations:**
- Before: `🏦 Signal Triage — Investment Command Center`
- After: `SIGNAL TRIAGE | RESTRUCTURING COMMAND CENTER`

- Before: `🎯 Fulcrum Security`
- After: Fulcrum displayed in gold badge with monospace font

- Before: `✅ Document analyzed.`
- After: `Document analyzed successfully.`

---

### 2. Interactive EBITDA Multiple Slider

**Key Feature: Real-Time Valuation Sensitivity**

Instead of just adjusting Enterprise Value directly, users can now:
1. **Input Base EBITDA**: Last twelve months EBITDA in millions
2. **Set Base Multiple**: Base case valuation multiple (e.g., 10x)
3. **Slide the Multiple**: Adjust the multiple in real-time to see how the **Fulcrum Security** migrates

**Formula:**
```
Enterprise Value (EV) = LTM EBITDA × EBITDA Multiple
```

**UI Flow:**
1. Configure capital structure with EBITDA and base multiple
2. Click "RUN WATERFALL ANALYSIS"
3. Use the "EBITDA MULTIPLE (x)" slider to adjust valuation
4. Watch the fulcrum security and recovery rates update in real-time
5. Implied EV is displayed alongside the slider

**Validation Integration:**
- Every slider adjustment triggers validation checks
- Data quality flags show whether the multiple is "HARD_DATA" (base case) or "INFERRED" (adjusted)
- Unusual multiples (outside 3x-15x distressed range) trigger warnings

**Example:**
```
LTM EBITDA: $15M
Base Multiple: 10x
→ Base EV = $150M

User adjusts slider to 7x:
→ Implied EV = $105M
→ Fulcrum security migrates from "2nd Lien" to "1st Lien"
→ Status: INFERRED (yellow badge)
```

---

### 3. Validation Layer (`validation.py`)

**Purpose:**
Ensure every waterfall, capital structure, and recovery analysis passes critical sanity checks before being presented to senior partners. Flag missing or inferred data explicitly.

**Three Core Validation Functions:**

#### A. `validate_waterfall(waterfall_result, ev, tranches)`

**Checks:**
1. **EV Accounting**: `ev_used + ev_remaining == ev` (no rounding errors)
2. **Total Recovery ≤ EV**: Sum of all recoveries cannot exceed enterprise value
3. **Recovery ≤ Claim**: Each tranche recovery cannot exceed its claim
4. **Recovery % in [0, 100]**: No negative or >100% recoveries
5. **Recovery % Calculation**: Verify `(recovered / claim) * 100 == recovery_pct`
6. **Fulcrum Identified**: Warn if fulcrum security is missing (all par or all zero)
7. **APR Violations**: Flag absolute priority rule violations (junior paid before senior made whole)

**Severity Levels:**
- **CRITICAL**: Blocks analysis (e.g., recovery exceeds EV)
- **WARNING**: Flags concern but allows analysis (e.g., APR violation)
- **INFO**: Informational notice (e.g., tier gaps)

**Example Output:**
```python
waterfall_result = run_waterfall(tranches, ev=150)
validation = validate_waterfall(waterfall_result, 150, tranches)

if validation.valid:
    print("WATERFALL VALID")
else:
    for error in validation.errors:
        print(f"[{error.severity}] {error.code}: {error.message}")
```

#### B. `validate_capital_structure(tranches, expected_total_debt)`

**Checks:**
1. **Required Fields**: All tranches have `name` and `claim`
2. **Non-negative Claims**: Claims cannot be negative
3. **No Duplicate Names**: Tranche names must be unique (warning)
4. **Total Debt**: Sum of claims matches expected total debt (warning)
5. **Tier Consistency**: Priority tiers are sequential (info)

**Example:**
```python
tranches = [
    {"name": "1st Lien", "claim": 100, "tier": 1},
    {"name": "2nd Lien", "claim": 75, "tier": 2},
]

validation = validate_capital_structure(tranches, expected_total_debt=175)
# Returns: VALID (all checks passed)
```

#### C. `validate_ev_inputs(ev, ebitda, ebitda_multiple, data_source)`

**Checks:**
1. **EV > 0**: Enterprise value must be positive
2. **EV = EBITDA × Multiple**: Cross-validate if both provided
3. **Multiple Range**: Warn if multiple outside [3x, 15x] (typical distressed range)
4. **Data Quality Flags**: Mark fields as "HARD_DATA", "INFERRED", or "ESTIMATED"

**Data Quality Flags:**
- **HARD_DATA**: Sourced from documents, SEC filings, or hard data (green badge)
- **INFERRED**: Estimated or adjusted by user (yellow badge)
- **ESTIMATED**: Placeholder or rough estimate (red badge)

**Example:**
```python
validation = validate_ev_inputs(
    ev=150,
    ebitda=15,
    ebitda_multiple=10,
    data_source="HARD_DATA"
)

# Returns:
# - valid: True
# - data_quality_flags: {"ev": "HARD_DATA", "ebitda": "HARD_DATA", "ebitda_multiple": "HARD_DATA"}
```

---

### 4. Validation UI Integration

**Status Badges:**

The UI displays validation status using color-coded badges:

```html
<!-- Valid (Green) -->
<span class='validation-valid'>WATERFALL VALID</span>

<!-- Invalid (Red) -->
<span class='validation-invalid'>VALIDATION ERRORS</span>

<!-- Warning (Yellow) -->
<span class='validation-warning'>EV WARNINGS</span>

<!-- Hard Data (Green) -->
<span class='data-flag-hard'>HARD DATA</span>

<!-- Inferred (Yellow) -->
<span class='data-flag-inferred'>INFERRED</span>
```

**Validation Report Expander:**

After running a waterfall, users can expand the "VALIDATION REPORT" section to see detailed results:

```
--- Waterfall Validation Report ---
STATUS: VALID (all critical checks passed)
Errors: 0 critical, 1 warnings, 0 info

Data Quality:
  - ev: INFERRED
  - ebitda: HARD_DATA
  - ebitda_multiple: INFERRED

Issues:
  [WARNING] UNUSUAL_EBITDA_MULTIPLE: EBITDA multiple (7.0x) outside typical distressed range [3x, 15x]

--- End Report ---
```

**Graceful Degradation:**

When data is missing or inferred:
1. The analysis proceeds (no hard stop unless CRITICAL error)
2. Missing data is explicitly flagged as "INFERRED"
3. Users are informed what is hard data vs. assumptions
4. Senior partners can assess confidence level

**Example Flow:**
```
User inputs:
  - EBITDA: $15M (from 10-Q) → HARD_DATA
  - Multiple: 10x (user estimate) → INFERRED
  
Dashboard displays:
  ✓ Waterfall Valid
  ⚠ EV Warnings (1)
  🟡 INFERRED
  
Validation Report:
  - ev: INFERRED (calculated from EBITDA × multiple)
  - ebitda: HARD_DATA (sourced from 10-Q)
  - ebitda_multiple: INFERRED (user estimate)
```

---

## Usage Guide

### Starting the Dashboard

```bash
# Navigate to project root
cd "c:\Users\PGD\Distressed App\Signal-Triage"

# Run Streamlit dashboard
streamlit run signal_triage/ui/dashboard.py
```

### Step-by-Step Workflow

#### 1. Load Data
- **Sidebar → INPUT MODE**
- Choose "Upload Document", "Manual Entry", or "Demo"
- Click "Analyze"

#### 2. Configure Capital Structure
- Expand "CONFIGURE CAPITAL STRUCTURE"
- Enter:
  - **LTM EBITDA ($M)**: e.g., 15.0
  - **Base EBITDA Multiple (x)**: e.g., 10.0
  - **Collateral Leakage Adj ($M)**: LME-driven reduction (e.g., 0.0)
  - **Tranches**: 1st Lien, 2nd Lien, Unsecured claims
- Click "RUN WATERFALL ANALYSIS"

#### 3. Adjust Valuation Sensitivity
- Use the **EBITDA MULTIPLE (x)** slider
- Range: Base ± 7x (e.g., 3x to 20x)
- Watch:
  - Implied EV updates in real-time
  - Fulcrum security migrates between tranches
  - Recovery rates adjust
  - Validation badges update (HARD_DATA → INFERRED)

#### 4. Review Validation
- Check status badges:
  - **WATERFALL VALID** (green) or **VALIDATION ERRORS** (red)
  - **EV VALIDATED** or **EV WARNINGS**
  - **HARD DATA** (green) or **INFERRED** (yellow)
- Expand "VALIDATION REPORT" for detailed analysis
- Critical errors block analysis
- Warnings allow analysis but flag concerns

#### 5. Analyze Recovery Table
- View "RECOVERY BY TRANCHE" table
- **Status** column shows "FULCRUM" for fulcrum security
- Check for APR violations (red alert)

#### 6. Run Monte Carlo (Optional)
- Expand "MONTE CARLO PARAMETERS"
- Set number of simulations (default: 10,000)
- Configure EV mean, std dev, leakage probability
- Click "RUN MONTE CARLO SIMULATION"
- Review probability distributions, fulcrum probabilities, risk heatmaps

#### 7. Generate IC Memo
- Click "GENERATE IC MEMO"
- Expand "VIEW FULL MEMO"
- Click "DOWNLOAD IC MEMO (MARKDOWN)"
- Memo includes audit trail with section/page citations

---

## Performance Optimization

### Target: <10s Response Times

**Optimizations Implemented:**

1. **Decimal Arithmetic**: All monetary calculations use `Decimal` for exact arithmetic (no float rounding errors)
2. **Efficient Validation**: Validation checks run in O(n) time where n = number of tranches
3. **Caching**: Streamlit session state caches waterfall results, validation results
4. **Lazy Evaluation**: Monte Carlo and tornado charts only run when explicitly requested

**Best Practices:**
- Use "Demo" mode for testing (faster than uploading large documents)
- For production, enable caching for API calls (market data, SEC filings)
- Run Monte Carlo with 10K simulations initially; increase to 50K only if needed

---

## Testing

### Run Validation Tests

```bash
# Run all validation tests
pytest tests/test_validation.py -v

# Run specific test
pytest tests/test_validation.py::test_validate_waterfall_success -v
```

### Manual Testing Checklist

- [ ] Dashboard loads with dark theme (no white backgrounds)
- [ ] All emojis removed from UI
- [ ] EBITDA multiple slider updates EV in real-time
- [ ] Fulcrum security badge displays correctly (gold background)
- [ ] Validation badges show correct colors (green/red/yellow)
- [ ] Validation report expands and shows detailed errors
- [ ] APR violations trigger red alert
- [ ] Data quality flags distinguish HARD_DATA vs INFERRED
- [ ] Recovery table shows "FULCRUM" status
- [ ] Monte Carlo simulation completes in <30s (10K sims)
- [ ] IC memo downloads as .md file

---

## API Reference

### Validation Functions

#### `validate_waterfall(waterfall_result, ev, tranches=None) -> ValidationResult`

Validate waterfall analysis results.

**Args:**
- `waterfall_result` (dict): Output from `run_waterfall()`
- `ev` (float | Decimal): Enterprise value used
- `tranches` (list, optional): Original tranches for cross-validation

**Returns:**
- `ValidationResult` with `valid` (bool), `errors` (list), `data_quality_flags` (dict)

#### `validate_capital_structure(tranches, expected_total_debt=None) -> ValidationResult`

Validate capital structure integrity.

**Args:**
- `tranches` (list): List of tranches with name, claim, optional tier
- `expected_total_debt` (float | Decimal, optional): Expected total debt

**Returns:**
- `ValidationResult`

#### `validate_ev_inputs(ev, ebitda=None, ebitda_multiple=None, data_source="INFERRED") -> ValidationResult`

Validate enterprise value and related inputs.

**Args:**
- `ev` (float | Decimal): Enterprise value
- `ebitda` (float | Decimal, optional): EBITDA
- `ebitda_multiple` (float | Decimal, optional): EBITDA multiple
- `data_source` (str): "HARD_DATA" | "INFERRED" | "ESTIMATED"

**Returns:**
- `ValidationResult`

#### `graceful_degradation_report(validation_result, component="Analysis") -> str`

Generate human-readable validation report.

**Args:**
- `validation_result` (ValidationResult): Result from validation functions
- `component` (str): Component name (e.g., "Waterfall", "Capital Structure")

**Returns:**
- Formatted report string

---

## Design Philosophy

### Bloomberg-Terminal Principles

1. **High Information Density**: Every pixel serves a purpose; no wasted space
2. **Professional Typography**: Inter for text, Roboto Mono for numbers
3. **Dark Theme**: Reduces eye strain during long analysis sessions
4. **Zero Casual Language**: Senior partners expect institutional-grade interface
5. **Status-First**: Validation status displayed prominently (green/red/yellow badges)
6. **Graceful Degradation**: Never block analysis; flag missing data and proceed

### Institutional Standards

- **Audit Trail**: Every flag includes source (HARD_DATA vs INFERRED)
- **Sanity Checks**: Every model run validated before display
- **Performance**: <10s response times for interactive workflows
- **Reliability**: Decimal arithmetic eliminates rounding errors
- **Transparency**: Validation reports explain every error/warning

---

## Troubleshooting

### Common Issues

**Issue**: Dashboard shows white background instead of dark theme
- **Cause**: CSS not loading or Streamlit cache
- **Fix**: Hard refresh (Ctrl+Shift+R) or clear Streamlit cache: `streamlit cache clear`

**Issue**: EBITDA slider doesn't update fulcrum
- **Cause**: Tranches not configured or waterfall not run
- **Fix**: Click "RUN WATERFALL ANALYSIS" first, then adjust slider

**Issue**: Validation shows "CRITICAL" errors but allows analysis
- **Cause**: Only CRITICAL errors block analysis; check severity
- **Fix**: Review "VALIDATION REPORT" for details; fix critical issues

**Issue**: "Recovery exceeds EV" error
- **Cause**: Waterfall logic error or negative EV
- **Fix**: Check collateral leakage adjustment; ensure EV > 0

**Issue**: Fonts not loading (Inter, Roboto Mono)
- **Cause**: Google Fonts blocked or network issue
- **Fix**: Check internet connection; fonts load from `fonts.googleapis.com`

---

## Future Enhancements

### Roadmap

1. **Parallel Processing**: Use `concurrent.futures` for Monte Carlo (target: 50K sims in 10s)
2. **Live Data Integration**: Connect to SEC EDGAR, Bloomberg API for real-time EBITDA
3. **Advanced Validation**: Machine learning to detect unusual covenant add-backs
4. **Export to Excel**: Generate institutional-grade Excel workbooks with charts
5. **Multi-Company Comparison**: Side-by-side waterfall comparisons for portfolio analysis

---

## Contact & Support

For questions, issues, or feature requests:
- **GitHub Issues**: (if project is on GitHub)
- **Internal Slack**: #signal-triage (if internal project)
- **Documentation**: See `/docs` folder for additional guides

---

**Last Updated**: January 29, 2026  
**Version**: 2.0 (Professional UI & Validation Layer)

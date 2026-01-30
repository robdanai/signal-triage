# UI Quick Reference — Signal Triage Professional Interface

## Color Palette (Bloomberg-Terminal Style)

### Backgrounds
```css
--bg-primary:    #0a0e17  /* Deep dark blue-black (main background) */
--bg-secondary:  #141822  /* Panels, cards, expanders */
--bg-tertiary:   #1a1f2e  /* Input fields, metrics */
```

### Text
```css
--text-primary:   #e0e3eb  /* High-contrast off-white (body text) */
--text-secondary: #9ca3af  /* Muted gray (labels, captions) */
--text-muted:     #6b7280  /* Very muted (footer, hints) */
```

### Accents
```css
--accent-blue:    #3b82f6  /* Primary action buttons, highlights */
--accent-green:   #10b981  /* Success, VALID, HARD_DATA */
--accent-red:     #ef4444  /* Errors, CRITICAL, INVALID */
--accent-yellow:  #f59e0b  /* Warnings, INFERRED data */
--border-color:   #2d3748  /* Borders, dividers */
--fulcrum:        #fbbf24  /* Gold badge for fulcrum security */
```

---

## Typography

### Fonts
- **Headings & Body:** Inter (Google Fonts)
- **Numbers & Data:** Roboto Mono (monospace for alignment)

### Font Weights
- **Regular:** 400 (body text, labels)
- **Medium:** 500 (buttons, subheadings)
- **Semibold:** 600 (headings, metrics)
- **Bold:** 700 (fulcrum badge, critical alerts)

### Font Sizes
- **h1:** 2rem (32px) — Main page title
- **h2:** 1.5rem (24px) — Section headers
- **h3:** 1.25rem (20px) — Subsection headers
- **Body:** 1rem (16px) — Standard text
- **Small:** 0.875rem (14px) — Labels, captions
- **Tiny:** 0.75rem (12px) — Footnotes, data flags

---

## Status Badges

### Validation Status
```html
<!-- Green: All checks passed -->
<span class='validation-valid'>WATERFALL VALID</span>
<span class='validation-valid'>CAPITAL STRUCTURE VALIDATED</span>

<!-- Red: Critical errors detected -->
<span class='validation-invalid'>VALIDATION ERRORS</span>
<span class='validation-invalid'>WATERFALL ERRORS</span>

<!-- Yellow: Warnings (non-critical) -->
<span class='validation-warning'>EV WARNINGS</span>
<span class='validation-warning'>APR VIOLATIONS</span>
```

### Data Quality Flags
```html
<!-- Green: Hard data from documents -->
<span class='data-flag-hard'>HARD DATA</span>

<!-- Yellow: Inferred or estimated -->
<span class='data-flag-inferred'>INFERRED</span>
```

### Fulcrum Security Badge
```html
<!-- Gold badge with dark text -->
<span class='fulcrum-badge'>1ST LIEN SECURED</span>
```

---

## Button Styles

### Primary Action
```html
<button type="primary">RUN WATERFALL ANALYSIS</button>
<button type="primary">GENERATE IC MEMO</button>
```
- Background: `#3b82f6` (blue)
- Text: white
- Hover: `#2563eb` (darker blue with shadow)

### Secondary Action
```html
<button>CONFIGURE PARAMETERS</button>
<button>VIEW DETAILS</button>
```
- Background: `#141822` (secondary background)
- Text: `#e0e3eb` (primary text)
- Border: 1px solid `#2d3748`

---

## UI Components

### Metrics Cards
```
┌─────────────────────────┐
│ DISTRESS SCORE          │  ← Label (small, uppercase, gray)
│ 85/100                  │  ← Value (large, bold, white)
└─────────────────────────┘
```
- Background: `#141822`
- Border: 1px solid `#2d3748`
- Label: 0.875rem, uppercase, `#9ca3af`
- Value: 1.75rem, bold, `#e0e3eb`

### Expanders
```
▼ CONFIGURE CAPITAL STRUCTURE  ← Header (clickable)
  ├─ Input fields
  └─ Buttons
```
- Header background: `#141822`
- Header text: `#e0e3eb`
- Border: 1px solid `#2d3748`
- Collapsed: shows ►
- Expanded: shows ▼

### Input Fields
```
┌─────────────────────────┐
│ LTM EBITDA ($M)         │  ← Label
│ [   15.0   ]            │  ← Input box
└─────────────────────────┘
```
- Background: `#1a1f2e`
- Text: `#e0e3eb`
- Border: 1px solid `#2d3748`
- Placeholder: `#6b7280` (muted gray)

### Sliders
```
EBITDA MULTIPLE (x)
───●──────────────────    ← Blue dot on dark track
3.0x        10.0x    20.0x
```
- Track: `#2d3748` (border color)
- Thumb: `#3b82f6` (blue)
- Active: `#2563eb` (darker blue)

---

## Alert Boxes

### Success (Green)
```
✓ Document analyzed successfully.
```
- Background: `rgba(16, 185, 129, 0.1)` (green tint)
- Border-left: 4px solid `#10b981`
- Text: `#10b981`

### Warning (Yellow)
```
⚠ Unusual EBITDA multiple detected (20.0x outside typical range)
```
- Background: `rgba(245, 158, 11, 0.1)` (yellow tint)
- Border-left: 4px solid `#f59e0b`
- Text: `#f59e0b`

### Error (Red)
```
✗ CRITICAL DISTRESS — Headroom < 15%
```
- Background: `rgba(239, 68, 68, 0.1)` (red tint)
- Border-left: 4px solid `#ef4444`
- Text: `#ef4444`

### Info (Blue)
```
ℹ Note: In production, this would show actual OpCo/HoldCo structure
```
- Background: `rgba(59, 130, 246, 0.1)` (blue tint)
- Border-left: 4px solid `#3b82f6`
- Text: `#3b82f6`

---

## Data Tables

### Recovery Table
```
┌──────────────────┬────────────┬────────────┬──────────────┬──────────┐
│ Tranche          │ Claim ($M) │ Recovered  │ Recovery (%) │ Status   │
├──────────────────┼────────────┼────────────┼──────────────┼──────────┤
│ 1st Lien Secured │ $100.0     │ $100.0     │ 100.0%       │          │
│ 2nd Lien / Mezz  │ $75.0      │ $50.0      │ 66.7%        │ FULCRUM  │
│ Unsecured        │ $50.0      │ $0.0       │ 0.0%         │          │
└──────────────────┴────────────┴────────────┴──────────────┴──────────┘
```
- Background: `#141822`
- Border: 1px solid `#2d3748`
- Header: bold, `#9ca3af`
- Data: `#e0e3eb` (Roboto Mono for alignment)
- Fulcrum row: highlighted with `#fbbf24` badge

---

## Interactive Elements

### EBITDA Multiple Slider
```
┌────────────────────────────────────────────────────────┐
│ INTERACTIVE VALUATION SENSITIVITY                      │
│                                                        │
│ EBITDA MULTIPLE (x)                     IMPLIED EV     │
│ ───────●──────────────────────          $105.0M       │
│ 3.0x        10.0x           20.0x       15.0M × 7.0x  │
└────────────────────────────────────────────────────────┘
```
- Slider updates EV in real-time
- Implied EV formula displayed
- Fulcrum security updates as you drag

### Validation Status Row
```
┌─────────────────┬─────────────────┬─────────────────┐
│ [WATERFALL      │ [EV VALIDATED]  │ [HARD DATA]     │
│  VALID]         │                 │                 │
│ (green)         │ (green)         │ (green)         │
└─────────────────┴─────────────────┴─────────────────┘
```
- Updates in real-time as validation runs
- Color-coded for instant status recognition

---

## Before/After Examples

### Page Title
**Before:**
```
🏦 Signal Triage — Investment Command Center
**Bloomberg-style Institutional Dashboard | Powered by Librarian • Quant • Auditor**
```

**After:**
```
SIGNAL TRIAGE | RESTRUCTURING COMMAND CENTER
INSTITUTIONAL FORENSIC CREDIT ANALYSIS | LIBRARIAN · QUANT · AUDITOR · BENCHMARKER · REPORTER
```

### Section Headers
**Before:**
```
### 📊 Interactive EV Sensitivity Slider
_Adjust EV to see real-time fulcrum migration and recovery updates:_
```

**After:**
```
### INTERACTIVE VALUATION SENSITIVITY
<p style='color: var(--text-secondary);'>Adjust EBITDA multiple to see real-time fulcrum migration and recovery updates</p>
```

### Button Labels
**Before:**
```
🚀 Run Waterfall Analysis
📝 Generate IC Memo
⬇️ Download IC Memo (Markdown)
```

**After:**
```
RUN WATERFALL ANALYSIS
GENERATE IC MEMO
DOWNLOAD IC MEMO (MARKDOWN)
```

### Alerts
**Before:**
```
✅ Document analyzed.
⚠️ Please enter text.
🚨 **CRITICAL DISTRESS** — Headroom < 15%
```

**After:**
```
Document analyzed successfully.
Please enter text to analyze.
**CRITICAL DISTRESS** — Headroom < 15%
```

---

## Keyboard Shortcuts (Streamlit Default)

- **Ctrl + Shift + R:** Hard refresh (clear cache)
- **Ctrl + K:** Open command palette (Streamlit)
- **Tab:** Navigate between input fields
- **Space:** Toggle expanders
- **Arrow Keys:** Adjust slider values

---

## Mobile Responsiveness

The dashboard is optimized for desktop use (1920x1080 and above). For mobile/tablet:
- Use horizontal scrolling for wide tables
- Touch-friendly sliders (larger thumb area)
- Collapsible sections to reduce vertical scroll

---

## Accessibility

- **High Contrast:** Text-to-background contrast ratio ≥ 7:1 (WCAG AAA)
- **Monospace Numbers:** Roboto Mono ensures alignment for screen readers
- **Semantic HTML:** Headers use proper h1, h2, h3 hierarchy
- **Status Badges:** Color + text (not color alone) for colorblind users

---

## Browser Compatibility

Tested on:
- **Chrome 120+** ✓
- **Edge 120+** ✓
- **Firefox 121+** ✓
- **Safari 17+** ✓ (requires -webkit prefixes for some animations)

---

## Print Styling

When printing (Ctrl + P):
- Background colors removed (save ink)
- Dark theme inverted to light (black text on white)
- Charts exported as high-res images

---

## Custom CSS Classes Reference

### Validation Badges
```css
.validation-valid    /* Green badge: VALID */
.validation-invalid  /* Red badge: INVALID */
.validation-warning  /* Yellow badge: WARNING */
```

### Data Quality Flags
```css
.data-flag-hard      /* Green text: HARD DATA */
.data-flag-inferred  /* Yellow text: INFERRED */
```

### Fulcrum Security
```css
.fulcrum-badge       /* Gold badge: Fulcrum security name */
```

### Metrics
```css
.stMetric            /* Metric card (Streamlit default) */
```

---

## Footer

Standard footer text:
```
SIGNAL TRIAGE | RESTRUCTURING COMMAND CENTER
LIBRARIAN · QUANT · BENCHMARKER · AUDITOR · REPORTER
INSTITUTIONAL DISTRESSED DEBT ANALYSIS | AUDIT-GRADE CITATIONS
```
- Font size: 0.75rem
- Color: `#6b7280` (muted)
- Letter-spacing: 0.1em (wide for institutional look)
- Text-align: center

---

## Quick Tips

1. **Always run validation:** Click "RUN WATERFALL ANALYSIS" before adjusting sliders
2. **Check badges:** Green = proceed, Yellow = review warnings, Red = fix errors
3. **Expand validation reports:** Click "VALIDATION REPORT" for detailed diagnostics
4. **HARD_DATA vs INFERRED:** Track data quality with color-coded badges
5. **Fulcrum migration:** Watch gold badge change as you adjust EBITDA multiple

---

**Last Updated:** January 29, 2026  
**Version:** 2.0 (Professional UI)

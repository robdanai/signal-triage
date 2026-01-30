# Signal Triage 2.0 - Multi-Page Professional Edition

## 🎯 Quick Start

```powershell
START_APP.bat          # Windows
./START_APP.sh         # Mac/Linux
```

Then open: **http://localhost:8501**

---

## 📱 New Multi-Page Interface

### Home Page (Command Center)
Your starting point with:
- System status overview
- Workstream cards with descriptions
- Quick action buttons
- Recent activity feed

### Workstream Pages

#### 📄 Document Analysis
**What it does**: Parse and analyze documents  
**File formats**: PDF, DOCX, DOC, TXT, MD, RTF  
**Key features**:
- Upload credit agreements, 10-Ks, restructuring docs
- LME signal detection (40+ trap doors)
- Covenant extraction
- Filter by severity
- Evidence with citations

**How to use**:
1. Click "Launch Document Analysis" from Home
2. Select input mode (Upload / Manual / Demo)
3. Choose your file (PDF or DOCX recommended)
4. Click "ANALYZE DOCUMENT"
5. Review signals and covenant flags

---

#### 💰 Waterfall & Recovery
**What it does**: Model recovery scenarios  
**Key features**:
- Interactive EBITDA multiple slider
- Real-time fulcrum identification
- APR violation detection
- Tornado sensitivity charts
- Monte Carlo simulation

**How to use**:
1. Configure capital structure in sidebar
2. Enter debt tranches (1L, 2L, Unsecured)
3. Click "RUN WATERFALL"
4. Drag EBITDA slider to see fulcrum migrate
5. Review recovery rates and APR violations

---

#### 📊 Market Benchmarking
**What it does**: Compare against peers  
**Key features**:
- Peer valuation multiples
- Leverage ratio comparison
- Historical distressed comps
- Treasury yields & credit spreads
- Live API data integration

**How to use**:
1. Enter company ticker in sidebar
2. Select industry and geography filters
3. Choose time period
4. Click "RUN BENCHMARK ANALYSIS"
5. Review peer comparison and comps

---

#### 🔍 Covenant Forensics
**What it does**: Deep covenant analysis  
**Key features**:
- Covenant headroom calculator
- EBITDA add-back validation
- Chapter 11 feasibility
- Adequate protection analysis
- Conservative haircut application

**How to use**:
1. Select tab (Headroom / Ch. 11 / EBITDA Forensics)
2. Enter financial parameters
3. Click "CALCULATE" or "ASSESS"
4. Review breach risk and feasibility
5. Export results

---

#### 📋 Reports & Memos
**What it does**: Generate professional reports  
**Key features**:
- Investment Committee memos
- Executive summaries
- Audit trail reports
- Data room packages
- Multiple download formats

**How to use**:
1. Select report type
2. Configure settings (citations, visuals, etc.)
3. Click "GENERATE REPORT"
4. Review generated content
5. Download in preferred format

---

## 🔄 Navigation

### Sidebar Menu
All workstreams accessible via sidebar:
```
🏠 Home
📄 Document Analysis
💰 Waterfall & Recovery
📊 Market Benchmarking
🔍 Covenant Forensics
📋 Reports & Memos
```

### Cross-Page Workflow
1. **Document Analysis** → Analyze your document
2. **Waterfall & Recovery** → Model recovery scenarios
3. **Covenant Forensics** → Check breach risk
4. **Market Benchmarking** → Compare to peers
5. **Reports & Memos** → Generate IC memo

### Quick Actions
Home page provides quick jumps:
- "Run Demo Analysis" → Document Analysis (Demo mode)
- "Upload & Analyze" → Document Analysis (Upload mode)
- "View API Docs" → FastAPI documentation

---

## 📁 File Format Support

### Supported Types

| Format | Extension | Use Case | Library Required |
|--------|-----------|----------|------------------|
| PDF | `.pdf` | Credit agreements, 10-Ks | `pdfplumber` |
| Word | `.docx`, `.doc` | Draft agreements, redlines | `python-docx` |
| Text | `.txt` | Plain text documents | Built-in |
| Markdown | `.md` | Documentation, notes | Built-in |
| Rich Text | `.rtf` | Legacy documents | `striprtf` |

### Installation

```powershell
# Install all document parsers
pip install -r requirements_parsers.txt

# Or install individually:
pip install pdfplumber      # For PDF support
pip install python-docx     # For DOCX support
pip install striprtf        # For RTF support
```

### Best Practices

**PDF Files:**
- Use high-quality scans
- Ensure text is selectable (not image-only)
- Most credit agreements work perfectly

**Word Files:**
- Native `.docx` preferred over `.doc`
- Redlines and comments preserved
- Tables extracted as text

**Text Files:**
- UTF-8 encoding recommended
- Markdown formatting supported
- Code blocks preserved

---

## 🎨 Interface Design

### Dark Theme
Professional Bloomberg-terminal aesthetic:
- Dark background (#0a0e17)
- Light text (#e0e3eb)
- Blue accents (#3b82f6)
- Monospace for numbers

### Layout
- **Wide layout**: Maximum screen utilization
- **Sidebar**: Navigation and settings
- **Main area**: Workstream content
- **Tabs**: Sub-features within workstreams

### Components
- Metric cards with deltas
- Data tables with highlighting
- Interactive charts (Plotly)
- Expandable sections
- Download buttons

---

## 💾 Session State

### Persistent Data
Data persists across page navigation:
- `analysis_result` → Document analysis output
- `waterfall_result` → Recovery waterfall data
- `tranches` → Capital structure
- `ic_memo` → Generated reports

### Usage
Upload a document once, use results everywhere:
1. Upload in Document Analysis
2. Results available in all other workstreams
3. Generate reports using same data
4. No need to re-upload

---

## 🔧 Configuration

### Environment Variables
Edit `.env` file for:
- Database connection
- API keys (FRED, Alpha Vantage, etc.)
- Cache settings
- Log levels

### API Keys
Optional but enhances functionality:
```ini
# Free APIs
SEC_USER_AGENT=YourCompany/1.0 (your@email.com)
FRED_API_KEY=your_key_here
ALPHAVANTAGE_API_KEY=your_key_here

# Commercial APIs (optional)
IEX_API_TOKEN=your_token
NINEFIN_API_KEY=your_key
BLOOMBERG_API_KEY=your_key
```

---

## 📖 Documentation

**Getting Started:**
- `START_HERE.md` - User-friendly intro
- `QUICK_START.md` - Complete setup guide
- `README.md` - Project overview

**Technical:**
- `MULTI_PAGE_UPGRADE.md` - Multi-page app details
- `ISSUE_FIXED.md` - What was wrong & fixed
- `UPGRADE_COMPLETE.md` - Complete change log

**Deployment:**
- `docs/DEPLOYMENT.md` - Production setup
- `docs/MONITORING.md` - Observability
- `CONTRIBUTING.md` - Development guide

---

## 🚀 Performance

### Optimizations
- Lazy loading of workstreams
- Cached analysis results
- Efficient file parsing
- Minimal re-runs

### Responsiveness
- Fast page transitions
- Instant sidebar navigation
- Quick file uploads
- Real-time slider updates

---

## 🎯 Use Cases

### Investment Committee Review
```
1. Upload credit agreement (Document Analysis)
2. Review LME signals and covenant flags
3. Model recovery scenarios (Waterfall)
4. Check covenant headroom (Forensics)
5. Generate IC memo (Reports)
6. Download for presentation
```

### Quick Deal Screen
```
1. Run demo mode (Document Analysis)
2. Review distress score
3. Check if LME exposure is material
4. Make go/no-go decision
```

### Deep Dive Analysis
```
1. Upload all deal documents
2. Full LME analysis
3. Detailed waterfall modeling
4. Peer benchmarking
5. Chapter 11 feasibility
6. Comprehensive IC memo
```

---

## 🆘 Troubleshooting

### Navigation Issues
```powershell
# Make sure you're using Home.py
streamlit run signal_triage\ui\Home.py --server.port=8501
```

### File Upload Errors
```powershell
# Install parsers
pip install pdfplumber python-docx striprtf
```

### Session State Lost
- Refresh the page
- Re-upload document
- Check browser console for errors

### Want Old Dashboard
```powershell
# Use legacy version
streamlit run signal_triage\ui\dashboard.py
```

---

## 📊 Comparison

| Feature | Old Dashboard | New Multi-Page |
|---------|---------------|----------------|
| **Pages** | 1 (everything) | 6 (organized) |
| **Navigation** | Scroll | Sidebar menu |
| **File Support** | TXT only | PDF, DOCX, TXT, MD, RTF |
| **Workflow** | Linear | Workstream-based |
| **Reports** | Basic | Professional IC memos |
| **UX** | Cluttered | Clean, focused |
| **Code** | 1,000+ lines | Modular pages |

---

## 🎉 Summary

**What's New:**
- ✅ Professional multi-page architecture
- ✅ 5 workstream-based pages
- ✅ Multi-format file support (PDF, DOCX, RTF)
- ✅ Enhanced navigation and UX
- ✅ Institutional-grade interface

**To Start:**
```powershell
START_APP.bat
```

**Then Open:**
```
http://localhost:8501
```

**Documentation:**
See `UPGRADE_COMPLETE.md` for full details

---

**Signal Triage 2.0** | Institutional Restructuring Command Center

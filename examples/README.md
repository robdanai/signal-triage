# Signal Triage Examples

Real-world examples and case studies demonstrating Signal Triage's forensic analysis capabilities.

## 🚀 Quick Start (5 Minutes)

```bash
cd examples
python quickstart.py
```

This script demonstrates:
- ✅ Document analysis with LME detection
- ✅ Recovery waterfall modeling
- ✅ Covenant headroom forensics
- ✅ Chapter 11 feasibility assessment

## 📚 Case Studies

### Available Case Studies

Each case study analyzes a real-world restructuring with:
- Original credit agreement analysis
- LME trap doors identified
- Recovery waterfall with APR checks
- Comparison to actual outcome

#### 1. J.Crew (2017) - The Original Dropdown
- **File:** `case_studies/jcrew_analysis.md`
- **LME Type:** Dropdown / IP transfer to unrestricted subsidiary
- **Outcome:** $1.7B distressed exchange; lender lawsuit
- **Key Learning:** Importance of J.Crew blocker provisions

#### 2. Serta Simmons (2020) - Non-Consensual Uptier
- **File:** `case_studies/serta_analysis.md`
- **LME Type:** Uptiering / lender-on-lender violence
- **Outcome:** Majority lenders primed minority without consent
- **Key Learning:** Required Lenders (>50%) can subordinate minority

#### 3. Hertz (2020) - Equity Value in Bankruptcy
- **File:** `case_studies/hertz_analysis.md`
- **LME Type:** APR violation (equity getting value while creditors impaired)
- **Outcome:** Shareholders received value; creditors objected
- **Key Learning:** Market timing can create going-concern value exceeding liquidation

## 📊 Example Workflows

### Workflow 1: Analyze a Credit Agreement

```bash
# Basic analysis
signal-triage credit_agreement.pdf

# Full pipeline with live data
BENCHMARKER_USE_LIVE=1 signal-triage --pipeline credit_agreement.pdf

# With covenant forensics
signal-triage --pipeline credit_agreement.pdf \
  --covenant-params '{"reported_ebitda": 100, "total_debt": 550, "leverage_covenant": 6.0}'
```

### Workflow 2: Batch Portfolio Analysis

```bash
# Analyze multiple documents
signal-triage --pipeline --batch ./documents/

# With comparator (prior vs current)
signal-triage --pipeline --batch ./documents/ --recursive
```

### Workflow 3: API Integration

```bash
# Start API server
python -m uvicorn signal_triage.fastapi_app.main:create_app --factory --reload

# Submit analysis job
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: your_key" \
  -F "file=@credit_agreement.pdf" \
  -F 'request={"industry":"Technology","analysis_type":"full"}'

# Check job status
curl http://localhost:8000/jobs/{job_id}

# Get results
curl http://localhost:8000/analyses/{analysis_id}
```

## 🎓 Interactive Learning

### Jupyter Notebook Demo

```bash
pip install jupyter
jupyter notebook jupyter_notebook_demo.ipynb
```

**Topics covered:**
1. Document ingestion (PDF, URL, SEC EDGAR)
2. Librarian extraction (covenants, baskets, LME flags)
3. Quant waterfall (recovery rates, fulcrum security)
4. Benchmarker validation (market multiples, precedent recovery)
5. Auditor stress-testing (APR, precision, Critical Variance)
6. Full pipeline orchestration

### Streamlit Dashboard

```bash
streamlit run ../signal_triage/ui/dashboard.py
```

**Features:**
- 📊 Upload credit agreements or paste text
- 🚩 Interactive LME flag explorer with definitions
- 💰 Recovery waterfall visualization
- 📈 Covenant headroom gauge
- ⚖️ Chapter 11 feasibility model

## 🐳 Docker Quick Start

```bash
# Build and run with docker-compose
docker-compose up

# API server will be available at http://localhost:8000
# Streamlit dashboard at http://localhost:8501
```

## 📂 Directory Structure

```
examples/
├── README.md                          # This file
├── quickstart.py                      # 5-minute getting started
├── jupyter_notebook_demo.ipynb        # Interactive tutorial
├── docker-compose.yml                 # One-command local setup
├── case_studies/
│   ├── jcrew_analysis.md              # J.Crew dropdown case
│   ├── serta_analysis.md              # Serta uptier case
│   ├── hertz_analysis.md              # Hertz equity value case
│   ├── sample_documents/              # Sanitized sample docs
│   └── README.md                      # Case study index
└── advanced/
    ├── custom_recovery_model.py       # Custom waterfall logic
    ├── basket_stacking_detection.py   # Multi-basket leakage
    └── monte_carlo_stress_test.py     # Probabilistic analysis
```

## 🔧 Environment Setup

### Free Tier (SEC EDGAR + FRED)

```bash
# Enable live data
export BENCHMARKER_USE_LIVE=1
export BENCHMARKER_DATA_SOURCE=edgar

# Get FRED API key (free, 5 minutes)
# https://fred.stlouisfed.org/docs/api/api_key.html
export FRED_API_KEY=your_key_here

# Run analysis
signal-triage --pipeline credit_agreement.pdf
```

### Institutional Tier (Add 9fin / Bloomberg)

```bash
# Free tier + commercial APIs
export NINEFIN_API_KEY=your_9fin_key
export BLOOMBERG_API_KEY=your_bloomberg_key  # or use Bloomberg Terminal

# Now get live precedent recovery rates and peer multiples
signal-triage --pipeline credit_agreement.pdf
```

## 📖 Learning Resources

### Documentation

- **Forensic Capabilities:** `../docs/FORENSIC_ENHANCEMENTS.md`
- **LME Categories:** `../docs/LME_CATEGORIES.md`
- **API Documentation:** `../docs/API_INFRASTRUCTURE.md`
- **Live Data Setup:** `../docs/LIVE_DATA_SETUP.md`

### Video Tutorials (Coming Soon)

- [ ] 5-minute quickstart walkthrough
- [ ] J.Crew case study deep dive
- [ ] API integration tutorial
- [ ] Building custom recovery models

## 🤝 Contributing

Want to add a case study or example?

1. Fork the repository
2. Add your example to `examples/case_studies/`
3. Update this README with a link
4. Submit a pull request

**Case study format:**
- Markdown document with analysis narrative
- Sample input document (sanitized, no confidential data)
- Expected output (signals, waterfall, benchmarker results)
- Comparison to actual outcome (if public)

## ❓ Troubleshooting

### "Module not found: signal_triage"

```bash
# Make sure Signal Triage is installed
pip install -e .

# Or run from project root
cd ..
python examples/quickstart.py
```

### "No live market data"

```bash
# Check environment variables
echo $BENCHMARKER_USE_LIVE
echo $FRED_API_KEY

# Set if missing
export BENCHMARKER_USE_LIVE=1
export FRED_API_KEY=your_key
```

### "PDF parsing error"

```bash
# Install PDF dependencies
pip install pypdf pdfplumber

# Try text file instead
signal-triage sample.txt
```

## 📞 Support

- **GitHub Issues:** Report bugs or request features
- **Documentation:** Check `../docs/` for detailed guides
- **Community:** [Join our Slack/Discord] (link when available)

---

**Happy Analyzing! 🚀**

For questions or contributions, please open an issue on GitHub.

"""
Reports & Memos Workstream — REPORTER

Generate Investment Committee memos, audit trails, and executive summaries.
Features:
- IC Memo generation (Markdown/PDF)
- Executive Summary
- Audit Trail Report
- Data Room Package
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from signal_triage.reports.memo_generator import generate_ic_memo
from signal_triage.reports.document_report import build_document_report

# Page config
st.set_page_config(
    page_title="Reports & Memos | Signal Triage",
    page_icon="📋",
    layout="wide",
)

# Apply dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    .stApp { background-color: #0a0e17; color: #e0e3eb; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e0e3eb; }
    .report-preview {
        background-color: #141822;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.9rem;
        max-height: 600px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📋 REPORTS & MEMOS")
st.markdown("**Workstream: REPORTER** | Generate institutional-grade documentation")
st.markdown("---")

# Initialize session state
if "generated_report" not in st.session_state:
    st.session_state["generated_report"] = None
if "selected_analysis" not in st.session_state:
    st.session_state["selected_analysis"] = None

# Sidebar: Report Type
st.sidebar.markdown("### REPORT TYPE")
report_type = st.sidebar.radio(
    "Select format",
    ["📝 IC Memo", "📊 Executive Summary", "🔍 Audit Trail", "📦 Data Room Package"],
    label_visibility="collapsed"
)

# Report configuration
st.sidebar.markdown("---")
st.sidebar.markdown("### CONFIGURATION")

include_citations = st.sidebar.checkbox("Include Citations", value=True)
include_evidence = st.sidebar.checkbox("Include Evidence Snippets", value=True)
include_charts = st.sidebar.checkbox("Include Charts & Tables", value=True)
confidential = st.sidebar.checkbox("Mark as Confidential", value=True)

if report_type == "📝 IC Memo":
    st.subheader("Investment Committee Memo Generator")
    
    st.markdown("""
    Generate a formal Investment Committee memorandum with:
    - Executive summary
    - Credit analysis
    - LME signals and trap doors
    - Recovery waterfall
    - Market benchmarking
    - Recommendation
    """)
    
    # Input: Company details
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input("Company Name", value="", placeholder="e.g., J.Crew Group")
        ticker = st.text_input("Ticker", value="", placeholder="e.g., JCG")
        industry = st.selectbox("Industry", ["Retail", "Energy", "Healthcare", "Technology", "Manufacturing", "Real Estate", "Financial Services", "Other"])
    
    with col2:
        total_debt = st.number_input("Total Debt ($M)", min_value=0.0, value=0.0, step=10.0)
        ev = st.number_input("Enterprise Value ($M)", min_value=0.0, value=0.0, step=10.0)
        distress_score = st.slider("Distress Score", min_value=0, max_value=100, value=50, step=1)
    
    # Analysis summary
    st.markdown("**Analysis Summary**")
    key_findings = st.text_area(
        "Key Findings",
        value="",
        placeholder="Summarize key findings from the analysis...",
        height=150
    )
    
    recommendation = st.selectbox(
        "Recommendation",
        ["BUY", "HOLD", "SELL", "PASS"]
    )
    
    if st.button("📝 Generate IC Memo", type="primary"):
        with st.spinner("Generating IC memo..."):
            try:
                # Build memo data
                memo_data = {
                    "company_name": company_name,
                    "ticker": ticker,
                    "industry": industry,
                    "total_debt": total_debt,
                    "enterprise_value": ev,
                    "distress_score": distress_score,
                    "key_findings": key_findings,
                    "recommendation": recommendation,
                    "date": datetime.now().strftime("%B %d, %Y"),
                }
                
                # Generate memo
                memo_text = generate_ic_memo(
                    company_name=company_name,
                    distress_score=distress_score,
                    signals=[],  # Load from analysis if available
                    waterfall=None,
                    benchmarking=None,
                    recommendation=recommendation,
                )
                
                st.session_state["generated_report"] = memo_text
                st.success("✅ IC Memo generated!")
            except Exception as e:
                st.error(f"Error generating memo: {e}")
    
    # Display memo
    if st.session_state.get("generated_report"):
        st.markdown("---")
        st.subheader("IC Memo Preview")
        
        memo = st.session_state["generated_report"]
        
        st.markdown(f"""
        <div class='report-preview'>
        {memo}
        </div>
        """, unsafe_allow_html=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Markdown",
                data=memo,
                file_name=f"ic_memo_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        with col2:
            # Note: PDF generation would require reportlab or similar
            st.info("PDF export: Install reportlab for PDF generation")

elif report_type == "📊 Executive Summary":
    st.subheader("Executive Summary Generator")
    
    st.markdown("""
    Generate a concise 1-page executive summary for senior management with:
    - Company overview
    - Distress indicators
    - Key risks (top 5)
    - Recovery scenario (fulcrum, APR violations)
    - Recommendation
    """)
    
    # Load from analysis or manual entry
    input_mode = st.radio(
        "Input Source",
        ["📄 From Analysis", "✍️ Manual Entry"],
        horizontal=True
    )
    
    if input_mode == "✍️ Manual Entry":
        company_name = st.text_input("Company Name", value="")
        distress_score = st.slider("Distress Score", 0, 100, 50, 1)
        
        st.markdown("**Top 5 Risks**")
        risks = []
        for i in range(5):
            risk = st.text_input(f"Risk {i+1}", key=f"risk_{i}", placeholder=f"Risk {i+1}...")
            if risk:
                risks.append(risk)
        
        recovery_summary = st.text_area(
            "Recovery Summary",
            placeholder="Summarize recovery waterfall and fulcrum...",
            height=100
        )
        
        if st.button("📊 Generate Executive Summary", type="primary"):
            with st.spinner("Generating executive summary..."):
                try:
                    # Build summary
                    summary = f"""# EXECUTIVE SUMMARY
## {company_name}
**Date:** {datetime.now().strftime("%B %d, %Y")}
**Distress Score:** {distress_score}/100

### KEY RISKS
"""
                    for i, risk in enumerate(risks, 1):
                        summary += f"{i}. {risk}\n"
                    
                    summary += f"\n### RECOVERY SCENARIO\n{recovery_summary}\n"
                    
                    st.session_state["generated_report"] = summary
                    st.success("✅ Executive summary generated!")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("**Feature:** Load from previous analysis. Coming soon!")
    
    # Display summary
    if st.session_state.get("generated_report"):
        st.markdown("---")
        st.subheader("Executive Summary Preview")
        
        summary = st.session_state["generated_report"]
        
        st.markdown(f"""
        <div class='report-preview'>
        {summary}
        </div>
        """, unsafe_allow_html=True)
        
        st.download_button(
            label="📥 Download Summary",
            data=summary,
            file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )

elif report_type == "🔍 Audit Trail":
    st.subheader("Audit Trail Report")
    
    st.markdown("""
    Generate a comprehensive audit trail with:
    - All analysis steps (Librarian → Quant → Benchmarker → Auditor)
    - Data sources and timestamps
    - Configuration versions
    - Input/output for each agent
    - Reproducibility manifest
    """)
    
    st.info("**Feature:** Audit trail requires a completed pipeline run. Use `--pipeline` CLI or API /analyze endpoint.")
    
    # Placeholder for loading from pipeline
    st.markdown("""
    **How to generate:**
    1. Run full pipeline: `python main.py --pipeline document.txt --out report.json`
    2. Load report.json here for audit trail visualization
    3. Export as PDF or HTML
    """)
    
    uploaded_report = st.file_uploader(
        "Upload Pipeline Report (JSON)",
        type=["json"],
        help="Upload the report.json from a --pipeline run"
    )
    
    if uploaded_report:
        try:
            report_data = json.load(uploaded_report)
            
            st.markdown("---")
            st.subheader("Audit Trail")
            
            # Display pipeline stages
            stages = ["Librarian", "Quant", "Benchmarker", "Auditor", "Reporter"]
            
            for stage in stages:
                stage_key = stage.lower()
                if f"{stage_key}_summary" in report_data:
                    with st.expander(f"✅ {stage}", expanded=False):
                        st.json(report_data[f"{stage_key}_summary"])
            
            # Reproducibility
            if "config_versions" in report_data:
                st.markdown("### Reproducibility")
                st.json(report_data["config_versions"])
            
            # Export
            if st.button("📥 Export Full Audit Trail"):
                audit_trail_json = json.dumps(report_data, indent=2)
                st.download_button(
                    label="Download Audit Trail (JSON)",
                    data=audit_trail_json,
                    file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        except Exception as e:
            st.error(f"Error parsing report: {e}")

elif report_type == "📦 Data Room Package":
    st.subheader("Data Room Package Generator")
    
    st.markdown("""
    Generate a comprehensive data room package with:
    - All analysis reports
    - Source documents (with citations)
    - Financial models (Excel export)
    - Covenant extraction
    - Audit trail
    - Executive summary
    """)
    
    st.info("**Feature:** Data room package combines all reports into a ZIP archive.")
    
    # Package configuration
    st.markdown("**Select Components**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_ic_memo = st.checkbox("IC Memo", value=True)
        include_exec_summary = st.checkbox("Executive Summary", value=True)
        include_audit_trail = st.checkbox("Audit Trail", value=True)
        include_covenant_extraction = st.checkbox("Covenant Extraction", value=True)
    
    with col2:
        include_waterfall = st.checkbox("Recovery Waterfall (Excel)", value=True)
        include_monte_carlo = st.checkbox("Monte Carlo Results", value=True)
        include_source_docs = st.checkbox("Source Documents", value=False)
        include_citations = st.checkbox("Citation Index", value=True)
    
    if st.button("📦 Generate Data Room Package", type="primary"):
        st.info("**Feature:** Data room package generation is coming soon. This will create a ZIP file with all selected components.")
        
        st.markdown("""
        **Package will include:**
        - `/memos/` - IC memo and executive summary
        - `/analysis/` - Full analysis reports
        - `/models/` - Excel waterfalls and Monte Carlo results
        - `/documents/` - Source documents (if included)
        - `/audit/` - Audit trail and reproducibility manifest
        - `README.md` - Package index
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>
    <p>SIGNAL TRIAGE | REPORTER Workstream</p>
    <p>IC Memos · Executive Summaries · Audit Trails · Data Room Packages</p>
</div>
""", unsafe_allow_html=True)

"""
Signal Triage — Home & Command Center

Landing page with system overview, quick actions, and navigation to workstreams.
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from signal_triage.config import get_config

# Page config
st.set_page_config(
    page_title="Signal Triage | Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #141822;
        --bg-tertiary: #1a1f2e;
        --text-primary: #e0e3eb;
        --text-secondary: #9ca3af;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --border-color: #2d3748;
    }
    
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    .workflow-card {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.2s;
    }
    
    .workflow-card:hover {
        border-color: var(--accent-blue);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: var(--accent-green);
    }
    
    .stButton > button {
        background-color: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 500;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style='text-align: center; padding: 2rem 0;'>
    <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>SIGNAL TRIAGE</h1>
    <p style='color: var(--text-secondary); font-size: 1rem; letter-spacing: 0.1em;'>
        INSTITUTIONAL RESTRUCTURING COMMAND CENTER
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# System Status
st.subheader("System Status")
col1, col2, col3, col4 = st.columns(4)

try:
    config = get_config()
    providers = config.get_available_providers()
    
    with col1:
        st.metric("Database", "Connected", delta="Online")
    with col2:
        api_count = sum(1 for p in providers.values() if p)
        st.metric("API Providers", f"{api_count}/7", delta=f"{api_count} Active")
    with col3:
        st.metric("Cache", "File-based", delta="Ready")
    with col4:
        st.metric("Environment", config.environment.upper(), delta="Active")
except Exception as e:
    st.error(f"Configuration error: {e}")

st.markdown("---")

# Workstreams
st.subheader("Analysis Workstreams")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    <div class='workflow-card'>
        <h3>📄 Document Analysis</h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Parse credit agreements, 10-Ks, and restructuring documents. Extract covenants, 
            capital structure, and financial metrics.
        </p>
        <p><strong>Key Features:</strong></p>
        <ul style='color: var(--text-secondary);'>
            <li>Multi-format document parsing (PDF, DOCX, TXT)</li>
            <li>Covenant extraction and classification</li>
            <li>LME signal detection (40+ trap doors)</li>
            <li>Capital structure reconstruction</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Document Analysis →", key="doc_analysis"):
        st.switch_page("pages/1_📄_Document_Analysis.py")
    
    st.markdown("""
    <div class='workflow-card'>
        <h3>📊 Market Benchmarking</h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Compare company metrics against sector peers and historical restructurings. 
            Live market data integration.
        </p>
        <p><strong>Data Sources:</strong></p>
        <ul style='color: var(--text-secondary);'>
            <li>SEC EDGAR (10-K, 8-K filings)</li>
            <li>FRED (Treasury yields, economic data)</li>
            <li>Alpha Vantage (stock prices)</li>
            <li>Historical distressed comps database</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Benchmarking →", key="benchmarking"):
        st.switch_page("pages/3_📊_Market_Benchmarking.py")
    
    st.markdown("""
    <div class='workflow-card'>
        <h3>📋 Reports & Memos</h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Generate Investment Committee memos, audit trails, and executive summaries 
            with visual citations.
        </p>
        <p><strong>Output Formats:</strong></p>
        <ul style='color: var(--text-secondary);'>
            <li>IC Memo (Markdown/PDF)</li>
            <li>Executive Summary</li>
            <li>Audit Trail Report</li>
            <li>Data Room Package</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Report Generator →", key="reports"):
        st.switch_page("pages/5_📋_Reports_&_Memos.py")

with col_right:
    st.markdown("""
    <div class='workflow-card'>
        <h3>💰 Waterfall & Recovery</h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Model recovery waterfalls, identify fulcrum securities, and run sensitivity 
            analysis across valuation scenarios.
        </p>
        <p><strong>Analysis Tools:</strong></p>
        <ul style='color: var(--text-secondary);'>
            <li>Interactive EBITDA multiple slider</li>
            <li>APR violation detection</li>
            <li>Monte Carlo simulation (10K+ scenarios)</li>
            <li>Tornado charts for recovery drivers</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Waterfall Analysis →", key="waterfall"):
        st.switch_page("pages/2_💰_Waterfall_&_Recovery.py")
    
    st.markdown("""
    <div class='workflow-card'>
        <h3>🔍 Covenant Forensics</h3>
        <p style='color: var(--text-secondary); margin-bottom: 1rem;'>
            Deep-dive covenant analysis, headroom calculations, and EBITDA add-back 
            validation. Chapter 11 feasibility modeling.
        </p>
        <p><strong>Forensic Tools:</strong></p>
        <ul style='color: var(--text-secondary);'>
            <li>Covenant headroom calculator</li>
            <li>EBITDA normalization & haircuts</li>
            <li>Chapter 11 feasibility assessment</li>
            <li>Adequate protection analysis</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Launch Covenant Forensics →", key="forensics"):
        st.switch_page("pages/4_🔍_Covenant_Forensics.py")

st.markdown("---")

# Quick Actions
st.subheader("Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🚀 Quick Start**")
    if st.button("Run Demo Analysis", use_container_width=True):
        st.switch_page("pages/1_📄_Document_Analysis.py")

with col2:
    st.markdown("**📤 Upload Document**")
    if st.button("Upload & Analyze", use_container_width=True):
        st.switch_page("pages/1_📄_Document_Analysis.py")

with col3:
    st.markdown("**📊 API Access**")
    if st.button("View API Docs", use_container_width=True):
        st.markdown("[API Documentation](http://127.0.0.1:8000/docs)")

st.markdown("---")

# Recent Activity (placeholder)
st.subheader("Recent Activity")
st.info("No recent analyses. Upload a document to get started.")

# Footer
st.markdown("""
<div style='text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.85rem;'>
    <p>SIGNAL TRIAGE v1.0 | Institutional Distressed Debt Analysis</p>
    <p>LIBRARIAN · QUANT · BENCHMARKER · AUDITOR · REPORTER</p>
</div>
""", unsafe_allow_html=True)

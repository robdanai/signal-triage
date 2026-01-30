"""
Market Benchmarking Workstream — BENCHMARKER

Compare company metrics against sector peers and historical restructurings.
Features:
- SEC EDGAR live data integration
- FRED economic data
- Historical distressed comparables
- Critical Variance analysis
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from signal_triage.agents.benchmarker import run_benchmarker

# Page config
st.set_page_config(
    page_title="Market Benchmarking | Signal Triage",
    page_icon="📊",
    layout="wide",
)

# Apply dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    .stApp { background-color: #0a0e17; color: #e0e3eb; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e0e3eb; }
    .benchmark-card {
        background-color: #141822;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .variance-critical {
        background-color: #7f1d1d;
        border-left: 4px solid #ef4444;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .variance-ok {
        background-color: #14532d;
        border-left: 4px solid #10b981;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📊 MARKET BENCHMARKING")
st.markdown("**Workstream: BENCHMARKER** | Compare against peers and historical precedents")
st.markdown("---")

# Initialize session state
if "benchmark_result" not in st.session_state:
    st.session_state["benchmark_result"] = None

# Sidebar: Configuration
st.sidebar.markdown("### FILTERS")

industry = st.sidebar.selectbox(
    "Industry",
    ["All", "Retail", "Energy", "Healthcare", "Technology", "Manufacturing", "Real Estate", "Financial Services"],
    index=0
)

geography = st.sidebar.selectbox(
    "Geography",
    ["All", "US", "Europe", "Asia", "Latin America"],
    index=0
)

include_live_data = st.sidebar.checkbox("Include Live Market Data", value=True)

if include_live_data:
    st.sidebar.info("✅ Live data enabled: SEC EDGAR, FRED, Alpha Vantage")
else:
    st.sidebar.warning("⚠️ Using historical/demo data only")

# Main content
tab1, tab2, tab3 = st.tabs(["📈 Market Multiples", "📋 Precedent Comparables", "🎯 Critical Variance"])

with tab1:
    st.subheader("Market Multiples Analysis")
    
    st.markdown("""
    Compare valuation multiples against sector peers and historical averages.
    
    **Data Sources:**
    - SEC EDGAR: Company financials (XBRL)
    - FRED: Treasury yields for credit spreads
    - Alpha Vantage: Real-time stock prices
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Company Metrics**")
        ticker = st.text_input("Ticker Symbol", value="", placeholder="e.g., GME")
        revenue = st.number_input("Revenue ($M)", min_value=0.0, value=0.0, step=10.0)
        ebitda = st.number_input("EBITDA ($M)", min_value=0.0, value=0.0, step=5.0)
        total_debt = st.number_input("Total Debt ($M)", min_value=0.0, value=0.0, step=10.0)
    
    with col2:
        st.markdown("**Comparables**")
        
        # Filter options
        filter_industry = industry if industry != "All" else None
        filter_geo = geography if geography != "All" else None
        
        st.info(f"**Filters:** Industry: {filter_industry or 'All'} | Geography: {filter_geo or 'All'}")
    
    if st.button("🚀 Run Benchmarking", type="primary"):
        with st.spinner("Fetching market data and comparables..."):
            try:
                # Run benchmarker
                benchmark_result = run_benchmarker(
                    industry=filter_industry,
                    geography=filter_geo,
                    model_recoveries=None,
                )
                
                st.session_state["benchmark_result"] = benchmark_result
                st.success("✅ Benchmarking complete!")
            except Exception as e:
                st.error(f"Error running benchmarker: {e}")
    
    # Display results
    if st.session_state.get("benchmark_result"):
        result = st.session_state["benchmark_result"]
        
        st.markdown("---")
        st.markdown("### Benchmark Results")
        
        # Market multiple (singular)
        market_multiple = result.get("market_multiple", {})
        ev_ebitda = market_multiple.get("ev_ebitda_multiple", 0)
        mm_source = market_multiple.get("source", "")
        
        # Precedents data
        precedents_data = result.get("precedents", {})
        exit_multiples = precedents_data.get("exit_multiples", [])
        comparables = precedents_data.get("comparables", [])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if ev_ebitda:
                st.metric("Market EV/EBITDA", f"{ev_ebitda:.1f}x")
            else:
                st.metric("Market EV/EBITDA", "N/A")
        with col2:
            # Calculate median leverage if we have exit multiples
            if exit_multiples:
                st.metric("Exit Multiples", len(exit_multiples))
            else:
                st.metric("Exit Multiples", "0")
        with col3:
            comparables_count = len(comparables) if comparables else 0
            st.metric("Comparables", comparables_count)
        
        # Show source for market multiple
        if mm_source:
            st.info(f"📊 {mm_source}")
        
        # Display exit multiples
        if exit_multiples:
            st.markdown("#### Exit Multiples")
            for mult in exit_multiples[:5]:
                company = mult.get("company", "Unknown")
                ev_ebitda_mult = mult.get("ev_ebitda_multiple", 0)
                outcome = mult.get("outcome", "")
                industry = mult.get("industry", "N/A")
                source = mult.get("source", "")
                note = mult.get("note", "")
                
                st.markdown(f"""
                <div class='benchmark-card'>
                    <strong>{company}</strong> - {industry}<br>
                    EV/EBITDA: {ev_ebitda_mult:.1f}x | Outcome: {outcome}<br>
                    <small style='color: #9ca3af;'>{note if note else source}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Data freshness
        if "data_freshness" in result:
            freshness = result["data_freshness"]
            last_updated = freshness.get("last_updated_iso", "Unknown")
            stale = freshness.get("stale", False)
            for_author = freshness.get("for_author", "")
            
            if stale:
                st.warning(f"⚠️ Data freshness: {last_updated}")
                if for_author:
                    st.info(f"💡 {for_author}")
            else:
                st.info(f"📅 Data last updated: {last_updated}")

with tab2:
    st.subheader("Precedent Restructuring Comparables")
    
    st.markdown("""
    Historical distressed debt restructurings with recovery rates by tranche.
    
    **Database includes:**
    - J.Crew (2020) - Dropdown LME
    - Serta Simmons (2020) - Uptier LME
    - Hertz (2020) - Ch. 11 restructuring
    - Neiman Marcus (2020)
    - And more...
    """)
    
    # Load waterfall for comparison
    st.markdown("**Compare Your Model Against Precedents**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Your Model:**")
        model_senior_recovery = st.slider("Senior Recovery (%)", 0, 100, 80, 5)
        model_mezz_recovery = st.slider("Mezzanine Recovery (%)", 0, 100, 40, 5)
        model_unsecured_recovery = st.slider("Unsecured Recovery (%)", 0, 100, 10, 5)
    
    with col2:
        st.markdown("**Precedent Averages:**")
        st.metric("Senior (Avg)", "85%", delta="+5%")
        st.metric("Mezzanine (Avg)", "35%", delta="-5%")
        st.metric("Unsecured (Avg)", "8%", delta="-2%")
    
    if st.button("📊 Run Precedent Comparison"):
        with st.spinner("Analyzing precedents..."):
            try:
                model_recoveries = [
                    {"name": "Senior", "recovery_pct": model_senior_recovery},
                    {"name": "Mezzanine", "recovery_pct": model_mezz_recovery},
                    {"name": "Unsecured", "recovery_pct": model_unsecured_recovery},
                ]
                
                benchmark_result = run_benchmarker(
                    industry=None,
                    geography=None,
                    model_recoveries=model_recoveries,
                )
                
                st.session_state["precedent_comparison"] = benchmark_result
                st.success("✅ Comparison complete!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display precedent results
    if st.session_state.get("precedent_comparison"):
        result = st.session_state["precedent_comparison"]
        
        st.markdown("---")
        st.markdown("### Precedent Analysis")
        
        # precedents is a dict with comparables, recovery_benchmarks, exit_multiples
        precedents_data = result.get("precedents", {})
        
        # Display recovery benchmarks (most relevant for precedent comparison)
        recovery_benchmarks = precedents_data.get("recovery_benchmarks", [])
        if recovery_benchmarks:
            st.markdown("#### Recovery Benchmarks")
            for p in recovery_benchmarks[:5]:
                tranche_type = p.get("tranche_type", "Unknown")
                recovery_pct = p.get("recovery_pct", 0)
                industry = p.get("industry", "N/A")
                year = p.get("year", "")
                source = p.get("source", "")
                note = p.get("note", "")
                
                recovery_display = f"{recovery_pct}%" if recovery_pct else "N/A"
                
                st.markdown(f"""
                <div class='benchmark-card'>
                    <strong>{tranche_type}</strong> - {industry} ({year})<br>
                    Recovery: {recovery_display}<br>
                    <small style='color: #9ca3af;'>{note if note else source}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recovery benchmarks available. Enable live data sources (NINEFIN_API_KEY or BENCHMARKER_USE_LIVE=1) for actual precedent recovery rates.")
        
        # Display comparables
        comparables = precedents_data.get("comparables", [])
        if comparables:
            st.markdown("#### Recent Comparables")
            for comp in comparables[:5]:
                name = comp.get("name", "Unknown")
                industry = comp.get("industry", "N/A")
                geography = comp.get("geography", "N/A")
                restructuring_date = comp.get("restructuring_date", "")
                source = comp.get("source", "")
                
                st.markdown(f"""
                <div class='benchmark-card'>
                    <strong>{name}</strong><br>
                    {industry} | {geography} | {restructuring_date}<br>
                    <small style='color: #9ca3af;'>{source}</small>
                </div>
                """, unsafe_allow_html=True)

with tab3:
    st.subheader("Critical Variance Analysis")
    
    st.markdown("""
    **Critical Variance:** When your model recovery differs from market precedents by >20%.
    
    This flags potential issues with:
    - Optimistic valuation assumptions
    - Missed collateral leakage
    - Incorrect capital structure
    - Unrealistic recovery expectations
    """)
    
    # Check for critical variance
    # Note: The precedent comparison should be used for variance analysis
    if st.session_state.get("precedent_comparison"):
        result = st.session_state["precedent_comparison"]
        
        # The benchmarker returns recovery_variance (not critical_variances)
        recovery_variance = result.get("recovery_variance", [])
        
        # Filter to only critical variances
        critical_variances = [rv for rv in recovery_variance if rv.get("critical_variance")]
        
        if critical_variances:
            st.warning("⚠️ **Critical Variances Detected**")
            
            for cv in critical_variances:
                tranche_name = cv.get("tranche_name", "Unknown")
                model_rec = cv.get("model_recovery_pct", 0)
                precedent_rec = cv.get("precedent_recovery_pct", 0)
                variance = cv.get("variance_pct", 0)
                for_auditor = cv.get("for_auditor", "")
                data_quality = cv.get("data_quality", "unknown")
                
                st.markdown(f"""
                <div class='variance-critical'>
                    <strong>{tranche_name}</strong><br>
                    Your Model: {model_rec:.1f}% | Precedent: {precedent_rec:.1f}% | 
                    <strong>Variance: {variance:.1f}%</strong><br>
                    <small style='color: #fca5a5;'>Data Quality: {data_quality}</small>
                </div>
                """, unsafe_allow_html=True)
        elif recovery_variance:
            # Have variance data but no critical variances
            st.markdown(f"""
            <div class='variance-ok'>
                ✅ No critical variances detected. Your model is within reasonable bounds.
            </div>
            """, unsafe_allow_html=True)
            
            # Show all variance checks
            st.markdown("#### All Variance Checks")
            for rv in recovery_variance:
                tranche_name = rv.get("tranche_name", "Unknown")
                model_rec = rv.get("model_recovery_pct", 0)
                precedent_rec = rv.get("precedent_recovery_pct")
                variance = rv.get("variance_pct")
                
                if precedent_rec is not None and variance is not None:
                    st.markdown(f"""
                    <div class='benchmark-card'>
                        <strong>{tranche_name}</strong><br>
                        Your Model: {model_rec:.1f}% | Precedent: {precedent_rec:.1f}% | Variance: {variance:.1f}%
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"**{tranche_name}**: {rv.get('for_auditor', 'No precedent data available')}")
        else:
            st.info("No variance checks available. Run precedent comparison with model recoveries to check for critical variances.")
    else:
        st.info("Run precedent comparison (Tab 2) with your model recoveries to check for critical variances.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>
    <p>SIGNAL TRIAGE | BENCHMARKER Workstream</p>
    <p>SEC EDGAR · FRED · Alpha Vantage · Historical Database</p>
</div>
""", unsafe_allow_html=True)

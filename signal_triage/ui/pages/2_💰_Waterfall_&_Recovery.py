"""
Waterfall & Recovery Analysis Workstream — QUANT

Model recovery waterfalls, identify fulcrum securities, and run sensitivity analysis.
Features:
- Interactive EBITDA multiple slider
- APR violation detection
- Monte Carlo simulation (10K+ scenarios)
- Tornado charts for recovery drivers
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from signal_triage.recovery_engine import run_waterfall, ev_sensitivity, tornado_drivers
from signal_triage.monte_carlo import run_monte_carlo
from signal_triage.validation import validate_waterfall

# Page config
st.set_page_config(
    page_title="Waterfall & Recovery | Signal Triage",
    page_icon="💰",
    layout="wide",
)

# Apply dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    .stApp { background-color: #0a0e17; color: #e0e3eb; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e0e3eb; }
    .metric-card {
        background-color: #141822;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 💰 WATERFALL & RECOVERY ANALYSIS")
st.markdown("**Workstream: QUANT** | Model recovery scenarios and identify fulcrum")
st.markdown("---")

# Initialize session state
if "waterfall_result" not in st.session_state:
    st.session_state["waterfall_result"] = None
if "sensitivity_results" not in st.session_state:
    st.session_state["sensitivity_results"] = None
if "monte_carlo_results" not in st.session_state:
    st.session_state["monte_carlo_results"] = None

# Sidebar: Input Mode
st.sidebar.markdown("### INPUT MODE")
input_mode = st.sidebar.radio(
    "Select source",
    ["📊 Manual Entry", "📄 From Analysis", "🎯 Demo"],
    label_visibility="collapsed"
)

if input_mode == "📊 Manual Entry":
    st.subheader("Capital Structure & Enterprise Value")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Tranches** (Name and Claim amount)")
        
        # Number of tranches
        num_tranches = st.number_input("Number of tranches", min_value=1, max_value=10, value=3, step=1)
        
        tranches = []
        for i in range(num_tranches):
            col_name, col_claim = st.columns([2, 1])
            with col_name:
                name = st.text_input(f"Tranche {i+1} Name", value=f"Tranche {i+1}", key=f"tranche_name_{i}")
            with col_claim:
                claim = st.number_input(f"Claim (M)", min_value=0.0, value=100.0, step=10.0, key=f"tranche_claim_{i}")
            tranches.append({"name": name, "claim": claim})
    
    with col2:
        st.markdown("**Enterprise Value**")
        
        # EV input with multiple slider for sensitivity
        base_ev = st.number_input("Base EV ($M)", min_value=0.0, value=250.0, step=10.0)
        
        # Optional: EBITDA-based calculation
        use_ebitda = st.checkbox("Calculate from EBITDA", value=False)
        if use_ebitda:
            ebitda = st.number_input("EBITDA ($M)", min_value=0.0, value=50.0, step=5.0)
            multiple = st.slider("EV/EBITDA Multiple", min_value=1.0, max_value=15.0, value=5.0, step=0.5)
            calculated_ev = ebitda * multiple
            st.info(f"Calculated EV: ${calculated_ev:.1f}M")
            base_ev = calculated_ev
    
    # Run waterfall button
    if st.button("🚀 Run Waterfall Analysis", type="primary"):
        with st.spinner("Running waterfall analysis..."):
            try:
                # Run waterfall
                result = run_waterfall(tranches, base_ev)
                
                # Validate
                validation = validate_waterfall(result)
                
                # Store in session state
                st.session_state["waterfall_result"] = result
                st.session_state["waterfall_validation"] = validation
                
                st.success("✅ Waterfall analysis complete!")
            except Exception as e:
                st.error(f"Error running waterfall: {e}")
    
    # Display results
    if st.session_state.get("waterfall_result"):
        result = st.session_state["waterfall_result"]
        validation = st.session_state.get("waterfall_validation", {})
        
        st.markdown("---")
        st.subheader("Recovery Waterfall Results")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Enterprise Value", f"${base_ev:.1f}M")
        with col2:
            st.metric("EV Used", f"${result['ev_used']:.1f}M")
        with col3:
            st.metric("EV Remaining", f"${result.get('ev_remaining', 0):.1f}M")
        with col4:
            fulcrum = result.get('fulcrum_security') or "N/A"
            st.metric("Fulcrum Security", fulcrum)
        
        # Recovery table
        st.markdown("### Recovery by Tranche")
        
        recoveries = result.get('recoveries', [])
        if recoveries:
            for r in recoveries:
                name = r['name']
                claim = r['claim']
                recovered = r['recovered']
                recovery_pct = r['recovery_pct']
                
                # Color coding
                if recovery_pct >= 100:
                    color = "#10b981"  # Green
                elif recovery_pct >= 50:
                    color = "#f59e0b"  # Orange
                else:
                    color = "#ef4444"  # Red
                
                st.markdown(f"""
                <div class='metric-card'>
                    <strong>{name}</strong><br>
                    Claim: ${claim:.1f}M | Recovered: ${recovered:.1f}M | 
                    <span style='color: {color}; font-weight: 600;'>{recovery_pct:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        # APR violations
        apr_violations = result.get('apr_violations', [])
        if apr_violations:
            st.warning("⚠️ **APR Violations Detected**")
            for v in apr_violations:
                st.markdown(f"- {v['senior_security']} ({v['senior_recovery_pct']:.1f}%) < 100%, but {v['junior_security']} ({v['junior_recovery_pct']:.1f}%) > 0%")
        
        # Validation warnings
        if validation.get('warnings'):
            st.warning("**Validation Warnings:**")
            for w in validation['warnings']:
                st.markdown(f"- {w}")
        
        # Sensitivity analysis
        st.markdown("---")
        st.subheader("Sensitivity Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Run EV Sensitivity"):
                with st.spinner("Running sensitivity analysis..."):
                    try:
                        sensitivity = ev_sensitivity(tranches, base_ev, ev_step=50.0, steps=5)
                        st.session_state["sensitivity_results"] = sensitivity
                        st.success("✅ Sensitivity analysis complete!")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with col2:
            if st.button("📈 Run Monte Carlo (10K scenarios)"):
                with st.spinner("Running Monte Carlo simulation..."):
                    try:
                        mc_results = run_monte_carlo(
                            tranches=tranches,
                            base_ev=base_ev,
                            ev_std_dev=base_ev * 0.3,
                            num_simulations=10000
                        )
                        st.session_state["monte_carlo_results"] = mc_results
                        st.success("✅ Monte Carlo complete!")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Display sensitivity results
        if st.session_state.get("sensitivity_results"):
            st.markdown("### EV Sensitivity Results")
            sens = st.session_state["sensitivity_results"]
            
            for s in sens:
                ev = s['ev']
                fulcrum = s['result'].get('fulcrum_security', 'N/A')
                st.markdown(f"- **EV = ${ev:.1f}M**: Fulcrum = {fulcrum}")
        
        # Display Monte Carlo results
        if st.session_state.get("monte_carlo_results"):
            st.markdown("### Monte Carlo Simulation Results")
            mc = st.session_state["monte_carlo_results"]
            
            st.markdown(f"**Simulations:** {mc.get('num_simulations', 0):,}")
            
            # Display statistics for each tranche
            for tranche_stat in mc.get('recovery_statistics', []):
                name = tranche_stat['name']
                mean = tranche_stat['mean_recovery_pct']
                median = tranche_stat['median_recovery_pct']
                p10 = tranche_stat['p10_recovery_pct']
                p90 = tranche_stat['p90_recovery_pct']
                
                st.markdown(f"""
                <div class='metric-card'>
                    <strong>{name}</strong><br>
                    Mean: {mean:.1f}% | Median: {median:.1f}% | P10: {p10:.1f}% | P90: {p90:.1f}%
                </div>
                """, unsafe_allow_html=True)

elif input_mode == "📄 From Analysis":
    st.info("**Feature:** Load waterfall from a previous document analysis. Coming soon!")
    
    # Placeholder for loading from analysis
    st.markdown("""
    This feature will allow you to:
    1. Select a previously completed analysis
    2. Load extracted capital structure automatically
    3. Run sensitivity and Monte Carlo on historical data
    """)

elif input_mode == "🎯 Demo":
    st.subheader("Demo: J.Crew Recovery Waterfall")
    
    st.markdown("""
    **Scenario:** J.Crew pre-restructuring capital structure
    
    - **First Lien Term Loan:** $1,700M
    - **Second Lien:** $400M  
    - **Unsecured Notes:** $300M
    - **Enterprise Value (Base):** $1,500M
    """)
    
    if st.button("🚀 Run Demo Analysis", type="primary"):
        demo_tranches = [
            {"name": "First Lien Term Loan", "claim": 1700},
            {"name": "Second Lien", "claim": 400},
            {"name": "Unsecured Notes", "claim": 300},
        ]
        demo_ev = 1500
        
        with st.spinner("Running demo waterfall..."):
            try:
                result = run_waterfall(demo_tranches, demo_ev)
                st.session_state["waterfall_result"] = result
                st.success("✅ Demo analysis complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>
    <p>SIGNAL TRIAGE | QUANT Workstream</p>
    <p>Recovery Engine · Monte Carlo · Sensitivity Analysis</p>
</div>
""", unsafe_allow_html=True)

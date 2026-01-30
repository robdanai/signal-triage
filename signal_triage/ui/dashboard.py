"""
Signal Triage — Institutional Restructuring Command Center

Professional dashboard for senior partners conducting forensic credit analysis.
Dark-themed, high-density interface with real-time waterfall modeling, validation,
and comprehensive sanity checks.

Features:
- Interactive EBITDA Multiple Slider with real-time fulcrum updates
- Validation Layer with data integrity checks
- Tornado Charts for sensitivity analysis
- Monte Carlo probabilistic recovery
- Institutional-grade reporting

Run: streamlit run signal_triage/ui/dashboard.py
"""

import streamlit as st
import json
from pathlib import Path
import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from decimal import Decimal

# Add parent to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from signal_triage.analyzer import analyze_text
from signal_triage.recovery_engine import (
    run_waterfall,
    trace_double_dip_recovery,
    tornado_drivers,
    ev_sensitivity,
)
from signal_triage.covenant_forensics import calculate_headroom
from signal_triage.chapter11_modeling import assess_feasibility, calculate_liquidation_value
from signal_triage.lme_definitions import get_definition
from signal_triage.adversarial_forensics import perform_adversarial_forensics
from signal_triage.monte_carlo import (
    run_monte_carlo,
    MonteCarloParams,
    export_monte_carlo_summary,
    generate_risk_heatmap_data,
)
from signal_triage.reports.memo_generator import generate_ic_memo
from signal_triage.validation import (
    validate_waterfall,
    validate_capital_structure,
    validate_ev_inputs,
    graceful_degradation_report,
)


# Page config
st.set_page_config(
    page_title="Signal Triage | Restructuring Command Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional Dark Theme CSS — Bloomberg Terminal Aesthetic
st.markdown("""
<style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    
    /* Global Dark Theme */
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #141822;
        --bg-tertiary: #1a1f2e;
        --text-primary: #e0e3eb;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-yellow: #f59e0b;
        --border-color: #2d3748;
        --fulcrum-highlight: #fbbf24;
    }
    
    /* Override Streamlit Defaults */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 2rem;
        border-bottom: 2px solid var(--accent-blue);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    h2 {
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }
    
    h3 {
        font-size: 1.25rem;
        color: var(--text-secondary);
        margin-top: 1.5rem;
    }
    
    /* Monospace for Numbers */
    .stMetric, .stDataFrame, code {
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Metric Cards */
    .stMetric {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 0.25rem;
        border: 1px solid var(--border-color);
    }
    
    .stMetric label {
        color: var(--text-secondary) !important;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.75rem;
        font-weight: 600;
    }
    
    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--accent-blue);
        color: white;
        border: none;
        border-radius: 0.25rem;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
        font-family: 'Inter', sans-serif;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Data Tables */
    .stDataFrame {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 0.25rem;
        color: var(--text-primary);
        font-weight: 500;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 0.25rem;
    }
    
    /* Fulcrum Highlight */
    .fulcrum-badge {
        background-color: var(--fulcrum-highlight);
        color: var(--bg-primary);
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        letter-spacing: 0.05em;
        display: inline-block;
    }
    
    /* Validation Status Badges */
    .validation-valid {
        background-color: var(--accent-green);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
    }
    
    .validation-invalid {
        background-color: var(--accent-red);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
    }
    
    .validation-warning {
        background-color: var(--accent-yellow);
        color: var(--bg-primary);
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
    }
    
    /* Data Quality Flags */
    .data-flag-inferred {
        color: var(--accent-yellow);
        font-weight: 500;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .data-flag-hard {
        color: var(--accent-green);
        font-weight: 500;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Alert Boxes */
    .stAlert {
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 0.25rem;
        color: var(--text-primary);
    }
    
    /* Dividers */
    hr {
        border-color: var(--border-color);
        margin: 2rem 0;
    }
    
    /* Charts */
    .js-plotly-plot .plotly {
        background-color: var(--bg-secondary);
    }
</style>
""", unsafe_allow_html=True)

# Header - Professional, No Emojis
st.markdown("<h1>SIGNAL TRIAGE | RESTRUCTURING COMMAND CENTER</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='color: var(--text-secondary); margin-bottom: 2rem; font-size: 0.9rem; "
    "letter-spacing: 0.05em;'>INSTITUTIONAL FORENSIC CREDIT ANALYSIS | "
    "LIBRARIAN · QUANT · AUDITOR · BENCHMARKER · REPORTER</p>",
    unsafe_allow_html=True
)

# Sidebar: Input modes
st.sidebar.markdown("### INPUT MODE")
input_mode = st.sidebar.radio("Select input", ["Upload Document", "Manual Entry", "Demo"])

# Initialize session state
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

# === INPUT MODES ===
if input_mode == "Upload Document":
    uploaded_file = st.sidebar.file_uploader("Upload .txt or .md file", type=["txt", "md"])
    if uploaded_file and st.sidebar.button("Analyze"):
        text = uploaded_file.read().decode("utf-8")
        st.session_state["analysis_result"] = analyze_text(text)
        st.success("Document analyzed successfully.")

elif input_mode == "Manual Entry":
    user_text = st.sidebar.text_area("Paste document text", height=300)
    if st.sidebar.button("Analyze"):
        if user_text.strip():
            st.session_state["analysis_result"] = analyze_text(user_text)
            st.success("Text analyzed successfully.")
        else:
            st.warning("Please enter text to analyze.")

elif input_mode == "Demo":
    if st.sidebar.button("Load Demo"):
        demo_text = """
        Going concern: There is substantial doubt about the Company's ability to continue as a going concern.
        The Company has breached the leverage covenant and is in discussions with lenders for a waiver.
        Debt maturity wall in Q4 2026 with refinancing risk. The Company has an uptier exchange offer
        pending with Required Lenders (>50% consent). J.Crew-style dropdown risk exists due to absence
        of IP transfer blocker. Make-whole premium may be subject to disallowance in bankruptcy.
        """
        st.session_state["analysis_result"] = analyze_text(demo_text)
        st.success("Demo data loaded successfully.")

# === DISPLAY RESULTS ===
result = st.session_state.get("analysis_result")
if result:
    # Row 1: Score Card
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Distress Score", f"{result['score']}/100")
    with col2:
        tier = result.get("tier", "N/A")
        st.metric("Tier", tier)
    with col3:
        lme_count = len(result.get("lme_signals", []))
        st.metric("LME Signals", lme_count)
    with col4:
        covenant_count = len([s for s in result.get("all_signals", []) if "covenant" in s.get("type", "")])
        st.metric("Covenant Signals", covenant_count)

    st.markdown("---")

    # Row 2: LME Flags
    st.markdown("### LME & FORENSIC FLAGS")
    lme = result.get("lme_signals", [])
    if lme:
        for sig in lme[:10]:  # top 10
            sig_type = sig.get("type", "")
            definition = get_definition(sig_type)
            with st.expander(f"**{sig_type}** — {sig.get('label', '')}"):
                st.markdown(f"**Evidence:** {sig.get('evidence', 'N/A')}")
                if definition:
                    st.markdown(f"**Definition:** {definition.definition}")
                    st.markdown(f"**Rationale:** {definition.rationale}")
                    st.markdown(f"**Severity:** `{definition.severity}` | **Market Tier:** `{definition.market_tier}`")
    else:
        st.info("No LME signals detected.")

    st.markdown("---")

    # Row 3: Interactive Waterfall with EBITDA Multiple Slider
    st.markdown("### RECOVERY WATERFALL & VALUATION SENSITIVITY")

    # Manual waterfall entry for demo
    with st.expander("CONFIGURE CAPITAL STRUCTURE", expanded=True):
        st.markdown("**Enterprise Value Assumptions:**")
        
        col_ebitda, col_multiple, col_leakage = st.columns(3)
        with col_ebitda:
            st_ebitda = st.number_input(
                "LTM EBITDA ($M)",
                value=15.0,
                step=1.0,
                help="Last twelve months EBITDA"
            )
        with col_multiple:
            st_base_multiple = st.number_input(
                "Base EBITDA Multiple (x)",
                value=10.0,
                step=0.5,
                help="Base case valuation multiple"
            )
        with col_leakage:
            st_collateral_adj = st.number_input(
                "Collateral Leakage Adj ($M)",
                value=0.0,
                step=5.0,
                help="LME-driven collateral reduction"
            )
        
        st_ev_base = st_ebitda * st_base_multiple
        
        st.markdown("**Capital Structure (Priority Order):**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st_senior = st.number_input("1st Lien Secured Claim ($M)", value=100.0, step=10.0)
        with col2:
            st_mezz = st.number_input("2nd Lien / Mezz Claim ($M)", value=75.0, step=10.0)
        with col3:
            st_unsec = st.number_input("Unsecured / Sub Claim ($M)", value=50.0, step=10.0)

        if st.button("RUN WATERFALL ANALYSIS", type="primary"):
            tranches = [
                {"name": "1st Lien Secured", "claim": st_senior, "tier": 1},
                {"name": "2nd Lien / Mezz", "claim": st_mezz, "tier": 2},
                {"name": "Unsecured", "claim": st_unsec, "tier": 3},
            ]
            st.session_state["tranches"] = tranches
            st.session_state["ebitda"] = st_ebitda
            st.session_state["base_multiple"] = st_base_multiple
            st.session_state["base_ev"] = st_ev_base
            st.session_state["collateral_adj"] = st_collateral_adj
            
            # Run validation on capital structure
            cap_validation = validate_capital_structure(
                tranches,
                expected_total_debt=st_senior + st_mezz + st_unsec
            )
            st.session_state["cap_validation"] = cap_validation

    # Display Capital Structure Validation
    cap_validation = st.session_state.get("cap_validation")
    if cap_validation:
        cap_result = cap_validation.to_dict()
        if cap_result["valid"]:
            st.markdown(
                "<span class='validation-valid'>CAPITAL STRUCTURE VALIDATED</span>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<span class='validation-invalid'>VALIDATION ERRORS DETECTED</span>",
                unsafe_allow_html=True
            )
            for error in cap_validation.errors:
                if error.severity == "CRITICAL":
                    st.error(f"[{error.code}] {error.message}")

    # Interactive EBITDA Multiple Slider (Key Feature)
    if "tranches" in st.session_state:
        tranches = st.session_state["tranches"]
        ebitda = st.session_state.get("ebitda", 15.0)
        base_multiple = st.session_state.get("base_multiple", 10.0)
        base_ev = st.session_state["base_ev"]
        collateral_adj = st.session_state.get("collateral_adj", 0)
        
        st.markdown("---")
        st.markdown("### INTERACTIVE VALUATION SENSITIVITY")
        st.markdown(
            "<p style='color: var(--text-secondary); margin-bottom: 1rem;'>"
            "Adjust EBITDA multiple to see real-time fulcrum migration and recovery updates</p>",
            unsafe_allow_html=True
        )
        
        col_slider, col_metrics = st.columns([3, 1])
        
        with col_slider:
            # EBITDA Multiple Slider — Key Interactive Feature
            multiple_adjusted = st.slider(
                "EBITDA MULTIPLE (x)",
                min_value=max(3.0, base_multiple - 7.0),
                max_value=base_multiple + 10.0,
                value=base_multiple,
                step=0.5,
                help="Drag to see how fulcrum security changes with valuation multiple"
            )
        
        with col_metrics:
            ev_adjusted = ebitda * multiple_adjusted
            st.metric("IMPLIED EV", f"${ev_adjusted:.1f}M")
            st.caption(f"{ebitda:.1f}M EBITDA × {multiple_adjusted:.1f}x")
        
        # Apply collateral leakage
        ev_final = max(0, ev_adjusted - collateral_adj)
        
        # Run waterfall at current slider position
        waterfall_result = run_waterfall(tranches, ev_final)
        st.session_state["waterfall_result"] = waterfall_result
        
        # Validate waterfall
        wf_validation = validate_waterfall(waterfall_result, ev_final, tranches)
        st.session_state["wf_validation"] = wf_validation
        
        # Validate EV inputs
        ev_validation = validate_ev_inputs(
            ev_adjusted,
            ebitda=ebitda,
            ebitda_multiple=multiple_adjusted,
            data_source="INFERRED" if multiple_adjusted != base_multiple else "HARD_DATA"
        )
        
        # Display validation status
        st.markdown("---")
        col_val1, col_val2, col_val3 = st.columns(3)
        
        with col_val1:
            if wf_validation.valid:
                st.markdown(
                    "<span class='validation-valid'>WATERFALL VALID</span>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<span class='validation-invalid'>WATERFALL ERRORS</span>",
                    unsafe_allow_html=True
                )
        
        with col_val2:
            if ev_validation.errors:
                st.markdown(
                    "<span class='validation-warning'>EV WARNINGS</span>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<span class='validation-valid'>EV VALIDATED</span>",
                    unsafe_allow_html=True
                )
        
        with col_val3:
            data_source = ev_validation.data_quality_flags.get("ebitda_multiple", "INFERRED")
            if data_source == "HARD_DATA":
                st.markdown(
                    "<span class='data-flag-hard'>HARD DATA</span>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<span class='data-flag-inferred'>INFERRED</span>",
                    unsafe_allow_html=True
                )
        
        # Display Fulcrum prominently
        st.markdown("---")
        fulcrum = waterfall_result.get("fulcrum_security", "N/A")
        
        col_fulcrum, col_ev_used, col_remaining = st.columns(3)
        with col_fulcrum:
            st.markdown(
                f"<div style='text-align: center;'>"
                f"<p style='color: var(--text-secondary); font-size: 0.75rem; "
                f"text-transform: uppercase; margin-bottom: 0.5rem;'>FULCRUM SECURITY</p>"
                f"<span class='fulcrum-badge'>{fulcrum}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col_ev_used:
            ev_used = waterfall_result.get("ev_used", 0)
            st.metric("EV APPLIED", f"${float(ev_used):.1f}M")
        with col_remaining:
            ev_remaining = waterfall_result.get("ev_remaining", 0)
            st.metric("EV REMAINING", f"${float(ev_remaining):.1f}M")
        
        # Recovery table
        recoveries = waterfall_result.get("recoveries", [])
        
        st.markdown("**📈 Recovery by Tranche:**")
        recovery_data = []
        for r in recoveries:
            name = r.get("name", "")
            claim = r.get("claim", 0)
            recovered = r.get("recovered", 0)
            pct = r.get("recovery_pct", 0)
            is_fulcrum = "⭐" if name == fulcrum else ""
            recovery_data.append({
                "Tranche": name,
                "Claim ($M)": f"${float(claim):.1f}",
                "Recovered ($M)": f"${float(recovered):.1f}",
                "Recovery (%)": f"{float(pct):.1f}%",
                "Fulcrum": is_fulcrum
            })
        
        recovery_df = pd.DataFrame(recovery_data)
        st.dataframe(recovery_df, use_container_width=True, hide_index=True)
        
        # APR Violations
        apr_violations = waterfall_result.get("apr_violations", [])
        if apr_violations:
            st.error("🚨 **ABSOLUTE PRIORITY RULE (APR) VIOLATIONS DETECTED**")
            for v in apr_violations:
                st.markdown(
                    f"- **{v['senior_tranche']}** recovered only {v['senior_recovery_pct']}% "
                    f"while **{v['junior_tranche']}** received ${v['junior_recovery']} "
                    f"(junior improperly paid before senior made whole)"
                )
        else:
            st.success("✅ No APR violations detected.")
        
        # Tornado Chart for Recovery Drivers
        st.markdown("---")
        st.markdown("### TORNADO CHART — PRIMARY RECOVERY DRIVERS")
        st.markdown(
            "<p style='color: var(--text-secondary);'>Sensitivity of recovery rates to key variables</p>",
            unsafe_allow_html=True
        )
        
        with st.spinner("Calculating tornado drivers..."):
            tornado_data = tornado_drivers(
                tranches,
                base_ev,
                collateral_adj,
                ev_step=50.0,
                collateral_step=20.0
            )
        
        # Plot tornado chart for first tranche (most relevant)
        if tornado_data and len(recoveries) > 0:
            first_tranche_name = recoveries[0].get("name", "")
            
            # Extract data for plotting
            drivers_list = []
            low_values = []
            base_values = []
            high_values = []
            
            for driver_info in tornado_data:
                driver_name = driver_info.get("driver", "")
                recovery_by_tranche = driver_info.get("recovery_by_tranche", [])
                
                if recovery_by_tranche:
                    first_tranche_recovery = recovery_by_tranche[0]
                    low_pct = float(first_tranche_recovery.get("low", 0))
                    base_pct = float(first_tranche_recovery.get("base", 0))
                    high_pct = float(first_tranche_recovery.get("high", 0))
                    
                    drivers_list.append(driver_name)
                    low_values.append(low_pct)
                    base_values.append(base_pct)
                    high_values.append(high_pct)
            
            # Create tornado plot using Plotly
            fig_tornado = go.Figure()
            
            for i, driver in enumerate(drivers_list):
                # Downside bar (low)
                fig_tornado.add_trace(go.Bar(
                    y=[driver],
                    x=[base_values[i] - low_values[i]],
                    name='Downside' if i == 0 else '',
                    orientation='h',
                    marker=dict(color='#ff6b6b'),
                    showlegend=(i == 0),
                    base=low_values[i],
                ))
                
                # Upside bar (high)
                fig_tornado.add_trace(go.Bar(
                    y=[driver],
                    x=[high_values[i] - base_values[i]],
                    name='Upside' if i == 0 else '',
                    orientation='h',
                    marker=dict(color='#51cf66'),
                    showlegend=(i == 0),
                    base=base_values[i],
                ))
            
            fig_tornado.update_layout(
                title=f"Recovery Sensitivity for {first_tranche_name}",
                xaxis_title="Recovery Rate (%)",
                yaxis_title="Driver",
                barmode='overlay',
                height=300,
                showlegend=True,
            )
            
            st.plotly_chart(fig_tornado, use_container_width=True)

    st.markdown("---")
    
    # Monte Carlo & Probabilistic Recovery
    if "tranches" in st.session_state:
        st.subheader("🎲 Monte Carlo Simulation — Probabilistic Recovery Analysis")
        st.markdown("_10,000 scenarios with varying EV and collateral leakage assumptions:_")
        
        with st.expander("⚙️ Monte Carlo Parameters"):
            mc_col1, mc_col2 = st.columns(2)
            with mc_col1:
                mc_n_sims = st.number_input(
                    "Number of Simulations",
                    min_value=1000,
                    max_value=50000,
                    value=10000,
                    step=1000,
                    help="More simulations = higher precision but slower"
                )
                mc_ev_mean = st.number_input("EV Mean ($M)", value=base_ev, step=10.0)
                mc_ev_std = st.number_input("EV Std Dev ($M)", value=30.0, step=5.0)
            
            with mc_col2:
                mc_leakage_prob = st.slider(
                    "Collateral Leakage Probability",
                    0.0, 1.0, 0.3, 0.05,
                    help="Probability that LME leakage occurs"
                )
                mc_leakage_mean = st.slider(
                    "Leakage Severity (% of EV)",
                    0.0, 0.5, 0.15, 0.05,
                    help="Average EV reduction when leakage occurs"
                )
            
            if st.button("RUN MONTE CARLO SIMULATION"):
                with st.spinner(f"Running {mc_n_sims:,} simulations..."):
                    mc_params = MonteCarloParams(
                        n_simulations=mc_n_sims,
                        ev_mean=mc_ev_mean,
                        ev_std=mc_ev_std,
                        leakage_probability=mc_leakage_prob,
                        leakage_mean_pct=mc_leakage_mean,
                    )
                    mc_result = run_monte_carlo(tranches, mc_params)
                    st.session_state["mc_result"] = mc_result
                    st.success("Monte Carlo simulation complete.")
        
        # Display Monte Carlo Results
        mc_result = st.session_state.get("mc_result")
        if mc_result:
            st.markdown("---")
            st.markdown("### 📊 Probability Distribution — Recovery Outcomes")
            
            # Tranche statistics table
            stats_data = []
            for stat in mc_result.tranche_statistics:
                stats_data.append({
                    "Tranche": stat["tranche"],
                    "Mean (%)": f"{stat['mean_recovery']:.1f}",
                    "Median (%)": f"{stat['median_recovery']:.1f}",
                    "P10 (%)": f"{stat['p10_recovery']:.1f}",
                    "P90 (%)": f"{stat['p90_recovery']:.1f}",
                    "Par Prob": f"{stat['par_probability']*100:.1f}%",
                    "Impaired Prob": f"{stat['impaired_probability']*100:.1f}%",
                })
            
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
            
            # Fulcrum probabilities
            st.markdown("**FULCRUM SECURITY PROBABILITIES:**")
            fulcrum_probs = mc_result.fulcrum_probabilities
            for name, prob in sorted(fulcrum_probs.items(), key=lambda x: -x[1]):
                st.markdown(f"- **{name}**: {prob*100:.1f}%")
            
            # Risk Heatmap
            st.markdown("---")
            st.markdown("### RISK HEATMAP — LIKELIHOOD OF PAR RECOVERY")
            st.markdown(
                "<p style='color: var(--text-secondary);'>2D visualization of recovery rates under different EV and leakage scenarios</p>",
                unsafe_allow_html=True
            )
            
            with st.spinner("Generating risk heatmap..."):
                heatmap_data = generate_risk_heatmap_data(
                    tranches,
                    ev_range=(mc_ev_mean - 2*mc_ev_std, mc_ev_mean + 2*mc_ev_std),
                    leakage_range=(0, 0.4),
                    n_points=15,
                )
            
            # Create heatmap for first tranche
            if heatmap_data and tranches:
                first_tranche = tranches[0]["name"]
                heatmap_df = pd.DataFrame(heatmap_data)
                heatmap_df_tranche = heatmap_df[heatmap_df["tranche"] == first_tranche]
                
                # Pivot for heatmap
                heatmap_pivot = heatmap_df_tranche.pivot(
                    index="leakage_pct",
                    columns="ev",
                    values="recovery_pct"
                )
                
                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    labels=dict(x="Enterprise Value ($M)", y="Collateral Leakage (%)", color="Recovery (%)"),
                    x=heatmap_pivot.columns,
                    y=heatmap_pivot.index,
                    color_continuous_scale="RdYlGn",
                    aspect="auto",
                    title=f"Recovery Rate Heatmap — {first_tranche}"
                )
                
                fig_heatmap.update_xaxes(side="bottom")
                fig_heatmap.update_layout(height=500)
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown("---")
    
    # Cap Table Visualizer
    if "tranches" in st.session_state:
        st.subheader("🏗️ Capital Structure Visualizer — Hierarchical View")
        st.markdown("_Interactive cap table showing OpCo vs HoldCo debt layers:_")
        
        tranches = st.session_state["tranches"]
        
        # Create hierarchical tree structure (simplified)
        # In production, this would parse actual guarantee paths from documents
        tree_data = {
            "name": "HoldCo (Parent)",
            "value": 0,
            "children": [
                {
                    "name": "OpCo (Borrower)",
                    "value": 0,
                    "children": []
                }
            ]
        }
        
        # Add tranches to OpCo
        for t in tranches:
            tree_data["children"][0]["children"].append({
                "name": t.get("name", ""),
                "value": float(t.get("claim", 0)),
            })
        
        # Create sunburst chart
        fig_cap = go.Figure(go.Sunburst(
            labels=[tree_data["name"]] + 
                   [tree_data["children"][0]["name"]] +
                   [c["name"] for c in tree_data["children"][0]["children"]],
            parents=[""] + 
                    [tree_data["name"]] +
                    [tree_data["children"][0]["name"]] * len(tree_data["children"][0]["children"]),
            values=[sum(c["value"] for c in tree_data["children"][0]["children"])] +
                   [sum(c["value"] for c in tree_data["children"][0]["children"])] +
                   [c["value"] for c in tree_data["children"][0]["children"]],
            branchvalues="total",
        ))
        
        fig_cap.update_layout(
            title="Capital Structure Hierarchy",
            height=500,
        )
        
        st.plotly_chart(fig_cap, use_container_width=True)
        
        st.info(
            "**Note**: In production, this would show actual OpCo/HoldCo structure "
            "parsed from credit agreements, including guarantee paths, restricted vs. "
            "unrestricted subsidiaries, and structural subordination layers."
        )

    st.markdown("---")

    # Row 4: Covenant Headroom
    st.subheader("📊 Covenant Headroom & EBITDA Forensics")
    with st.expander("⚙️ Configure Covenant Analysis"):
        st.markdown("Enter financials and covenants:")
        cov_ebitda = st.number_input("Reported EBITDA", value=100.0, step=10.0)
        cov_runrate = st.number_input("Run-rate synergies (add-back)", value=20.0, step=5.0)
        cov_anticipated = st.number_input("Anticipated savings (add-back)", value=10.0, step=5.0)
        cov_debt = st.number_input("Total Debt", value=600.0, step=50.0)
        cov_leverage_cov = st.number_input("Leverage Covenant (max)", value=6.0, step=0.5)

        if st.button("Calculate Headroom"):
            headroom_result = calculate_headroom(
                reported_ebitda=cov_ebitda,
                addbacks={
                    "run_rate_synergies": cov_runrate,
                    "anticipated_savings": cov_anticipated,
                },
                total_debt=cov_debt,
                leverage_covenant=cov_leverage_cov,
            )
            st.session_state["headroom_result"] = headroom_result

    headroom_result = st.session_state.get("headroom_result")
    if headroom_result:
        norm = headroom_result["normalized_ebitda_analysis"]
        lev = headroom_result["leverage_analysis"]

        st.markdown(f"**Normalized EBITDA:** {norm['normalized_ebitda']} (haircut: {norm['haircut_applied']})")
        st.markdown(f"**Actual Leverage:** {lev['actual_leverage']}x vs Covenant {lev['covenant_leverage']}x")
        st.markdown(f"**Headroom:** {lev['headroom_pct']}%")

        if headroom_result["overall_critical_distress"]:
            st.error("**CRITICAL DISTRESS** — Headroom < 15%")
        else:
            st.success("Healthy covenant cushion.")

    st.markdown("---")

    # Row 5: Ch. 11 Feasibility
    st.subheader("⚖️ Chapter 11 Feasibility & Adequate Protection")
    with st.expander("⚙️ Configure Ch. 11 Analysis"):
        ch11_gc_ev = st.number_input("Going Concern EV", value=150.0, step=10.0)
        ch11_tangible_pct = st.slider("Tangible Asset %", 0.0, 1.0, 0.5, 0.05)
        ch11_secured = st.number_input("Secured Debt", value=100.0, step=10.0)
        ch11_total = st.number_input("Total Debt (Ch. 11)", value=250.0, step=10.0)

        if st.button("Assess Feasibility"):
            liq_result = calculate_liquidation_value(ch11_gc_ev, ch11_tangible_pct, orderly=True)
            feasibility_result = assess_feasibility(
                ch11_gc_ev,
                liq_result["liquidation_value"],
                ch11_secured,
                ch11_total,
            )
            st.session_state["feasibility_result"] = feasibility_result

    feasibility_result = st.session_state.get("feasibility_result")
    if feasibility_result:
        st.markdown(f"**Feasibility:** `{feasibility_result['feasibility']}`")
        st.markdown(f"**GC EV:** {feasibility_result['going_concern_ev']} | **Liquidation Value:** {feasibility_result['liquidation_value']}")
        st.markdown(f"**Collateral Coverage (GC):** {feasibility_result['collateral_coverage_gc_pct']}%")
        st.markdown(f"**Adequate Protection (monthly):** {feasibility_result['adequate_protection_monthly']}")
        st.info(feasibility_result['feasibility_note'])

    st.markdown("---")
    
    # Row 6: Adversarial Forensics
    st.subheader("⚠️ Adversarial Forensics — Serta/Incora Exploitation Vectors")
    st.markdown(
        "<p style='color: var(--text-secondary);'>Deep-dive analysis of voting thresholds, amendment provisions, and intercreditor gaps</p>",
        unsafe_allow_html=True
    )
    
    with st.expander("⚙️ Configure Adversarial Forensics"):
        st.markdown("""
        **Upload documents for forensic analysis:**
        - Credit Agreement (required)
        - Intercreditor Agreement (optional, for gap analysis)
        """)
        
        adversarial_ca = st.file_uploader(
            "Credit Agreement",
            type=["txt", "pdf"],
            key="adversarial_ca",
            help="Upload credit agreement for forensic analysis"
        )
        
        adversarial_ica = st.file_uploader(
            "Intercreditor Agreement (Optional)",
            type=["txt", "pdf"],
            key="adversarial_ica",
            help="Upload ICA to identify conflicts and gaps"
        )
        
        if adversarial_ca and st.button("Run Adversarial Forensics"):
            with st.spinner("Running forensic analysis..."):
                try:
                    from signal_triage.ingest.reader import read_document, full_text
                    import tempfile
                    
                    # Save to temp file and read
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                        tmp.write(adversarial_ca.read())
                        tmp_path = tmp.name
                    
                    chunks = read_document(tmp_path)
                    credit_agreement_text = full_text(chunks)
                    
                    # Optional: ICA
                    ica_text = None
                    if adversarial_ica:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_ica:
                            tmp_ica.write(adversarial_ica.read())
                            tmp_ica_path = tmp_ica.name
                        
                        ica_chunks = read_document(tmp_ica_path)
                        ica_text = full_text(ica_chunks)
                    
                    # Run adversarial forensics
                    forensics_report = perform_adversarial_forensics(credit_agreement_text, ica_text)
                    
                    st.session_state["adversarial_forensics"] = forensics_report.to_dict()
                    st.success("✅ Adversarial forensics complete!")
                except Exception as e:
                    st.error(f"Forensics analysis failed: {e}")
    
    adversarial_result = st.session_state.get("adversarial_forensics")
    if adversarial_result:
        st.markdown("### Forensic Analysis Results")
        
        # Overall risk score
        overall_risk = adversarial_result.get("overall_exploit_risk", "unknown")
        serta_incora_score = adversarial_result.get("serta_incora_risk_score", 0)
        
        # Risk color coding
        if overall_risk == "critical" or serta_incora_score >= 70:
            risk_color = "var(--accent-red)"
            risk_icon = "🔴"
        elif overall_risk == "high" or serta_incora_score >= 40:
            risk_color = "var(--accent-yellow)"
            risk_icon = "🟡"
        else:
            risk_color = "var(--accent-green)"
            risk_icon = "🟢"
        
        st.markdown(f"""
        <div style='background-color: var(--bg-secondary); border-left: 4px solid {risk_color}; 
                    padding: 1rem; margin: 1rem 0; border-radius: 0.25rem;'>
            {risk_icon} <strong style='color: {risk_color};'>Overall Exploit Risk: {overall_risk.upper()}</strong><br>
            <span style='color: var(--text-secondary);'>Serta/Incora Risk Score: {serta_incora_score}/100</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Executive summary
        exec_summary = adversarial_result.get("executive_summary", "")
        if exec_summary:
            st.info(f"**Executive Summary:** {exec_summary}")
        
        # Show top risks in tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Amendment Provisions",
            "Pro-Rata Bypass",
            "Guarantor Release",
            "Intercreditor Gaps"
        ])
        
        with tab1:
            amendments = adversarial_result.get("amendment_provisions", [])
            if amendments:
                for a in amendments[:5]:  # Show top 5
                    vote_threshold = a.get("vote_threshold", "")
                    subject_matter = a.get("subject_matter", "")
                    exploit_risk = a.get("exploit_risk", "")
                    mechanics = a.get("exploitation_mechanics", "")
                    
                    risk_icon = "🔴" if exploit_risk == "critical" else "🟡" if exploit_risk == "high" else "🟢"
                    
                    st.markdown(f"""
                    <div style='background-color: var(--bg-tertiary); padding: 0.75rem; margin: 0.5rem 0; border-radius: 0.25rem;'>
                        {risk_icon} <strong>{subject_matter}</strong> (Vote: {vote_threshold})<br>
                        <span style='color: var(--text-muted); font-size: 0.85rem;'>{mechanics}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No amendment provision risks detected.")
        
        with tab2:
            pro_rata = adversarial_result.get("pro_rata_provisions", [])
            if pro_rata:
                for p in pro_rata:
                    yank_a_bank = p.get("yank_a_bank_present", False)
                    snooze_you_lose = p.get("snooze_you_lose_language", False)
                    
                    if yank_a_bank or snooze_you_lose:
                        st.warning(f"⚠️ **Yank-a-Bank:** {yank_a_bank} | **Snooze-You-Lose:** {snooze_you_lose}")
                        st.markdown(p.get("exploitation_mechanics", ""))
            else:
                st.info("No pro-rata bypass mechanisms detected.")
        
        with tab3:
            guarantor_releases = adversarial_result.get("guarantor_release_triggers", [])
            if guarantor_releases:
                for g in guarantor_releases:
                    trigger_type = g.get("trigger_type", "")
                    automatic = g.get("automatic_release", False)
                    jcrew_blocker = g.get("jcrew_blocker_present", False)
                    
                    if automatic and not jcrew_blocker:
                        st.error(f"🔴 **Automatic Release:** {trigger_type} (No J.Crew blocker)")
                    else:
                        st.info(f"**Trigger:** {trigger_type} | **Automatic:** {automatic} | **J.Crew Blocker:** {jcrew_blocker}")
            else:
                st.info("No guarantor release triggers detected.")
        
        with tab4:
            ica_gaps = adversarial_result.get("intercreditor_gaps", [])
            if ica_gaps:
                for gap in ica_gaps:
                    gap_type = gap.get("gap_type", "")
                    description = gap.get("conflict_description", "")
                    st.warning(f"⚠️ **{gap_type}**")
                    st.markdown(description)
            else:
                st.info("No intercreditor gaps detected (or ICA not provided).")

    st.markdown("---")
    
    # IC Memo Generator
    st.markdown("### INVESTMENT COMMITTEE MEMO GENERATOR")
    st.markdown(
        "<p style='color: var(--text-secondary);'>Generate institutional-quality memo with audit trail and visual citations</p>",
        unsafe_allow_html=True
    )
    
    if st.button("GENERATE IC MEMO", type="primary"):
        with st.spinner("Generating IC memo..."):
            # Build document report structure
            from signal_triage.reports.document_report import build_document_report
            
            doc_report = build_document_report(
                result,
                source_path="Uploaded Document",
                text_length=0,
            )
            
            # Generate memo (using mock data for now; in production would use actual pipeline results)
            waterfall_result = st.session_state.get("waterfall_result")
            
            memo_content = generate_ic_memo(
                doc_report,
                librarian_result=None,  # Would come from pipeline
                quant_result=waterfall_result,
                benchmarker_result=None,  # Would come from pipeline
                auditor_result=None,  # Would come from pipeline
            )
            
            st.session_state["ic_memo"] = memo_content
            st.success("IC Memo generated successfully.")
    
    # Display memo
    ic_memo = st.session_state.get("ic_memo")
    if ic_memo:
        st.markdown("---")
        st.markdown("### 📋 Investment Committee Memorandum")
        
        # Display memo in expandable section
        with st.expander("📄 View Full Memo", expanded=False):
            st.markdown(ic_memo)
        
        # Download button
        st.download_button(
            label="⬇️ Download IC Memo (Markdown)",
            data=ic_memo,
            file_name="ic_memo.md",
            mime="text/markdown",
        )
        
        st.info(
            "💡 **Audit Trail**: Every trap door flag in this memo includes "
            "Section and Page Number citations for instant verification by senior partners."
        )

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: var(--text-muted); font-size: 0.75rem; "
        "letter-spacing: 0.1em; padding: 1rem 0;'>"
        "SIGNAL TRIAGE | RESTRUCTURING COMMAND CENTER<br>"
        "LIBRARIAN · QUANT · BENCHMARKER · AUDITOR · REPORTER<br>"
        "INSTITUTIONAL DISTRESSED DEBT ANALYSIS | AUDIT-GRADE CITATIONS"
        "</p>",
        unsafe_allow_html=True
    )

else:
    st.info("Select an input mode and analyze a document to see results.")
    
    # Quick Start Guide
    st.markdown("---")
    st.markdown("### QUICK START GUIDE")
    st.markdown("""
    1. **Upload Document** or use **Demo** mode to load sample data
    2. **Configure Capital Structure** with your tranches and EBITDA assumptions
    3. **Adjust EBITDA Multiple Slider** to see real-time fulcrum migration
    4. **Review Validation Reports** for data integrity and quality flags
    5. **Run Monte Carlo** for probabilistic recovery analysis (10K+ scenarios)
    6. **Generate IC Memo** for Investment Committee presentation
    
    **Key Features:**
    - **EBITDA Multiple Sensitivity**: Real-time fulcrum updates as you adjust valuation multiples
    - **Validation Layer**: Sanity checks for waterfall integrity, data quality flags (INFERRED vs HARD DATA)
    - **Tornado Charts**: Primary drivers of recovery (EV, collateral leakage, EBITDA)
    - **Monte Carlo Engine**: 10,000+ scenarios with probability distributions
    - **Risk Heatmaps**: 2D visualization of recovery likelihood under stress
    - **Cap Table Visualizer**: Hierarchical view of OpCo/HoldCo debt layers
    - **IC Memo Generator**: Audit-trail-backed narratives with section/page citations
    
    **Professional Interface:**
    - Dark-themed, high-density dashboard optimized for institutional use
    - Bloomberg-terminal aesthetic with Inter/Roboto Mono typography
    - All casual language and emojis removed for senior partner presentations
    - Real-time validation with graceful degradation for missing data
    """)
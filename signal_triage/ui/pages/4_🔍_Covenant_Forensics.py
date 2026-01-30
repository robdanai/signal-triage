"""
Covenant Forensics Workstream — FORENSICS

Deep-dive covenant analysis, headroom calculations, and EBITDA add-back validation.
Features:
- Covenant headroom calculator
- EBITDA normalization with haircuts
- Chapter 11 feasibility assessment
- Adequate protection analysis
- Adversarial forensics (Serta/Incora vectors)
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from signal_triage.covenant_forensics import (
    normalize_ebitda,
    calculate_covenant_headroom,
    assess_covenant_status,
)
from signal_triage.chapter11_modeling import (
    assess_ch11_feasibility,
    calculate_liquidation_value,
    calculate_adequate_protection,
)
from signal_triage.adversarial_forensics import perform_adversarial_forensics

# Page config
st.set_page_config(
    page_title="Covenant Forensics | Signal Triage",
    page_icon="🔍",
    layout="wide",
)

# Apply dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    .stApp { background-color: #0a0e17; color: #e0e3eb; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e0e3eb; }
    .forensics-card {
        background-color: #141822;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .risk-critical {
        background-color: #7f1d1d;
        border-left: 4px solid #ef4444;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .risk-high {
        background-color: #92400e;
        border-left: 4px solid #f59e0b;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    .risk-ok {
        background-color: #14532d;
        border-left: 4px solid #10b981;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🔍 COVENANT FORENSICS")
st.markdown("**Workstream: FORENSICS** | Deep-dive covenant analysis and exploitation vectors")
st.markdown("---")

# Initialize session state
if "covenant_result" not in st.session_state:
    st.session_state["covenant_result"] = None
if "ch11_result" not in st.session_state:
    st.session_state["ch11_result"] = None
if "adversarial_result" not in st.session_state:
    st.session_state["adversarial_result"] = None

# Tabs for different forensic analyses
tab1, tab2, tab3 = st.tabs(["📊 Covenant Headroom", "⚖️ Ch. 11 Feasibility", "⚠️ Adversarial Forensics"])

with tab1:
    st.subheader("Covenant Headroom Analysis")
    
    st.markdown("""
    Calculate covenant headroom with EBITDA normalization and credibility haircuts.
    Identifies critical distress when headroom < 15%.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Reported Financials**")
        reported_ebitda = st.number_input("Reported EBITDA ($M)", min_value=0.0, value=100.0, step=5.0)
        total_debt = st.number_input("Total Debt ($M)", min_value=0.0, value=500.0, step=10.0)
        
        st.markdown("**EBITDA Add-backs**")
        run_rate_synergies = st.number_input("Run-Rate Synergies ($M)", min_value=0.0, value=0.0, step=1.0)
        one_time_charges = st.number_input("One-Time Charges ($M)", min_value=0.0, value=0.0, step=1.0)
        anticipated_savings = st.number_input("Anticipated Savings ($M)", min_value=0.0, value=0.0, step=1.0)
        other_addbacks = st.number_input("Other Add-backs ($M)", min_value=0.0, value=0.0, step=1.0)
    
    with col2:
        st.markdown("**Covenant Limits**")
        leverage_covenant = st.number_input("Max Leverage Ratio (x)", min_value=0.0, value=6.0, step=0.5)
        fccr_covenant = st.number_input("Min Fixed Charge Coverage Ratio (x)", min_value=0.0, value=1.0, step=0.1)
        
        st.markdown("**Cash Flow**")
        fixed_charges = st.number_input("Fixed Charges ($M)", min_value=0.0, value=50.0, step=5.0)
    
    if st.button("🔬 Run Covenant Analysis", type="primary"):
        with st.spinner("Analyzing covenant headroom..."):
            try:
                # Build addbacks dict
                addbacks = {
                    "run_rate_synergies": run_rate_synergies,
                    "one_time_charges": one_time_charges,
                    "anticipated_savings": anticipated_savings,
                    "other": other_addbacks,
                }
                
                # Normalize EBITDA
                normalized = normalize_ebitda(reported_ebitda, addbacks)
                
                # Calculate headroom
                headroom = calculate_covenant_headroom(
                    reported_ebitda=reported_ebitda,
                    addbacks=addbacks,
                    total_debt=total_debt,
                    leverage_covenant=leverage_covenant,
                    fixed_charges=fixed_charges if fccr_covenant else None,
                    fccr_covenant=fccr_covenant if fccr_covenant else None,
                )
                
                # Assess status
                status = assess_covenant_status(headroom)
                
                st.session_state["covenant_result"] = {
                    "normalized": normalized,
                    "headroom": headroom,
                    "status": status,
                }
                
                st.success("✅ Covenant analysis complete!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display results
    if st.session_state.get("covenant_result"):
        result = st.session_state["covenant_result"]
        normalized = result["normalized"]
        headroom = result["headroom"]
        status = result["status"]
        
        st.markdown("---")
        st.markdown("### Analysis Results")
        
        # EBITDA normalization
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Reported EBITDA", f"${reported_ebitda:.1f}M")
        with col2:
            adjusted = normalized.get("adjusted_ebitda", reported_ebitda)
            st.metric("Adjusted EBITDA", f"${adjusted:.1f}M")
        with col3:
            haircut_amount = normalized.get("total_haircut_amount", 0)
            st.metric("Total Haircut", f"${haircut_amount:.1f}M", delta=f"-{haircut_amount:.1f}M")
        
        # Leverage headroom
        st.markdown("### Leverage Headroom")
        
        leverage_headroom_pct = headroom.get("leverage_headroom_pct", 0)
        current_leverage = headroom.get("current_leverage", 0)
        
        if leverage_headroom_pct < 15:
            risk_class = "risk-critical"
            status_icon = "🔴"
        elif leverage_headroom_pct < 30:
            risk_class = "risk-high"
            status_icon = "🟡"
        else:
            risk_class = "risk-ok"
            status_icon = "🟢"
        
        st.markdown(f"""
        <div class='{risk_class}'>
            {status_icon} <strong>Leverage Headroom: {leverage_headroom_pct:.1f}%</strong><br>
            Current Leverage: {current_leverage:.2f}x | Max Covenant: {leverage_covenant:.2f}x
        </div>
        """, unsafe_allow_html=True)
        
        # FCCR headroom (if applicable)
        if fccr_covenant:
            st.markdown("### Fixed Charge Coverage Headroom")
            
            fccr_headroom_pct = headroom.get("fccr_headroom_pct", 0)
            current_fccr = headroom.get("current_fccr", 0)
            
            if fccr_headroom_pct < 15:
                risk_class = "risk-critical"
                status_icon = "🔴"
            elif fccr_headroom_pct < 30:
                risk_class = "risk-high"
                status_icon = "🟡"
            else:
                risk_class = "risk-ok"
                status_icon = "🟢"
            
            st.markdown(f"""
            <div class='{risk_class}'>
                {status_icon} <strong>FCCR Headroom: {fccr_headroom_pct:.1f}%</strong><br>
                Current FCCR: {current_fccr:.2f}x | Min Covenant: {fccr_covenant:.2f}x
            </div>
            """, unsafe_allow_html=True)
        
        # Haircut details
        st.markdown("### Add-back Haircuts Applied")
        
        haircuts = normalized.get("haircut_details", [])
        if haircuts:
            for h in haircuts:
                category = h.get("category", "Unknown")
                amount = h.get("amount", 0)
                haircut_pct = h.get("haircut_pct", 0)
                haircut_amount = h.get("haircut_amount", 0)
                rationale = h.get("rationale", "")
                
                st.markdown(f"""
                <div class='forensics-card'>
                    <strong>{category}</strong>: ${amount:.1f}M<br>
                    Haircut: {haircut_pct}% (${haircut_amount:.1f}M)<br>
                    <em>{rationale}</em>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.subheader("Chapter 11 Feasibility Assessment")
    
    st.markdown("""
    Model going concern vs liquidation value and assess reorganization viability.
    Calculates adequate protection requirements and DIP financing capacity.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Enterprise Value**")
        going_concern_ev = st.number_input("Going Concern EV ($M)", min_value=0.0, value=200.0, step=10.0)
        tangible_asset_pct = st.slider("Tangible Asset %", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
        
        st.markdown("**Debt Structure**")
        secured_debt = st.number_input("Secured Debt ($M)", min_value=0.0, value=300.0, step=10.0)
        ch11_total_debt = st.number_input("Total Debt ($M)", min_value=0.0, value=500.0, step=10.0, key="ch11_total_debt")
    
    with col2:
        st.markdown("**Operating Metrics**")
        monthly_cash_burn = st.number_input("Monthly Cash Burn ($M)", min_value=0.0, value=5.0, step=0.5)
        professional_fees = st.number_input("Professional Fees (Total, $M)", min_value=0.0, value=10.0, step=1.0)
    
    if st.button("⚖️ Run Ch. 11 Assessment", type="primary"):
        with st.spinner("Assessing Chapter 11 feasibility..."):
            try:
                # Calculate liquidation value
                liquidation_value = calculate_liquidation_value(going_concern_ev, tangible_asset_pct)
                
                # Calculate adequate protection
                adequate_protection = calculate_adequate_protection(secured_debt, liquidation_value)
                
                # Assess feasibility
                feasibility = assess_ch11_feasibility(
                    going_concern_ev=going_concern_ev,
                    tangible_asset_pct=tangible_asset_pct,
                    secured_debt=secured_debt,
                    total_debt=ch11_total_debt,
                )
                
                st.session_state["ch11_result"] = {
                    "liquidation_value": liquidation_value,
                    "adequate_protection": adequate_protection,
                    "feasibility": feasibility,
                }
                
                st.success("✅ Ch. 11 assessment complete!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display results
    if st.session_state.get("ch11_result"):
        result = st.session_state["ch11_result"]
        liquidation_value = result["liquidation_value"]
        adequate_protection = result["adequate_protection"]
        feasibility = result["feasibility"]
        
        st.markdown("---")
        st.markdown("### Ch. 11 Assessment Results")
        
        # Valuation comparison
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Going Concern EV", f"${going_concern_ev:.1f}M")
        with col2:
            st.metric("Liquidation Value", f"${liquidation_value:.1f}M")
        with col3:
            going_concern_premium = ((going_concern_ev / liquidation_value) - 1) * 100 if liquidation_value > 0 else 0
            st.metric("Going Concern Premium", f"{going_concern_premium:.1f}%")
        
        # Adequate protection
        st.markdown("### Adequate Protection")
        
        cushion = adequate_protection.get("cushion", 0)
        cushion_pct = adequate_protection.get("cushion_pct", 0)
        
        if cushion < 0:
            risk_class = "risk-critical"
            status_icon = "🔴"
            status_text = "INADEQUATE"
        elif cushion_pct < 20:
            risk_class = "risk-high"
            status_icon = "🟡"
            status_text = "MARGINAL"
        else:
            risk_class = "risk-ok"
            status_icon = "🟢"
            status_text = "ADEQUATE"
        
        st.markdown(f"""
        <div class='{risk_class}'>
            {status_icon} <strong>Adequate Protection: {status_text}</strong><br>
            Liquidation Value: ${liquidation_value:.1f}M | Secured Debt: ${secured_debt:.1f}M<br>
            Cushion: ${cushion:.1f}M ({cushion_pct:.1f}%)
        </div>
        """, unsafe_allow_html=True)
        
        # Reorganization feasibility
        st.markdown("### Reorganization Feasibility")
        
        is_feasible = feasibility.get("reorganization_feasible", False)
        feasibility_score = feasibility.get("feasibility_score", 0)
        
        if is_feasible:
            st.markdown(f"""
            <div class='risk-ok'>
                ✅ <strong>Reorganization FEASIBLE</strong><br>
                Feasibility Score: {feasibility_score}/100
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='risk-critical'>
                ❌ <strong>Reorganization NOT FEASIBLE</strong><br>
                Feasibility Score: {feasibility_score}/100<br>
                Liquidation may be more appropriate.
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.subheader("Adversarial Forensics")
    
    st.markdown("""
    **Deep-Needle Analysis:** Identify Serta/Incora/J.Crew exploitation vectors.
    
    Analyzes:
    - Amendment provisions and voting thresholds
    - Pro-rata sharing bypass mechanics (Yank-a-Bank)
    - Guarantor release triggers
    - Intercreditor agreement gaps
    """)
    
    st.markdown("**Document Upload**")
    
    credit_agreement_file = st.file_uploader(
        "Credit Agreement",
        type=["txt", "pdf"],
        help="Upload the credit agreement for forensic analysis"
    )
    
    ica_file = st.file_uploader(
        "Intercreditor Agreement (Optional)",
        type=["txt", "pdf"],
        help="Upload ICA to identify conflicts and gaps"
    )
    
    if credit_agreement_file and st.button("🔬 Run Adversarial Forensics", type="primary"):
        with st.spinner("Running forensic analysis..."):
            try:
                # Extract text from uploaded files
                from signal_triage.ingest.reader import read_document, full_text
                import tempfile
                
                # Save to temp file and read
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    tmp.write(credit_agreement_file.read())
                    tmp_path = tmp.name
                
                chunks = read_document(tmp_path)
                credit_agreement_text = full_text(chunks)
                
                # Optional: ICA
                ica_text = None
                if ica_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_ica:
                        tmp_ica.write(ica_file.read())
                        tmp_ica_path = tmp_ica.name
                    
                    ica_chunks = read_document(tmp_ica_path)
                    ica_text = full_text(ica_chunks)
                
                # Run adversarial forensics
                forensics_report = perform_adversarial_forensics(credit_agreement_text, ica_text)
                
                st.session_state["adversarial_result"] = forensics_report.to_dict()
                st.success("✅ Forensic analysis complete!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display results
    if st.session_state.get("adversarial_result"):
        result = st.session_state["adversarial_result"]
        
        st.markdown("---")
        st.markdown("### Adversarial Forensics Results")
        
        # Overall risk
        overall_risk = result.get("overall_exploit_risk", "unknown")
        serta_incora_score = result.get("serta_incora_risk_score", 0)
        
        if overall_risk == "critical" or serta_incora_score >= 70:
            risk_class = "risk-critical"
            status_icon = "🔴"
        elif overall_risk == "high" or serta_incora_score >= 40:
            risk_class = "risk-high"
            status_icon = "🟡"
        else:
            risk_class = "risk-ok"
            status_icon = "🟢"
        
        st.markdown(f"""
        <div class='{risk_class}'>
            {status_icon} <strong>Overall Exploit Risk: {overall_risk.upper()}</strong><br>
            Serta/Incora Risk Score: {serta_incora_score}/100
        </div>
        """, unsafe_allow_html=True)
        
        # Executive summary
        exec_summary = result.get("executive_summary", "")
        if exec_summary:
            st.markdown("### Executive Summary")
            st.info(exec_summary)
        
        # Amendment provisions
        amendments = result.get("amendment_provisions", [])
        if amendments:
            st.markdown("### Amendment Provisions")
            for a in amendments:
                vote_threshold = a.get("vote_threshold", "")
                subject_matter = a.get("subject_matter", "")
                exploit_risk = a.get("exploit_risk", "")
                mechanics = a.get("exploitation_mechanics", "")
                
                if exploit_risk == "critical":
                    icon = "🔴"
                elif exploit_risk == "high":
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                st.markdown(f"""
                <div class='forensics-card'>
                    {icon} <strong>{subject_matter}</strong> (Vote: {vote_threshold})<br>
                    Risk: {exploit_risk.upper()}<br>
                    {mechanics}
                </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>
    <p>SIGNAL TRIAGE | FORENSICS Workstream</p>
    <p>Covenant Headroom · Ch. 11 Feasibility · Adversarial Analysis</p>
</div>
""", unsafe_allow_html=True)

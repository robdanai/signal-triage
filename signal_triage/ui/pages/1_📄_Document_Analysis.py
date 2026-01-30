"""
Document Analysis Workstream — LIBRARIAN

Upload and parse credit agreements, 10-Ks, and restructuring documents.
Extract covenants, capital structure, and detect LME signals.

Supported formats: PDF, DOCX, TXT, MD, RTF
"""

import streamlit as st
import sys
from pathlib import Path
import io

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from signal_triage.analyzer import analyze_text
from signal_triage.lme_definitions import get_definition

# Page config
st.set_page_config(
    page_title="Document Analysis | Signal Triage",
    page_icon="📄",
    layout="wide",
)

# Apply dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');
    .stApp { background-color: #0a0e17; color: #e0e3eb; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e0e3eb; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📄 DOCUMENT ANALYSIS")
st.markdown("**Workstream: LIBRARIAN** | Parse documents and extract distress signals")
st.markdown("---")

# Initialize session state
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
if "uploaded_filename" not in st.session_state:
    st.session_state["uploaded_filename"] = None

# Sidebar: Input Mode
st.sidebar.markdown("### INPUT MODE")
input_mode = st.sidebar.radio(
    "Select source",
    ["📤 Upload Document", "✍️ Manual Entry", "🎯 Demo"],
    label_visibility="collapsed"
)

# File Type Support
def extract_text_from_file(uploaded_file):
    """
    Extract text from various file formats.
    
    Supported: PDF, DOCX, DOC, TXT, MD, RTF
    """
    file_extension = Path(uploaded_file.name).suffix.lower()
    
    try:
        if file_extension == ".txt" or file_extension == ".md":
            # Plain text
            return uploaded_file.read().decode("utf-8")
        
        elif file_extension == ".pdf":
            # PDF extraction
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            except ImportError:
                st.error("PDF support requires 'pdfplumber'. Install with: pip install pdfplumber")
                return None
        
        elif file_extension in [".docx", ".doc"]:
            # Word document extraction
            try:
                import docx
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                return text
            except ImportError:
                st.error("DOCX support requires 'python-docx'. Install with: pip install python-docx")
                return None
        
        elif file_extension == ".rtf":
            # RTF extraction (basic)
            try:
                from striprtf.striprtf import rtf_to_text
                content = uploaded_file.read().decode("utf-8", errors="ignore")
                return rtf_to_text(content)
            except ImportError:
                st.error("RTF support requires 'striprtf'. Install with: pip install striprtf")
                return None
        
        else:
            st.error(f"Unsupported file type: {file_extension}")
            return None
    
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return None


# === INPUT MODES ===

if input_mode == "📤 Upload Document":
    st.sidebar.markdown("### UPLOAD SETTINGS")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload document",
        type=["pdf", "docx", "doc", "txt", "md", "rtf"],
        help="Supported: PDF, DOCX, DOC, TXT, MD, RTF"
    )
    
    if uploaded_file:
        st.sidebar.markdown(f"**File:** {uploaded_file.name}")
        st.sidebar.markdown(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        st.sidebar.markdown(f"**Type:** {Path(uploaded_file.name).suffix.upper()}")
    
    if st.sidebar.button("🔍 ANALYZE DOCUMENT", type="primary", use_container_width=True):
        if uploaded_file:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                text = extract_text_from_file(uploaded_file)
                
                if text:
                    st.session_state["uploaded_filename"] = uploaded_file.name
                    st.session_state["analysis_result"] = analyze_text(text)
                    st.success(f"✅ Analysis complete: {uploaded_file.name}")
        else:
            st.sidebar.warning("Please upload a file first")

elif input_mode == "✍️ Manual Entry":
    st.sidebar.markdown("### TEXT INPUT")
    
    user_text = st.sidebar.text_area(
        "Paste document text",
        height=300,
        placeholder="Paste credit agreement, 10-K excerpt, or restructuring document..."
    )
    
    char_count = len(user_text)
    st.sidebar.caption(f"{char_count:,} characters")
    
    if st.sidebar.button("🔍 ANALYZE TEXT", type="primary", use_container_width=True):
        if user_text.strip():
            with st.spinner("Analyzing text..."):
                st.session_state["uploaded_filename"] = "Manual Entry"
                st.session_state["analysis_result"] = analyze_text(user_text)
                st.success("✅ Analysis complete")
        else:
            st.sidebar.warning("Please enter text to analyze")

elif input_mode == "🎯 Demo":
    st.sidebar.markdown("### DEMO MODE")
    st.sidebar.markdown("""
    Load pre-configured demo data showing:
    - Going concern doubt
    - Leverage covenant breach
    - Uptier exchange risk
    - Make-whole disallowance
    """)
    
    if st.sidebar.button("🚀 LOAD DEMO", type="primary", use_container_width=True):
        demo_text = """
        Going concern: There is substantial doubt about the Company's ability to continue as a going concern.
        The Company has breached the leverage covenant and is in discussions with lenders for a waiver.
        Debt maturity wall in Q4 2026 with refinancing risk. The Company has an uptier exchange offer
        pending with Required Lenders (>50% consent). J.Crew-style dropdown risk exists due to absence
        of IP transfer blocker. Make-whole premium may be subject to disallowance in bankruptcy.
        Priming liens may be granted to new money lenders. The Company's EBITDA includes $30M in
        run-rate synergies and $15M in anticipated cost savings, which may be subject to haircut.
        First Lien / Last Out structure creates structural subordination risk. Non-pro rata distributions
        to certain lenders detected in amendment. Restricted Payments basket expanded to $50M.
        Debt incurrence test uses pro forma EBITDA with aggressive add-backs.
        """
        
        st.session_state["uploaded_filename"] = "Demo Document"
        st.session_state["analysis_result"] = analyze_text(demo_text)
        st.success("✅ Demo data loaded")

# === DISPLAY RESULTS ===

result = st.session_state.get("analysis_result")
filename = st.session_state.get("uploaded_filename")

if result:
    # Document Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Document: `{filename}`")
    with col2:
        if st.button("🔄 Clear & Start Over", use_container_width=True):
            st.session_state["analysis_result"] = None
            st.session_state["uploaded_filename"] = None
            st.rerun()
    
    st.markdown("---")
    
    # Score Card
    st.subheader("DISTRESS ASSESSMENT")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        score = result.get("score", 0)
        st.metric("Distress Score", f"{score}/100", delta="High" if score > 60 else "Moderate")
    with col2:
        tier = result.get("tier", "N/A")
        st.metric("Credit Tier", tier)
    with col3:
        lme_count = len(result.get("lme_signals", []))
        st.metric("LME Signals", lme_count)
    with col4:
        covenant_count = len([s for s in result.get("all_signals", []) if "covenant" in s.get("type", "").lower()])
        st.metric("Covenant Flags", covenant_count)
    
    st.markdown("---")
    
    # LME Signals
    st.subheader("LME & TRAP DOOR FLAGS")
    
    lme_signals = result.get("lme_signals", [])
    
    if lme_signals:
        # Filter and sort options
        col1, col2 = st.columns([2, 1])
        with col1:
            severity_filter = st.multiselect(
                "Filter by severity",
                ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                default=["CRITICAL", "HIGH"]
            )
        with col2:
            sort_by = st.selectbox("Sort by", ["Severity", "Type", "None"])
        
        # Filter signals
        filtered_signals = lme_signals
        if severity_filter:
            filtered_signals = [s for s in lme_signals if get_definition(s.get("type", "")).severity.upper() in severity_filter]
        
        # Display signals
        st.markdown(f"**Showing {len(filtered_signals)} of {len(lme_signals)} signals**")
        
        for sig in filtered_signals[:20]:  # Limit to 20 for performance
            sig_type = sig.get("type", "")
            definition = get_definition(sig_type)
            
            # Color code by severity
            severity = definition.severity if definition else "UNKNOWN"
            severity_colors = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }
            severity_icon = severity_colors.get(severity.upper(), "⚪")
            
            with st.expander(f"{severity_icon} **{sig_type}** — {sig.get('label', '')}"):
                st.markdown(f"**Evidence:** {sig.get('evidence', 'N/A')}")
                
                if definition:
                    st.markdown(f"**Definition:** {definition.definition}")
                    st.markdown(f"**Rationale:** {definition.rationale}")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.caption(f"**Severity:** `{definition.severity}`")
                    with col_b:
                        st.caption(f"**Market Tier:** `{definition.market_tier}`")
                    with col_c:
                        st.caption(f"**Recovery Impact:** {definition.recovery_impact}")
    else:
        st.info("✅ No LME signals detected. Document appears clean.")
    
    st.markdown("---")
    
    # All Signals Summary
    st.subheader("ALL SIGNALS SUMMARY")
    
    all_signals = result.get("all_signals", [])
    
    if all_signals:
        # Group by category
        categories = {}
        for sig in all_signals:
            category = sig.get("type", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(sig)
        
        # Display by category
        for category, sigs in sorted(categories.items()):
            with st.expander(f"**{category}** ({len(sigs)} signals)"):
                for sig in sigs[:10]:  # Limit per category
                    st.markdown(f"- {sig.get('label', 'N/A')}")
                    if sig.get('evidence'):
                        st.caption(f"  Evidence: {sig['evidence'][:100]}...")
    
    st.markdown("---")
    
    # Next Steps
    st.subheader("NEXT STEPS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💰 Run Waterfall Analysis", use_container_width=True):
            st.switch_page("pages/2_💰_Waterfall_&_Recovery.py")
    
    with col2:
        if st.button("🔍 Covenant Forensics", use_container_width=True):
            st.switch_page("pages/4_🔍_Covenant_Forensics.py")
    
    with col3:
        if st.button("📋 Generate IC Memo", use_container_width=True):
            st.switch_page("pages/5_📋_Reports_&_Memos.py")

else:
    # Welcome message
    st.info("👈 Select an input mode from the sidebar to begin analysis")
    
    st.markdown("### Supported File Types")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Document Formats:**
        - 📄 PDF (`.pdf`)
        - 📝 Word (`.docx`, `.doc`)
        - 📋 Text (`.txt`)
        - 📑 Markdown (`.md`)
        - 📃 Rich Text (`.rtf`)
        """)
    
    with col2:
        st.markdown("""
        **Best Practices:**
        - Use high-quality scans for PDFs
        - Ensure text is selectable (not image-only)
        - Credit agreements work best
        - 10-K filings supported
        - SEC EDGAR documents compatible
        """)
    
    st.markdown("---")
    
    st.markdown("### Quick Start")
    st.markdown("""
    1. **Upload**: Click "📤 Upload Document" in sidebar
    2. **Select**: Choose your credit agreement, 10-K, or restructuring doc
    3. **Analyze**: Click "🔍 ANALYZE DOCUMENT"
    4. **Review**: See distress score, LME signals, and covenant flags
    5. **Export**: Generate reports or run deeper analysis
    """)

# Footer
st.markdown("---")
st.caption("Signal Triage | Document Analysis Workstream | LIBRARIAN Agent")

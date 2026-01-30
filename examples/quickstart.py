"""
Signal Triage Quickstart Example

Get from zero to first analysis in < 5 minutes.

This script demonstrates:
1. Basic document analysis
2. Recovery waterfall modeling
3. Covenant forensics
4. Live market data integration (if enabled)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import signal_triage
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Run quickstart examples."""
    print("=" * 70)
    print("Signal Triage Quickstart")
    print("Forensic Decision Engine for Distressed Investing")
    print("=" * 70)
    print()
    
    # Check if live data is enabled
    live_data_enabled = os.environ.get("BENCHMARKER_USE_LIVE", "").lower() in ("1", "true", "yes")
    fred_key = os.environ.get("FRED_API_KEY", "").strip()
    
    print("📊 Configuration:")
    print(f"  Live Market Data: {'✅ Enabled' if live_data_enabled else '⚠️  Disabled (set BENCHMARKER_USE_LIVE=1)'}")
    print(f"  FRED API Key: {'✅ Set' if fred_key else '⚠️  Not set (register at fred.stlouisfed.org)'}")
    print()
    
    # Example 1: Analyze a sample document
    print("=" * 70)
    print("Example 1: Document Analysis")
    print("=" * 70)
    print()
    
    sample_text = """
CREDIT AGREEMENT

SENIOR SECURED CREDIT FACILITY

Total Facility: $500 million
Interest Rate: SOFR + 450 bps

NEGATIVE COVENANTS:

Section 7.01: Leverage Covenant
- Maximum Total Leverage Ratio: 6.0x
- Tested quarterly
- Springing covenant (85% capacity)

Section 7.02: Restricted Payments
- Asset Sale basket: $50 million annually
- Investment basket: $25 million
- Restricted payment basket: $10 million

Section 7.03: Debt Incurrence
- Additional debt permitted up to $100 million
- Requires 2.0x FCCR for incremental facilities

DROPDOWN LANGUAGE:
- Unrestricted subsidiaries permitted
- No J.Crew blocker provision
- IP transfers to unrestricted subs allowed

FINANCIAL DATA:
- EBITDA: $100 million
- Add-backs: $20 million run-rate synergies, $15 million anticipated cost savings
- Total Debt: $550 million
"""
    
    # Save sample to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        sample_file = f.name
    
    try:
        from signal_triage.pipeline import run_pipeline
        
        print("Running full pipeline analysis...")
        print()
        
        result = run_pipeline(
            file_path=sample_file,
            require_audit_gate=False,
            include_tornado=True,
            industry="Technology",
        )
        
        # Display results
        doc = result.get("document", {})
        print(f"📈 DISTRESS SCORE: {doc.get('score', 'N/A')}/100 ({doc.get('tier_label', 'N/A')})")
        print()
        
        # LME flags
        librarian = result.get("librarian_summary", {})
        signals = librarian.get("signals", [])
        lme_signals = [s for s in signals if s.get("signal_level") in ("high", "medium")]
        
        if lme_signals:
            print(f"🚨 LME FLAGS DETECTED: {len(lme_signals)}")
            for sig in lme_signals[:3]:  # Show top 3
                print(f"  - {sig.get('signal_type', 'Unknown')}: {sig.get('signal_level', 'unknown').upper()}")
            print()
        
        # Quant analysis
        quant = result.get("quant_summary")
        if quant:
            recoveries = quant.get("waterfall", {}).get("recoveries", [])
            if recoveries:
                print("💰 RECOVERY WATERFALL:")
                for rec in recoveries:
                    name = rec.get("name", "Unknown")
                    recovery_pct = rec.get("recovery_pct", 0)
                    print(f"  {name}: {recovery_pct}%")
                print()
        
        # Benchmarker
        benchmarker = result.get("benchmarker_summary")
        if benchmarker:
            market_mult = benchmarker.get("market_multiple", {})
            if market_mult:
                mult = market_mult.get("ev_ebitda_multiple")
                source = market_mult.get("source", "")
                if mult:
                    print(f"📊 MARKET MULTIPLE: {mult}x EV/EBITDA")
                    if "live" in source.lower() or "edgar" in source.lower():
                        print(f"   Source: {source}")
                    else:
                        print(f"   ⚠️  Using historical average (enable live data for real-time)")
                    print()
        
        # Auditor
        auditor = result.get("auditor_summary")
        if auditor:
            audit_result = auditor.get("audit_result", "")
            if "pass" in audit_result.lower():
                print("✅ AUDITOR: PASSED")
            else:
                print("⚠️  AUDITOR: Has warnings")
            print()
        
        print("=" * 70)
        print("Example 2: Covenant Forensics")
        print("=" * 70)
        print()
        
        # Demonstrate covenant headroom calculation
        from signal_triage.covenant_forensics import calculate_headroom
        
        headroom_result = calculate_headroom(
            reported_ebitda=100,
            addbacks={
                "run_rate_synergies": 20,      # 30% credible → 70% haircut
                "anticipated_savings": 15,     # 20% credible → 80% haircut
            },
            total_debt=550,
            leverage_covenant=6.0,
        )
        
        normalized_ebitda = headroom_result["normalized_ebitda_analysis"]["normalized_ebitda"]
        actual_leverage = headroom_result["leverage_analysis"]["actual_leverage"]
        headroom_pct = headroom_result["leverage_analysis"]["headroom_pct"]
        critical_distress = headroom_result["overall_critical_distress"]
        
        print(f"Reported EBITDA: $100M")
        print(f"Add-backs: $35M (run-rate synergies + anticipated savings)")
        print(f"→ Normalized EBITDA: ${normalized_ebitda}M (after credibility haircuts)")
        print()
        print(f"Total Debt: $550M")
        print(f"Leverage Covenant: 6.0x")
        print(f"Actual Leverage: {actual_leverage:.2f}x")
        print(f"Headroom: {headroom_pct:.1f}%")
        print()
        if critical_distress:
            print("🚨 CRITICAL DISTRESS: Headroom < 15% (covenant breach risk)")
        else:
            print("✅ Adequate headroom")
        print()
        
        print("=" * 70)
        print("Example 3: Chapter 11 Feasibility")
        print("=" * 70)
        print()
        
        from signal_triage.chapter11_modeling import assess_feasibility, calculate_liquidation_value
        
        # Calculate liquidation value
        going_concern_ev = 150  # million
        liq = calculate_liquidation_value(
            going_concern_ev=going_concern_ev,
            tangible_asset_pct=0.5,  # 50% tangible
            orderly=True
        )
        
        # Assess feasibility
        feas = assess_feasibility(
            going_concern_ev=going_concern_ev,
            liquidation_value=liq["liquidation_value"],
            secured_debt=100,
            total_debt=250,
        )
        
        print(f"Going Concern EV: ${going_concern_ev}M")
        print(f"Liquidation Value: ${liq['liquidation_value']:.1f}M")
        print(f"  - Tangible: ${liq['tangible_value']:.1f}M (recovery: {liq['tangible_recovery_pct']}%)")
        print(f"  - Intangible: ${liq['intangible_value']:.1f}M (recovery: {liq['intangible_recovery_pct']}%)")
        print()
        print(f"Secured Debt: $100M")
        print(f"Collateral Coverage (GC): {feas['collateral_coverage_gc']}%")
        print(f"Collateral Coverage (Liq): {feas['collateral_coverage_liq']}%")
        print()
        print(f"💡 FEASIBILITY: {feas['feasibility'].upper().replace('_', ' ')}")
        print(f"   {feas['feasibility_note']}")
        print()
        
        print("=" * 70)
        print("✅ Quickstart Complete!")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("1. Enable live data: BENCHMARKER_USE_LIVE=1 BENCHMARKER_DATA_SOURCE=edgar")
        print("2. Get FRED API key (free): https://fred.stlouisfed.org/docs/api/api_key.html")
        print("3. Run pipeline on real credit agreements: signal-triage --pipeline your_doc.pdf")
        print("4. Check out examples/case_studies/ for J.Crew, Serta, Hertz analyses")
        print("5. Try the Streamlit dashboard: streamlit run signal_triage/ui/dashboard.py")
        print()
        
        return True
        
    finally:
        # Clean up temp file
        try:
            Path(sample_file).unlink()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

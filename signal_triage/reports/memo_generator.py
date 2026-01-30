"""
Investment Committee (IC) Memo Generator — Institutional One-Pager

Synthesizes forensic signals from Librarian, waterfall math from Quant, and market context
from Benchmarker into a professional, audit-trail-backed narrative suitable for senior
partners and investment committees.

Every "trap door" flag includes Section and Page Number for instant verification.
"""

from decimal import Decimal
from typing import Any
from pathlib import Path


def generate_ic_memo(
    document_report: dict[str, Any],
    *,
    librarian_result: dict[str, Any] | None = None,
    quant_result: dict[str, Any] | None = None,
    benchmarker_result: dict[str, Any] | None = None,
    auditor_result: dict[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> str:
    """
    Generate an Investment Committee (IC) memo in Markdown format.

    Args:
        document_report: From build_document_report (score, tier, signals, provenance).
        librarian_result: ExtractionResult with baskets, collateral_leakage_flags, citations.
        quant_result: Waterfall output with recoveries, fulcrum, situational_summary.
        benchmarker_result: Market multiples, precedent recoveries, variance flags.
        auditor_result: Stress-test results, APR validation, audit trail.
        output_path: Optional path to write the memo. If None, returns string only.

    Returns:
        Markdown string of the IC memo.
    """
    memo_lines = []
    
    # Header
    memo_lines.append("# INVESTMENT COMMITTEE MEMORANDUM")
    memo_lines.append("")
    memo_lines.append("---")
    memo_lines.append("")
    
    # Document info
    provenance = document_report.get("provenance", {})
    source = provenance.get("source_path", "N/A")
    memo_lines.append(f"**Document:** `{source}`")
    memo_lines.append(f"**Analysis Date:** {_current_date()}")
    memo_lines.append("")
    memo_lines.append("---")
    memo_lines.append("")
    
    # === 1. EXECUTIVE SUMMARY ===
    memo_lines.append("## 1. EXECUTIVE SUMMARY")
    memo_lines.append("")
    
    score = document_report.get("score", 0)
    tier = document_report.get("tier", "N/A")
    tier_label = document_report.get("tier_label", "")
    
    memo_lines.append(f"**Distress Score:** {score}/100 | **Tier:** {tier} — _{tier_label}_")
    memo_lines.append("")
    
    # Investment thesis
    thesis = _build_investment_thesis(document_report, quant_result, benchmarker_result)
    memo_lines.append("**Investment Thesis:**")
    memo_lines.append("")
    memo_lines.append(thesis)
    memo_lines.append("")
    
    # Key risks
    memo_lines.append("**Key Structural Risks:**")
    memo_lines.append("")
    top_signals = document_report.get("top_signals", [])
    for i, sig in enumerate(top_signals[:5], 1):
        sig_type = sig.get("type", "")
        evidence = sig.get("evidence", "")[:150]
        memo_lines.append(f"{i}. **{sig_type}**: _{evidence}..._")
    memo_lines.append("")
    memo_lines.append("---")
    memo_lines.append("")
    
    # === 2. CAPITAL STRUCTURE OVERVIEW ===
    memo_lines.append("## 2. CAPITAL STRUCTURE OVERVIEW")
    memo_lines.append("")
    
    if quant_result:
        recoveries = quant_result.get("recoveries", [])
        fulcrum = quant_result.get("fulcrum_security", "N/A")
        ev_used = quant_result.get("ev_used", 0)
        
        memo_lines.append(f"**Enterprise Value (Applied):** ${_format_decimal(ev_used)}M")
        memo_lines.append(f"**Fulcrum Security:** {fulcrum}")
        memo_lines.append("")
        
        memo_lines.append("| Tranche | Claim ($M) | Recovered ($M) | Recovery (%) | Fulcrum |")
        memo_lines.append("|---------|------------|----------------|--------------|---------|")
        
        for rec in recoveries:
            name = rec.get("name", "")
            claim = _format_decimal(rec.get("claim", 0))
            recovered = _format_decimal(rec.get("recovered", 0))
            pct = _format_decimal(rec.get("recovery_pct", 0))
            is_fulcrum = "**✓**" if name == fulcrum else ""
            memo_lines.append(f"| {name} | {claim} | {recovered} | {pct}% | {is_fulcrum} |")
        
        memo_lines.append("")
        
        # APR Violations
        apr_violations = quant_result.get("apr_violations", [])
        if apr_violations:
            memo_lines.append("**⚠️ ABSOLUTE PRIORITY RULE (APR) VIOLATIONS DETECTED:**")
            memo_lines.append("")
            for v in apr_violations:
                senior = v.get("senior_tranche", "")
                senior_pct = v.get("senior_recovery_pct", "")
                junior = v.get("junior_tranche", "")
                junior_rec = v.get("junior_recovery", "")
                memo_lines.append(
                    f"- **{senior}** recovered only {senior_pct}% while **{junior}** "
                    f"received ${junior_rec}M (junior improperly paid before senior made whole)"
                )
            memo_lines.append("")
    else:
        memo_lines.append("_Capital structure analysis not available._")
        memo_lines.append("")
    
    memo_lines.append("---")
    memo_lines.append("")
    
    # === 3. STRUCTURAL RISK SCORECARD ===
    memo_lines.append("## 3. STRUCTURAL RISK SCORECARD — TRAP DOORS & LME FLAGS")
    memo_lines.append("")
    
    if librarian_result:
        leakage_flags = librarian_result.get("collateral_leakage_flags", [])
        baskets = librarian_result.get("baskets") or librarian_result.get("trap_doors", [])
        
        if leakage_flags or baskets:
            memo_lines.append("**Collateral Leakage / LME Risks:**")
            memo_lines.append("")
            
            for flag in leakage_flags[:10]:
                flag_type = flag.get("type", "")
                description = flag.get("description", "")
                section = flag.get("section", "N/A")
                page = flag.get("page", "N/A")
                severity = flag.get("severity", "medium")
                
                severity_icon = "🔴" if severity == "critical" else "🟡" if severity == "high" else "🔵"
                
                memo_lines.append(
                    f"- {severity_icon} **{flag_type}** — {description} "
                    f"_(Section {section}, Page {page})_"
                )
            
            memo_lines.append("")
            
            if baskets:
                memo_lines.append("**Basket / Covenant Carve-Outs:**")
                memo_lines.append("")
                for basket in baskets[:10]:
                    name = basket.get("name", "")
                    amount = basket.get("amount", "N/A")
                    section = basket.get("section", "N/A")
                    page = basket.get("page", "N/A")
                    memo_lines.append(
                        f"- **{name}**: {amount} _(Section {section}, Page {page})_"
                    )
                memo_lines.append("")
        else:
            memo_lines.append("_No critical structural risks identified by Librarian._")
            memo_lines.append("")
    else:
        memo_lines.append("_Librarian analysis not available._")
        memo_lines.append("")
    
    # === 4. SO WHAT? — NARRATIVE SYNTHESIS ===
    memo_lines.append("---")
    memo_lines.append("")
    memo_lines.append("## 4. SO WHAT? — INVESTMENT IMPLICATIONS")
    memo_lines.append("")
    
    narrative = _build_narrative_synthesis(
        document_report, librarian_result, quant_result, benchmarker_result
    )
    memo_lines.append(narrative)
    memo_lines.append("")
    
    # === 5. RECOVERY SENSITIVITY TABLE ===
    if quant_result:
        memo_lines.append("---")
        memo_lines.append("")
        memo_lines.append("## 5. RECOVERY SENSITIVITY TABLE")
        memo_lines.append("")
        memo_lines.append("_EV sensitivity showing fulcrum migration:_")
        memo_lines.append("")
        
        # Generate quick sensitivity scenarios (placeholder - can be enhanced with actual tornado data)
        base_ev = float(quant_result.get("ev_used", 0))
        memo_lines.append("| Scenario | EV ($M) | Fulcrum Security | 1L Recovery | 2L Recovery |")
        memo_lines.append("|----------|---------|------------------|-------------|-------------|")
        memo_lines.append(f"| Bear | {base_ev * 0.7:.1f} | TBD | TBD | TBD |")
        memo_lines.append(f"| Base | {base_ev:.1f} | {quant_result.get('fulcrum_security', 'N/A')} | TBD | TBD |")
        memo_lines.append(f"| Bull | {base_ev * 1.3:.1f} | TBD | TBD | TBD |")
        memo_lines.append("")
        memo_lines.append("_Use the interactive dashboard for detailed sensitivity analysis._")
        memo_lines.append("")
    
    # === 6. MARKET CONTEXT ===
    if benchmarker_result:
        memo_lines.append("---")
        memo_lines.append("")
        memo_lines.append("## 6. MARKET CONTEXT & PRECEDENT ANALYSIS")
        memo_lines.append("")
        
        market_multiple = benchmarker_result.get("market_multiple", {})
        if market_multiple:
            ev_ebitda = market_multiple.get("ev_ebitda", "N/A")
            peers = market_multiple.get("peers_analyzed", 0)
            memo_lines.append(f"**Market EV/EBITDA Multiple:** {ev_ebitda}x (based on {peers} peers)")
            memo_lines.append("")
        
        recovery_variance = benchmarker_result.get("recovery_variance", [])
        if recovery_variance:
            memo_lines.append("**Recovery Variance vs. Market Precedents:**")
            memo_lines.append("")
            for var in recovery_variance:
                tranche = var.get("tranche", "")
                model = var.get("model_recovery", 0)
                market = var.get("precedent_recovery", 0)
                variance = var.get("variance_pct", 0)
                critical = var.get("critical_variance", False)
                
                flag = "🚨" if critical else "✓"
                memo_lines.append(
                    f"- {flag} **{tranche}**: Model {model}% vs Market {market}% "
                    f"(variance: {variance:+.1f}%)"
                )
            memo_lines.append("")
    
    # === 7. AUDIT TRAIL ===
    if auditor_result:
        memo_lines.append("---")
        memo_lines.append("")
        memo_lines.append("## 7. AUDIT TRAIL & VALIDATION")
        memo_lines.append("")
        
        passed = auditor_result.get("passed", True)
        status_icon = "✅" if passed else "❌"
        memo_lines.append(f"**Audit Status:** {status_icon} {'PASSED' if passed else 'FAILED'}")
        memo_lines.append("")
        
        audit_trail = auditor_result.get("audit_trail", {})
        if audit_trail:
            config_version = audit_trail.get("config_version", "N/A")
            sources = audit_trail.get("sources", [])
            memo_lines.append(f"**Config Version:** {config_version}")
            memo_lines.append(f"**Sources:** {', '.join(sources[:3])}")
            memo_lines.append("")
        
        for_reporter = auditor_result.get("for_reporter", "")
        if for_reporter:
            memo_lines.append(f"**Auditor Notes:** {for_reporter}")
            memo_lines.append("")
    
    # Footer
    memo_lines.append("---")
    memo_lines.append("")
    memo_lines.append("_Generated by Signal-Triage Reporting Engine | Librarian + Quant + Benchmarker + Auditor_")
    memo_lines.append("")
    
    # Assemble
    memo_content = "\n".join(memo_lines)
    
    # Write to file if requested
    if output_path:
        Path(output_path).write_text(memo_content, encoding="utf-8")
    
    return memo_content


def _build_investment_thesis(
    document_report: dict[str, Any],
    quant_result: dict[str, Any] | None,
    benchmarker_result: dict[str, Any] | None,
) -> str:
    """Construct a concise investment thesis based on score, fulcrum, and market context."""
    score = document_report.get("score", 0)
    tier = document_report.get("tier", "N/A")
    
    # Determine recommendation based on score
    if score >= 75:
        stance = "**HIGH RISK** — Significant distress indicators suggest elevated default probability."
    elif score >= 50:
        stance = "**MODERATE RISK** — Material structural concerns warrant close monitoring."
    elif score >= 25:
        stance = "**LOW-MODERATE RISK** — Some structural weaknesses identified."
    else:
        stance = "**LOW RISK** — Minimal distress signals detected."
    
    thesis_parts = [stance]
    
    if quant_result:
        fulcrum = quant_result.get("fulcrum_security", "")
        if fulcrum:
            thesis_parts.append(
                f"Current recovery analysis identifies **{fulcrum}** as the fulcrum security "
                f"under base-case valuation assumptions."
            )
    
    if benchmarker_result:
        variance_critical = any(
            v.get("critical_variance", False)
            for v in benchmarker_result.get("recovery_variance", [])
        )
        if variance_critical:
            thesis_parts.append(
                "⚠️ **Critical variance detected**: Model recovery assumptions deviate significantly "
                "from market precedents, warranting additional diligence."
            )
    
    return " ".join(thesis_parts)


def _build_narrative_synthesis(
    document_report: dict[str, Any],
    librarian_result: dict[str, Any] | None,
    quant_result: dict[str, Any] | None,
    benchmarker_result: dict[str, Any] | None,
) -> str:
    """
    Explain the 'So What?' behind key signals with institutional context.
    
    Example: "The lack of a J.Crew blocker in Section 6.04(b) creates a $250M 
    collateral leakage risk to 1st Lien holders."
    """
    narratives = []
    
    # Analyze top signals for institutional implications
    top_signals = document_report.get("top_signals", [])
    
    for sig in top_signals[:3]:
        sig_type = sig.get("type", "")
        
        if "dropdown" in sig_type.lower() or "j.crew" in sig_type.lower():
            if quant_result:
                recoveries = quant_result.get("recoveries", [])
                if recoveries and len(recoveries) > 0:
                    first_lien = recoveries[0]
                    claim = first_lien.get("claim", 0)
                    narratives.append(
                        f"**Dropdown Risk**: The absence of IP transfer restrictions (J.Crew blocker) "
                        f"in the covenant package exposes 1st Lien holders to potential collateral "
                        f"leakage of up to ${_format_decimal(claim)}M if borrower transfers assets "
                        f"to unrestricted subsidiaries."
                    )
        
        elif "uptier" in sig_type.lower() or "s-prime" in sig_type.lower():
            narratives.append(
                f"**Liability Management Risk**: Evidence of uptier exchange or super-priority "
                f"structuring suggests potential future dilution to existing lenders through "
                f"priming transactions requiring only >50% consent."
            )
        
        elif "double-dip" in sig_type.lower() or "triple-dip" in sig_type.lower():
            narratives.append(
                f"**Economic Dilution**: Double/triple-dip structure artificially inflates stated "
                f"claims relative to true economic value, reducing effective recovery rates for "
                f"existing creditors in restructuring scenarios."
            )
        
        elif "going concern" in sig_type.lower():
            narratives.append(
                f"**Liquidity Crisis**: Management has expressed substantial doubt about the "
                f"company's ability to continue as a going concern, indicating imminent default "
                f"risk and potential Chapter 11 filing within 12 months."
            )
        
        elif "covenant breach" in sig_type.lower():
            narratives.append(
                f"**Technical Default**: Covenant breach provides lenders with acceleration rights "
                f"and negotiating leverage for amendments, potentially leading to fee extraction "
                f"or liability management exercises."
            )
    
    if not narratives:
        narratives.append(
            "Analysis reveals moderate structural risks typical of leveraged credit agreements. "
            "No immediate red flags requiring extraordinary diligence, but continued monitoring "
            "of covenant compliance and liquidity metrics is warranted."
        )
    
    return "\n\n".join(narratives)


def _format_decimal(value: Any) -> str:
    """Format Decimal or float for display (2 decimal places)."""
    if isinstance(value, Decimal):
        return f"{float(value):.2f}"
    elif isinstance(value, (int, float)):
        return f"{value:.2f}"
    return str(value)


def _current_date() -> str:
    """Return current date in ISO format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

"""
Validation Report Generator for Enhanced Parser
Generates comprehensive quality assurance reports for parser validation

WORKSTREAM 3: Enhanced Parser Validation
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from datetime import datetime
import tempfile

from signal_triage.document_intel.enhanced_parser import extract_forensic_data


@dataclass
class ValidationMetrics:
    """Metrics for a single validation test."""
    scenario_name: str
    document_type: str
    success: bool
    error_message: str | None = None
    
    # Capital Structure Metrics
    debt_tranches_found: int = 0
    debt_tranches_expected: int = 0
    capital_structure_accuracy: float = 0.0
    
    # EBITDA Metrics
    ebitda_found: bool = False
    ebitda_risk_score: float = 0.0
    synergies_flagged: bool = False
    future_savings_flagged: bool = False
    addbacks_count: int = 0
    
    # LME Risk Metrics
    lme_risks_found: int = 0
    max_lme_risk_score: float = 0.0
    asset_sale_risks: int = 0
    unrestricted_sub_risks: int = 0
    
    # Performance Metrics
    extraction_time_ms: float = 0.0
    
    # Quality Flags
    metadata_complete: bool = False
    page_citations_present: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    """Complete validation report."""
    report_date: str
    total_scenarios: int
    successful_scenarios: int
    failed_scenarios: int
    
    # Aggregate Metrics
    avg_ebitda_risk_score: float
    avg_lme_risk_score: float
    total_lme_risks_found: int
    ebitda_detection_rate: float  # % of docs with EBITDA found
    
    # Individual Test Results
    test_results: List[ValidationMetrics]
    
    # Quality Assessment
    overall_quality_score: float  # 0-100
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_date": self.report_date,
            "summary": {
                "total_scenarios": self.total_scenarios,
                "successful_scenarios": self.successful_scenarios,
                "failed_scenarios": self.failed_scenarios,
                "success_rate": f"{(self.successful_scenarios / self.total_scenarios * 100):.1f}%",
            },
            "aggregate_metrics": {
                "avg_ebitda_risk_score": round(self.avg_ebitda_risk_score, 2),
                "avg_lme_risk_score": round(self.avg_lme_risk_score, 2),
                "total_lme_risks_found": self.total_lme_risks_found,
                "ebitda_detection_rate": f"{self.ebitda_detection_rate:.1f}%",
            },
            "overall_quality_score": round(self.overall_quality_score, 1),
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "test_results": [t.to_dict() for t in self.test_results],
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        md = f"""# Enhanced Parser Validation Report

**Generated:** {self.report_date}

---

## Executive Summary

### Test Coverage
- **Total Scenarios Tested:** {self.total_scenarios}
- **Successful:** {self.successful_scenarios} ({self.successful_scenarios / self.total_scenarios * 100:.1f}%)
- **Failed:** {self.failed_scenarios} ({self.failed_scenarios / self.total_scenarios * 100:.1f}% if self.total_scenarios else 0)

### Aggregate Performance Metrics
- **Average EBITDA Risk Score:** {self.avg_ebitda_risk_score:.2f}/10.0
- **Average LME Risk Score:** {self.avg_lme_risk_score:.2f}/10.0
- **Total LME Risks Detected:** {self.total_lme_risks_found}
- **EBITDA Detection Rate:** {self.ebitda_detection_rate:.1f}%

### Overall Quality Score
**{self.overall_quality_score:.1f}/100**

"""
        
        # Quality assessment
        if self.overall_quality_score >= 90:
            quality_label = "🟢 EXCELLENT"
        elif self.overall_quality_score >= 75:
            quality_label = "🟡 GOOD"
        elif self.overall_quality_score >= 60:
            quality_label = "🟠 ACCEPTABLE"
        else:
            quality_label = "🔴 NEEDS IMPROVEMENT"
        
        md += f"**Quality Assessment:** {quality_label}\n\n"
        
        # Critical issues
        if self.critical_issues:
            md += "### ⚠️ Critical Issues\n\n"
            for issue in self.critical_issues:
                md += f"- {issue}\n"
            md += "\n"
        
        # Warnings
        if self.warnings:
            md += "### ⚡ Warnings\n\n"
            for warning in self.warnings:
                md += f"- {warning}\n"
            md += "\n"
        
        # Recommendations
        if self.recommendations:
            md += "### 💡 Recommendations\n\n"
            for rec in self.recommendations:
                md += f"- {rec}\n"
            md += "\n"
        
        # Detailed results
        md += "---\n\n## Detailed Test Results\n\n"
        
        for i, result in enumerate(self.test_results, 1):
            status_emoji = "✅" if result.success else "❌"
            
            md += f"### {i}. {result.scenario_name} {status_emoji}\n\n"
            md += f"**Document Type:** {result.document_type}\n\n"
            
            if not result.success:
                md += f"**Error:** {result.error_message}\n\n"
                continue
            
            # Capital Structure
            if result.debt_tranches_found > 0:
                md += f"**Capital Structure:**\n"
                md += f"- Tranches Found: {result.debt_tranches_found}\n"
                if result.debt_tranches_expected > 0:
                    md += f"- Expected: {result.debt_tranches_expected}\n"
                    md += f"- Accuracy: {result.capital_structure_accuracy:.1f}%\n"
                md += "\n"
            
            # EBITDA
            if result.ebitda_found:
                md += f"**EBITDA Analysis:**\n"
                md += f"- Risk Score: {result.ebitda_risk_score:.1f}/10.0\n"
                md += f"- Synergies Flagged: {'Yes' if result.synergies_flagged else 'No'}\n"
                md += f"- Future Savings Flagged: {'Yes' if result.future_savings_flagged else 'No'}\n"
                md += f"- Add-backs Detected: {result.addbacks_count}\n"
                md += "\n"
            else:
                md += "**EBITDA Analysis:** Not found\n\n"
            
            # LME Risks
            if result.lme_risks_found > 0:
                md += f"**LME Leakage Risks:**\n"
                md += f"- Total Risks: {result.lme_risks_found}\n"
                md += f"- Max Risk Score: {result.max_lme_risk_score:.1f}/10.0\n"
                md += f"- Asset Sale Baskets: {result.asset_sale_risks}\n"
                md += f"- Unrestricted Sub Risks: {result.unrestricted_sub_risks}\n"
                md += "\n"
            else:
                md += "**LME Leakage Risks:** None detected\n\n"
            
            # Quality
            md += f"**Quality Metrics:**\n"
            md += f"- Metadata Complete: {'Yes' if result.metadata_complete else 'No'}\n"
            md += f"- Page Citations: {'Yes' if result.page_citations_present else 'No'}\n"
            md += f"- Extraction Time: {result.extraction_time_ms:.1f}ms\n"
            md += "\n"
        
        md += "---\n\n"
        md += f"*Report generated by Enhanced Parser Validation Suite*\n"
        md += f"*Signal-Triage Workstream 3: Enhanced Parser Validation*\n"
        
        return md


def validate_scenario(
    scenario_name: str,
    document_content: str,
    document_type: str,
    expected_tranches: int = 0
) -> ValidationMetrics:
    """
    Validate a single scenario and return metrics.
    """
    import time
    
    metrics = ValidationMetrics(
        scenario_name=scenario_name,
        document_type=document_type,
        success=False,
        debt_tranches_expected=expected_tranches,
    )
    
    # Create temp document
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', delete=False, encoding='utf-8'
    ) as f:
        f.write(document_content)
        temp_path = Path(f.name)
    
    try:
        # Time the extraction
        start_time = time.time()
        result = extract_forensic_data(temp_path)
        end_time = time.time()
        
        metrics.extraction_time_ms = (end_time - start_time) * 1000
        metrics.success = True
        
        # Capital Structure
        metrics.debt_tranches_found = len(result.debt_tranches)
        if expected_tranches > 0:
            metrics.capital_structure_accuracy = min(
                100.0,
                (metrics.debt_tranches_found / expected_tranches) * 100
            )
        
        # EBITDA
        if result.ebitda_definition:
            metrics.ebitda_found = True
            metrics.ebitda_risk_score = result.ebitda_definition.addback_risk_score
            metrics.synergies_flagged = result.ebitda_definition.synergies_flagged
            metrics.future_savings_flagged = result.ebitda_definition.future_cost_savings_flagged
            metrics.addbacks_count = len(result.ebitda_definition.addbacks)
        
        # LME Risks
        metrics.lme_risks_found = len(result.lme_risks)
        if result.lme_risks:
            metrics.max_lme_risk_score = max(r.leakage_risk_score for r in result.lme_risks)
            metrics.asset_sale_risks = sum(
                1 for r in result.lme_risks if "Asset Sale" in r.category
            )
            metrics.unrestricted_sub_risks = sum(
                1 for r in result.lme_risks if "Unrestricted" in r.category
            )
        
        # Quality
        metrics.metadata_complete = all([
            "ebitda_definition_found" in result.metadata,
            "lme_risks_identified" in result.metadata,
        ])
        
        # Check for page citations
        has_citations = False
        if result.ebitda_definition and result.ebitda_definition.page_number:
            has_citations = True
        if any(r.page_number for r in result.lme_risks):
            has_citations = True
        metrics.page_citations_present = has_citations
        
    except Exception as e:
        metrics.success = False
        metrics.error_message = str(e)
    
    finally:
        # Cleanup
        try:
            temp_path.unlink()
        except:
            pass
    
    return metrics


def generate_validation_report(test_results: List[ValidationMetrics]) -> ValidationReport:
    """
    Generate comprehensive validation report from test results.
    """
    total = len(test_results)
    successful = sum(1 for r in test_results if r.success)
    failed = total - successful
    
    # Calculate aggregate metrics
    successful_results = [r for r in test_results if r.success]
    
    if successful_results:
        ebitda_results = [r for r in successful_results if r.ebitda_found]
        avg_ebitda_risk = (
            sum(r.ebitda_risk_score for r in ebitda_results) / len(ebitda_results)
            if ebitda_results else 0.0
        )
        
        lme_results = [r for r in successful_results if r.lme_risks_found > 0]
        avg_lme_risk = (
            sum(r.max_lme_risk_score for r in lme_results) / len(lme_results)
            if lme_results else 0.0
        )
        
        total_lme_risks = sum(r.lme_risks_found for r in successful_results)
        ebitda_detection_rate = (len(ebitda_results) / len(successful_results)) * 100
    else:
        avg_ebitda_risk = 0.0
        avg_lme_risk = 0.0
        total_lme_risks = 0
        ebitda_detection_rate = 0.0
    
    # Quality assessment
    critical_issues = []
    warnings = []
    recommendations = []
    
    # Check for critical issues
    if failed > 0:
        critical_issues.append(f"{failed} scenario(s) failed validation")
    
    if ebitda_detection_rate < 50:
        warnings.append(f"Low EBITDA detection rate: {ebitda_detection_rate:.1f}%")
    
    # Check metadata completeness
    incomplete_metadata = sum(1 for r in successful_results if not r.metadata_complete)
    if incomplete_metadata > 0:
        warnings.append(f"{incomplete_metadata} scenario(s) have incomplete metadata")
    
    # Check page citations
    no_citations = sum(1 for r in successful_results if not r.page_citations_present)
    if no_citations > 0:
        warnings.append(f"{no_citations} scenario(s) missing page citations")
    
    # Recommendations
    if avg_ebitda_risk < 3.0:
        recommendations.append("Consider testing more aggressive EBITDA definitions")
    
    if total_lme_risks < 10:
        recommendations.append("Increase test coverage for LME leakage scenarios")
    
    if any(r.extraction_time_ms > 5000 for r in successful_results):
        recommendations.append("Some extractions took >5s; consider performance optimization")
    
    # Calculate overall quality score (0-100)
    quality_score = 0.0
    
    # Success rate (40 points)
    quality_score += (successful / total) * 40
    
    # EBITDA detection (20 points)
    quality_score += (ebitda_detection_rate / 100) * 20
    
    # LME risk detection (20 points)
    lme_detection_rate = (sum(1 for r in successful_results if r.lme_risks_found > 0) / len(successful_results)) if successful_results else 0
    quality_score += lme_detection_rate * 20
    
    # Metadata completeness (10 points)
    metadata_rate = (sum(1 for r in successful_results if r.metadata_complete) / len(successful_results)) if successful_results else 0
    quality_score += metadata_rate * 10
    
    # Page citations (10 points)
    citation_rate = (sum(1 for r in successful_results if r.page_citations_present) / len(successful_results)) if successful_results else 0
    quality_score += citation_rate * 10
    
    return ValidationReport(
        report_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_scenarios=total,
        successful_scenarios=successful,
        failed_scenarios=failed,
        avg_ebitda_risk_score=avg_ebitda_risk,
        avg_lme_risk_score=avg_lme_risk,
        total_lme_risks_found=total_lme_risks,
        ebitda_detection_rate=ebitda_detection_rate,
        test_results=test_results,
        overall_quality_score=quality_score,
        critical_issues=critical_issues,
        warnings=warnings,
        recommendations=recommendations,
    )


def save_report(report: ValidationReport, output_dir: Path | None = None):
    """
    Save validation report to disk (JSON + Markdown).
    """
    if output_dir is None:
        output_dir = Path(".")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "enhanced_parser_validation_report.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print(f"✓ JSON report saved: {json_path.resolve()}")
    
    # Save Markdown
    md_path = output_dir / "enhanced_parser_validation_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report.to_markdown())
    
    print(f"✓ Markdown report saved: {md_path.resolve()}")
    
    return json_path, md_path


if __name__ == "__main__":
    print("Validation Report Generator")
    print("Usage: Import and call generate_validation_report()")

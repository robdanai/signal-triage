"""
Run Enhanced Parser Validation Suite
Executes all validation scenarios and generates comprehensive report

WORKSTREAM 3: Enhanced Parser Validation (MEDIUM PRIORITY)
Goal: Validate on 10+ real credit agreements
Impact: Quality assurance & feature visibility

Usage:
    python tests/run_validation_suite.py
    
Output:
    - enhanced_parser_validation_report.json
    - enhanced_parser_validation_report.md
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_report_generator import (
    validate_scenario,
    generate_validation_report,
    save_report,
)
from tests.validation_scenarios import SCENARIOS


def main():
    """
    Execute validation suite and generate reports.
    """
    print("="*80)
    print("ENHANCED PARSER VALIDATION SUITE")
    print("="*80)
    print()
    print("WORKSTREAM 3: Enhanced Parser Validation")
    print("Goal: Validate on 10+ real credit agreements")
    print("Impact: Quality assurance & feature visibility")
    print()
    print("="*80)
    print()
    
    # Get scenarios from centralized module
    scenarios = SCENARIOS
    
    print(f"Running {len(scenarios)} validation scenarios...")
    print()
    
    # Run validation tests
    test_results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] Testing: {scenario['name']}")
        
        try:
            metrics = validate_scenario(
                scenario_name=scenario['name'],
                document_content=scenario['content'],
                document_type=scenario['doc_type'],
                expected_tranches=scenario['expected_tranches'],
            )
            
            test_results.append(metrics)
            
            # Print quick status
            if metrics.success:
                status = "✅ PASS"
                details = []
                if metrics.ebitda_found:
                    details.append(f"EBITDA: {metrics.ebitda_risk_score:.1f}/10")
                if metrics.lme_risks_found > 0:
                    details.append(f"LME: {metrics.lme_risks_found} risks")
                if metrics.debt_tranches_found > 0:
                    details.append(f"Tranches: {metrics.debt_tranches_found}")
                
                detail_str = ", ".join(details) if details else "No extractions"
                print(f"    {status} ({detail_str})")
            else:
                print(f"    ❌ FAIL: {metrics.error_message}")
        
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
            # Create error metric
            from validation_report_generator import ValidationMetrics
            metrics = ValidationMetrics(
                scenario_name=scenario['name'],
                document_type=scenario['doc_type'],
                success=False,
                error_message=str(e),
            )
            test_results.append(metrics)
        
        print()
    
    print("="*80)
    print("Generating validation report...")
    print("="*80)
    print()
    
    # Generate comprehensive report
    report = generate_validation_report(test_results)
    
    # Save reports
    output_dir = Path(__file__).parent.parent / "docs"
    json_path, md_path = save_report(report, output_dir)
    
    print()
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print()
    print(f"Total Scenarios:        {report.total_scenarios}")
    print(f"Successful:             {report.successful_scenarios} ({report.successful_scenarios / report.total_scenarios * 100:.1f}%)")
    print(f"Failed:                 {report.failed_scenarios}")
    print()
    print(f"Avg EBITDA Risk Score:  {report.avg_ebitda_risk_score:.2f}/10.0")
    print(f"Avg LME Risk Score:     {report.avg_lme_risk_score:.2f}/10.0")
    print(f"Total LME Risks Found:  {report.total_lme_risks_found}")
    print(f"EBITDA Detection Rate:  {report.ebitda_detection_rate:.1f}%")
    print()
    print(f"Overall Quality Score:  {report.overall_quality_score:.1f}/100")
    
    if report.overall_quality_score >= 90:
        quality_label = "🟢 EXCELLENT"
    elif report.overall_quality_score >= 75:
        quality_label = "🟡 GOOD"
    elif report.overall_quality_score >= 60:
        quality_label = "🟠 ACCEPTABLE"
    else:
        quality_label = "🔴 NEEDS IMPROVEMENT"
    
    print(f"Quality Assessment:     {quality_label}")
    print()
    
    if report.critical_issues:
        print("⚠️  CRITICAL ISSUES:")
        for issue in report.critical_issues:
            print(f"    - {issue}")
        print()
    
    if report.warnings:
        print("⚡ WARNINGS:")
        for warning in report.warnings:
            print(f"    - {warning}")
        print()
    
    if report.recommendations:
        print("💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"    - {rec}")
        print()
    
    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print()
    print(f"Reports saved to:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")
    print()
    
    # Return exit code based on quality score
    if report.overall_quality_score >= 75:
        return 0  # Success
    else:
        return 1  # Failure


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

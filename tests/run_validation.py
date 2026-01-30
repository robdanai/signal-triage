#!/usr/bin/env python
"""
Enhanced Parser Validation CLI
Comprehensive, flexible validation tool with multiple options

WORKSTREAM 3: Enhanced Parser Validation - User-Friendly CLI

Usage Examples:
    # Quick check (3 scenarios)
    python tests/run_validation.py --quick
    
    # Full validation (12 scenarios)
    python tests/run_validation.py --full
    
    # Specific scenarios by number
    python tests/run_validation.py --scenarios 1 2 3
    
    # Filter by risk level
    python tests/run_validation.py --risk-level HIGH CRITICAL
    
    # Filter by capability
    python tests/run_validation.py --capability ebitda lme
    
    # Custom output location
    python tests/run_validation.py --output-dir ./my_reports
    
    # JSON only (no markdown)
    python tests/run_validation.py --format json
    
    # Quiet mode (minimal output)
    python tests/run_validation.py --quiet
    
    # Verbose mode (detailed output)
    python tests/run_validation.py --verbose
    
    # Compare with previous run
    python tests/run_validation.py --compare docs/enhanced_parser_validation_report.json
    
    # Set custom quality threshold
    python tests/run_validation.py --quality-threshold 90
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_report_generator import (
    validate_scenario,
    generate_validation_report,
    ValidationReport,
)
from tests.validation_scenarios import SCENARIOS


# Risk level mappings
RISK_LEVELS = {
    "Investment Grade Borrower": "LOW",
    "Aggressive EBITDA Definition": "HIGH",
    "J.Crew Style Dropdown Risk": "CRITICAL",
    "Large Asset Sale Basket": "HIGH",
    "Complex Capital Structure": "MODERATE",
    "Incremental Priming Risk": "CRITICAL",
    "Moderate Balanced Structure": "MODERATE",
    "No EBITDA Definition (Edge Case)": "LOW",
    "Tech Company (Non-Cash Heavy)": "MODERATE",
    "Dividend Recapitalization": "MODERATE",
    "Covenant-Lite Structure": "HIGH",
    "Multi-Currency Complex": "MODERATE",
}

# Capability mappings
CAPABILITIES = {
    "Investment Grade Borrower": ["capital_structure", "ebitda"],
    "Aggressive EBITDA Definition": ["ebitda"],
    "J.Crew Style Dropdown Risk": ["lme"],
    "Large Asset Sale Basket": ["lme"],
    "Complex Capital Structure": ["capital_structure"],
    "Incremental Priming Risk": ["lme"],
    "Moderate Balanced Structure": ["capital_structure", "ebitda", "lme"],
    "No EBITDA Definition (Edge Case)": ["edge_cases"],
    "Tech Company (Non-Cash Heavy)": ["ebitda"],
    "Dividend Recapitalization": ["lme"],
    "Covenant-Lite Structure": ["ebitda", "lme"],
    "Multi-Currency Complex": ["capital_structure"],
}


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(text: str, color: str = ""):
    """Print colored text if terminal supports it."""
    try:
        print(f"{color}{text}{Colors.ENDC}")
    except:
        print(text)


def filter_scenarios(
    scenarios: List[dict],
    scenario_nums: Optional[List[int]] = None,
    risk_levels: Optional[List[str]] = None,
    capabilities: Optional[List[str]] = None,
) -> List[dict]:
    """
    Filter scenarios based on user criteria.
    
    Args:
        scenarios: List of all scenarios
        scenario_nums: Specific scenario numbers (1-indexed)
        risk_levels: Risk levels to include (LOW, MODERATE, HIGH, CRITICAL)
        capabilities: Capabilities to test (capital_structure, ebitda, lme, edge_cases)
    
    Returns:
        Filtered list of scenarios
    """
    filtered = scenarios.copy()
    
    # Filter by scenario number
    if scenario_nums:
        filtered = [s for i, s in enumerate(scenarios, 1) if i in scenario_nums]
    
    # Filter by risk level
    if risk_levels:
        risk_levels_upper = [r.upper() for r in risk_levels]
        filtered = [
            s for s in filtered
            if RISK_LEVELS.get(s['name'], 'MODERATE') in risk_levels_upper
        ]
    
    # Filter by capability
    if capabilities:
        capabilities_lower = [c.lower() for c in capabilities]
        filtered = [
            s for s in filtered
            if any(cap in CAPABILITIES.get(s['name'], []) for cap in capabilities_lower)
        ]
    
    return filtered


def print_progress_bar(current: int, total: int, scenario_name: str, width: int = 50):
    """Print a progress bar."""
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    percent = 100 * current / total
    print(f"\r[{bar}] {percent:.0f}% | {scenario_name[:30]:<30}", end="", flush=True)


def compare_reports(current_report: ValidationReport, previous_path: Path):
    """
    Compare current report with previous run.
    
    Args:
        current_report: Current validation report
        previous_path: Path to previous validation JSON report
    """
    print()
    print_colored("="*80, Colors.HEADER)
    print_colored("COMPARISON WITH PREVIOUS RUN", Colors.HEADER)
    print_colored("="*80, Colors.HEADER)
    print()
    
    try:
        with open(previous_path, 'r') as f:
            prev_data = json.load(f)
        
        prev_quality = prev_data.get('overall_quality_score', 0)
        curr_quality = current_report.overall_quality_score
        quality_diff = curr_quality - prev_quality
        
        prev_success = prev_data['summary']['successful_scenarios']
        curr_success = current_report.successful_scenarios
        success_diff = curr_success - prev_success
        
        print(f"Previous Quality Score: {prev_quality:.1f}/100")
        print(f"Current Quality Score:  {curr_quality:.1f}/100")
        
        if quality_diff > 0:
            print_colored(f"Change: +{quality_diff:.1f} ⬆️ IMPROVED", Colors.OKGREEN)
        elif quality_diff < 0:
            print_colored(f"Change: {quality_diff:.1f} ⬇️ DECLINED", Colors.FAIL)
        else:
            print("Change: 0.0 ➡️ NO CHANGE")
        
        print()
        print(f"Previous Success: {prev_success}")
        print(f"Current Success:  {curr_success}")
        
        if success_diff > 0:
            print_colored(f"Change: +{success_diff} ⬆️ MORE PASSING", Colors.OKGREEN)
        elif success_diff < 0:
            print_colored(f"Change: {success_diff} ⬇️ FEWER PASSING", Colors.FAIL)
        else:
            print("Change: 0 ➡️ NO CHANGE")
        
        print()
        
    except FileNotFoundError:
        print_colored(f"⚠️  Previous report not found: {previous_path}", Colors.WARNING)
    except json.JSONDecodeError:
        print_colored(f"⚠️  Invalid JSON in previous report", Colors.WARNING)
    except Exception as e:
        print_colored(f"⚠️  Error comparing reports: {e}", Colors.WARNING)


def save_report_files(report: ValidationReport, output_dir: Path, format: str, verbose: bool = False):
    """
    Save validation report to files.
    
    Args:
        report: ValidationReport to save
        output_dir: Directory to save reports
        format: Output format (json, markdown, both)
        verbose: Print verbose output
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files_saved = []
    
    # Save JSON
    if format in ['json', 'both']:
        json_path = output_dir / "enhanced_parser_validation_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
        files_saved.append(str(json_path))
        if verbose:
            print(f"✓ JSON report saved: {json_path}")
    
    # Save Markdown
    if format in ['markdown', 'both']:
        md_path = output_dir / "enhanced_parser_validation_report.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report.to_markdown())
        files_saved.append(str(md_path))
        if verbose:
            print(f"✓ Markdown report saved: {md_path}")
    
    return files_saved


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced Parser Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Quick check (3 scenarios):
    python tests/run_validation.py --quick
  
  Full validation (12 scenarios):
    python tests/run_validation.py --full
  
  Specific scenarios:
    python tests/run_validation.py --scenarios 1 2 3
  
  Filter by risk level:
    python tests/run_validation.py --risk-level HIGH CRITICAL
  
  Filter by capability:
    python tests/run_validation.py --capability ebitda lme
  
  Custom output:
    python tests/run_validation.py --output-dir ./reports --format json
  
  Compare with previous:
    python tests/run_validation.py --compare docs/enhanced_parser_validation_report.json
  
  Verbose mode:
    python tests/run_validation.py --full --verbose
        """
    )
    
    # Scenario selection
    scenario_group = parser.add_mutually_exclusive_group()
    scenario_group.add_argument(
        '--quick',
        action='store_true',
        help='Run quick check (3 representative scenarios, ~5s)'
    )
    scenario_group.add_argument(
        '--full',
        action='store_true',
        help='Run full validation suite (12 scenarios, ~30s)'
    )
    scenario_group.add_argument(
        '--scenarios',
        type=int,
        nargs='+',
        metavar='N',
        help='Run specific scenarios by number (1-12)'
    )
    
    # Filtering
    parser.add_argument(
        '--risk-level',
        choices=['LOW', 'MODERATE', 'HIGH', 'CRITICAL'],
        nargs='+',
        help='Filter scenarios by risk level'
    )
    parser.add_argument(
        '--capability',
        choices=['capital_structure', 'ebitda', 'lme', 'edge_cases'],
        nargs='+',
        help='Filter scenarios by capability'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('docs'),
        help='Output directory for reports (default: docs/)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save report files (console output only)'
    )
    
    # Comparison
    parser.add_argument(
        '--compare',
        type=Path,
        metavar='PREV_REPORT',
        help='Compare with previous validation report (JSON)'
    )
    
    # Quality threshold
    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=75.0,
        metavar='SCORE',
        help='Minimum quality score to pass (default: 75.0)'
    )
    
    # Verbosity
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    verbosity_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (minimal output)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine scenarios to run
    if args.quick:
        # Quick check: scenarios 1, 2, 3
        selected_scenarios = [SCENARIOS[i] for i in [0, 1, 2]]
    elif args.full:
        # Full suite: all 12 scenarios
        selected_scenarios = SCENARIOS
    elif args.scenarios:
        # Specific scenarios by number
        selected_scenarios = [
            SCENARIOS[i-1] for i in args.scenarios
            if 1 <= i <= len(SCENARIOS)
        ]
    else:
        # Default: full suite
        selected_scenarios = SCENARIOS
    
    # Apply filters
    selected_scenarios = filter_scenarios(
        selected_scenarios,
        risk_levels=args.risk_level,
        capabilities=args.capability,
    )
    
    if not selected_scenarios:
        print_colored("❌ No scenarios match the specified criteria", Colors.FAIL)
        return 1
    
    # Print header
    if not args.quiet:
        print_colored("="*80, Colors.HEADER)
        print_colored("ENHANCED PARSER VALIDATION", Colors.HEADER)
        print_colored("="*80, Colors.HEADER)
        print()
        print(f"Scenarios to run: {len(selected_scenarios)}")
        print(f"Output directory: {args.output_dir}")
        print(f"Output format: {args.format}")
        print(f"Quality threshold: {args.quality_threshold}/100")
        print()
    
    # Run validation
    test_results = []
    
    if not args.quiet:
        print_colored("Running validation...", Colors.OKBLUE)
        print()
    
    for i, scenario in enumerate(selected_scenarios, 1):
        if not args.quiet and not args.verbose:
            print_progress_bar(i-1, len(selected_scenarios), scenario['name'])
        
        if args.verbose:
            print(f"[{i}/{len(selected_scenarios)}] Testing: {scenario['name']}")
        
        try:
            metrics = validate_scenario(
                scenario_name=scenario['name'],
                document_content=scenario['content'],
                document_type=scenario['doc_type'],
                expected_tranches=scenario['expected_tranches'],
            )
            
            test_results.append(metrics)
            
            if args.verbose:
                if metrics.success:
                    print_colored(f"  ✅ PASS", Colors.OKGREEN)
                    if metrics.ebitda_found:
                        print(f"     EBITDA Risk: {metrics.ebitda_risk_score:.1f}/10.0")
                    if metrics.lme_risks_found > 0:
                        print(f"     LME Risks: {metrics.lme_risks_found} (max: {metrics.max_lme_risk_score:.1f}/10.0)")
                else:
                    print_colored(f"  ❌ FAIL: {metrics.error_message}", Colors.FAIL)
        
        except Exception as e:
            if args.verbose:
                print_colored(f"  ❌ ERROR: {e}", Colors.FAIL)
            
            from tests.validation_report_generator import ValidationMetrics
            metrics = ValidationMetrics(
                scenario_name=scenario['name'],
                document_type=scenario['doc_type'],
                success=False,
                error_message=str(e),
            )
            test_results.append(metrics)
    
    if not args.quiet and not args.verbose:
        print_progress_bar(len(selected_scenarios), len(selected_scenarios), "Complete")
        print()  # Newline after progress bar
    
    print()
    
    # Generate report
    report = generate_validation_report(test_results)
    
    # Save report files
    if not args.no_save:
        if not args.quiet:
            print_colored("Saving reports...", Colors.OKBLUE)
        
        files_saved = save_report_files(
            report,
            args.output_dir,
            args.format,
            verbose=args.verbose
        )
        
        if not args.quiet and not args.verbose:
            print(f"✓ Reports saved to: {args.output_dir}")
    
    # Print summary
    print()
    print_colored("="*80, Colors.HEADER)
    print_colored("VALIDATION SUMMARY", Colors.HEADER)
    print_colored("="*80, Colors.HEADER)
    print()
    
    print(f"Scenarios Run:   {report.total_scenarios}")
    
    if report.successful_scenarios == report.total_scenarios:
        print_colored(f"Passed:          {report.successful_scenarios} ✅", Colors.OKGREEN)
    else:
        print(f"Passed:          {report.successful_scenarios}")
    
    if report.failed_scenarios > 0:
        print_colored(f"Failed:          {report.failed_scenarios} ❌", Colors.FAIL)
    else:
        print(f"Failed:          {report.failed_scenarios}")
    
    print()
    print(f"Quality Score:   {report.overall_quality_score:.1f}/100")
    
    if report.overall_quality_score >= args.quality_threshold:
        print_colored(f"Status:          PASS (≥{args.quality_threshold}) ✅", Colors.OKGREEN)
    else:
        print_colored(f"Status:          FAIL (<{args.quality_threshold}) ❌", Colors.FAIL)
    
    print()
    
    # Print issues/warnings if any
    if report.critical_issues:
        print_colored("⚠️  CRITICAL ISSUES:", Colors.FAIL)
        for issue in report.critical_issues:
            print(f"  - {issue}")
        print()
    
    if report.warnings and not args.quiet:
        print_colored("⚡ WARNINGS:", Colors.WARNING)
        for warning in report.warnings:
            print(f"  - {warning}")
        print()
    
    # Compare with previous run
    if args.compare:
        compare_reports(report, args.compare)
    
    # Exit code
    if report.overall_quality_score >= args.quality_threshold and report.failed_scenarios == 0:
        return 0  # Success
    else:
        return 1  # Failure


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_colored(f"\n❌ CRITICAL ERROR: {e}", Colors.FAIL)
        sys.exit(1)

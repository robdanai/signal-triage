"""
Quick Validation Check for Enhanced Parser
Runs a fast smoke test to verify parser functionality

WORKSTREAM 3: Enhanced Parser Validation - Quick Check

Usage:
    python tests/quick_validation_check.py
    
This runs 3 representative scenarios (fast, ~5 seconds):
- Conservative (investment grade)
- Aggressive (high risk EBITDA)
- Critical LME (J.Crew dropdown)
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_report_generator import validate_scenario
from tests.validation_scenarios import (
    INVESTMENT_GRADE_AGREEMENT,
    DISTRESSED_AGGRESSIVE_EBITDA,
    HIGH_LME_RISK_JCREW,
)


def main():
    """Run quick validation check on 3 representative scenarios."""
    print("="*80)
    print("ENHANCED PARSER - QUICK VALIDATION CHECK")
    print("="*80)
    print()
    print("Running 3 smoke tests (conservative → aggressive → critical)...")
    print()
    
    start_time = time.time()
    
    # Test 1: Conservative
    print("[1/3] Testing Conservative Structure...")
    result1 = validate_scenario(
        "Investment Grade (Conservative)",
        INVESTMENT_GRADE_AGREEMENT,
        "Investment Grade",
        expected_tranches=2,
    )
    
    if result1.success:
        print(f"  ✅ PASS")
        if result1.ebitda_found:
            print(f"     EBITDA Risk: {result1.ebitda_risk_score:.1f}/10.0 (Conservative)")
    else:
        print(f"  ❌ FAIL: {result1.error_message}")
    print()
    
    # Test 2: Aggressive
    print("[2/3] Testing Aggressive EBITDA...")
    result2 = validate_scenario(
        "Aggressive EBITDA Definition",
        DISTRESSED_AGGRESSIVE_EBITDA,
        "Distressed",
        expected_tranches=0,
    )
    
    if result2.success:
        print(f"  ✅ PASS")
        if result2.ebitda_found:
            print(f"     EBITDA Risk: {result2.ebitda_risk_score:.1f}/10.0 (Aggressive)")
            print(f"     Synergies: {'Yes' if result2.synergies_flagged else 'No'}")
            print(f"     Add-backs: {result2.addbacks_count}")
    else:
        print(f"  ❌ FAIL: {result2.error_message}")
    print()
    
    # Test 3: Critical LME
    print("[3/3] Testing Critical LME Risk (J.Crew)...")
    result3 = validate_scenario(
        "J.Crew Style Dropdown",
        HIGH_LME_RISK_JCREW,
        "High LME Risk",
        expected_tranches=0,
    )
    
    if result3.success:
        print(f"  ✅ PASS")
        if result3.lme_risks_found > 0:
            print(f"     LME Risks: {result3.lme_risks_found}")
            print(f"     Max Risk Score: {result3.max_lme_risk_score:.1f}/10.0 (Critical)")
    else:
        print(f"  ❌ FAIL: {result3.error_message}")
    print()
    
    elapsed = time.time() - start_time
    
    print("="*80)
    print("QUICK CHECK SUMMARY")
    print("="*80)
    
    passed = sum([result1.success, result2.success, result3.success])
    failed = 3 - passed
    
    print(f"Passed: {passed}/3")
    print(f"Failed: {failed}/3")
    print(f"Time: {elapsed:.1f}s")
    print()
    
    if passed == 3:
        print("✅ QUICK CHECK PASSED - Parser working correctly")
        print()
        print("For full validation, run:")
        print("  python tests/run_validation_suite.py")
        print()
        return 0
    else:
        print("❌ QUICK CHECK FAILED - See errors above")
        print()
        print("Debug steps:")
        print("  1. Check that pdfplumber is installed: pip install pdfplumber")
        print("  2. Run individual unit tests: pytest tests/test_enhanced_parser.py -v")
        print("  3. Check parser imports: python -c 'from signal_triage.document_intel import extract_forensic_data'")
        print()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("\nPlease ensure:")
        print("  1. Python environment is activated")
        print("  2. Dependencies installed: pip install -r requirements.txt")
        print("  3. Working directory is project root")
        sys.exit(1)

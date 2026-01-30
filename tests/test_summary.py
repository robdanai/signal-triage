"""
Test Summary Utility
Lists all available Enhanced Parser validation tests

WORKSTREAM 3: Enhanced Parser Validation

Usage:
    python tests/test_summary.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_scenarios import SCENARIOS


def main():
    """Display summary of all available validation tests."""
    print("="*80)
    print("ENHANCED PARSER VALIDATION TEST SUITE")
    print("="*80)
    print()
    print(f"Total Scenarios: {len(SCENARIOS)}")
    print()
    
    print("Available Tests:")
    print("-" * 80)
    print()
    
    for i, scenario in enumerate(SCENARIOS, 1):
        name = scenario['name']
        doc_type = scenario['doc_type']
        expected_tranches = scenario['expected_tranches']
        
        # Determine risk category
        if 'Investment Grade' in name or 'Balanced' in name:
            risk = "LOW-MODERATE"
        elif 'Aggressive' in name or 'Covenant-Lite' in name or 'Large Asset' in name:
            risk = "HIGH"
        elif 'J.Crew' in name or 'Priming' in name:
            risk = "CRITICAL"
        else:
            risk = "MODERATE"
        
        print(f"{i:2d}. {name}")
        print(f"    Type: {doc_type}")
        print(f"    Risk Level: {risk}")
        if expected_tranches > 0:
            print(f"    Expected Tranches: {expected_tranches}")
        print()
    
    print("-" * 80)
    print()
    print("How to Run:")
    print()
    print("  Quick Check (3 scenarios, ~5 seconds):")
    print("    python tests/quick_validation_check.py")
    print()
    print("  Full Suite (12 scenarios, ~30 seconds):")
    print("    python tests/run_validation_suite.py")
    print()
    print("  Individual Test (pytest):")
    print("    pytest tests/test_enhanced_parser_integration.py::test_scenario_2_aggressive_ebitda -v")
    print()
    print("  All Integration Tests:")
    print("    pytest tests/test_enhanced_parser_integration.py -v -s")
    print()
    print("-" * 80)
    print()
    print("Documentation:")
    print("  - docs/ENHANCED_PARSER_VALIDATION.md - Comprehensive validation report")
    print("  - docs/ENHANCED_PARSER.md - Parser features and usage")
    print("  - tests/fixtures/validation_suite/README.md - Fixture descriptions")
    print()


if __name__ == "__main__":
    main()

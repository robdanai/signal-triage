#!/usr/bin/env python
"""
Custom Scenario Creation Wizard
Interactive tool to create custom validation scenarios

WORKSTREAM 3: Enhanced Parser Validation - Custom Scenarios

Usage:
    python tests/create_custom_scenario.py
    
This will guide you through creating a custom credit agreement scenario
for testing specific parser capabilities.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(text)
    print("="*80 + "\n")


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else default


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']


def get_multiline_input(prompt: str) -> str:
    """Get multiline input (end with empty line)."""
    print(f"\n{prompt}")
    print("(Enter text, press Enter twice when done)")
    print("-" * 40)
    
    lines = []
    while True:
        line = input()
        if not line and lines:  # Empty line and we have content
            break
        lines.append(line)
    
    return "\n".join(lines)


def create_scenario():
    """Interactive scenario creation wizard."""
    print_header("CUSTOM SCENARIO CREATION WIZARD")
    
    print("This wizard will help you create a custom validation scenario.")
    print("You'll be prompted for each component of the credit agreement.")
    print()
    
    # Basic info
    print("=" * 40)
    print("BASIC INFORMATION")
    print("=" * 40)
    
    name = get_input("Scenario Name", "My Custom Scenario")
    borrower = get_input("Borrower Name", "Custom Borrower Inc.")
    date = get_input("Agreement Date", datetime.now().strftime("%B %Y"))
    doc_type = get_input("Document Type", "Custom Structure")
    
    # Risk assessment
    print("\n" + "=" * 40)
    print("RISK ASSESSMENT")
    print("=" * 40)
    
    print("\nWhat risk level is this scenario?")
    print("  1. LOW (Conservative, investment grade)")
    print("  2. MODERATE (Balanced, typical middle market)")
    print("  3. HIGH (Aggressive covenants, large baskets)")
    print("  4. CRITICAL (J.Crew dropdown, priming risk)")
    
    risk_choice = get_input("Choice", "2")
    risk_map = {"1": "LOW", "2": "MODERATE", "3": "HIGH", "4": "CRITICAL"}
    risk_level = risk_map.get(risk_choice, "MODERATE")
    
    # Components
    components = []
    
    # Capital Structure
    print("\n" + "=" * 40)
    print("CAPITAL STRUCTURE")
    print("=" * 40)
    
    has_cap_structure = get_yes_no("Include capital structure table?", True)
    
    cap_structure_text = ""
    if has_cap_structure:
        print("\nHow many debt tranches?")
        num_tranches = int(get_input("Number of tranches", "2"))
        
        print("\nEnter capital structure details:")
        print("(Example: First Lien Term Loan  $500,000,000  Dec 2028  SOFR+450)")
        
        tranches = []
        for i in range(num_tranches):
            print(f"\nTranche {i+1}:")
            tranche_name = get_input("  Name", f"First Lien Term Loan {chr(65+i)}")
            amount = get_input("  Amount", "$100,000,000")
            maturity = get_input("  Maturity", "Dec 2028")
            rate = get_input("  Rate", "SOFR + 400")
            security = get_input("  Security", "First Priority")
            
            tranches.append({
                "name": tranche_name,
                "amount": amount,
                "maturity": maturity,
                "rate": rate,
                "security": security,
            })
        
        cap_structure_text = "\nCAPITAL STRUCTURE\n\n"
        cap_structure_text += "Facility                    Amount              Maturity        Rate            Security\n"
        for t in tranches:
            cap_structure_text += f"{t['name']:<26} {t['amount']:<18} {t['maturity']:<15} {t['rate']:<15} {t['security']}\n"
        
        components.append("capital_structure")
    
    # EBITDA Definition
    print("\n" + "=" * 40)
    print("EBITDA DEFINITION")
    print("=" * 40)
    
    has_ebitda = get_yes_no("Include EBITDA definition?", True)
    
    ebitda_text = ""
    if has_ebitda:
        print("\nSelect add-backs to include:")
        
        addbacks = []
        
        if get_yes_no("  - Standard (interest, tax, D&A)?", True):
            addbacks.append("(a) interest expense, income tax expense, depreciation, and amortization;")
        
        if get_yes_no("  - Non-cash charges (stock-based comp)?", True):
            addbacks.append("(b) non-cash charges and expenses, including stock-based compensation;")
        
        if get_yes_no("  - Restructuring charges?", False):
            addbacks.append("(c) restructuring charges and one-time expenses;")
        
        if get_yes_no("  - Run-rate synergies (AGGRESSIVE)?", False):
            addbacks.append("(d) run-rate cost savings and synergies anticipated to be realized within 12 months;")
        
        if get_yes_no("  - Pro-forma adjustments (AGGRESSIVE)?", False):
            addbacks.append("(e) pro-forma EBITDA adjustments for acquisitions;")
        
        if get_yes_no("  - Future cost savings (VERY AGGRESSIVE)?", False):
            addbacks.append("(f) anticipated cost savings from pending restructuring initiatives;")
        
        ebitda_text = '\n"Consolidated EBITDA" means, for any period, net income plus:\n\n'
        ebitda_text += "\n".join(addbacks)
        ebitda_text += "\n"
        
        components.append("ebitda")
    
    # LME Risks
    print("\n" + "=" * 40)
    print("LME LEAKAGE RISKS")
    print("=" * 40)
    
    has_lme = get_yes_no("Include LME leakage risks?", False)
    
    lme_text = ""
    if has_lme:
        # Asset sale basket
        if get_yes_no("\n  Include asset sale basket?", True):
            basket_size = get_input("    Basket size", "$50,000,000")
            sweep_threshold = get_input("    Sweep threshold", "$25,000,000")
            
            lme_text += f"\nSection 7.05. Asset Sales.\n\n"
            lme_text += f"Permitted Asset Sales up to {basket_size} per fiscal year.\n"
            lme_text += f"Net Cash Proceeds in excess of {sweep_threshold} shall be applied to prepayment.\n"
            
            components.append("lme")
        
        # Unrestricted subsidiary
        if get_yes_no("\n  Include unrestricted subsidiary basket?", False):
            unrestricted_size = get_input("    Basket size", "$25,000,000")
            ip_transfer = get_yes_no("    Allow IP transfer? (HIGH RISK)", False)
            
            lme_text += f"\nSection 7.08. Investments in Unrestricted Subsidiaries.\n\n"
            lme_text += f"The Borrower may make investments in Unrestricted Subsidiaries up to {unrestricted_size}.\n"
            
            if ip_transfer:
                lme_text += "This includes transfers of intellectual property and other intangible assets.\n"
                lme_text += "⚠️  HIGH RISK: IP transfer permitted (J.Crew-style dropdown)\n"
            
            components.append("lme")
    
    # Custom clauses
    print("\n" + "=" * 40)
    print("CUSTOM CLAUSES")
    print("=" * 40)
    
    has_custom = get_yes_no("Include custom clauses?", False)
    
    custom_text = ""
    if has_custom:
        custom_text = get_multiline_input("Enter custom clauses:")
        custom_text = "\n\n" + custom_text + "\n"
    
    # Build full scenario
    print("\n" + "=" * 40)
    print("GENERATING SCENARIO")
    print("=" * 40)
    
    scenario_content = f"""CREDIT AGREEMENT
{borrower}
Dated: {date}

{'='*80}
{cap_structure_text}
{'='*80 if cap_structure_text else ''}
{ebitda_text}
{'='*80 if ebitda_text else ''}
{lme_text}
{custom_text}

Generated by Custom Scenario Creation Wizard
Risk Level: {risk_level}
Components: {', '.join(components) if components else 'None'}
"""
    
    # Save scenario
    print("\n✅ Scenario generated successfully!\n")
    
    save = get_yes_no("Save scenario to file?", True)
    
    if save:
        default_filename = name.lower().replace(" ", "_") + ".txt"
        filename = get_input("Filename", default_filename)
        
        output_dir = Path(__file__).parent / "fixtures" / "custom_scenarios"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(scenario_content)
        
        print(f"\n✅ Scenario saved to: {output_path}\n")
        
        # Generate Python code
        print("Python code to use this scenario:")
        print("-" * 40)
        print(f"""
# Import validation tools
from tests.validation_report_generator import validate_scenario

# Read custom scenario
with open('{output_path}', 'r', encoding='utf-8') as f:
    content = f.read()

# Validate scenario
metrics = validate_scenario(
    scenario_name="{name}",
    document_content=content,
    document_type="{doc_type}",
    expected_tranches={num_tranches if has_cap_structure else 0},
)

# Check results
if metrics.success:
    print("✅ Validation passed!")
    if metrics.ebitda_found:
        print(f"EBITDA Risk: {{metrics.ebitda_risk_score:.1f}}/10.0")
    if metrics.lme_risks_found > 0:
        print(f"LME Risks: {{metrics.lme_risks_found}}")
else:
    print(f"❌ Validation failed: {{metrics.error_message}}")
        """)
        print("-" * 40)
    
    else:
        print("\nScenario content:")
        print("-" * 80)
        print(scenario_content)
        print("-" * 80)
    
    print("\n✅ Done!")


def main():
    """Main entry point."""
    try:
        create_scenario()
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Scenario creation cancelled")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

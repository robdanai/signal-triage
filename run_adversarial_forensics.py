"""
Run adversarial forensics on sample covenant document and generate JSON report.
"""

import json
from pathlib import Path
from signal_triage.adversarial_forensics import perform_adversarial_forensics


def main():
    # Read sample covenant document
    covenant_path = Path("sample_covenant.txt")
    
    if not covenant_path.exists():
        print(f"ERROR: {covenant_path} not found")
        return
    
    with open(covenant_path, "r") as f:
        covenant_text = f.read()
    
    print("=" * 80)
    print("ADVERSARIAL FORENSICS: Deep-Needle Analysis")
    print("=" * 80)
    print(f"\nAnalyzing: {covenant_path}")
    print(f"Document length: {len(covenant_text)} characters\n")
    
    # Perform forensics
    print("Running adversarial forensics...")
    report = perform_adversarial_forensics(covenant_text, ica_text=None)
    
    # Print executive summary
    print("\n" + "=" * 80)
    print(report.executive_summary)
    print("=" * 80)
    
    # Print detailed findings
    print("\n\n" + "=" * 80)
    print("DETAILED FINDINGS")
    print("=" * 80)
    
    print(f"\n### AMENDMENT PROVISIONS ({len(report.amendment_provisions)} found)")
    print("-" * 80)
    for i, ap in enumerate(report.amendment_provisions, 1):
        print(f"\n{i}. {ap.provision_type.upper()} - {ap.subject_matter}")
        print(f"   Risk: {ap.exploit_risk.value.upper()}")
        print(f"   Vote Threshold: {ap.vote_threshold}")
        print(f"   Section: {ap.section_number or 'N/A'}")
        print(f"   Exploitation Mechanics: {ap.exploitation_mechanics}")
        if ap.serta_incora_precedent:
            print(f"   ⚠️  Precedent: {ap.serta_incora_precedent}")
        print(f"   Evidence: {ap.evidence_snippet[:150]}...")
    
    print(f"\n\n### PRO RATA PROVISIONS ({len(report.pro_rata_provisions)} found)")
    print("-" * 80)
    for i, pr in enumerate(report.pro_rata_provisions, 1):
        print(f"\n{i}. Pro Rata Sharing Analysis")
        print(f"   Risk: {pr.exploit_risk.value.upper()}")
        print(f"   Pro Rata Required: {pr.pro_rata_required}")
        print(f"   Exceptions: {', '.join(pr.exceptions) if pr.exceptions else 'None'}")
        print(f"   Yank-a-Bank Present: {pr.yank_a_bank_present}")
        print(f"   Snooze You Lose: {pr.snooze_you_lose_language}")
        print(f"   Exploitation Mechanics: {pr.exploitation_mechanics}")
        print(f"   Evidence: {pr.evidence_snippet[:150]}...")
    
    print(f"\n\n### GUARANTOR RELEASE TRIGGERS ({len(report.guarantor_release_triggers)} found)")
    print("-" * 80)
    for i, gt in enumerate(report.guarantor_release_triggers, 1):
        print(f"\n{i}. {gt.trigger_type}")
        print(f"   Risk: {gt.exploit_risk.value.upper()}")
        print(f"   Vote Requirement: {gt.vote_requirement}")
        print(f"   Automatic Release: {gt.automatic_release}")
        print(f"   J.Crew Blocker Present: {gt.jcrew_blocker_present}")
        print(f"   Exploitation Mechanics: {gt.exploitation_mechanics}")
        print(f"   Evidence: {gt.evidence_snippet[:150]}...")
    
    print(f"\n\n### INTERCREDITOR GAPS ({len(report.intercreditor_gaps)} found)")
    print("-" * 80)
    for i, ig in enumerate(report.intercreditor_gaps, 1):
        print(f"\n{i}. {ig.gap_type.replace('_', ' ').title()}")
        print(f"   Risk: {ig.exploit_risk.value.upper()}")
        print(f"   Conflict: {ig.conflict_description}")
        print(f"   Exploitation Mechanics: {ig.exploitation_mechanics}")
        print(f"   Credit Agreement: {ig.credit_agreement_provision[:100]}...")
    
    # Generate JSON output
    print("\n\n" + "=" * 80)
    print("GENERATING JSON REPORT")
    print("=" * 80)
    
    json_output = report.to_dict()
    output_path = Path("adversarial_forensics_report.json")
    
    with open(output_path, "w") as f:
        json.dump(json_output, f, indent=2)
    
    print(f"\n✓ JSON report saved to: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Overall Exploit Risk: {report.overall_exploit_risk.value.upper()}")
    print(f"Serta/Incora Risk Score: {report.serta_incora_risk_score}/100")
    print(f"Total Findings: {len(report.amendment_provisions) + len(report.pro_rata_provisions) + len(report.guarantor_release_triggers) + len(report.intercreditor_gaps)}")
    print(f"  - Amendment Provisions: {len(report.amendment_provisions)}")
    print(f"  - Pro Rata Provisions: {len(report.pro_rata_provisions)}")
    print(f"  - Guarantor Release Triggers: {len(report.guarantor_release_triggers)}")
    print(f"  - Intercreditor Gaps: {len(report.intercreditor_gaps)}")
    
    # Risk breakdown
    all_risks = (
        [a.exploit_risk for a in report.amendment_provisions] +
        [p.exploit_risk for p in report.pro_rata_provisions] +
        [g.exploit_risk for g in report.guarantor_release_triggers] +
        [i.exploit_risk for i in report.intercreditor_gaps]
    )
    
    print(f"\nRisk Breakdown:")
    print(f"  - CRITICAL: {sum(1 for r in all_risks if r.value == 'critical')}")
    print(f"  - HIGH: {sum(1 for r in all_risks if r.value == 'high')}")
    print(f"  - MEDIUM: {sum(1 for r in all_risks if r.value == 'medium')}")
    print(f"  - LOW: {sum(1 for r in all_risks if r.value == 'low')}")
    
    print("\n" + "=" * 80)
    print("FORENSICS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

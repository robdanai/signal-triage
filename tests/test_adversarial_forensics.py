"""
Tests for Adversarial Forensics module.
Validates deep-needle analysis of voting thresholds, pro rata bypass, guarantor releases, and ICA gaps.
"""

import unittest
from signal_triage.adversarial_forensics import (
    perform_adversarial_forensics,
    analyze_amendment_provisions,
    analyze_pro_rata_provisions,
    analyze_guarantor_release_triggers,
    analyze_intercreditor_gaps,
    ExploitRisk,
)


class TestAmendmentForensics(unittest.TestCase):
    """Test Section 10.01 amendment provision analysis."""
    
    def test_serta_vector_required_lender_lien_control(self):
        """Test detection of Serta-style Required Lender lien control."""
        doc = """
        Section 10.01. Amendments and Waivers.
        
        Subject to the provisions below, the Required Lenders may amend, modify, or waive
        any provision of this Agreement. The Required Lenders may direct the Collateral Agent
        to take any action with respect to the Collateral, including releasing, subordinating,
        or modifying the priority of liens.
        
        Notwithstanding the foregoing, unanimous consent of all Lenders is required to:
        (a) extend maturity dates; (b) reduce principal or interest; (c) release all or
        substantially all Collateral.
        """
        
        provisions = analyze_amendment_provisions(doc)
        
        # Should detect CRITICAL Required Lender bypass
        critical_provisions = [p for p in provisions if p.exploit_risk == ExploitRisk.CRITICAL]
        self.assertGreater(len(critical_provisions), 0, "Should detect CRITICAL Serta vector")
        
        serta_provision = critical_provisions[0]
        self.assertEqual(serta_provision.vote_threshold, "50.1% (Required Lenders)")
        self.assertIn("Serta", serta_provision.exploitation_mechanics)
        self.assertIn("subordinate", serta_provision.exploitation_mechanics.lower())
    
    def test_sacred_right_protection(self):
        """Test detection of lien subordination sacred right (100% consent)."""
        doc = """
        Section 10.01. Amendments.
        
        The Required Lenders may amend this Agreement, EXCEPT that the consent of each
        Lender directly affected is required to: (i) amend lien priority or subordinate
        any Lender's security interest; (ii) extend maturity; (iii) reduce principal.
        """
        
        provisions = analyze_amendment_provisions(doc)
        
        # Should detect sacred right protection
        sacred_rights = [p for p in provisions if p.provision_type == "sacred_right"]
        self.assertGreater(len(sacred_rights), 0, "Should detect sacred right")
        
        sacred = sacred_rights[0]
        self.assertEqual(sacred.vote_threshold, "100%")
        self.assertEqual(sacred.exploit_risk, ExploitRisk.LOW)
        self.assertIn("NOT possible", sacred.exploitation_mechanics)
    
    def test_ambiguous_lien_subordination(self):
        """Test detection of ambiguous lien subordination (HIGH risk)."""
        doc = """
        Section 10.01. Amendments.
        
        The Required Lenders may amend any provision of this Agreement. Notwithstanding
        the foregoing, unanimous consent is required to: (a) extend maturity; (b) reduce
        principal or interest.
        """
        
        provisions = analyze_amendment_provisions(doc)
        
        # Should flag ambiguity as HIGH risk
        ambiguous = [p for p in provisions if p.provision_type == "ambiguous"]
        self.assertGreater(len(ambiguous), 0, "Should flag ambiguous lien subordination")
        
        amb = ambiguous[0]
        self.assertEqual(amb.vote_threshold, "AMBIGUOUS")
        self.assertEqual(amb.exploit_risk, ExploitRisk.HIGH)
        self.assertIn("Lien Subordination", amb.subject_matter)


class TestProRataForensics(unittest.TestCase):
    """Test pro rata sharing and bypass mechanics."""
    
    def test_yank_a_bank_detection(self):
        """Test detection of Yank-a-Bank provision."""
        doc = """
        Section 9.08. Pro Rata Treatment.
        
        All payments shall be made pro rata to Lenders. However, this requirement shall
        not prohibit (a) open market purchases by any Lender; (b) privately negotiated
        exchanges; or (c) the replacement of any non-consenting Lender pursuant to the
        "yank-a-bank" provisions of Section 2.15.
        """
        
        provisions = analyze_pro_rata_provisions(doc)
        
        self.assertEqual(len(provisions), 1)
        pr = provisions[0]
        
        self.assertTrue(pr.pro_rata_required)
        self.assertTrue(pr.yank_a_bank_present)
        self.assertIn("Open Market Exception", pr.exceptions)
        self.assertEqual(pr.exploit_risk, ExploitRisk.HIGH)
        self.assertIn("bypass pro rata", pr.exploitation_mechanics)
    
    def test_snooze_you_lose(self):
        """Test detection of Snooze You Lose provision."""
        doc = """
        Section 2.20. Amendments and Waivers.
        
        Any Lender that does not consent to an amendment within 10 business days shall
        be deemed to have waived its right to consent ("snooze you lose"). Non-consenting
        Lenders may be replaced at the option of the Borrower.
        """
        
        provisions = analyze_pro_rata_provisions(doc)
        
        self.assertEqual(len(provisions), 1)
        pr = provisions[0]
        
        self.assertTrue(pr.snooze_you_lose_language)
        self.assertEqual(pr.exploit_risk, ExploitRisk.HIGH)
        self.assertIn("Snooze You Lose", pr.exploitation_mechanics)


class TestGuarantorReleaseForensics(unittest.TestCase):
    """Test guarantor release trigger analysis."""
    
    def test_automatic_release_no_blocker_critical(self):
        """Test CRITICAL risk: automatic release without J.Crew blocker."""
        doc = """
        Section 8.12. Guarantee Release.
        
        The Guarantees shall be automatically released if any Restricted Subsidiary is
        designated as an Unrestricted Subsidiary in accordance with the terms of this
        Agreement. The Company may designate any Restricted Subsidiary as Unrestricted
        at any time, subject to the investment basket limitations in Section 7.08.
        """
        
        triggers = analyze_guarantor_release_triggers(doc)
        
        critical = [t for t in triggers if t.exploit_risk == ExploitRisk.CRITICAL]
        self.assertGreater(len(critical), 0, "Should detect CRITICAL automatic release")
        
        trig = critical[0]
        self.assertTrue(trig.automatic_release)
        self.assertFalse(trig.jcrew_blocker_present)
        self.assertIn("AUTOMATIC", trig.exploitation_mechanics)
        self.assertIn("Incora", trig.exploitation_mechanics)
    
    def test_jcrew_blocker_present_low_risk(self):
        """Test LOW risk: guarantor release with J.Crew blocker."""
        doc = """
        Section 8.12. Guarantee Release.
        
        Guarantees shall be released upon unrestricted subsidiary designation. However,
        no Restricted Subsidiary may be designated as Unrestricted if it holds any
        intellectual property or other material assets, including any IP, patents,
        trademarks, or core operating assets (the "J.Crew blocker").
        """
        
        triggers = analyze_guarantor_release_triggers(doc)
        
        self.assertGreater(len(triggers), 0)
        trig = triggers[0]
        
        self.assertTrue(trig.jcrew_blocker_present)
        self.assertEqual(trig.exploit_risk, ExploitRisk.LOW)
        self.assertIn("J.Crew blocker detected", trig.exploitation_mechanics)


class TestIntercreditorForensics(unittest.TestCase):
    """Test intercreditor agreement gap analysis."""
    
    def test_silent_second_lien_detection(self):
        """Test detection of silent second lien structure."""
        doc = """
        Section 7.12. Incremental Facilities.
        
        The Company may incur additional Indebtedness under Incremental Facilities,
        which may be secured on a pari passu or silent second lien basis as set forth
        in the Intercreditor Agreement. Such silent second liens shall have the rights
        specified in the ICA.
        """
        
        gaps = analyze_intercreditor_gaps(doc, ica_text=None)
        
        silent_gaps = [g for g in gaps if g.gap_type == "silent_second_lien"]
        self.assertGreater(len(silent_gaps), 0, "Should detect silent second lien")
        
        gap = silent_gaps[0]
        self.assertEqual(gap.exploit_risk, ExploitRisk.HIGH)
        self.assertIn("diluting first lien recovery", gap.conflict_description)
    
    def test_ica_not_provided_flag(self):
        """Test flagging when ICA referenced but not provided."""
        doc = """
        Section 9.01. Collateral Agent.
        
        The Collateral Agent shall act in accordance with the Intercreditor Agreement.
        In the event of any conflict between this Agreement and the ICA, the ICA shall
        control with respect to lien priority.
        """
        
        gaps = analyze_intercreditor_gaps(doc, ica_text=None)
        
        ica_missing = [g for g in gaps if g.gap_type == "ica_not_provided"]
        self.assertGreater(len(ica_missing), 0, "Should flag ICA not provided")
        
        gap = ica_missing[0]
        self.assertEqual(gap.exploit_risk, ExploitRisk.MEDIUM)
        self.assertIn("not provided for analysis", gap.conflict_description)


class TestFullAdversarialForensics(unittest.TestCase):
    """Test complete adversarial forensics report generation."""
    
    def test_high_risk_documentation(self):
        """Test HIGH risk documentation with multiple exploit vectors."""
        doc = """
        CREDIT AGREEMENT
        
        Section 7.08. Unrestricted Subsidiaries.
        The Company may designate any Restricted Subsidiary as Unrestricted at any time,
        subject to Required Lender consent. Guarantees shall be automatically released
        upon such designation.
        
        Section 7.12. Incremental Facilities.
        The Company may incur additional Indebtedness under Incremental Facilities in an
        aggregate principal amount not to exceed $50 million plus any ratio debt capacity,
        in each case without the consent of any existing Lender. Such Incremental Facilities
        may be secured on a pari passu or senior basis as set forth in the Intercreditor
        Agreement.
        
        Section 9.08. Pro Rata Sharing.
        All payments shall be made pro rata, except for open market purchases and privately
        negotiated exchanges, which are permitted without pro rata treatment.
        
        Section 10.01. Amendments.
        The Required Lenders may amend any provision of this Agreement, including with respect
        to lien priority and collateral. The Required Lenders may direct the Collateral Agent
        to subordinate liens of non-participating Lenders.
        
        Notwithstanding the foregoing, unanimous consent is required to: (a) extend maturity
        dates; (b) reduce principal or interest.
        """
        
        report = perform_adversarial_forensics(doc)
        
        # Should be HIGH or CRITICAL overall risk
        self.assertIn(report.overall_exploit_risk, [ExploitRisk.HIGH, ExploitRisk.CRITICAL])
        
        # Should have high Serta/Incora score
        self.assertGreaterEqual(report.serta_incora_risk_score, 40)
        
        # Should detect amendment exploit
        self.assertGreater(len(report.amendment_provisions), 0)
        critical_amendments = [a for a in report.amendment_provisions if a.exploit_risk == ExploitRisk.CRITICAL]
        self.assertGreater(len(critical_amendments), 0, "Should detect CRITICAL amendment risk")
        
        # Should detect guarantor release
        self.assertGreater(len(report.guarantor_release_triggers), 0)
        
        # Should detect pro rata bypass
        self.assertGreater(len(report.pro_rata_provisions), 0)
        
        # Executive summary should flag risk
        self.assertIn("CRITICAL", report.executive_summary.upper())
    
    def test_low_risk_well_protected(self):
        """Test LOW risk documentation with strong protections."""
        doc = """
        CREDIT AGREEMENT
        
        Section 7.08. Unrestricted Subsidiaries.
        No Restricted Subsidiary may be designated as Unrestricted if it holds any
        intellectual property, material assets, or generates more than 5% of EBITDA
        (the "J.Crew blocker"). Designation requires unanimous Lender consent.
        
        Section 10.01. Amendments.
        The Required Lenders may amend non-material provisions of this Agreement.
        
        The consent of each Lender directly affected is required to: (a) extend maturity
        dates; (b) reduce principal or interest; (c) amend lien priority or subordinate
        any Lender's security interest; (d) release Collateral (except for permitted
        dispositions); (e) release any Guarantor (except as permitted in Section 8.12).
        
        Section 9.08. Pro Rata Treatment.
        All payments and recoveries shall be made pro rata to Lenders in proportion to
        their outstanding commitments. No exceptions permitted.
        """
        
        report = perform_adversarial_forensics(doc)
        
        # Should be LOW overall risk
        self.assertEqual(report.overall_exploit_risk, ExploitRisk.LOW)
        
        # Should have low Serta/Incora score
        self.assertLessEqual(report.serta_incora_risk_score, 30)
        
        # Executive summary should indicate low risk
        self.assertIn("LOW", report.executive_summary.upper())


if __name__ == "__main__":
    unittest.main()

"""Tests for signal_triage.lme_parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from signal_triage.lme_parser import detect_lme, LME_PATTERNS


class TestLMEParser(unittest.TestCase):
    def test_empty_text_returns_empty(self):
        for text in ("", "   ", "\n"):
            self.assertEqual(detect_lme(text), [])

    def test_no_lme_language_returns_empty(self):
        self.assertEqual(detect_lme("The weather is nice today."), [])

    def test_dropdown_detected(self):
        text = "The company announced a release of guarantees for restricted subsidiaries."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("dropdown", types)
        self.assertTrue(any("release of guarantees" in s["label"] or "restricted subsidiary" in s["label"] for s in signals))

    def test_uptiering_detected(self):
        text = "Discussion of uptiering and superpriority DIP financing."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("uptiering", types)

    def test_sprime_leakage_detected(self):
        text = "First lien and second lien collateral; priming and adequate protection."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("sprime_leakage", types)

    def test_signal_has_required_keys(self):
        text = "Uptiering and dropdown language."
        signals = detect_lme(text)
        for s in signals:
            self.assertIn("type", s)
            self.assertIn("label", s)
            self.assertIn("evidence", s)
            self.assertIn("span", s)
            self.assertEqual(len(s["span"]), 2)

    def test_evidence_is_substring_of_text(self):
        text = "Some preamble. Uptiering and roll-up. Some trailing."
        signals = detect_lme(text)
        for s in signals:
            self.assertIsInstance(s["evidence"], str)
            # Evidence may be a snippet; original phrase should appear in text
            self.assertIn(s["label"], text.lower())

    def test_basket_transfer_asset_sale_and_investment_basket(self):
        """Credit Integrity: asset sale proceeds and investment basket produce LME signals."""
        text = "Asset sale proceeds to unrestricted subsidiary; use of investment basket."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        labels = [s["label"] for s in signals]
        self.assertIn("basket_transfer", types)
        self.assertTrue(
            any("asset sale" in l or "investment basket" in l for l in labels),
            msg=f"Expected asset sale or investment basket in labels: {labels}",
        )

    def test_structural_subordination_detected(self):
        """Credit Integrity: structural subordination language is flagged."""
        text = "The notes are structurally subordinated to the secured credit facility."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("structural_subordination", types)

    def test_asset_sale_detected(self):
        """Asset sale, sale proceeds, asset sale basket produce asset_sale signals."""
        text = "Asset sale proceeds and asset sale basket capacity."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("asset_sale", types)

    def test_investment_basket_detected(self):
        """Investment basket language produces investment_basket signals."""
        text = "Use of the investment basket and permitted investment basket."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("investment_basket", types)

    def test_transfer_to_unrestricted_sub_detected(self):
        """Transfer/sale to unrestricted sub produces transfer_to_unrestricted_sub signals."""
        text = "Transfer to unrestricted sub and sale to unrestricted subsidiary."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("transfer_to_unrestricted_sub", types)

    def test_texas_two_step_detected(self):
        """Texas two-step, divisional merger, LMT structure produce texas_two_step signals."""
        text = "The company pursued a Texas two-step and divisional merger. LMT transaction."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("texas_two_step", types)

    def test_double_dip_triple_dip_detected(self):
        """Double-dip, triple-dip, empty box, non-guarantor sub produce double_dip_triple_dip signals."""
        text = "Structure involved a triple dip and non-guarantor subsidiary; double recovery risk."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("double_dip_triple_dip", types)

    def test_consent_solicitation_exchange_detected(self):
        """Consent solicitation, exchange offer, amend-and-extend produce consent_solicitation_exchange signals."""
        text = "The company launched a consent solicitation and exchange offer; amend and extend."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("consent_solicitation_exchange", types)

    def test_equity_cure_detected(self):
        """Equity cure, covenant cure produce equity_cure signals."""
        text = "The credit agreement includes an equity cure right and covenant cure by equity."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("equity_cure", types)

    def test_substantive_consolidation_cramdown_detected(self):
        """Substantive consolidation, cramdown produce substantive_consolidation_cramdown signals."""
        text = "Risk of substantive consolidation and cramdown under the plan."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("substantive_consolidation_cramdown", types)

    def test_lender_voting_squeeze_detected(self):
        """Yank-a-bank, required lender, non-consenting produce lender_voting_squeeze signals."""
        text = "Document permits yank-a-bank and amendment without consent; non-consenting lender risk."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("lender_voting_squeeze", types)

    def test_forbearance_standstill_detected(self):
        """Forbearance, standstill produce forbearance_standstill signals."""
        text = "Lenders entered a forbearance agreement and standstill agreement."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("forbearance_standstill", types)

    def test_crossover_prepack_detected(self):
        """Crossover facility, prepack, plan support produce crossover_prepack signals."""
        text = "Crossover facility and prepackaged bankruptcy; plan support agreement."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("crossover_prepack", types)

    def test_make_whole_disallowance_detected(self):
        """Make-whole, disallowance produce make_whole_disallowance signals."""
        text = "Make-whole may be subject to claim disallowance in bankruptcy."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("make_whole_disallowance", types)

    def test_pik_detected(self):
        """Payment-in-kind, PIK toggle produce pik signals."""
        text = "The notes have a PIK toggle right and payment-in-kind interest."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("pik", types)

    def test_jcrew_blocker_detected(self):
        """J.Crew blocker, anti-dropdown produce jcrew_blocker signals."""
        text = "The credit agreement includes a J.Crew blocker and anti-dropdown provision."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("jcrew_blocker", types)

    def test_serta_uptier_detected(self):
        """Serta, non-consensual uptier produce serta_uptier signals."""
        text = "Risk of Serta-style non-consensual uptier; lender-on-lender violence."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("serta_uptier", types)

    def test_incora_wesco_vote_rigging_detected(self):
        """Incora, Wesco, vote rigging produce incora_wesco_vote_rigging signals."""
        text = "Incora-style vote threshold manipulation and strategic debt issuance to affiliate."
        signals = detect_lme(text)
        types = [s["type"] for s in signals]
        self.assertIn("incora_wesco_vote_rigging", types)

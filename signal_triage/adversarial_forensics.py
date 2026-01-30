"""
Adversarial Forensics: Deep-Needle Analysis for Voting Threshold Exploits.

Identifies provisions that enable majority lender groups (50.1%) to weaponize credit
documentation through:
- Non-consensual uptiers (Serta/Rite Aid)
- Guarantor stripping (Incora/Wesco)
- Pro rata bypass (Yank-a-Bank)
- Intercreditor conflicts (silent second lien)

This module performs forensic analysis of amendment provisions, voting thresholds,
guarantor release mechanics, and intercreditor agreement gaps to identify creditor-
on-creditor violence vectors.
"""

import re
from typing import Any
from dataclasses import dataclass, field
from enum import Enum


class ExploitRisk(str, Enum):
    """Severity of exploitation risk."""
    CRITICAL = "critical"  # Direct Serta/Incora vector present
    HIGH = "high"  # Multiple gaps enable sophisticated attack
    MEDIUM = "medium"  # Some gaps present, harder to exploit
    LOW = "low"  # Well-protected documentation


@dataclass
class AmendmentProvision:
    """Parsed amendment/voting provision with exploit assessment."""
    section_number: str | None
    page_number: int | None
    provision_type: str  # "sacred_right" | "required_lender" | "unanimous_consent"
    vote_threshold: str  # "100%", "50.1%", "66.67%", etc.
    subject_matter: str  # "Lien Subordination", "Payment Terms", "Collateral Release"
    evidence_snippet: str
    exploit_risk: ExploitRisk
    exploitation_mechanics: str  # How this could be weaponized
    serta_incora_precedent: str | None = None  # Reference to case if applicable


@dataclass
class ProRataProvision:
    """Pro rata sharing and bypass mechanics."""
    section_number: str | None
    page_number: int | None
    pro_rata_required: bool
    exceptions: list[str]  # "open market purchases", "exchange offers", etc.
    yank_a_bank_present: bool
    snooze_you_lose_language: bool
    evidence_snippet: str
    exploit_risk: ExploitRisk
    exploitation_mechanics: str


@dataclass
class GuarantorReleaseTrigger:
    """Conditions under which subsidiary guarantees can be released."""
    section_number: str | None
    page_number: int | None
    trigger_type: str  # "unrestricted_designation" | "asset_sale" | "automatic" | "springing"
    vote_requirement: str  # "None", "Required Lender", "Unanimous"
    automatic_release: bool
    jcrew_blocker_present: bool  # Anti-dropdown language
    evidence_snippet: str
    exploit_risk: ExploitRisk
    exploitation_mechanics: str


@dataclass
class IntercreditorGap:
    """Conflicts between Credit Agreement and Intercreditor Agreement."""
    gap_type: str  # "lien_subordination_conflict" | "silent_second" | "amendment_authority"
    credit_agreement_provision: str
    ica_provision: str | None
    conflict_description: str
    exploit_risk: ExploitRisk
    exploitation_mechanics: str


@dataclass
class AdversarialForensicsReport:
    """Complete forensic report on exploitation vectors."""
    overall_exploit_risk: ExploitRisk
    amendment_provisions: list[AmendmentProvision] = field(default_factory=list)
    pro_rata_provisions: list[ProRataProvision] = field(default_factory=list)
    guarantor_release_triggers: list[GuarantorReleaseTrigger] = field(default_factory=list)
    intercreditor_gaps: list[IntercreditorGap] = field(default_factory=list)
    executive_summary: str = ""
    serta_incora_risk_score: int = 0  # 0-100: likelihood of uptier/stripping
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_exploit_risk": self.overall_exploit_risk.value,
            "serta_incora_risk_score": self.serta_incora_risk_score,
            "executive_summary": self.executive_summary,
            "amendment_provisions": [
                {
                    "section_number": ap.section_number,
                    "page_number": ap.page_number,
                    "provision_type": ap.provision_type,
                    "vote_threshold": ap.vote_threshold,
                    "subject_matter": ap.subject_matter,
                    "evidence_snippet": ap.evidence_snippet,
                    "exploit_risk": ap.exploit_risk.value,
                    "exploitation_mechanics": ap.exploitation_mechanics,
                    "serta_incora_precedent": ap.serta_incora_precedent,
                }
                for ap in self.amendment_provisions
            ],
            "pro_rata_provisions": [
                {
                    "section_number": pr.section_number,
                    "page_number": pr.page_number,
                    "pro_rata_required": pr.pro_rata_required,
                    "exceptions": pr.exceptions,
                    "yank_a_bank_present": pr.yank_a_bank_present,
                    "snooze_you_lose_language": pr.snooze_you_lose_language,
                    "evidence_snippet": pr.evidence_snippet,
                    "exploit_risk": pr.exploit_risk.value,
                    "exploitation_mechanics": pr.exploitation_mechanics,
                }
                for pr in self.pro_rata_provisions
            ],
            "guarantor_release_triggers": [
                {
                    "section_number": gt.section_number,
                    "page_number": gt.page_number,
                    "trigger_type": gt.trigger_type,
                    "vote_requirement": gt.vote_requirement,
                    "automatic_release": gt.automatic_release,
                    "jcrew_blocker_present": gt.jcrew_blocker_present,
                    "evidence_snippet": gt.evidence_snippet,
                    "exploit_risk": gt.exploit_risk.value,
                    "exploitation_mechanics": gt.exploitation_mechanics,
                }
                for gt in self.guarantor_release_triggers
            ],
            "intercreditor_gaps": [
                {
                    "gap_type": ig.gap_type,
                    "credit_agreement_provision": ig.credit_agreement_provision,
                    "ica_provision": ig.ica_provision,
                    "conflict_description": ig.conflict_description,
                    "exploit_risk": ig.exploit_risk.value,
                    "exploitation_mechanics": ig.exploitation_mechanics,
                }
                for ig in self.intercreditor_gaps
            ],
        }


# ==================== FORENSIC PATTERNS ====================

# Section 10.01 Amendment Patterns
AMENDMENT_SECTION_PATTERNS = [
    r"Section\s+10\.01\s*[:\.]?\s*Amendments?",
    r"Article\s+(?:X|10)\s*[:\.]?\s*Amendments?",
    r"Amendments?\s+and\s+Waivers?",
    r"Amendment\s+Provisions?",
]

# Sacred Rights (require 100% consent)
SACRED_RIGHT_PATTERNS = [
    (r"sacred\s+right", "explicit_sacred_right"),
    (r"unanimous\s+consent.*(?:lien|priority|payment|maturity|principal|interest)", "unanimous_required"),
    (r"consent\s+of\s+(?:each|every|all)\s+lender.*(?:lien|subordination|payment)", "each_lender_consent"),
    (r"(?:lien|security\s+interest).*priority.*(?:may\s+not|cannot|shall\s+not).*without.*(?:unanimous|consent\s+of\s+each)", "lien_subordination_protected"),
]

# Required Lender Bypass (50.1% can override)
REQUIRED_LENDER_BYPASS_PATTERNS = [
    (r"required\s+lender(?:s)?\s+(?:may|can|shall\s+be\s+entitled\s+to).*(?:amend|modify|consent).*(?:lien|priority|collateral)", "required_lender_lien_control"),
    (r"(?:50|51|majority)\s*%.*(?:may\s+)?(?:amend|modify|direct).*(?:lien|collateral|security)", "majority_lien_control"),
    (r"lender[- ]?directed\s+collateral\s+agent", "lender_directed_agent"),
    (r"required\s+lender(?:s)?.*(?:may\s+)?(?:direct|instruct).*collateral\s+agent", "required_lender_agent_direction"),
    (r"collateral\s+agent.*(?:shall\s+)?(?:act|take\s+direction)\s+(?:at\s+the\s+)?(?:instruction|direction)\s+of.*required\s+lender", "agent_follows_required_lenders"),
]

# Pro Rata Sharing Patterns
PRO_RATA_SHARING_PATTERNS = [
    (r"pro\s+rata\s+(?:share|sharing|basis|distribution)", "pro_rata_sharing"),
    (r"share\s+(?:ratably|pro\s+rata|pari\s+passu)", "ratable_sharing"),
    (r"each\s+lender.*(?:entitled|receive).*(?:pro\s+rata|ratable|proportionate)\s+share", "proportionate_sharing"),
]

# Pro Rata Exceptions (non-pro-rata treatment allowed)
PRO_RATA_EXCEPTION_PATTERNS = [
    (r"open\s+market\s+purchase", "open_market_exception"),
    (r"privately\s+negotiated.*(?:purchase|exchange|transaction)", "private_negotiation_exception"),
    (r"dutch\s+auction", "dutch_auction_exception"),
    (r"exchange\s+offer", "exchange_offer_exception"),
    (r"tender\s+offer", "tender_offer_exception"),
    (r"non[- ]?consenting\s+lender", "non_consenting_lender"),
    (r"yank[- ]?a[- ]?bank", "yank_a_bank"),
    (r"snooze\s+you\s+lose|snooze[- ]?you[- ]?lose", "snooze_you_lose"),
    (r"replaceable\s+lender", "replaceable_lender"),
]

# Guarantor Release Triggers
GUARANTOR_RELEASE_PATTERNS = [
    (r"release\s+of\s+guarantee(?:s)?.*(?:upon|when|if|in\s+the\s+event)", "conditional_release"),
    (r"guarantee(?:s)?\s+(?:shall\s+be\s+)?(?:automatically\s+)?released?", "automatic_release"),
    (r"unrestricted\s+subsidiary.*release", "unrestricted_designation_release"),
    (r"(?:cease|ceases)\s+to\s+be\s+(?:a\s+)?(?:restricted\s+)?subsidiary.*release", "subsidiary_designation_release"),
    (r"guarantor.*released.*(?:upon|if|when).*(?:asset\s+sale|disposition|transfer)", "asset_sale_release"),
    (r"springing\s+guarantee", "springing_guarantee"),
]

# J.Crew Blocker (anti-dropdown protection)
JCREW_BLOCKER_PATTERNS = [
    (r"j\.?\s*crew\s+blocker", "explicit_jcrew_blocker"),
    (r"(?:intellectual\s+property|IP).*(?:may\s+not|cannot|shall\s+not).*(?:transfer|convey).*unrestricted", "ip_transfer_blocker"),
    (r"material\s+assets?.*(?:prohibited|may\s+not).*unrestricted\s+subsidiary", "material_asset_blocker"),
    (r"anti[- ]?dropdown", "anti_dropdown"),
]

# Intercreditor Agreement Patterns
INTERCREDITOR_PATTERNS = [
    (r"intercreditor\s+agreement", "ica_reference"),
    (r"lien\s+(?:priority|subordination).*(?:intercreditor|ICA)", "lien_priority_ica"),
    (r"silent\s+second(?:\s+lien)?", "silent_second_lien"),
    (r"(?:first\s+lien|senior).*subordinated\s+to.*(?:by|pursuant\s+to).*intercreditor", "ica_subordination"),
    (r"collateral\s+agent.*(?:authority|power|right).*(?:conflicting|inconsistent).*intercreditor", "ica_conflict_language"),
]


def analyze_amendment_provisions(text: str) -> list[AmendmentProvision]:
    """
    Forensic analysis of Section 10.01 (Amendment) provisions.
    
    Identifies:
    - Sacred Rights (100% consent required)
    - Required Lender bypass (50.1% can amend lien priority)
    - Lender-directed collateral agent language
    
    Returns list of AmendmentProvision with exploit risk assessment.
    """
    provisions = []
    text_lower = text.lower()
    
    # Find Section 10.01 or Amendment section
    section_match = None
    section_number = None
    for pattern in AMENDMENT_SECTION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            section_match = match
            section_number = "10.01" if "10.01" in match.group(0) else "Article X"
            break
    
    # If no Section 10.01 found, still search entire document
    search_text = text[section_match.end():section_match.end() + 5000] if section_match else text
    
    # Check for Sacred Rights (100% consent protections)
    sacred_rights_found = []
    for pattern, label in SACRED_RIGHT_PATTERNS:
        for match in re.finditer(pattern, search_text, re.IGNORECASE):
            start = max(0, match.start() - 100)
            end = min(len(search_text), match.end() + 200)
            snippet = search_text[start:end].strip()
            
            # Determine subject matter
            subject = "Unknown"
            if re.search(r"lien|priority|security|collateral", snippet, re.IGNORECASE):
                subject = "Lien Subordination / Priority"
            elif re.search(r"payment|principal|interest|maturity", snippet, re.IGNORECASE):
                subject = "Payment Terms"
            elif re.search(r"release|guarantee", snippet, re.IGNORECASE):
                subject = "Guarantee Release"
            
            sacred_rights_found.append((label, subject, snippet))
            
            provisions.append(AmendmentProvision(
                section_number=section_number,
                page_number=None,  # Would need PDF parsing
                provision_type="sacred_right",
                vote_threshold="100%",
                subject_matter=subject,
                evidence_snippet=snippet[:300],
                exploit_risk=ExploitRisk.LOW,
                exploitation_mechanics="Protected by unanimous consent requirement; Serta-style uptier NOT possible on this subject matter.",
                serta_incora_precedent=None,
            ))
    
    # Check for Required Lender Bypass (CRITICAL RISK)
    for pattern, label in REQUIRED_LENDER_BYPASS_PATTERNS:
        for match in re.finditer(pattern, search_text, re.IGNORECASE):
            start = max(0, match.start() - 100)
            end = min(len(search_text), match.end() + 200)
            snippet = search_text[start:end].strip()
            
            # This is a CRITICAL exploit vector
            provisions.append(AmendmentProvision(
                section_number=section_number,
                page_number=None,
                provision_type="required_lender",
                vote_threshold="50.1% (Required Lenders)",
                subject_matter="Lien Priority / Collateral Direction",
                evidence_snippet=snippet[:300],
                exploit_risk=ExploitRisk.CRITICAL,
                exploitation_mechanics="Serta-style attack vector: Required Lenders (50.1%) can amend lien priority or direct collateral agent to subordinate non-participating lenders. Minority lenders can be primed without consent.",
                serta_incora_precedent="Serta Simmons (2020), Rite Aid (2020)",
            ))
    
    # If NO sacred rights on lien subordination AND no explicit Required Lender bypass found,
    # flag as HIGH risk (ambiguity exploitable)
    lien_subordination_protected = any(
        "Lien Subordination" in sr[1] for sr in sacred_rights_found
    )
    required_lender_bypass_found = any(
        p.provision_type == "required_lender" for p in provisions
    )
    
    if not lien_subordination_protected and not required_lender_bypass_found:
        provisions.append(AmendmentProvision(
            section_number=section_number,
            page_number=None,
            provision_type="ambiguous",
            vote_threshold="AMBIGUOUS",
            subject_matter="Lien Subordination",
            evidence_snippet="No explicit sacred right protection for lien subordination; no explicit Required Lender override detected. Ambiguity creates exploit risk.",
            exploit_risk=ExploitRisk.HIGH,
            exploitation_mechanics="Lien subordination consent threshold AMBIGUOUS. In litigation, Required Lenders may argue they can amend lien priority under general amendment provisions. Recommend explicit 100% consent requirement.",
            serta_incora_precedent="Similar ambiguity exploited in Serta Simmons (2020)",
        ))
    
    return provisions


def analyze_pro_rata_provisions(text: str) -> list[ProRataProvision]:
    """
    Forensic analysis of pro rata sharing provisions and exceptions.
    
    Identifies:
    - Pro rata sharing requirements
    - Open market purchase / private negotiation exceptions
    - Yank-a-Bank / Snooze You Lose provisions
    
    Returns list of ProRataProvision with exploit assessment.
    """
    provisions = []
    text_lower = text.lower()
    
    # Find pro rata sharing language
    pro_rata_found = False
    pro_rata_snippet = None
    for pattern, label in PRO_RATA_SHARING_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            pro_rata_found = True
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 150)
            pro_rata_snippet = text[start:end].strip()
            break
    
    # Find exceptions
    exceptions = []
    yank_a_bank = False
    snooze_you_lose = False
    
    for pattern, label in PRO_RATA_EXCEPTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            exceptions.append(label.replace("_", " ").title())
            if "yank" in label:
                yank_a_bank = True
            if "snooze" in label:
                snooze_you_lose = True
    
    if pro_rata_found or exceptions:
        # Assess risk
        if len(exceptions) >= 3 or yank_a_bank or snooze_you_lose:
            risk = ExploitRisk.HIGH
            mechanics = f"Pro rata sharing has {len(exceptions)} exception(s): {', '.join(exceptions)}. Majority lenders can bypass pro rata treatment through open market purchases or exchange offers, accumulating strategic blocking position."
            if yank_a_bank:
                mechanics += " 'Yank-a-Bank' provision allows removal of non-consenting lenders."
            if snooze_you_lose:
                mechanics += " 'Snooze You Lose' provision penalizes non-participating lenders."
        elif len(exceptions) > 0:
            risk = ExploitRisk.MEDIUM
            mechanics = f"Pro rata sharing has {len(exceptions)} exception(s): {', '.join(exceptions)}. Some bypass mechanisms present."
        else:
            risk = ExploitRisk.LOW
            mechanics = "Pro rata sharing required; no significant exceptions detected."
        
        provisions.append(ProRataProvision(
            section_number=None,  # Pro rata often in multiple sections
            page_number=None,
            pro_rata_required=pro_rata_found,
            exceptions=exceptions,
            yank_a_bank_present=yank_a_bank,
            snooze_you_lose_language=snooze_you_lose,
            evidence_snippet=pro_rata_snippet[:300] if pro_rata_snippet else "Exceptions found but no base pro rata provision detected",
            exploit_risk=risk,
            exploitation_mechanics=mechanics,
        ))
    
    return provisions


def analyze_guarantor_release_triggers(text: str) -> list[GuarantorReleaseTrigger]:
    """
    Forensic analysis of subsidiary guarantee release mechanics.
    
    Identifies:
    - Unrestricted Subsidiary designation triggers
    - Automatic release conditions
    - J.Crew blocker presence (anti-dropdown protection)
    
    Returns list of GuarantorReleaseTrigger with exploit assessment.
    """
    triggers = []
    text_lower = text.lower()
    
    # Check for guarantor release triggers
    for pattern, label in GUARANTOR_RELEASE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 200)
            snippet = text[start:end].strip()
            
            # Determine trigger type
            trigger_type = label.replace("_", " ").title()
            
            # Check if automatic
            automatic = "automatic" in snippet.lower()
            
            # Check vote requirement
            vote_req = "None (Automatic)"
            if re.search(r"required\s+lender(?:s)?.*consent", snippet, re.IGNORECASE):
                vote_req = "Required Lenders"
            elif re.search(r"(?:all|each|every|unanimous).*lender.*consent", snippet, re.IGNORECASE):
                vote_req = "Unanimous"
            elif not automatic:
                vote_req = "UNCLEAR"
            
            # Check for J.Crew blocker
            jcrew_blocker = False
            for blocker_pattern, _ in JCREW_BLOCKER_PATTERNS:
                if re.search(blocker_pattern, text, re.IGNORECASE):
                    jcrew_blocker = True
                    break
            
            # Assess risk
            if automatic and not jcrew_blocker:
                risk = ExploitRisk.CRITICAL
                mechanics = "Guarantor release is AUTOMATIC upon unrestricted subsidiary designation. NO J.Crew blocker detected. Company can strip guarantees and transfer material assets (including IP) to unrestricted subsidiaries without lender consent. Classic Incora/J.Crew attack vector."
            elif "unrestricted" in label and not jcrew_blocker:
                risk = ExploitRisk.HIGH
                mechanics = f"Guarantor release triggered by unrestricted subsidiary designation (vote requirement: {vote_req}). NO J.Crew blocker detected for material assets/IP. Guarantor stripping risk present."
            elif jcrew_blocker:
                risk = ExploitRisk.LOW
                mechanics = f"Guarantor release present but J.Crew blocker detected. Material assets and IP transfers to unrestricted subsidiaries are blocked. Vote requirement: {vote_req}."
            else:
                risk = ExploitRisk.MEDIUM
                mechanics = f"Guarantor release trigger: {trigger_type}. Vote requirement: {vote_req}. Review conditions carefully."
            
            triggers.append(GuarantorReleaseTrigger(
                section_number=None,
                page_number=None,
                trigger_type=trigger_type,
                vote_requirement=vote_req,
                automatic_release=automatic,
                jcrew_blocker_present=jcrew_blocker,
                evidence_snippet=snippet[:300],
                exploit_risk=risk,
                exploitation_mechanics=mechanics,
            ))
    
    return triggers


def analyze_intercreditor_gaps(credit_agreement_text: str, ica_text: str | None = None) -> list[IntercreditorGap]:
    """
    Forensic analysis of conflicts between Credit Agreement and Intercreditor Agreement.
    
    Identifies:
    - Lien subordination conflicts
    - Silent second lien structures
    - Amendment authority conflicts
    
    Returns list of IntercreditorGap with exploit assessment.
    """
    gaps = []
    
    # Find ICA references in Credit Agreement
    ica_mentioned = bool(re.search(r"intercreditor\s+agreement", credit_agreement_text, re.IGNORECASE))
    
    if ica_mentioned:
        # Check for lien priority references
        ca_lien_provisions = []
        for pattern, label in INTERCREDITOR_PATTERNS:
            for match in re.finditer(pattern, credit_agreement_text, re.IGNORECASE):
                start = max(0, match.start() - 80)
                end = min(len(credit_agreement_text), match.end() + 120)
                snippet = credit_agreement_text[start:end].strip()
                ca_lien_provisions.append((label, snippet))
        
        # Flag potential conflicts
        for label, snippet in ca_lien_provisions:
            if "silent_second" in label:
                gaps.append(IntercreditorGap(
                    gap_type="silent_second_lien",
                    credit_agreement_provision=snippet[:200],
                    ica_provision=None,
                    conflict_description="Credit Agreement references 'silent second lien' structure. This allows junior lenders to appear as senior creditors in bankruptcy, diluting first lien recovery.",
                    exploit_risk=ExploitRisk.HIGH,
                    exploitation_mechanics="Silent second lien structures create ambiguity in lien priority during bankruptcy. First lien lenders may face unexpected dilution. Confirm ICA explicitly subordinates silent second liens.",
                ))
            elif "ica_conflict" in label:
                gaps.append(IntercreditorGap(
                    gap_type="amendment_authority_conflict",
                    credit_agreement_provision=snippet[:200],
                    ica_provision=None,
                    conflict_description="Credit Agreement contains language suggesting potential conflict between collateral agent authority and intercreditor agreement.",
                    exploit_risk=ExploitRisk.MEDIUM,
                    exploitation_mechanics="Conflicting amendment authority between Credit Agreement and ICA can be exploited in distressed scenarios. Majority lenders may argue Credit Agreement provisions override ICA restrictions.",
                ))
        
        # If ICA text not provided, flag for review
        if not ica_text:
            gaps.append(IntercreditorGap(
                gap_type="ica_not_provided",
                credit_agreement_provision="Credit Agreement references Intercreditor Agreement",
                ica_provision=None,
                conflict_description="Intercreditor Agreement referenced but not provided for analysis. Cannot confirm lien priority protections.",
                exploit_risk=ExploitRisk.MEDIUM,
                exploitation_mechanics="ICA must be reviewed to confirm: (1) lien subordination is absolute; (2) no silent second lien carveouts; (3) amendment authority doesn't conflict with Credit Agreement Required Lender provisions.",
            ))
    
    return gaps


def perform_adversarial_forensics(
    credit_agreement_text: str,
    ica_text: str | None = None,
) -> AdversarialForensicsReport:
    """
    Complete adversarial forensics analysis: Deep-Needle search for Serta/Incora vectors.
    
    Args:
        credit_agreement_text: Full text of Credit Agreement
        ica_text: Optional full text of Intercreditor Agreement
    
    Returns:
        AdversarialForensicsReport with all identified exploit vectors and risk scoring.
    """
    # Run all forensic analyses
    amendments = analyze_amendment_provisions(credit_agreement_text)
    pro_rata = analyze_pro_rata_provisions(credit_agreement_text)
    guarantor_releases = analyze_guarantor_release_triggers(credit_agreement_text)
    ica_gaps = analyze_intercreditor_gaps(credit_agreement_text, ica_text)
    
    # Calculate overall risk
    all_risks = (
        [a.exploit_risk for a in amendments] +
        [p.exploit_risk for p in pro_rata] +
        [g.exploit_risk for g in guarantor_releases] +
        [i.exploit_risk for i in ica_gaps]
    )
    
    critical_count = sum(1 for r in all_risks if r == ExploitRisk.CRITICAL)
    high_count = sum(1 for r in all_risks if r == ExploitRisk.HIGH)
    
    if critical_count >= 2:
        overall_risk = ExploitRisk.CRITICAL
    elif critical_count >= 1 or high_count >= 3:
        overall_risk = ExploitRisk.HIGH
    elif high_count >= 1:
        overall_risk = ExploitRisk.MEDIUM
    else:
        overall_risk = ExploitRisk.LOW
    
    # Calculate Serta/Incora risk score (0-100)
    serta_incora_score = 0
    
    # Amendment risks (+40 points)
    if any(a.exploit_risk == ExploitRisk.CRITICAL for a in amendments):
        serta_incora_score += 40
    elif any(a.exploit_risk == ExploitRisk.HIGH for a in amendments):
        serta_incora_score += 25
    
    # Guarantor release risks (+35 points)
    if any(g.exploit_risk == ExploitRisk.CRITICAL for g in guarantor_releases):
        serta_incora_score += 35
    elif any(g.exploit_risk == ExploitRisk.HIGH for g in guarantor_releases):
        serta_incora_score += 20
    
    # Pro rata bypass (+15 points)
    if any(p.yank_a_bank_present or p.snooze_you_lose_language for p in pro_rata):
        serta_incora_score += 15
    elif any(p.exploit_risk == ExploitRisk.HIGH for p in pro_rata):
        serta_incora_score += 10
    
    # ICA gaps (+10 points)
    if any(i.exploit_risk in (ExploitRisk.CRITICAL, ExploitRisk.HIGH) for i in ica_gaps):
        serta_incora_score += 10
    
    # Generate executive summary
    exec_summary = f"""
ADVERSARIAL FORENSICS EXECUTIVE SUMMARY

Overall Exploit Risk: {overall_risk.value.upper()}
Serta/Incora Risk Score: {serta_incora_score}/100

CRITICAL FINDINGS:
- Amendment Provisions: {len([a for a in amendments if a.exploit_risk == ExploitRisk.CRITICAL])} CRITICAL, {len([a for a in amendments if a.exploit_risk == ExploitRisk.HIGH])} HIGH risk
- Guarantor Releases: {len([g for g in guarantor_releases if g.exploit_risk == ExploitRisk.CRITICAL])} CRITICAL, {len([g for g in guarantor_releases if g.exploit_risk == ExploitRisk.HIGH])} HIGH risk
- Pro Rata Bypass: {len([p for p in pro_rata if p.yank_a_bank_present])} Yank-a-Bank provisions detected
- ICA Gaps: {len(ica_gaps)} potential conflicts identified

""".strip()
    
    if serta_incora_score >= 60:
        exec_summary += "\n\n🚨 HIGH LIKELIHOOD: This documentation contains multiple Serta/Incora-style exploit vectors. Majority lender group can likely execute non-consensual uptier and/or guarantor stripping."
    elif serta_incora_score >= 40:
        exec_summary += "\n\n⚠️  MODERATE LIKELIHOOD: This documentation has significant gaps that could enable sophisticated creditor-on-creditor attacks. Recommend immediate amendment to close loopholes."
    else:
        exec_summary += "\n\n✓ LOW LIKELIHOOD: Documentation appears reasonably well-protected against Serta/Incora-style attacks, though some gaps remain."
    
    return AdversarialForensicsReport(
        overall_exploit_risk=overall_risk,
        amendment_provisions=amendments,
        pro_rata_provisions=pro_rata,
        guarantor_release_triggers=guarantor_releases,
        intercreditor_gaps=ica_gaps,
        executive_summary=exec_summary,
        serta_incora_risk_score=serta_incora_score,
    )

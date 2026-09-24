"""EngiTrace AI — Canonical Compliance Rules Catalog (Phase 3)

Authoritative Source: docs/data_dictionary.md (Section 6: Compliance Rules)
"""

from dataclasses import dataclass
from typing import Dict
from backend.app.domain.models import FindingSeverity, TargetEntityType


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    name: str
    target_entity_type: str
    severity: str
    epistemic_category: str
    phase: int
    description: str
    remediation_guidance: str


# -----------------------------------------------------------------------------
# Canonical Catalog of 20 Compliance Rules
# -----------------------------------------------------------------------------

RULE_CATALOG: Dict[str, RuleDefinition] = {
    # Phase 1: Basic Requirements & Syntax (5 rules)
    "REQ-001": RuleDefinition(
        rule_id="REQ-001",
        name="Missing Engineering Rationale",
        target_entity_type=TargetEntityType.Requirement.value,
        severity=FindingSeverity.WARNING.value,
        epistemic_category="[Source-backed: ISO/IEC/IEEE 29148]",
        phase=1,
        description="Requirement rationale must be populated and contain at least 15 characters.",
        remediation_guidance="Provide technical engineering justification and origin for the requirement."
    ),
    "REQ-002": RuleDefinition(
        rule_id="REQ-002",
        name="Vague Requirement Language",
        target_entity_type=TargetEntityType.Requirement.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: INCOSE Rule R7]",
        phase=1,
        description="Requirement description must not contain non-verifiable or subjective terms (fast, adequate, minimize, sufficient, user-friendly, optimal).",
        remediation_guidance="Replace subjective terms with quantitative engineering tolerances and boundary conditions."
    ),
    "REQ-003": RuleDefinition(
        rule_id="REQ-003",
        name="Missing Verification Method",
        target_entity_type=TargetEntityType.Requirement.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: ISO/IEC/IEEE 29148]",
        phase=1,
        description="Requirement must specify a valid verification method (Analysis, Test, Inspection, Demonstration).",
        remediation_guidance="Select an authorized INCOSE verification method for the requirement."
    ),
    "REQ-004": RuleDefinition(
        rule_id="REQ-004",
        name="Compound Requirement Sentence",
        target_entity_type=TargetEntityType.Requirement.value,
        severity=FindingSeverity.WARNING.value,
        epistemic_category="[Source-backed: INCOSE Rule R18 / Prototype design decision]",
        phase=1,
        description="Requirement description contains conjunctions ('and') suggesting multiple capabilities in one statement. Triggers quality review warning.",
        remediation_guidance="Decompose compound requirements into discrete atomic single-sentence constraints."
    ),
    "AUD-001": RuleDefinition(
        rule_id="AUD-001",
        name="Missing Mutation Audit Log",
        target_entity_type=TargetEntityType.Subsystem.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: IECRE OD-501]",
        phase=1,
        description="Record mutation executed without corresponding audit log generation.",
        remediation_guidance="Ensure all entity creations, updates, and state transitions append an immutable audit log record."
    ),

    # Phase 2: Core Traceability & Risk Governance (5 rules)
    "RSK-001": RuleDefinition(
        rule_id="RSK-001",
        name="Orphan Risk",
        target_entity_type=TargetEntityType.Risk.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: ISO 31000]",
        phase=2,
        description="Risk must link to an existing, valid parent Requirement.",
        remediation_guidance="Attach the risk to a baseline requirement that the failure mode threatens."
    ),
    "RSK-002": RuleDefinition(
        rule_id="RSK-002",
        name="Unmitigated High Risk",
        target_entity_type=TargetEntityType.Risk.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Prototype design decision: Triage Convention]",
        phase=2,
        description="Risk with Risk_Score >= 15 must link to at least one mitigating Control. Note: 15 is a prototype triage convention, not an official certification limit.",
        remediation_guidance="Define and implement an ISO 12100 control to suppress high-severity risks."
    ),
    "RSK-003": RuleDefinition(
        rule_id="RSK-003",
        name="Ineffective Risk Control",
        target_entity_type=TargetEntityType.Control.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Prototype design decision]",
        phase=2,
        description="Residual_Risk must be strictly less than parent Risk_Score. Control cannot increase or leave risk unchanged.",
        remediation_guidance="Adjust control design or re-evaluate post-mitigation severity/likelihood to achieve genuine risk reduction."
    ),
    "TRC-001": RuleDefinition(
        rule_id="TRC-001",
        name="Weak Mitigation for Catastrophic Hazard",
        target_entity_type=TargetEntityType.Control.value,
        severity=FindingSeverity.WARNING.value,
        epistemic_category="[Industry practice / synthesis: ISO 12100]",
        phase=2,
        description="Mitigating a catastrophic risk (Pre_Severity = 5) using only Information_for_Use triggers a quality concern.",
        remediation_guidance="Prioritize Inherently Safe Design (Tier 1) or Safeguarding (Tier 2) over procedural documentation."
    ),
    "TRC-002": RuleDefinition(
        rule_id="TRC-002",
        name="Orphan Requirement",
        target_entity_type=TargetEntityType.Requirement.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: INCOSE V&V]",
        phase=2,
        description="Every requirement must trace to at least one planned verification protocol.",
        remediation_guidance="Create a verification activity linking to the requirement."
    ),

    # Phase 3: Verification & Evidence Integrity (5 rules)
    "VRF-001": RuleDefinition(
        rule_id="VRF-001",
        name="Unsupported Passed Verification",
        target_entity_type=TargetEntityType.Verification.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Industry practice / synthesis: IEC 61400-23]",
        phase=3,
        description="A verification marked 'Passed' must link to at least one Evidence record with Approval_Status = 'Approved'.",
        remediation_guidance="Attach and approve verified test or simulation evidence before marking verification as Passed."
    ),
    "VRF-002": RuleDefinition(
        rule_id="VRF-002",
        name="Verification Methodology Mismatch",
        target_entity_type=TargetEntityType.Verification.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Industry practice / synthesis]",
        phase=3,
        description="Verification method must match Requirement planned verification method. Scoped strictly to Requirement targets.",
        remediation_guidance="Align verification execution method with the planned verification method in the parent requirement."
    ),
    "VRF-003": RuleDefinition(
        rule_id="VRF-003",
        name="Verification Self-Review Conflict of Interest",
        target_entity_type=TargetEntityType.Verification.value,
        severity=FindingSeverity.WARNING.value,
        epistemic_category="[Industry practice / synthesis]",
        phase=3,
        description="Verification reviewer matches Requirement author/owner. Systems engineering best practice requires independent review.",
        remediation_guidance="Assign an independent certification delegate or peer engineer as reviewer."
    ),
    "EVD-001": RuleDefinition(
        rule_id="EVD-001",
        name="Stale Test Evidence",
        target_entity_type=TargetEntityType.Evidence.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Industry practice / synthesis]",
        phase=3,
        description="Evidence date predates the last modification timestamp of the baseline requirement.",
        remediation_guidance="Re-execute verification test/simulation to validate against the updated requirement revision."
    ),
    "EVD-002": RuleDefinition(
        rule_id="EVD-002",
        name="Missing Physical Artifact Reference",
        target_entity_type=TargetEntityType.Evidence.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: IECRE OD-501]",
        phase=3,
        description="Evidence record must specify a non-empty URI, S3 locator, or file path to the stored artifact.",
        remediation_guidance="Provide a valid repository locator or storage reference for the test artifact."
    ),

    # Phase 4: Domain Constraints, Gateways & AI Governance (5 rules)
    "CMP-001": RuleDefinition(
        rule_id="CMP-001",
        name="Subsystem Blocked by Failed Test",
        target_entity_type=TargetEntityType.Subsystem.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: IECRE OD-501]",
        phase=4,
        description="A subsystem cannot achieve compliance if any underlying verification record is in 'Failed' status.",
        remediation_guidance="Resolve test non-conformance, execute design modifications, and re-run verification."
    ),
    "CMP-002": RuleDefinition(
        rule_id="CMP-002",
        name="False Administrative Approval",
        target_entity_type=TargetEntityType.Requirement.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Prototype design decision]",
        phase=4,
        description="Requirement cannot be transitioned to 'Approved' if it has zero linked verification activities.",
        remediation_guidance="Define at least one planned verification protocol before baselining requirement approval."
    ),
    "AI-001": RuleDefinition(
        rule_id="AI-001",
        name="Autonomous AI Mutation Violation",
        target_entity_type=TargetEntityType.Subsystem.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Prototype design decision: AI Safety Boundary]",
        phase=4,
        description="AI agents are strictly barred from autonomously modifying Risk_Score, Pre_Severity, or authoritative Statuses.",
        remediation_guidance="Route AI suggestions through human engineer sign-off workflow ('AI_Suggestion_Applied')."
    ),
    "WND-001": RuleDefinition(
        rule_id="WND-001",
        name="Invalid Fatigue Verification Method",
        target_entity_type=TargetEntityType.Verification.value,
        severity=FindingSeverity.ERROR.value,
        epistemic_category="[Source-backed: IEC 61400-5 / IEC 61400-23]",
        phase=4,
        description="Blade fatigue life requirements (DEL) cannot be verified by visual Inspection; must be Analysis or Test.",
        remediation_guidance="Change verification method to Analysis (FEA/fatigue calculation) or physical full-scale fatigue testing."
    ),
    "WND-002": RuleDefinition(
        rule_id="WND-002",
        name="Ultrasonic Testing Scope Miscategorization",
        target_entity_type=TargetEntityType.Evidence.value,
        severity=FindingSeverity.WARNING.value,
        epistemic_category="[Source-backed: IEC 61400-5]",
        phase=4,
        description="Ultrasonic testing (UT_Scan) evidence should validate Material or Manufacturing requirements.",
        remediation_guidance="Verify whether UT scan artifact is correctly mapped to composite material/manufacturing requirements."
    ),
}

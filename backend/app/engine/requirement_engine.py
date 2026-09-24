"""EngiTrace AI — Requirement Engine (Phase 3)

Evaluates:
  - REQ-001 (Missing Rationale -> WARNING)
  - REQ-002 (Vague Language -> ERROR)
  - REQ-003 (Missing Verification Method -> ERROR)
  - REQ-004 (Compound Sentence -> WARNING)
"""

import re
from typing import List, Optional
from backend.app.domain.models import Requirement, ComplianceFinding, FindingSeverity, TargetEntityType
from backend.app.domain.rules import RULE_CATALOG

# INCOSE Rule R7 Vague Term List
VAGUE_TERMS_PATTERN = re.compile(
    r'\b(fast|adequate|minimize|minimise|sufficient|user-friendly|optimal|easy|good|robust|reasonable)\b',
    re.IGNORECASE
)

# INCOSE Rule R18 Compound Sentence Pattern
COMPOUND_SENTENCE_PATTERN = re.compile(r'\band\b', re.IGNORECASE)


class RequirementEngine:
    """Deterministic validation engine for engineering requirements."""

    @staticmethod
    def evaluate_requirement(req: Requirement, finding_id_prefix: str = "CMP-REQ") -> List[ComplianceFinding]:
        findings: List[ComplianceFinding] = []

        # ---------------------------------------------------------------------
        # Rule REQ-001: Missing Engineering Rationale (WARNING)
        # ---------------------------------------------------------------------
        rule_req001 = RULE_CATALOG["REQ-001"]
        if not req.rationale or len(req.rationale.strip()) < 15:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{req.req_id}-001",
                target_entity_type=TargetEntityType.Requirement.value,
                target_entity_id=req.req_id,
                rule_violated=rule_req001.rule_id,
                severity=rule_req001.severity,
                message=f"Requirement '{req.req_id}' is missing engineering rationale or rationale is shorter than 15 characters."
            ))

        # ---------------------------------------------------------------------
        # Rule REQ-002: Vague Requirement Language (ERROR)
        # ---------------------------------------------------------------------
        rule_req002 = RULE_CATALOG["REQ-002"]
        if req.description:
            vague_match = VAGUE_TERMS_PATTERN.search(req.description)
            if vague_match:
                findings.append(ComplianceFinding(
                    finding_id=f"{finding_id_prefix}-{req.req_id}-002",
                    target_entity_type=TargetEntityType.Requirement.value,
                    target_entity_id=req.req_id,
                    rule_violated=rule_req002.rule_id,
                    severity=rule_req002.severity,
                    message=f"Requirement '{req.req_id}' contains non-verifiable vague term: '{vague_match.group(0)}' (INCOSE R7 violation)."
                ))

        # ---------------------------------------------------------------------
        # Rule REQ-003: Missing Verification Method (ERROR)
        # ---------------------------------------------------------------------
        rule_req003 = RULE_CATALOG["REQ-003"]
        if not req.verification_method or not req.verification_method.strip():
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{req.req_id}-003",
                target_entity_type=TargetEntityType.Requirement.value,
                target_entity_id=req.req_id,
                rule_violated=rule_req003.rule_id,
                severity=rule_req003.severity,
                message=f"Requirement '{req.req_id}' lacks an assigned verification method (ISO 29148 violation)."
            ))

        # ---------------------------------------------------------------------
        # Rule REQ-004: Compound Sentence Detection (WARNING)
        # ---------------------------------------------------------------------
        rule_req004 = RULE_CATALOG["REQ-004"]
        if req.description and COMPOUND_SENTENCE_PATTERN.search(req.description):
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{req.req_id}-004",
                target_entity_type=TargetEntityType.Requirement.value,
                target_entity_id=req.req_id,
                rule_violated=rule_req004.rule_id,
                severity=rule_req004.severity,
                message=f"Requirement '{req.req_id}' description contains 'and', which may indicate a compound requirement (INCOSE R18 quality notice)."
            ))

        return findings

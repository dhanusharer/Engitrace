"""EngiTrace AI — Verification Engine (Phase 3)

Evaluates:
  - Dual-target constraint (exactly ONE target populated)
  - VRF-001 (Passed status requires >= 1 approved Evidence -> ERROR)
  - VRF-002 (Methodology consistency for Requirement targets -> ERROR)
  - VRF-003 (Self-review conflict of interest -> WARNING)
  - WND-001 (Fatigue category cannot use Inspection -> ERROR)
"""

from typing import List, Optional, Dict
from backend.app.domain.models import (
    Verification, Requirement, Control, Evidence,
    ComplianceFinding, FindingSeverity, TargetEntityType
)
from backend.app.domain.rules import RULE_CATALOG


class VerificationEngine:
    """Deterministic validation engine for V&V test and simulation activities."""

    @classmethod
    def evaluate_verification(
        cls,
        verif: Verification,
        requirements: Dict[str, Requirement],
        controls: Dict[str, Control],
        linked_evidence: List[Evidence],
        finding_id_prefix: str = "CMP-VRF"
    ) -> List[ComplianceFinding]:
        findings: List[ComplianceFinding] = []

        # ---------------------------------------------------------------------
        # Single-Target Structural Constraint Validation
        # Exactly ONE target must exist (not both empty, not both populated)
        # ---------------------------------------------------------------------
        has_req = bool(verif.target_req_id and verif.target_req_id.strip())
        has_ctrl = bool(verif.target_control_id and verif.target_control_id.strip())

        if not has_req and not has_ctrl:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{verif.verif_id}-target-empty",
                target_entity_type=TargetEntityType.Verification.value,
                target_entity_id=verif.verif_id,
                rule_violated="VRF-SINGLE-TARGET",
                severity=FindingSeverity.ERROR.value,
                message=f"Verification '{verif.verif_id}' has both target_req_id and target_control_id empty. Exactly one target must be populated."
            ))
            return findings

        if has_req and has_ctrl:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{verif.verif_id}-target-both",
                target_entity_type=TargetEntityType.Verification.value,
                target_entity_id=verif.verif_id,
                rule_violated="VRF-SINGLE-TARGET",
                severity=FindingSeverity.ERROR.value,
                message=f"Verification '{verif.verif_id}' has both target_req_id and target_control_id populated. Exactly one target must be populated."
            ))
            return findings

        # Target Type Consistency
        if verif.target_type == "Requirement" and not has_req:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{verif.verif_id}-type-mismatch",
                target_entity_type=TargetEntityType.Verification.value,
                target_entity_id=verif.verif_id,
                rule_violated="VRF-TARGET-CONSISTENCY",
                severity=FindingSeverity.ERROR.value,
                message=f"Verification '{verif.verif_id}' specifies Target_Type='Requirement' but target_req_id is not populated."
            ))
            return findings

        if verif.target_type == "Control" and not has_ctrl:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{verif.verif_id}-type-mismatch",
                target_entity_type=TargetEntityType.Verification.value,
                target_entity_id=verif.verif_id,
                rule_violated="VRF-TARGET-CONSISTENCY",
                severity=FindingSeverity.ERROR.value,
                message=f"Verification '{verif.verif_id}' specifies Target_Type='Control' but target_control_id is not populated."
            ))
            return findings

        # ---------------------------------------------------------------------
        # Rule VRF-001: Unsupported Passed Verification (ERROR)
        # Passed verification requires at least one approved Evidence artifact
        # ---------------------------------------------------------------------
        rule_vrf001 = RULE_CATALOG["VRF-001"]
        if verif.status == "Passed":
            approved_evidence = [e for e in linked_evidence if e.approval_status == "Approved"]
            if len(approved_evidence) == 0:
                findings.append(ComplianceFinding(
                    finding_id=f"{finding_id_prefix}-{verif.verif_id}-001",
                    target_entity_type=TargetEntityType.Verification.value,
                    target_entity_id=verif.verif_id,
                    rule_violated=rule_vrf001.rule_id,
                    severity=rule_vrf001.severity,
                    message=f"Verification '{verif.verif_id}' is marked 'Passed' but contains 0 approved Evidence records (IEC 61400-23 violation)."
                ))

        # ---------------------------------------------------------------------
        # Requirement-Targeted Verification Rules
        # ---------------------------------------------------------------------
        if verif.target_type == "Requirement" and verif.target_req_id:
            parent_req = requirements.get(verif.target_req_id)
            if parent_req:
                # Rule VRF-002: Methodology Mismatch (ERROR)
                # Note: Applies ONLY when verifying Requirements!
                rule_vrf002 = RULE_CATALOG["VRF-002"]
                if verif.method != parent_req.verification_method:
                    findings.append(ComplianceFinding(
                        finding_id=f"{finding_id_prefix}-{verif.verif_id}-002",
                        target_entity_type=TargetEntityType.Verification.value,
                        target_entity_id=verif.verif_id,
                        rule_violated=rule_vrf002.rule_id,
                        severity=rule_vrf002.severity,
                        message=(
                            f"Verification '{verif.verif_id}' method '{verif.method}' diverges from "
                            f"parent requirement '{parent_req.req_id}' planned method '{parent_req.verification_method}'."
                        )
                    ))

                # Rule VRF-003: Self-Review Conflict of Interest (WARNING)
                rule_vrf003 = RULE_CATALOG["VRF-003"]
                if verif.reviewer and parent_req.owner and verif.reviewer.strip() == parent_req.owner.strip():
                    findings.append(ComplianceFinding(
                        finding_id=f"{finding_id_prefix}-{verif.verif_id}-003",
                        target_entity_type=TargetEntityType.Verification.value,
                        target_entity_id=verif.verif_id,
                        rule_violated=rule_vrf003.rule_id,
                        severity=rule_vrf003.severity,
                        message=(
                            f"Verification '{verif.verif_id}' reviewer '{verif.reviewer}' matches author/owner "
                            f"of parent requirement '{parent_req.req_id}'. Systems engineering best practice requires independent review."
                        )
                    ))

                # Rule WND-001: Invalid Fatigue Verification Method (ERROR)
                # Blade fatigue limits (DEL) require 'Analysis' or 'Test', not visual 'Inspection'
                rule_wnd001 = RULE_CATALOG["WND-001"]
                is_fatigue = parent_req.category in ("Fatigue_Life", "Fatigue")
                if is_fatigue and verif.method == "Inspection":
                    findings.append(ComplianceFinding(
                        finding_id=f"{finding_id_prefix}-{verif.verif_id}-wnd001",
                        target_entity_type=TargetEntityType.Verification.value,
                        target_entity_id=verif.verif_id,
                        rule_violated=rule_wnd001.rule_id,
                        severity=rule_wnd001.severity,
                        message=(
                            f"Verification '{verif.verif_id}' uses 'Inspection' to verify fatigue constraint "
                            f"'{parent_req.req_id}'. Fatigue limits require Analysis (DEL calculation) or physical Test (IEC 61400-5/23)."
                        )
                    ))

        return findings

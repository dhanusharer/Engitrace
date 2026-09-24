"""EngiTrace AI — Evidence Engine (Phase 3)

Evaluates:
  - EVD-001 (Stale Test Evidence -> ERROR)
  - EVD-002 (Missing Physical Artifact Reference -> ERROR)
  - WND-002 (Ultrasonic Testing Scope Miscategorization -> WARNING)
"""

from typing import List, Optional, Dict
from datetime import datetime
from backend.app.domain.models import (
    Evidence, Verification, Requirement, Control, Risk,
    ComplianceFinding, FindingSeverity, TargetEntityType
)
from backend.app.domain.rules import RULE_CATALOG


class EvidenceEngine:
    """Deterministic validation engine for empirical test and simulation artifacts."""

    @classmethod
    def evaluate_evidence(
        cls,
        evid: Evidence,
        verifications: Dict[str, Verification],
        requirements: Dict[str, Requirement],
        controls: Dict[str, Control],
        risks: Dict[str, Risk],
        finding_id_prefix: str = "CMP-EVD"
    ) -> List[ComplianceFinding]:
        findings: List[ComplianceFinding] = []

        # ---------------------------------------------------------------------
        # Rule EVD-002: Missing Physical Artifact Pointer (ERROR)
        # ---------------------------------------------------------------------
        rule_evd002 = RULE_CATALOG["EVD-002"]
        if not evid.artifact_ref or not evid.artifact_ref.strip():
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{evid.evid_id}-002",
                target_entity_type=TargetEntityType.Evidence.value,
                target_entity_id=evid.evid_id,
                rule_violated=rule_evd002.rule_id,
                severity=rule_evd002.severity,
                message=f"Evidence '{evid.evid_id}' lacks a physical storage URI/locator (IECRE OD-501 violation)."
            ))

        parent_verif = verifications.get(evid.parent_verif_id)
        if not parent_verif:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{evid.evid_id}-orphan",
                target_entity_type=TargetEntityType.Evidence.value,
                target_entity_id=evid.evid_id,
                rule_violated="EVD-ORPHAN",
                severity=FindingSeverity.ERROR.value,
                message=f"Evidence '{evid.evid_id}' references non-existent parent verification '{evid.parent_verif_id}'."
            ))
            return findings

        # Resolve the root requirement across the thread
        root_req: Optional[Requirement] = None
        if parent_verif.target_type == "Requirement" and parent_verif.target_req_id:
            root_req = requirements.get(parent_verif.target_req_id)
        elif parent_verif.target_type == "Control" and parent_verif.target_control_id:
            parent_ctrl = controls.get(parent_verif.target_control_id)
            if parent_ctrl:
                parent_risk = risks.get(parent_ctrl.parent_risk_id)
                if parent_risk:
                    root_req = requirements.get(parent_risk.parent_req_id)

        # ---------------------------------------------------------------------
        # Rule EVD-001: Stale Test Evidence (ERROR)
        # If baseline requirement was modified after evidence generation date
        # ---------------------------------------------------------------------
        rule_evd001 = RULE_CATALOG["EVD-001"]
        if root_req and root_req.last_modified_date and evid.date_generated:
            if evid.date_generated < root_req.last_modified_date:
                findings.append(ComplianceFinding(
                    finding_id=f"{finding_id_prefix}-{evid.evid_id}-001",
                    target_entity_type=TargetEntityType.Evidence.value,
                    target_entity_id=evid.evid_id,
                    rule_violated=rule_evd001.rule_id,
                    severity=rule_evd001.severity,
                    message=(
                        f"Evidence '{evid.evid_id}' generated on {evid.date_generated.isoformat()} predates "
                        f"last modification of requirement '{root_req.req_id}' ({root_req.last_modified_date.isoformat()}). "
                        f"Evidence is stale and requires re-qualification."
                    )
                ))

        # ---------------------------------------------------------------------
        # Rule WND-002: Ultrasonic Testing Domain Miscategorization (WARNING)
        # UT scans apply to Material or Manufacturing quality requirements
        # ---------------------------------------------------------------------
        rule_wnd002 = RULE_CATALOG["WND-002"]
        if evid.evidence_type == "UT_Scan" and root_req:
            valid_cats = ("Material", "Material_Integrity", "Manufacturing", "Manufacturing_Quality")
            if root_req.category not in valid_cats:
                findings.append(ComplianceFinding(
                    finding_id=f"{finding_id_prefix}-{evid.evid_id}-wnd002",
                    target_entity_type=TargetEntityType.Evidence.value,
                    target_entity_id=evid.evid_id,
                    rule_violated=rule_wnd002.rule_id,
                    severity=rule_wnd002.severity,
                    message=(
                        f"Evidence '{evid.evid_id}' is a UT_Scan mapped to requirement '{root_req.req_id}' "
                        f"with category '{root_req.category}'. Ultrasonic NDE typically validates Material or Manufacturing constraints."
                    )
                ))

        return findings

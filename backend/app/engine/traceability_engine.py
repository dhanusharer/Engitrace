"""EngiTrace AI — Traceability Engine (Phase 3)

Evaluates:
  - Canonical Forward Thread: Requirement -> Risk -> Control -> Verification -> Evidence
  - Backward Root Cause & Impact Traversal: Evidence -> Verification -> Control/Requirement
  - TRC-002 (Orphan Requirement -> ERROR)
  - Thread completeness and coverage analytics
"""

from typing import List, Dict, Set, Any, Optional
from backend.app.domain.models import (
    Requirement, Risk, Control, Verification, Evidence,
    ComplianceFinding, FindingSeverity, TargetEntityType
)
from backend.app.domain.rules import RULE_CATALOG


class TraceabilityEngine:
    """Deterministic graph engine for systems-engineering digital thread traceability."""

    @staticmethod
    def evaluate_requirement_traceability(
        req: Requirement,
        linked_verifications: List[Verification],
        finding_id_prefix: str = "CMP-TRC"
    ) -> List[ComplianceFinding]:
        findings: List[ComplianceFinding] = []

        # ---------------------------------------------------------------------
        # Rule TRC-002: Orphan Requirement (ERROR)
        # Requirement must trace to >= 1 planned verification activity
        # ---------------------------------------------------------------------
        rule_trc002 = RULE_CATALOG["TRC-002"]
        if len(linked_verifications) == 0:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{req.req_id}-002",
                target_entity_type=TargetEntityType.Requirement.value,
                target_entity_id=req.req_id,
                rule_violated=rule_trc002.rule_id,
                severity=rule_trc002.severity,
                message=f"Requirement '{req.req_id}' has 0 planned verification protocols (INCOSE V&V orphan violation)."
            ))

        return findings

    @staticmethod
    def trace_forward(
        req_id: str,
        requirements: Dict[str, Requirement],
        risks: Dict[str, Risk],
        controls: Dict[str, Control],
        verifications: Dict[str, Verification],
        evidence: Dict[str, Evidence]
    ) -> Dict[str, Any]:
        """Traverse forward from a Requirement through the entire digital thread."""
        req = requirements.get(req_id)
        if not req:
            return {"error": f"Requirement {req_id} not found"}

        # Find child risks
        child_risks = [r for r in risks.values() if r.parent_req_id == req_id]
        
        # Find child controls of those risks
        risk_ids = {r.risk_id for r in child_risks}
        child_controls = [c for c in controls.values() if c.parent_risk_id in risk_ids]
        
        # Find verifications targeting Requirement directly OR targeting child controls
        control_ids = {c.control_id for c in child_controls}
        req_verifications = [v for v in verifications.values() if v.target_req_id == req_id]
        ctrl_verifications = [v for v in verifications.values() if v.target_control_id in control_ids]
        all_verifs = req_verifications + ctrl_verifications

        # Find evidence attached to any of these verifications
        verif_ids = {v.verif_id for v in all_verifs}
        child_evidence = [e for e in evidence.values() if e.parent_verif_id in verif_ids]

        return {
            "req_id": req_id,
            "risks": [r.risk_id for r in child_risks],
            "controls": [c.control_id for c in child_controls],
            "verifications": [v.verif_id for v in all_verifs],
            "evidence": [e.evid_id for e in child_evidence]
        }

    @staticmethod
    def trace_backward(
        evid_id: str,
        requirements: Dict[str, Requirement],
        risks: Dict[str, Risk],
        controls: Dict[str, Control],
        verifications: Dict[str, Verification],
        evidence: Dict[str, Evidence]
    ) -> Dict[str, Any]:
        """Traverse backward from an Evidence record up to the originating Requirement(s)."""
        evid = evidence.get(evid_id)
        if not evid:
            return {"error": f"Evidence {evid_id} not found"}

        parent_verif = verifications.get(evid.parent_verif_id)
        if not parent_verif:
            return {"evid_id": evid_id, "error": f"Orphan evidence: missing verification {evid.parent_verif_id}"}

        target_req: Optional[Requirement] = None
        target_ctrl: Optional[Control] = None
        parent_risk: Optional[Risk] = None

        if parent_verif.target_type == "Requirement" and parent_verif.target_req_id:
            target_req = requirements.get(parent_verif.target_req_id)
        elif parent_verif.target_type == "Control" and parent_verif.target_control_id:
            target_ctrl = controls.get(parent_verif.target_control_id)
            if target_ctrl:
                parent_risk = risks.get(target_ctrl.parent_risk_id)
                if parent_risk:
                    target_req = requirements.get(parent_risk.parent_req_id)

        return {
            "evid_id": evid_id,
            "verification_id": parent_verif.verif_id,
            "target_type": parent_verif.target_type,
            "target_control_id": target_ctrl.control_id if target_ctrl else None,
            "risk_id": parent_risk.risk_id if parent_risk else None,
            "requirement_id": target_req.req_id if target_req else None
        }

    @staticmethod
    def compute_coverage(
        requirements: Dict[str, Requirement],
        risks: Dict[str, Risk],
        controls: Dict[str, Control],
        verifications: Dict[str, Verification],
        evidence: Dict[str, Evidence]
    ) -> Dict[str, Any]:
        """Computes systems-engineering coverage metrics across the digital thread."""
        total_reqs = len(requirements)
        verified_req_ids = {v.target_req_id for v in verifications.values() if v.target_req_id}
        req_coverage_pct = (len(verified_req_ids) / total_reqs * 100.0) if total_reqs > 0 else 0.0

        total_risks = len(risks)
        mitigated_risk_ids = {c.parent_risk_id for c in controls.values()}
        risk_coverage_pct = (len(mitigated_risk_ids) / total_risks * 100.0) if total_risks > 0 else 0.0

        total_verifs = len(verifications)
        evidenced_verif_ids = {e.parent_verif_id for e in evidence.values() if e.approval_status == "Approved"}
        verif_passed_count = sum(1 for v in verifications.values() if v.status == "Passed")

        return {
            "total_requirements": total_reqs,
            "requirements_with_verification": len(verified_req_ids),
            "requirement_coverage_pct": round(req_coverage_pct, 1),
            "total_risks": total_risks,
            "risks_with_controls": len(mitigated_risk_ids),
            "risk_mitigation_pct": round(risk_coverage_pct, 1),
            "total_verifications": total_verifs,
            "verifications_with_approved_evidence": len(evidenced_verif_ids),
            "verifications_passed": verif_passed_count,
            "total_evidence": len(evidence)
        }

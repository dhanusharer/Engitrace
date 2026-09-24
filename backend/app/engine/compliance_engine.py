"""EngiTrace AI — Master Deterministic Compliance Engine (Phase 3)

Coordinates all domain engines to evaluate the complete digital thread graph.
Evaluates:
  - Phase 1: REQ-001, REQ-002, REQ-003, REQ-004, AUD-001
  - Phase 2: RSK-001, RSK-002, RSK-003, TRC-001, TRC-002
  - Phase 3: VRF-001, VRF-002, VRF-003, EVD-001, EVD-002
  - Phase 4: CMP-001, CMP-002, AI-001, WND-001, WND-002

Deterministic Guarantee:
  Input A + Input A = Identical Findings and Compliance Result.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.domain.models import (
    DigitalThread, ComplianceEvaluationResult, ComplianceFinding,
    FindingSeverity, TargetEntityType
)
from backend.app.domain.rules import RULE_CATALOG
from backend.app.engine.requirement_engine import RequirementEngine
from backend.app.engine.risk_engine import RiskEngine
from backend.app.engine.control_engine import ControlEngine
from backend.app.engine.traceability_engine import TraceabilityEngine
from backend.app.engine.verification_engine import VerificationEngine
from backend.app.engine.evidence_engine import EvidenceEngine
from backend.app.engine.audit_validator import AuditValidator


class ComplianceEngine:
    """Master deterministic compliance evaluation orchestrator."""

    def __init__(self):
        self.req_engine = RequirementEngine()
        self.risk_engine = RiskEngine()
        self.ctrl_engine = ControlEngine()
        self.trace_engine = TraceabilityEngine()
        self.verif_engine = VerificationEngine()
        self.evid_engine = EvidenceEngine()
        self.audit_validator = AuditValidator()

    def evaluate(
        self,
        thread: DigitalThread,
        evaluation_id: Optional[str] = None
    ) -> ComplianceEvaluationResult:
        """Executes full deterministic evaluation across the digital thread."""
        findings: List[ComplianceFinding] = []
        eval_id = evaluation_id or "EVAL-RUN-001"
        eval_timestamp = "2026-09-24T20:00:00Z"

        # ---------------------------------------------------------------------
        # 1. Evaluate Requirements (REQ-001, REQ-002, REQ-003, REQ-004, TRC-002, CMP-002)
        # ---------------------------------------------------------------------
        for req in thread.requirements.values():
            # Domain syntax and attribute checks
            findings.extend(self.req_engine.evaluate_requirement(req))

            # Linked verifications for requirement
            linked_verifs = [v for v in thread.verifications.values() if v.target_req_id == req.req_id]

            # Rule TRC-002: Orphan Requirement
            findings.extend(self.trace_engine.evaluate_requirement_traceability(req, linked_verifs))

            # Rule CMP-002: False Administrative Approval
            # Cannot be 'Approved' if count of linked verifications is 0
            if req.status == "Approved" and len(linked_verifs) == 0:
                rule_cmp002 = RULE_CATALOG["CMP-002"]
                findings.append(ComplianceFinding(
                    finding_id=f"CMP-REQ-{req.req_id}-cmp002",
                    target_entity_type=TargetEntityType.Requirement.value,
                    target_entity_id=req.req_id,
                    rule_violated=rule_cmp002.rule_id,
                    severity=rule_cmp002.severity,
                    message=f"Requirement '{req.req_id}' is marked 'Approved' but has 0 planned verification protocols (CMP-002 violation)."
                ))

        # ---------------------------------------------------------------------
        # 2. Evaluate Risks (RSK-001, RSK-002)
        # ---------------------------------------------------------------------
        valid_req_ids = set(thread.requirements.keys())
        for risk in thread.risks.values():
            linked_ctrls = [c for c in thread.controls.values() if c.parent_risk_id == risk.risk_id]
            findings.extend(self.risk_engine.evaluate_risk(risk, valid_req_ids, linked_ctrls))

        # ---------------------------------------------------------------------
        # 3. Evaluate Controls (RSK-003, TRC-001)
        # ---------------------------------------------------------------------
        for ctrl in thread.controls.values():
            parent_risk = thread.risks.get(ctrl.parent_risk_id)
            findings.extend(self.ctrl_engine.evaluate_control(ctrl, parent_risk))

        # ---------------------------------------------------------------------
        # 4. Evaluate Verifications (VRF-001, VRF-002, VRF-003, WND-001)
        # ---------------------------------------------------------------------
        for verif in thread.verifications.values():
            linked_evid = [e for e in thread.evidence.values() if e.parent_verif_id == verif.verif_id]
            findings.extend(self.verif_engine.evaluate_verification(
                verif, thread.requirements, thread.controls, linked_evid
            ))

        # ---------------------------------------------------------------------
        # 5. Evaluate Evidence (EVD-001, EVD-002, WND-002)
        # ---------------------------------------------------------------------
        for evid in thread.evidence.values():
            findings.extend(self.evid_engine.evaluate_evidence(
                evid, thread.verifications, thread.requirements, thread.controls, thread.risks
            ))

        # ---------------------------------------------------------------------
        # 6. Evaluate System Gates & Subsystem Status (CMP-001)
        # ---------------------------------------------------------------------
        failed_verifications = [v for v in thread.verifications.values() if v.status == "Failed"]
        if len(failed_verifications) > 0:
            rule_cmp001 = RULE_CATALOG["CMP-001"]
            failed_ids = ", ".join(v.verif_id for v in failed_verifications)
            findings.append(ComplianceFinding(
                finding_id=f"CMP-SYS-subsystem-001",
                target_entity_type=TargetEntityType.Subsystem.value,
                target_entity_id="Blade_Subsystem",
                rule_violated=rule_cmp001.rule_id,
                severity=rule_cmp001.severity,
                message=f"Subsystem compliance locked to NON_COMPLIANT due to failed verification(s): {failed_ids} (IECRE OD-501 violation)."
            ))

        # ---------------------------------------------------------------------
        # 7. Evaluate Audit Logs & AI Governance (AI-001)
        # ---------------------------------------------------------------------
        for log in thread.audit_logs:
            ai_finding = self.audit_validator.evaluate_ai_safety(log)
            if ai_finding:
                findings.append(ai_finding)

        # ---------------------------------------------------------------------
        # 8. Sort findings deterministically for repeatable output
        # ---------------------------------------------------------------------
        findings.sort(key=lambda f: (f.target_entity_type, f.target_entity_id, f.rule_violated, f.finding_id))

        # ---------------------------------------------------------------------
        # 9. Compute Overall Status & Metrics
        # ---------------------------------------------------------------------
        error_count = sum(1 for f in findings if f.severity == FindingSeverity.ERROR.value)
        warning_count = sum(1 for f in findings if f.severity == FindingSeverity.WARNING.value)
        info_count = sum(1 for f in findings if f.severity == FindingSeverity.INFO.value)

        if error_count > 0:
            compliance_status = "NON_COMPLIANT"
        elif warning_count > 0:
            compliance_status = "FINDINGS_WARNINGS"
        else:
            compliance_status = "COMPLIANT"

        coverage_stats = self.trace_engine.compute_coverage(
            thread.requirements, thread.risks, thread.controls,
            thread.verifications, thread.evidence
        )

        return ComplianceEvaluationResult(
            evaluation_id=eval_id,
            timestamp=eval_timestamp,
            compliance_status=compliance_status,
            total_findings=len(findings),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            traceability_coverage=coverage_stats,
            findings=findings
        )

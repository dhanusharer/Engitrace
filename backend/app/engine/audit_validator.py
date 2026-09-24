"""EngiTrace AI — Audit & AI Governance Validator (Phase 3)

Evaluates:
  - AUD-001 (Missing Mutation Audit Log -> ERROR)
  - AI-001 (Autonomous AI Mutation Violation -> ERROR)
"""

from typing import List, Optional, Dict, Any
from backend.app.domain.models import AuditLog, ComplianceFinding, FindingSeverity, TargetEntityType
from backend.app.domain.rules import RULE_CATALOG


class AuditValidator:
    """Deterministic validator for audit ledger provenance and AI Copilot safety boundaries."""

    @staticmethod
    def validate_mutation_audit(
        entity_type: str,
        entity_id: str,
        action: str,
        has_audit_log: bool,
        finding_id_prefix: str = "CMP-AUD"
    ) -> List[ComplianceFinding]:
        """Rule AUD-001: Verifies that an engineering record mutation generated an audit log."""
        findings: List[ComplianceFinding] = []
        rule_aud001 = RULE_CATALOG["AUD-001"]

        if not has_audit_log:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{entity_id}-001",
                target_entity_type=entity_type,
                target_entity_id=entity_id,
                rule_violated=rule_aud001.rule_id,
                severity=rule_aud001.severity,
                message=f"Entity '{entity_id}' ({entity_type}) underwent action '{action}' without an associated audit log (IECRE OD-501 violation)."
            ))
        return findings

    @staticmethod
    def evaluate_ai_safety(
        log: AuditLog,
        finding_id_prefix: str = "CMP-AI"
    ) -> Optional[ComplianceFinding]:
        """Rule AI-001: AI Copilot Governance Guardrail.

        Prohibits AI agents from autonomously altering Risk_Score, Pre_Severity, Pre_Likelihood,
        or authoritative lifecycle Statuses without human sign-off.
        """
        rule_ai001 = RULE_CATALOG["AI-001"]

        # Check if mutation originates from an AI agent
        if log.user_id and log.user_id.startswith("AI_"):
            # Autonomous mutations of safety-critical fields are strictly forbidden
            restricted_fields = {"Risk_Score", "Pre_Severity", "Pre_Likelihood", "Status", "residual_risk"}
            if log.action in ("Update", "State_Change") and log.field_name in restricted_fields:
                return ComplianceFinding(
                    finding_id=f"{finding_id_prefix}-{log.log_id}-001",
                    target_entity_type=log.entity_type,
                    target_entity_id=log.entity_id,
                    rule_violated=rule_ai001.rule_id,
                    severity=rule_ai001.severity,
                    message=(
                        f"AI Agent '{log.user_id}' attempted autonomous mutation of critical field '{log.field_name}' "
                        f"on {log.entity_type} '{log.entity_id}'. AI suggestions must be approved by an authorized human engineer."
                    )
                )
        return None

"""EngiTrace AI — Risk Engine (Phase 3)

Evaluates:
  - Risk scoring (Risk_Score = Pre_Severity * Pre_Likelihood)
  - RSK-001 (Orphan Risk -> ERROR)
  - RSK-002 (Unmitigated High Risk -> ERROR)
"""

from typing import List, Dict, Set
from backend.app.domain.models import Risk, Control, ComplianceFinding, FindingSeverity, TargetEntityType
from backend.app.domain.rules import RULE_CATALOG


class RiskEngine:
    """Deterministic validation and scoring engine for engineering risks."""

    @staticmethod
    def calculate_score(pre_severity: int, pre_likelihood: int) -> int:
        """Deterministic calculation of Risk_Score = Pre_Severity * Pre_Likelihood."""
        return pre_severity * pre_likelihood

    @classmethod
    def evaluate_risk(
        cls,
        risk: Risk,
        valid_req_ids: Set[str],
        linked_controls: List[Control],
        finding_id_prefix: str = "CMP-RSK"
    ) -> List[ComplianceFinding]:
        findings: List[ComplianceFinding] = []

        # ---------------------------------------------------------------------
        # Rule RSK-001: Orphan Risk (ERROR)
        # ---------------------------------------------------------------------
        rule_rsk001 = RULE_CATALOG["RSK-001"]
        if not risk.parent_req_id or risk.parent_req_id not in valid_req_ids:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{risk.risk_id}-001",
                target_entity_type=TargetEntityType.Risk.value,
                target_entity_id=risk.risk_id,
                rule_violated=rule_rsk001.rule_id,
                severity=rule_rsk001.severity,
                message=f"Risk '{risk.risk_id}' references non-existent or null parent requirement '{risk.parent_req_id}' (ISO 31000 violation)."
            ))

        # ---------------------------------------------------------------------
        # Rule RSK-002: Unmitigated High Risk (ERROR)
        # ---------------------------------------------------------------------
        rule_rsk002 = RULE_CATALOG["RSK-002"]
        calculated_score = cls.calculate_score(risk.pre_severity, risk.pre_likelihood)
        
        # Prototype triage rule: Risk_Score >= 15 requires at least one mitigating control
        if calculated_score >= 15 and len(linked_controls) == 0:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{risk.risk_id}-002",
                target_entity_type=TargetEntityType.Risk.value,
                target_entity_id=risk.risk_id,
                rule_violated=rule_rsk002.rule_id,
                severity=rule_rsk002.severity,
                message=(
                    f"Risk '{risk.risk_id}' has a high criticality score of {calculated_score} "
                    f"(>= 15) but lacks linked mitigating controls. Note: 15 is a prototype triage "
                    f"convention [Prototype design decision], not an official regulatory limit."
                )
            ))

        return findings

"""EngiTrace AI — Control Engine (Phase 3)

Evaluates:
  - Residual risk calculation (Residual_Risk = Post_Severity * Post_Likelihood)
  - RSK-003 (Ineffective Risk Control -> ERROR)
  - TRC-001 (Weak Mitigation for Catastrophic Hazard -> WARNING)
"""

from typing import List, Optional
from backend.app.domain.models import Control, Risk, ComplianceFinding, FindingSeverity, TargetEntityType
from backend.app.domain.rules import RULE_CATALOG


class ControlEngine:
    """Deterministic validation and scoring engine for risk mitigating controls."""

    @staticmethod
    def calculate_residual(post_severity: int, post_likelihood: int) -> int:
        """Deterministic calculation of Residual_Risk = Post_Severity * Post_Likelihood."""
        return post_severity * post_likelihood

    @classmethod
    def evaluate_control(
        cls,
        control: Control,
        parent_risk: Optional[Risk],
        finding_id_prefix: str = "CMP-CTRL"
    ) -> List[ComplianceFinding]:
        findings: List[ComplianceFinding] = []

        if not parent_risk:
            # Broken parent risk linkage is flagged as an error
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{control.control_id}-orphan",
                target_entity_type=TargetEntityType.Control.value,
                target_entity_id=control.control_id,
                rule_violated="RSK-001",
                severity=FindingSeverity.ERROR.value,
                message=f"Control '{control.control_id}' references non-existent parent risk '{control.parent_risk_id}'."
            ))
            return findings

        residual_risk = cls.calculate_residual(control.post_severity, control.post_likelihood)
        parent_score = parent_risk.calculate_score()

        # ---------------------------------------------------------------------
        # Rule RSK-003: Ineffective Risk Control (ERROR)
        # Residual_Risk must be strictly less than parent Risk_Score
        # ---------------------------------------------------------------------
        rule_rsk003 = RULE_CATALOG["RSK-003"]
        if residual_risk >= parent_score:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{control.control_id}-003",
                target_entity_type=TargetEntityType.Control.value,
                target_entity_id=control.control_id,
                rule_violated=rule_rsk003.rule_id,
                severity=rule_rsk003.severity,
                message=(
                    f"Control '{control.control_id}' residual risk ({residual_risk}) is greater than or equal to "
                    f"parent risk '{parent_risk.risk_id}' score ({parent_score}). Controls must achieve risk reduction."
                )
            ))

        # ---------------------------------------------------------------------
        # Rule TRC-001: Weak Mitigation for Catastrophic Hazard (WARNING)
        # ISO 12100: Catastrophic hazard (Pre_Severity=5) addressed only via Information_for_Use
        # ---------------------------------------------------------------------
        rule_trc001 = RULE_CATALOG["TRC-001"]
        if control.hierarchy_type == "Information_for_Use" and parent_risk.pre_severity == 5:
            findings.append(ComplianceFinding(
                finding_id=f"{finding_id_prefix}-{control.control_id}-trc001",
                target_entity_type=TargetEntityType.Control.value,
                target_entity_id=control.control_id,
                rule_violated=rule_trc001.rule_id,
                severity=rule_trc001.severity,
                message=(
                    f"Control '{control.control_id}' utilizes Tier 3 'Information_for_Use' against catastrophic hazard "
                    f"'{parent_risk.risk_id}' (Pre_Severity = 5). ISO 12100 prioritizes Inherently Safe Design."
                )
            ))

        return findings

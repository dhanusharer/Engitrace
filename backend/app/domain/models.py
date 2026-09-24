"""EngiTrace AI — Domain Entities & Schema Models (Phase 3)

Authoritative Reference: docs/data_dictionary.md (Approved for Implementation)
Governing Axiom: "AI suggests. Rules validate. Humans approve. The system records."
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union


# -----------------------------------------------------------------------------
# Domain Enumerations (Matching Lookups & PostgreSQL Schema Exactly)
# -----------------------------------------------------------------------------

class RequirementCategory(str, Enum):
    Structural_Loading = "Structural_Loading"
    Aerodynamic_Performance = "Aerodynamic_Performance"
    Fatigue_Life = "Fatigue_Life"
    Material_Integrity = "Material_Integrity"
    Geometric_Constraints = "Geometric_Constraints"
    Manufacturing_Quality = "Manufacturing_Quality"
    Environmental_Survivability = "Environmental_Survivability"


class RequirementPriority(str, Enum):
    Must_Have = "Must_Have"
    Should_Have = "Should_Have"
    Could_Have = "Could_Have"
    Won_t_Have = "Won_t_Have"


class RequirementStatus(str, Enum):
    Draft = "Draft"
    Under_Review = "Under_Review"
    Approved = "Approved"
    Rejected = "Rejected"
    Retired = "Retired"


class VerificationMethod(str, Enum):
    Analysis = "Analysis"
    Test = "Test"
    Inspection = "Inspection"
    Demonstration = "Demonstration"


class RiskCategory(str, Enum):
    Aerodynamic_Instability = "Aerodynamic_Instability"
    Structural_Yielding = "Structural_Yielding"
    Fatigue_Delamination = "Fatigue_Delamination"
    Adhesive_Debonding = "Adhesive_Debonding"
    Buckling_Instability = "Buckling_Instability"
    Environmental_Damage = "Environmental_Damage"
    Manufacturing_Defect = "Manufacturing_Defect"


class RiskStatus(str, Enum):
    Identified = "Identified"
    Under_Assessment = "Under_Assessment"
    Mitigated = "Mitigated"
    Accepted = "Accepted"
    Closed = "Closed"


class ControlHierarchyType(str, Enum):
    Inherently_Safe_Design = "Inherently_Safe_Design"
    Safeguarding = "Safeguarding"
    Information_for_Use = "Information_for_Use"


class ControlStatus(str, Enum):
    Proposed = "Proposed"
    Approved = "Approved"
    Implemented = "Implemented"
    Verified = "Verified"
    Deprecated = "Deprecated"


class VerificationTargetType(str, Enum):
    Requirement = "Requirement"
    Control = "Control"


class VerificationStatus(str, Enum):
    Planned = "Planned"
    In_Progress = "In_Progress"
    Passed = "Passed"
    Failed = "Failed"
    Blocked = "Blocked"


class EvidenceType(str, Enum):
    Simulation_Report = "Simulation_Report"
    Test_Data_Log = "Test_Data_Log"
    UT_Scan = "UT_Scan"
    Material_Certificate = "Material_Certificate"
    Visual_Inspection_Log = "Visual_Inspection_Log"
    Calibration_Record = "Calibration_Record"


class EvidenceApprovalStatus(str, Enum):
    Uploaded = "Uploaded"
    Under_Review = "Under_Review"
    Approved = "Approved"
    Rejected = "Rejected"
    Superseded = "Superseded"


class FindingSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class FindingStatus(str, Enum):
    Open = "Open"
    Under_Investigation = "Under_Investigation"
    Resolved = "Resolved"
    Waived = "Waived"


class TargetEntityType(str, Enum):
    Requirement = "Requirement"
    Risk = "Risk"
    Control = "Control"
    Verification = "Verification"
    Evidence = "Evidence"
    Subsystem = "Subsystem"


class AuditAction(str, Enum):
    Create = "Create"
    Update = "Update"
    Delete = "Delete"
    State_Change = "State_Change"
    AI_Suggestion_Applied = "AI_Suggestion_Applied"


# -----------------------------------------------------------------------------
# Core Domain Entities
# -----------------------------------------------------------------------------

@dataclass
class Requirement:
    req_id: str
    version: str = "v1.0"
    description: str = ""
    category: str = RequirementCategory.Structural_Loading.value
    rationale: str = ""
    source: str = ""
    priority: str = RequirementPriority.Must_Have.value
    owner: Optional[str] = None
    verification_method: str = VerificationMethod.Analysis.value
    acceptance_criteria: str = ""
    status: str = RequirementStatus.Draft.value
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None


@dataclass
class Risk:
    risk_id: str
    parent_req_id: str
    failure_mode: str
    cause: str
    effect: str
    pre_severity: int
    pre_likelihood: int
    detectability: Optional[int] = None
    risk_score: Optional[int] = None  # Derived: pre_severity * pre_likelihood
    risk_category: str = RiskCategory.Structural_Yielding.value
    owner: Optional[str] = None
    status: str = RiskStatus.Identified.value

    def calculate_score(self) -> int:
        """Deterministic calculation of Risk_Score = Pre_Severity * Pre_Likelihood."""
        return self.pre_severity * self.pre_likelihood


@dataclass
class Control:
    control_id: str
    parent_risk_id: str
    hierarchy_type: str
    description: str
    rationale: Optional[str] = None
    post_severity: int = 1
    post_likelihood: int = 1
    residual_risk: Optional[int] = None  # Derived: post_severity * post_likelihood
    owner: Optional[str] = None
    status: str = ControlStatus.Proposed.value
    implementation_date: Optional[datetime] = None

    def calculate_residual(self) -> int:
        """Deterministic calculation of Residual_Risk = Post_Severity * Post_Likelihood."""
        return self.post_severity * self.post_likelihood


@dataclass
class Verification:
    verif_id: str
    target_type: str  # Requirement or Control
    target_req_id: Optional[str] = None
    target_control_id: Optional[str] = None
    method: str = VerificationMethod.Analysis.value
    acceptance_crit: str = ""
    reviewer: Optional[str] = None
    status: str = VerificationStatus.Planned.value


@dataclass
class Evidence:
    evid_id: str
    parent_verif_id: str
    evidence_type: str
    file_name: str
    artifact_ref: str
    hash: Optional[str] = None
    result_value: Optional[str] = None
    date_generated: Optional[datetime] = None
    approval_status: str = EvidenceApprovalStatus.Uploaded.value


@dataclass
class ComplianceFinding:
    finding_id: str
    target_entity_type: str
    target_entity_id: str
    rule_violated: str
    severity: str
    message: str
    finding_status: str = FindingStatus.Open.value
    created_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    resolution: Optional[str] = None
    assigned_to: Optional[str] = None


@dataclass
class AuditLog:
    log_id: str
    entity_type: str
    entity_id: str
    action: str
    field_name: Optional[str] = None
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Dict[str, Any] = field(default_factory=dict)
    user_id: str = "System"
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None


# -----------------------------------------------------------------------------
# Digital Thread Graph Container & Evaluation Result
# -----------------------------------------------------------------------------

@dataclass
class DigitalThread:
    """In-memory representation of the complete digital thread graph."""
    requirements: Dict[str, Requirement] = field(default_factory=dict)
    risks: Dict[str, Risk] = field(default_factory=dict)
    controls: Dict[str, Control] = field(default_factory=dict)
    verifications: Dict[str, Verification] = field(default_factory=dict)
    evidence: Dict[str, Evidence] = field(default_factory=dict)
    audit_logs: List[AuditLog] = field(default_factory=list)
    findings: List[ComplianceFinding] = field(default_factory=list)


@dataclass
class ComplianceEvaluationResult:
    """Structured, machine-readable output of deterministic compliance evaluation."""
    evaluation_id: str
    timestamp: str
    compliance_status: str  # COMPLIANT, NON_COMPLIANT, FINDINGS_WARNINGS
    total_findings: int
    error_count: int
    warning_count: int
    info_count: int
    traceability_coverage: Dict[str, Any]
    findings: List[ComplianceFinding]

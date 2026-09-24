"""EngiTrace AI — Compliance Evaluation Schemas (Phase 4)"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.findings import FindingResponse


class ComplianceEvaluationRequest(BaseModel):
    evaluation_id: Optional[str] = Field(default=None, description="Optional custom evaluation identifier")
    persist_findings: bool = Field(default=False, description="Whether to persist generated findings to database")


class TraceabilitySummary(BaseModel):
    total_requirements: int
    requirements_with_verification: int
    requirement_coverage_pct: float
    total_risks: int
    risks_with_controls: int
    risk_mitigation_pct: float
    total_verifications: int
    verifications_with_approved_evidence: int
    verifications_passed: int
    total_evidence: int


class ComplianceEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    evaluation_id: str
    timestamp: str
    status: str
    errors: int
    warnings: int
    info: int
    total_findings: int
    traceability_summary: Dict[str, Any]
    risk_summary: Dict[str, Any]
    verification_summary: Dict[str, Any]
    evidence_summary: Dict[str, Any]
    findings: List[FindingResponse]

"""EngiTrace AI — Traceability Schemas (Phase 4)"""

from typing import List, Optional
from pydantic import BaseModel


class ForwardTraceabilityResponse(BaseModel):
    req_id: str
    risks: List[str]
    controls: List[str]
    verifications: List[str]
    evidence: List[str]


class BackwardTraceabilityResponse(BaseModel):
    evid_id: str
    verification_id: Optional[str] = None
    target_type: Optional[str] = None
    target_control_id: Optional[str] = None
    risk_id: Optional[str] = None
    requirement_id: Optional[str] = None


class TraceabilityCoverageResponse(BaseModel):
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

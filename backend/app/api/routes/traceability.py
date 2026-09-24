"""EngiTrace AI — Traceability Endpoints (Phase 4)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.traceability import (
    ForwardTraceabilityResponse, BackwardTraceabilityResponse, TraceabilityCoverageResponse
)
from backend.app.services.traceability_service import TraceabilityService

router = APIRouter(prefix="/traceability", tags=["Traceability"])


@router.get(
    "/requirements/{req_id}",
    response_model=ForwardTraceabilityResponse,
    summary="Forward Digital Thread Traversal"
)
def get_requirement_traceability(
    req_id: str,
    db: Session = Depends(get_db)
):
    """Traverses forward across the canonical systems-engineering digital thread:

    Requirement → Risks → Controls → Verifications → Evidence.
    Uses Phase 3 TraceabilityEngine.
    """
    service = TraceabilityService()
    return service.get_forward_traceability(db=db, req_id=req_id)


@router.get(
    "/evidence/{evid_id}",
    response_model=BackwardTraceabilityResponse,
    summary="Backward Root-Cause & Impact Traversal"
)
def get_evidence_traceability(
    evid_id: str,
    db: Session = Depends(get_db)
):
    """Traverses backward from physical test Evidence to Verification, Control, Risk, and parent Requirement."""
    service = TraceabilityService()
    return service.get_backward_traceability(db=db, evid_id=evid_id)


@router.get(
    "/coverage",
    response_model=TraceabilityCoverageResponse,
    summary="Systems-Engineering Coverage Metrics"
)
def get_coverage_metrics(
    db: Session = Depends(get_db)
):
    """Computes comprehensive digital thread coverage metrics (V&V coverage, hazard mitigation %, passed tests)."""
    service = TraceabilityService()
    return service.get_coverage_metrics(db=db)

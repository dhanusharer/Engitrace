"""EngiTrace AI — Compliance Evaluation Endpoints (Phase 4)"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.compliance import (
    ComplianceEvaluationRequest, ComplianceEvaluationResponse
)
from backend.app.schemas.findings import FindingResponse
from backend.app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post(
    "/evaluate",
    response_model=ComplianceEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic compliance evaluation"
)
def evaluate_compliance(
    payload: Optional[ComplianceEvaluationRequest] = None,
    persist_findings: bool = Query(False, description="Persist generated findings to database"),
    evaluation_id: Optional[str] = Query(None, description="Optional evaluation run identifier"),
    db: Session = Depends(get_db)
):
    """Executes the Phase 3 deterministic compliance engine against the active digital thread in PostgreSQL.

    API endpoints do NOT contain or alter any compliance rules.
    All evaluations are strictly performed by the deterministic domain engine.
    """
    should_persist = persist_findings
    eval_id = evaluation_id
    if payload:
        if payload.persist_findings:
            should_persist = True
        if payload.evaluation_id:
            eval_id = payload.evaluation_id

    service = ComplianceService()
    result = service.evaluate_database(
        db=db, persist_findings=should_persist, evaluation_id=eval_id
    )

    cov = result.traceability_coverage or {}

    from datetime import datetime, timezone
    findings_out = [
        FindingResponse(
            finding_id=f.finding_id,
            target_entity_type=f.target_entity_type,
            target_entity_id=f.target_entity_id,
            rule_violated=f.rule_violated,
            severity=f.severity,
            message=f.message,
            finding_status=f.finding_status,
            created_date=f.created_date or datetime.now(timezone.utc),
            resolved_date=f.resolved_date,
            resolution=f.resolution,
            assigned_to=f.assigned_to
        )
        for f in result.findings
    ]

    return ComplianceEvaluationResponse(
        evaluation_id=result.evaluation_id,
        timestamp=result.timestamp,
        status=result.compliance_status,
        errors=result.error_count,
        warnings=result.warning_count,
        info=result.info_count,
        total_findings=result.total_findings,
        traceability_summary=cov,
        risk_summary={
            "total_risks": cov.get("total_risks", 0),
            "risks_with_controls": cov.get("risks_with_controls", 0),
            "risk_mitigation_pct": cov.get("risk_mitigation_pct", 0.0)
        },
        verification_summary={
            "total_verifications": cov.get("total_verifications", 0),
            "verifications_passed": cov.get("verifications_passed", 0)
        },
        evidence_summary={
            "total_evidence": cov.get("total_evidence", 0),
            "verifications_with_approved_evidence": cov.get("verifications_with_approved_evidence", 0)
        },
        findings=findings_out
    )

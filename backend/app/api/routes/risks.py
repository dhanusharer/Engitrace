"""EngiTrace AI — Risk Endpoints (Phase 4)"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.risks import RiskCreate, RiskUpdate, RiskResponse
from backend.app.services.risk_service import RiskService

router = APIRouter(prefix="/risks", tags=["Risks"])


@router.post(
    "",
    response_model=RiskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new engineering risk/hazard"
)
def create_risk(
    payload: RiskCreate,
    user_id: str = Query("System", description="ID of the user or system creating the record"),
    reason: Optional[str] = Query("Risk created via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Creates a new failure mode risk. Risk_Score is strictly server-derived (Pre_Severity × Pre_Likelihood)."""
    return RiskService.create_risk(
        db=db, data=payload, user_id=user_id, reason=reason
    )


@router.get(
    "",
    response_model=List[RiskResponse],
    summary="List engineering risks"
)
def list_risks(
    parent_req_id: Optional[str] = Query(None, description="Filter by parent requirement ID"),
    category: Optional[str] = Query(None, description="Filter by risk category"),
    status: Optional[str] = Query(None, description="Filter by risk status"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    """Retrieves risk records with optional parent requirement, category, and status filters."""
    return RiskService.list_risks(
        db=db, parent_req_id=parent_req_id, category=category, status_filter=status, limit=limit, offset=offset
    )


@router.get(
    "/{risk_id}",
    response_model=RiskResponse,
    summary="Get risk by ID"
)
def get_risk(
    risk_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single risk entity by primary key ID."""
    return RiskService.get_risk(db=db, risk_id=risk_id)


@router.put(
    "/{risk_id}",
    response_model=RiskResponse,
    summary="Update engineering risk"
)
def update_risk(
    risk_id: str,
    payload: RiskUpdate,
    user_id: str = Query("System", description="ID of the user performing the update"),
    reason: Optional[str] = Query("Risk updated via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Updates an existing risk record. Computed score is updated server-side."""
    return RiskService.update_risk(
        db=db, risk_id=risk_id, data=payload, user_id=user_id, reason=reason
    )


@router.delete(
    "/{risk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete engineering risk"
)
def delete_risk(
    risk_id: str,
    user_id: str = Query("System", description="ID of the user performing the deletion"),
    reason: Optional[str] = Query("Risk deleted via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Deletes an engineering risk if no child controls depend on it."""
    RiskService.delete_risk(
        db=db, risk_id=risk_id, user_id=user_id, reason=reason
    )
    return None

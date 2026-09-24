"""EngiTrace AI — Evidence Endpoints (Phase 4)"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.evidence import (
    EvidenceCreate, EvidenceUpdate, EvidenceResponse
)
from backend.app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new physical evidence record"
)
def create_evidence(
    payload: EvidenceCreate,
    user_id: str = Query("System", description="ID of the user or system creating the record"),
    reason: Optional[str] = Query("Evidence created via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Attaches a physical evidence artifact to a parent verification activity.

    Does not automatically certify or approve parent verifications.
    """
    return EvidenceService.create_evidence(
        db=db, data=payload, user_id=user_id, reason=reason
    )


@router.get(
    "",
    response_model=List[EvidenceResponse],
    summary="List evidence records"
)
def list_evidence(
    parent_verif_id: Optional[str] = Query(None, description="Filter by parent verification ID"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    """Retrieves physical evidence records with optional verification, type, and approval filters."""
    return EvidenceService.list_evidence(
        db=db,
        parent_verif_id=parent_verif_id,
        evidence_type=evidence_type,
        approval_status=approval_status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{evid_id}",
    response_model=EvidenceResponse,
    summary="Get evidence record by ID"
)
def get_evidence(
    evid_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single physical evidence entity by primary key ID."""
    return EvidenceService.get_evidence(db=db, evid_id=evid_id)


@router.put(
    "/{evid_id}",
    response_model=EvidenceResponse,
    summary="Update evidence record"
)
def update_evidence(
    evid_id: str,
    payload: EvidenceUpdate,
    user_id: str = Query("System", description="ID of the user performing the update"),
    reason: Optional[str] = Query("Evidence updated via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Updates an existing evidence record with append-only audit provenance."""
    return EvidenceService.update_evidence(
        db=db, evid_id=evid_id, data=payload, user_id=user_id, reason=reason
    )


@router.delete(
    "/{evid_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete evidence record"
)
def delete_evidence(
    evid_id: str,
    user_id: str = Query("System", description="ID of the user performing the deletion"),
    reason: Optional[str] = Query("Evidence deleted via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Deletes an evidence record with audit tracking."""
    EvidenceService.delete_evidence(
        db=db, evid_id=evid_id, user_id=user_id, reason=reason
    )
    return None

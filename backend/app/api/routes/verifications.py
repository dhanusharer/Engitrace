"""EngiTrace AI — Verification Endpoints (Phase 4)"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.verifications import (
    VerificationCreate, VerificationUpdate, VerificationResponse
)
from backend.app.services.verification_service import VerificationService

router = APIRouter(prefix="/verifications", tags=["Verifications"])


@router.post(
    "",
    response_model=VerificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new verification plan"
)
def create_verification(
    payload: VerificationCreate,
    user_id: str = Query("System", description="ID of the user or system creating the record"),
    reason: Optional[str] = Query("Verification created via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Creates a verification activity. Strictly enforces single-target constraint (Target_Req_ID XOR Target_Control_ID)."""
    return VerificationService.create_verification(
        db=db, data=payload, user_id=user_id, reason=reason
    )


@router.get(
    "",
    response_model=List[VerificationResponse],
    summary="List verification activities"
)
def list_verifications(
    target_type: Optional[str] = Query(None, description="Filter by target type ('Requirement' or 'Control')"),
    target_req_id: Optional[str] = Query(None, description="Filter by target requirement ID"),
    target_control_id: Optional[str] = Query(None, description="Filter by target control ID"),
    status: Optional[str] = Query(None, description="Filter by status ('Planned', 'Passed', etc.)"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    """Retrieves verification activities with optional target and status filtering."""
    return VerificationService.list_verifications(
        db=db,
        target_type=target_type,
        target_req_id=target_req_id,
        target_control_id=target_control_id,
        status_filter=status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{verif_id}",
    response_model=VerificationResponse,
    summary="Get verification by ID"
)
def get_verification(
    verif_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single verification activity by primary key ID."""
    return VerificationService.get_verification(db=db, verif_id=verif_id)


@router.put(
    "/{verif_id}",
    response_model=VerificationResponse,
    summary="Update verification activity"
)
def update_verification(
    verif_id: str,
    payload: VerificationUpdate,
    user_id: str = Query("System", description="ID of the user performing the update"),
    reason: Optional[str] = Query("Verification updated via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Updates an existing verification activity with single-target constraint enforcement."""
    return VerificationService.update_verification(
        db=db, verif_id=verif_id, data=payload, user_id=user_id, reason=reason
    )


@router.delete(
    "/{verif_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete verification activity"
)
def delete_verification(
    verif_id: str,
    user_id: str = Query("System", description="ID of the user performing the deletion"),
    reason: Optional[str] = Query("Verification deleted via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Deletes a verification activity if no child evidence records depend on it."""
    VerificationService.delete_verification(
        db=db, verif_id=verif_id, user_id=user_id, reason=reason
    )
    return None

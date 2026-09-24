"""EngiTrace AI — Requirement Endpoints (Phase 4)"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.requirements import (
    RequirementCreate, RequirementUpdate, RequirementResponse
)
from backend.app.services.requirement_service import RequirementService

router = APIRouter(prefix="/requirements", tags=["Requirements"])


@router.post(
    "",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new engineering requirement"
)
def create_requirement(
    payload: RequirementCreate,
    user_id: str = Query("System", description="ID of the user or system creating the record"),
    reason: Optional[str] = Query("Requirement created via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Creates a new authoritative engineering requirement with append-only audit provenance."""
    return RequirementService.create_requirement(
        db=db, data=payload, user_id=user_id, reason=reason
    )


@router.get(
    "",
    response_model=List[RequirementResponse],
    summary="List engineering requirements"
)
def list_requirements(
    category: Optional[str] = Query(None, description="Filter by requirement category"),
    status: Optional[str] = Query(None, description="Filter by requirement status"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    """Retrieves engineering requirements with optional category and status filtering."""
    return RequirementService.list_requirements(
        db=db, category=category, status_filter=status, limit=limit, offset=offset
    )


@router.get(
    "/{req_id}",
    response_model=RequirementResponse,
    summary="Get requirement by ID"
)
def get_requirement(
    req_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single engineering requirement by primary key ID."""
    return RequirementService.get_requirement(db=db, req_id=req_id)


@router.put(
    "/{req_id}",
    response_model=RequirementResponse,
    summary="Update engineering requirement"
)
def update_requirement(
    req_id: str,
    payload: RequirementUpdate,
    user_id: str = Query("System", description="ID of the user performing the update"),
    reason: Optional[str] = Query("Requirement updated via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Updates an existing requirement and records an audit log entry."""
    return RequirementService.update_requirement(
        db=db, req_id=req_id, data=payload, user_id=user_id, reason=reason
    )


@router.delete(
    "/{req_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete engineering requirement"
)
def delete_requirement(
    req_id: str,
    user_id: str = Query("System", description="ID of the user performing the deletion"),
    reason: Optional[str] = Query("Requirement deleted via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Deletes an engineering requirement if no child hazards depend on it."""
    RequirementService.delete_requirement(
        db=db, req_id=req_id, user_id=user_id, reason=reason
    )
    return None

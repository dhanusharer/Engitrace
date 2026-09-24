"""EngiTrace AI — Control Endpoints (Phase 4)"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.controls import ControlCreate, ControlUpdate, ControlResponse
from backend.app.services.control_service import ControlService

router = APIRouter(prefix="/controls", tags=["Controls"])


@router.post(
    "",
    response_model=ControlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new risk reduction control"
)
def create_control(
    payload: ControlCreate,
    user_id: str = Query("System", description="ID of the user or system creating the record"),
    reason: Optional[str] = Query("Control created via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Creates a new ISO 12100 countermeasure control. Residual_Risk is strictly server-derived."""
    return ControlService.create_control(
        db=db, data=payload, user_id=user_id, reason=reason
    )


@router.get(
    "",
    response_model=List[ControlResponse],
    summary="List risk controls"
)
def list_controls(
    parent_risk_id: Optional[str] = Query(None, description="Filter by parent risk ID"),
    hierarchy_type: Optional[str] = Query(None, description="Filter by 3-step hierarchy type"),
    status: Optional[str] = Query(None, description="Filter by control status"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    """Retrieves control records with optional parent risk, hierarchy type, and status filtering."""
    return ControlService.list_controls(
        db=db,
        parent_risk_id=parent_risk_id,
        hierarchy_type=hierarchy_type,
        status_filter=status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{control_id}",
    response_model=ControlResponse,
    summary="Get control by ID"
)
def get_control(
    control_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single control entity by primary key ID."""
    return ControlService.get_control(db=db, control_id=control_id)


@router.put(
    "/{control_id}",
    response_model=ControlResponse,
    summary="Update risk control"
)
def update_control(
    control_id: str,
    payload: ControlUpdate,
    user_id: str = Query("System", description="ID of the user performing the update"),
    reason: Optional[str] = Query("Control updated via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Updates an existing control record with derived residual risk recomputation."""
    return ControlService.update_control(
        db=db, control_id=control_id, data=payload, user_id=user_id, reason=reason
    )


@router.delete(
    "/{control_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete risk control"
)
def delete_control(
    control_id: str,
    user_id: str = Query("System", description="ID of the user performing the deletion"),
    reason: Optional[str] = Query("Control deleted via API", description="Audit provenance reason"),
    db: Session = Depends(get_db)
):
    """Deletes an engineering control if no child verifications depend on it."""
    ControlService.delete_control(
        db=db, control_id=control_id, user_id=user_id, reason=reason
    )
    return None

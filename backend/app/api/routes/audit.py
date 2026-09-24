"""EngiTrace AI — Audit Trail Endpoints (Phase 4)"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.audit import AuditLogResponse
from backend.app.repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/audit", tags=["Audit & Provenance"])


@router.get(
    "",
    response_model=List[AuditLogResponse],
    summary="Query append-only audit provenance ledger"
)
def get_audit_trail(
    entity_type: Optional[str] = Query(None, description="Filter by entity type ('Requirement', 'Risk', etc.)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    user_id: Optional[str] = Query(None, description="Filter by user / actor ID"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db)
):
    """Retrieves immutable audit log records. Modification or deletion of audit logs is strictly prohibited."""
    return AuditRepository.get_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        limit=limit,
        offset=offset
    )

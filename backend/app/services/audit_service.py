"""EngiTrace AI — Audit Service (Phase 4)

Coordinates append-only provenance logging across all entities.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.models.db_models import DBAuditLog


class AuditService:

    @staticmethod
    def log_mutation(
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        new_value: Dict[str, Any],
        previous_value: Optional[Dict[str, Any]] = None,
        user_id: str = "System",
        field_name: Optional[str] = None,
        reason: Optional[str] = None
    ) -> DBAuditLog:
        return AuditRepository.append_log(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            new_value=new_value,
            previous_value=previous_value,
            user_id=user_id,
            field_name=field_name,
            reason=reason
        )

    @staticmethod
    def get_audit_trail(
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        return AuditRepository.get_logs(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )

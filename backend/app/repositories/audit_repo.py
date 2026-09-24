"""EngiTrace AI — Audit Repository (Phase 4)

Append-only data access for audit logs (IECRE OD-501 provenance).
Mutation/deletion is strictly prohibited by application design and database trigger.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from backend.app.models.db_models import DBAuditLog


class AuditRepository:
    """Repository for append-only audit logging and retrieval."""

    @staticmethod
    def _generate_log_id(db: Session) -> str:
        """Generates a valid log_id matching ^LOG-[0-9]{5,8}$."""
        # Query current count to generate a monotonically increasing ID
        res = db.execute(text("SELECT count(*) FROM audit_logs")).scalar() or 0
        candidate_num = res + 1
        # Format as 5-digit number
        log_id = f"LOG-{candidate_num:05d}"
        
        # Verify uniqueness just in case
        while db.query(DBAuditLog).filter(DBAuditLog.log_id == log_id).first() is not None:
            candidate_num += 1
            log_id = f"LOG-{candidate_num:05d}"
            
        return log_id

    @classmethod
    def append_log(
        cls,
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
        """Appends an immutable audit log entry."""
        log_id = cls._generate_log_id(db)
        log_entry = DBAuditLog(
            log_id=log_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=field_name,
            previous_value=previous_value,
            new_value=new_value,
            user_id=user_id,
            reason=reason,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.flush()
        return log_entry

    @staticmethod
    def get_logs(
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBAuditLog]:
        query = db.query(DBAuditLog)
        if entity_type:
            query = query.filter(DBAuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(DBAuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(DBAuditLog.user_id == user_id)
        return query.order_by(DBAuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, log_id: str) -> Optional[DBAuditLog]:
        return db.query(DBAuditLog).filter(DBAuditLog.log_id == log_id).first()

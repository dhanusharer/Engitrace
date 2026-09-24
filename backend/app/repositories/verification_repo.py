"""EngiTrace AI — Verification Repository (Phase 4)"""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.db_models import DBVerification


class VerificationRepository:

    @staticmethod
    def get_by_id(db: Session, verif_id: str) -> Optional[DBVerification]:
        return db.query(DBVerification).filter(DBVerification.verif_id == verif_id).first()

    @staticmethod
    def get_all(
        db: Session,
        target_type: Optional[str] = None,
        target_req_id: Optional[str] = None,
        target_control_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBVerification]:
        query = db.query(DBVerification)
        if target_type:
            query = query.filter(DBVerification.target_type == target_type)
        if target_req_id:
            query = query.filter(DBVerification.target_req_id == target_req_id)
        if target_control_id:
            query = query.filter(DBVerification.target_control_id == target_control_id)
        if status:
            query = query.filter(DBVerification.status == status)
        return query.order_by(DBVerification.verif_id.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def count(db: Session, target_type: Optional[str] = None, status: Optional[str] = None) -> int:
        query = db.query(DBVerification)
        if target_type:
            query = query.filter(DBVerification.target_type == target_type)
        if status:
            query = query.filter(DBVerification.status == status)
        return query.count()

    @staticmethod
    def create(db: Session, verif: DBVerification) -> DBVerification:
        db.add(verif)
        db.flush()
        db.refresh(verif)
        return verif

    @staticmethod
    def update(db: Session, verif: DBVerification) -> DBVerification:
        db.flush()
        db.refresh(verif)
        return verif

    @staticmethod
    def delete(db: Session, verif: DBVerification) -> None:
        db.delete(verif)
        db.flush()

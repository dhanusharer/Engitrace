"""EngiTrace AI — Evidence Repository (Phase 4)"""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.db_models import DBEvidence


class EvidenceRepository:

    @staticmethod
    def get_by_id(db: Session, evid_id: str) -> Optional[DBEvidence]:
        return db.query(DBEvidence).filter(DBEvidence.evid_id == evid_id).first()

    @staticmethod
    def get_all(
        db: Session,
        parent_verif_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
        approval_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBEvidence]:
        query = db.query(DBEvidence)
        if parent_verif_id:
            query = query.filter(DBEvidence.parent_verif_id == parent_verif_id)
        if evidence_type:
            query = query.filter(DBEvidence.evidence_type == evidence_type)
        if approval_status:
            query = query.filter(DBEvidence.approval_status == approval_status)
        return query.order_by(DBEvidence.evid_id.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def count(db: Session, parent_verif_id: Optional[str] = None, approval_status: Optional[str] = None) -> int:
        query = db.query(DBEvidence)
        if parent_verif_id:
            query = query.filter(DBEvidence.parent_verif_id == parent_verif_id)
        if approval_status:
            query = query.filter(DBEvidence.approval_status == approval_status)
        return query.count()

    @staticmethod
    def create(db: Session, evidence: DBEvidence) -> DBEvidence:
        db.add(evidence)
        db.flush()
        db.refresh(evidence)
        return evidence

    @staticmethod
    def update(db: Session, evidence: DBEvidence) -> DBEvidence:
        db.flush()
        db.refresh(evidence)
        return evidence

    @staticmethod
    def delete(db: Session, evidence: DBEvidence) -> None:
        db.delete(evidence)
        db.flush()

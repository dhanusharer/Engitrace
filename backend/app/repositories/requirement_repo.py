"""EngiTrace AI — Requirement Repository (Phase 4)"""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.db_models import DBRequirement


class RequirementRepository:

    @staticmethod
    def get_by_id(db: Session, req_id: str) -> Optional[DBRequirement]:
        return db.query(DBRequirement).filter(DBRequirement.req_id == req_id).first()

    @staticmethod
    def get_all(
        db: Session,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBRequirement]:
        query = db.query(DBRequirement)
        if category:
            query = query.filter(DBRequirement.category == category)
        if status:
            query = query.filter(DBRequirement.status == status)
        return query.order_by(DBRequirement.req_id.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def count(db: Session, category: Optional[str] = None, status: Optional[str] = None) -> int:
        query = db.query(DBRequirement)
        if category:
            query = query.filter(DBRequirement.category == category)
        if status:
            query = query.filter(DBRequirement.status == status)
        return query.count()

    @staticmethod
    def create(db: Session, req: DBRequirement) -> DBRequirement:
        db.add(req)
        db.flush()
        db.refresh(req)
        return req

    @staticmethod
    def update(db: Session, req: DBRequirement) -> DBRequirement:
        db.flush()
        db.refresh(req)
        return req

    @staticmethod
    def delete(db: Session, req: DBRequirement) -> None:
        db.delete(req)
        db.flush()

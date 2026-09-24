"""EngiTrace AI — Risk Repository (Phase 4)"""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.db_models import DBRisk


class RiskRepository:

    @staticmethod
    def get_by_id(db: Session, risk_id: str) -> Optional[DBRisk]:
        return db.query(DBRisk).filter(DBRisk.risk_id == risk_id).first()

    @staticmethod
    def get_all(
        db: Session,
        parent_req_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBRisk]:
        query = db.query(DBRisk)
        if parent_req_id:
            query = query.filter(DBRisk.parent_req_id == parent_req_id)
        if category:
            query = query.filter(DBRisk.risk_category == category)
        if status:
            query = query.filter(DBRisk.status == status)
        return query.order_by(DBRisk.risk_id.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def count(db: Session, parent_req_id: Optional[str] = None, status: Optional[str] = None) -> int:
        query = db.query(DBRisk)
        if parent_req_id:
            query = query.filter(DBRisk.parent_req_id == parent_req_id)
        if status:
            query = query.filter(DBRisk.status == status)
        return query.count()

    @staticmethod
    def create(db: Session, risk: DBRisk) -> DBRisk:
        db.add(risk)
        db.flush()
        db.refresh(risk)
        return risk

    @staticmethod
    def update(db: Session, risk: DBRisk) -> DBRisk:
        db.flush()
        db.refresh(risk)
        return risk

    @staticmethod
    def delete(db: Session, risk: DBRisk) -> None:
        db.delete(risk)
        db.flush()

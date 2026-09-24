"""EngiTrace AI — Control Repository (Phase 4)"""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.db_models import DBControl


class ControlRepository:

    @staticmethod
    def get_by_id(db: Session, control_id: str) -> Optional[DBControl]:
        return db.query(DBControl).filter(DBControl.control_id == control_id).first()

    @staticmethod
    def get_all(
        db: Session,
        parent_risk_id: Optional[str] = None,
        hierarchy_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBControl]:
        query = db.query(DBControl)
        if parent_risk_id:
            query = query.filter(DBControl.parent_risk_id == parent_risk_id)
        if hierarchy_type:
            query = query.filter(DBControl.hierarchy_type == hierarchy_type)
        if status:
            query = query.filter(DBControl.status == status)
        return query.order_by(DBControl.control_id.asc()).offset(offset).limit(limit).all()

    @staticmethod
    def count(db: Session, parent_risk_id: Optional[str] = None, status: Optional[str] = None) -> int:
        query = db.query(DBControl)
        if parent_risk_id:
            query = query.filter(DBControl.parent_risk_id == parent_risk_id)
        if status:
            query = query.filter(DBControl.status == status)
        return query.count()

    @staticmethod
    def create(db: Session, control: DBControl) -> DBControl:
        db.add(control)
        db.flush()
        db.refresh(control)
        return control

    @staticmethod
    def update(db: Session, control: DBControl) -> DBControl:
        db.flush()
        db.refresh(control)
        return control

    @staticmethod
    def delete(db: Session, control: DBControl) -> None:
        db.delete(control)
        db.flush()

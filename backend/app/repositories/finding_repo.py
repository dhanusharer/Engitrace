"""EngiTrace AI — Compliance Finding Repository (Phase 4)"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.db_models import DBComplianceFinding


class FindingRepository:

    @staticmethod
    def get_by_id(db: Session, finding_id: str) -> Optional[DBComplianceFinding]:
        return db.query(DBComplianceFinding).filter(DBComplianceFinding.finding_id == finding_id).first()

    @staticmethod
    def get_all(
        db: Session,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        rule_violated: Optional[str] = None,
        target_entity_type: Optional[str] = None,
        target_entity_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBComplianceFinding]:
        query = db.query(DBComplianceFinding)
        if severity:
            query = query.filter(DBComplianceFinding.severity == severity)
        if status:
            query = query.filter(DBComplianceFinding.finding_status == status)
        if rule_violated:
            query = query.filter(DBComplianceFinding.rule_violated == rule_violated)
        if target_entity_type:
            query = query.filter(DBComplianceFinding.target_entity_type == target_entity_type)
        if target_entity_id:
            query = query.filter(DBComplianceFinding.target_entity_id == target_entity_id)
        return query.order_by(DBComplianceFinding.created_date.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def create(db: Session, finding: DBComplianceFinding) -> DBComplianceFinding:
        db.add(finding)
        db.flush()
        db.refresh(finding)
        return finding

    @staticmethod
    def save_bulk(db: Session, findings: List[DBComplianceFinding]) -> List[DBComplianceFinding]:
        """Upserts or adds findings to the database."""
        for f in findings:
            existing = db.query(DBComplianceFinding).filter(DBComplianceFinding.finding_id == f.finding_id).first()
            if existing:
                existing.severity = f.severity
                existing.message = f.message
                existing.finding_status = f.finding_status
                existing.resolution = f.resolution
                existing.assigned_to = f.assigned_to
            else:
                db.add(f)
        db.flush()
        return findings

    @staticmethod
    def update(db: Session, finding: DBComplianceFinding) -> DBComplianceFinding:
        db.flush()
        db.refresh(finding)
        return finding

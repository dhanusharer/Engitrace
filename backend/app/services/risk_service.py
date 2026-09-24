"""EngiTrace AI — Risk Service (Phase 4)"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.app.models.db_models import DBRisk, DBRequirement
from backend.app.repositories.risk_repo import RiskRepository
from backend.app.repositories.requirement_repo import RequirementRepository
from backend.app.schemas.risks import RiskCreate, RiskUpdate
from backend.app.services.audit_service import AuditService
from backend.app.domain.models import TargetEntityType, AuditAction


def serialize_risk(risk: DBRisk) -> Dict[str, Any]:
    score = risk.risk_score if risk.risk_score is not None else (risk.pre_severity * risk.pre_likelihood)
    return {
        "risk_id": risk.risk_id,
        "parent_req_id": risk.parent_req_id,
        "failure_mode": risk.failure_mode,
        "cause": risk.cause,
        "effect": risk.effect,
        "pre_severity": risk.pre_severity,
        "pre_likelihood": risk.pre_likelihood,
        "detectability": risk.detectability,
        "risk_score": score,
        "risk_category": risk.risk_category,
        "owner": risk.owner,
        "status": risk.status,
    }


class RiskService:

    @staticmethod
    def get_risk(db: Session, risk_id: str) -> DBRisk:
        risk = RiskRepository.get_by_id(db, risk_id)
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk with ID '{risk_id}' not found."
            )
        return risk

    @staticmethod
    def list_risks(
        db: Session,
        parent_req_id: Optional[str] = None,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBRisk]:
        return RiskRepository.get_all(
            db, parent_req_id=parent_req_id, category=category, status=status_filter, limit=limit, offset=offset
        )

    @staticmethod
    def create_risk(
        db: Session,
        data: RiskCreate,
        user_id: str = "System",
        reason: Optional[str] = "Risk creation via API"
    ) -> DBRisk:
        # Check duplicate
        existing = RiskRepository.get_by_id(db, data.risk_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Risk with ID '{data.risk_id}' already exists."
            )

        # Check parent requirement exists
        parent_req = RequirementRepository.get_by_id(db, data.parent_req_id)
        if not parent_req:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent requirement '{data.parent_req_id}' does not exist."
            )

        # Pre_Severity and Pre_Likelihood are authoritative; risk_score is strictly derived
        new_risk = DBRisk(
            risk_id=data.risk_id,
            parent_req_id=data.parent_req_id,
            failure_mode=data.failure_mode,
            cause=data.cause,
            effect=data.effect,
            pre_severity=data.pre_severity,
            pre_likelihood=data.pre_likelihood,
            detectability=data.detectability,
            risk_category=data.risk_category.value if hasattr(data.risk_category, "value") else str(data.risk_category),
            owner=data.owner,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
        )

        try:
            db.add(new_risk)
            db.flush()
            db.refresh(new_risk)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Risk.value,
                entity_id=new_risk.risk_id,
                action=AuditAction.Create.value,
                new_value=serialize_risk(new_risk),
                previous_value=None,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(new_risk)
            return new_risk
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def update_risk(
        db: Session,
        risk_id: str,
        data: RiskUpdate,
        user_id: str = "System",
        reason: Optional[str] = "Risk update via API"
    ) -> DBRisk:
        risk = RiskRepository.get_by_id(db, risk_id)
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk with ID '{risk_id}' not found."
            )

        prev_state = serialize_risk(risk)
        action = AuditAction.Update.value

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return risk

        # Never let client manually override risk_score
        update_dict.pop("risk_score", None)

        if "parent_req_id" in update_dict and update_dict["parent_req_id"] != risk.parent_req_id:
            parent = RequirementRepository.get_by_id(db, update_dict["parent_req_id"])
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target parent requirement '{update_dict['parent_req_id']}' does not exist."
                )

        for k, v in update_dict.items():
            if v is not None:
                if k == "status" and str(v) != risk.status:
                    action = AuditAction.State_Change.value
                val_to_set = v.value if hasattr(v, "value") else v
                setattr(risk, k, val_to_set)

        try:
            db.flush()
            db.refresh(risk)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Risk.value,
                entity_id=risk.risk_id,
                action=action,
                new_value=serialize_risk(risk),
                previous_value=prev_state,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(risk)
            return risk
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def delete_risk(
        db: Session,
        risk_id: str,
        user_id: str = "System",
        reason: Optional[str] = "Risk deletion via API"
    ) -> None:
        risk = RiskRepository.get_by_id(db, risk_id)
        if not risk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk with ID '{risk_id}' not found."
            )

        prev_state = serialize_risk(risk)

        try:
            RiskRepository.delete(db, risk)
            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Risk.value,
                entity_id=risk_id,
                action=AuditAction.Delete.value,
                new_value={"deleted": True},
                previous_value=prev_state,
                user_id=user_id,
                reason=reason
            )
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete risk '{risk_id}' because child controls or verifications depend on it."
            )

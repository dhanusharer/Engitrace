"""EngiTrace AI — Control Service (Phase 4)"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.app.models.db_models import DBControl
from backend.app.repositories.control_repo import ControlRepository
from backend.app.repositories.risk_repo import RiskRepository
from backend.app.schemas.controls import ControlCreate, ControlUpdate
from backend.app.services.audit_service import AuditService
from backend.app.domain.models import TargetEntityType, AuditAction


def serialize_control(ctrl: DBControl) -> Dict[str, Any]:
    res_risk = ctrl.residual_risk if ctrl.residual_risk is not None else (ctrl.post_severity * ctrl.post_likelihood)
    return {
        "control_id": ctrl.control_id,
        "parent_risk_id": ctrl.parent_risk_id,
        "hierarchy_type": ctrl.hierarchy_type,
        "description": ctrl.description,
        "rationale": ctrl.rationale,
        "post_severity": ctrl.post_severity,
        "post_likelihood": ctrl.post_likelihood,
        "residual_risk": res_risk,
        "owner": ctrl.owner,
        "status": ctrl.status,
        "implementation_date": ctrl.implementation_date.isoformat() if ctrl.implementation_date else None,
    }


class ControlService:

    @staticmethod
    def get_control(db: Session, control_id: str) -> DBControl:
        ctrl = ControlRepository.get_by_id(db, control_id)
        if not ctrl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control with ID '{control_id}' not found."
            )
        return ctrl

    @staticmethod
    def list_controls(
        db: Session,
        parent_risk_id: Optional[str] = None,
        hierarchy_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBControl]:
        return ControlRepository.get_all(
            db, parent_risk_id=parent_risk_id, hierarchy_type=hierarchy_type, status=status_filter, limit=limit, offset=offset
        )

    @staticmethod
    def create_control(
        db: Session,
        data: ControlCreate,
        user_id: str = "System",
        reason: Optional[str] = "Control creation via API"
    ) -> DBControl:
        existing = ControlRepository.get_by_id(db, data.control_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Control with ID '{data.control_id}' already exists."
            )

        parent_risk = RiskRepository.get_by_id(db, data.parent_risk_id)
        if not parent_risk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent risk '{data.parent_risk_id}' does not exist."
            )

        new_ctrl = DBControl(
            control_id=data.control_id,
            parent_risk_id=data.parent_risk_id,
            hierarchy_type=data.hierarchy_type.value if hasattr(data.hierarchy_type, "value") else str(data.hierarchy_type),
            description=data.description,
            rationale=data.rationale,
            post_severity=data.post_severity,
            post_likelihood=data.post_likelihood,
            owner=data.owner,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            implementation_date=data.implementation_date,
        )

        try:
            db.add(new_ctrl)
            db.flush()
            db.refresh(new_ctrl)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Control.value,
                entity_id=new_ctrl.control_id,
                action=AuditAction.Create.value,
                new_value=serialize_control(new_ctrl),
                previous_value=None,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(new_ctrl)
            return new_ctrl
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def update_control(
        db: Session,
        control_id: str,
        data: ControlUpdate,
        user_id: str = "System",
        reason: Optional[str] = "Control update via API"
    ) -> DBControl:
        ctrl = ControlRepository.get_by_id(db, control_id)
        if not ctrl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control with ID '{control_id}' not found."
            )

        prev_state = serialize_control(ctrl)
        action = AuditAction.Update.value

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return ctrl

        update_dict.pop("residual_risk", None)

        if "parent_risk_id" in update_dict and update_dict["parent_risk_id"] != ctrl.parent_risk_id:
            parent = RiskRepository.get_by_id(db, update_dict["parent_risk_id"])
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target parent risk '{update_dict['parent_risk_id']}' does not exist."
                )

        for k, v in update_dict.items():
            if v is not None:
                if k == "status" and str(v) != ctrl.status:
                    action = AuditAction.State_Change.value
                val_to_set = v.value if hasattr(v, "value") else v
                setattr(ctrl, k, val_to_set)

        try:
            db.flush()
            db.refresh(ctrl)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Control.value,
                entity_id=ctrl.control_id,
                action=action,
                new_value=serialize_control(ctrl),
                previous_value=prev_state,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(ctrl)
            return ctrl
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def delete_control(
        db: Session,
        control_id: str,
        user_id: str = "System",
        reason: Optional[str] = "Control deletion via API"
    ) -> None:
        ctrl = ControlRepository.get_by_id(db, control_id)
        if not ctrl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control with ID '{control_id}' not found."
            )

        prev_state = serialize_control(ctrl)

        try:
            ControlRepository.delete(db, ctrl)
            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Control.value,
                entity_id=control_id,
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
                detail=f"Cannot delete control '{control_id}' because child verifications depend on it."
            )

"""EngiTrace AI — Verification Service (Phase 4)"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.app.models.db_models import DBVerification
from backend.app.repositories.verification_repo import VerificationRepository
from backend.app.repositories.requirement_repo import RequirementRepository
from backend.app.repositories.control_repo import ControlRepository
from backend.app.schemas.verifications import VerificationCreate, VerificationUpdate
from backend.app.services.audit_service import AuditService
from backend.app.domain.models import TargetEntityType, AuditAction


def serialize_verification(v: DBVerification) -> Dict[str, Any]:
    return {
        "verif_id": v.verif_id,
        "target_type": v.target_type,
        "target_req_id": v.target_req_id,
        "target_control_id": v.target_control_id,
        "method": v.method,
        "acceptance_crit": v.acceptance_crit,
        "reviewer": v.reviewer,
        "status": v.status,
    }


class VerificationService:

    @staticmethod
    def get_verification(db: Session, verif_id: str) -> DBVerification:
        v = VerificationRepository.get_by_id(db, verif_id)
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification with ID '{verif_id}' not found."
            )
        return v

    @staticmethod
    def list_verifications(
        db: Session,
        target_type: Optional[str] = None,
        target_req_id: Optional[str] = None,
        target_control_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBVerification]:
        return VerificationRepository.get_all(
            db,
            target_type=target_type,
            target_req_id=target_req_id,
            target_control_id=target_control_id,
            status=status_filter,
            limit=limit,
            offset=offset
        )

    @staticmethod
    def create_verification(
        db: Session,
        data: VerificationCreate,
        user_id: str = "System",
        reason: Optional[str] = "Verification creation via API"
    ) -> DBVerification:
        existing = VerificationRepository.get_by_id(db, data.verif_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Verification with ID '{data.verif_id}' already exists."
            )

        # Validate parent target existence
        if data.target_type.value == "Requirement":
            req = RequirementRepository.get_by_id(db, data.target_req_id)
            if not req:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target requirement '{data.target_req_id}' does not exist."
                )
        elif data.target_type.value == "Control":
            ctrl = ControlRepository.get_by_id(db, data.target_control_id)
            if not ctrl:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target control '{data.target_control_id}' does not exist."
                )

        new_v = DBVerification(
            verif_id=data.verif_id,
            target_type=data.target_type.value if hasattr(data.target_type, "value") else str(data.target_type),
            target_req_id=data.target_req_id,
            target_control_id=data.target_control_id,
            method=data.method.value if hasattr(data.method, "value") else str(data.method),
            acceptance_crit=data.acceptance_crit,
            reviewer=data.reviewer,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
        )

        try:
            db.add(new_v)
            db.flush()
            db.refresh(new_v)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Verification.value,
                entity_id=new_v.verif_id,
                action=AuditAction.Create.value,
                new_value=serialize_verification(new_v),
                previous_value=None,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(new_v)
            return new_v
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def update_verification(
        db: Session,
        verif_id: str,
        data: VerificationUpdate,
        user_id: str = "System",
        reason: Optional[str] = "Verification update via API"
    ) -> DBVerification:
        v = VerificationRepository.get_by_id(db, verif_id)
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification with ID '{verif_id}' not found."
            )

        prev_state = serialize_verification(v)
        action = AuditAction.Update.value

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return v

        for k, val in update_dict.items():
            if val is not None:
                if k == "status" and str(val) != v.status:
                    action = AuditAction.State_Change.value
                val_to_set = val.value if hasattr(val, "value") else val
                setattr(v, k, val_to_set)

        # Single target check on entity
        req_present = v.target_req_id is not None and bool(str(v.target_req_id).strip())
        ctrl_present = v.target_control_id is not None and bool(str(v.target_control_id).strip())
        if (req_present and ctrl_present) or (not req_present and not ctrl_present):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dual-target constraint violation: Exactly one of target_req_id or target_control_id must be populated."
            )

        try:
            db.flush()
            db.refresh(v)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Verification.value,
                entity_id=v.verif_id,
                action=action,
                new_value=serialize_verification(v),
                previous_value=prev_state,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(v)
            return v
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def delete_verification(
        db: Session,
        verif_id: str,
        user_id: str = "System",
        reason: Optional[str] = "Verification deletion via API"
    ) -> None:
        v = VerificationRepository.get_by_id(db, verif_id)
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification with ID '{verif_id}' not found."
            )

        prev_state = serialize_verification(v)

        try:
            VerificationRepository.delete(db, v)
            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Verification.value,
                entity_id=verif_id,
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
                detail=f"Cannot delete verification '{verif_id}' because child evidence records depend on it."
            )

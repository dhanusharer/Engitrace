"""EngiTrace AI — Evidence Service (Phase 4)"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.app.models.db_models import DBEvidence
from backend.app.repositories.evidence_repo import EvidenceRepository
from backend.app.repositories.verification_repo import VerificationRepository
from backend.app.schemas.evidence import EvidenceCreate, EvidenceUpdate
from backend.app.services.audit_service import AuditService
from backend.app.domain.models import TargetEntityType, AuditAction


def serialize_evidence(e: DBEvidence) -> Dict[str, Any]:
    return {
        "evid_id": e.evid_id,
        "parent_verif_id": e.parent_verif_id,
        "evidence_type": e.evidence_type,
        "file_name": e.file_name,
        "artifact_ref": e.artifact_ref,
        "hash": e.hash,
        "result_value": e.result_value,
        "date_generated": e.date_generated.isoformat() if e.date_generated else None,
        "approval_status": e.approval_status,
    }


class EvidenceService:

    @staticmethod
    def get_evidence(db: Session, evid_id: str) -> DBEvidence:
        e = EvidenceRepository.get_by_id(db, evid_id)
        if not e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence with ID '{evid_id}' not found."
            )
        return e

    @staticmethod
    def list_evidence(
        db: Session,
        parent_verif_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
        approval_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBEvidence]:
        return EvidenceRepository.get_all(
            db,
            parent_verif_id=parent_verif_id,
            evidence_type=evidence_type,
            approval_status=approval_status,
            limit=limit,
            offset=offset
        )

    @staticmethod
    def create_evidence(
        db: Session,
        data: EvidenceCreate,
        user_id: str = "System",
        reason: Optional[str] = "Evidence creation via API"
    ) -> DBEvidence:
        existing = EvidenceRepository.get_by_id(db, data.evid_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Evidence with ID '{data.evid_id}' already exists."
            )

        verif = VerificationRepository.get_by_id(db, data.parent_verif_id)
        if not verif:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent verification '{data.parent_verif_id}' does not exist."
            )

        # Do NOT automatically mark parent verification as passed or approved!
        new_e = DBEvidence(
            evid_id=data.evid_id,
            parent_verif_id=data.parent_verif_id,
            evidence_type=data.evidence_type.value if hasattr(data.evidence_type, "value") else str(data.evidence_type),
            file_name=data.file_name,
            artifact_ref=data.artifact_ref,
            hash=data.hash,
            result_value=data.result_value,
            date_generated=data.date_generated,
            approval_status=data.approval_status.value if hasattr(data.approval_status, "value") else str(data.approval_status),
        )

        try:
            db.add(new_e)
            db.flush()
            db.refresh(new_e)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Evidence.value,
                entity_id=new_e.evid_id,
                action=AuditAction.Create.value,
                new_value=serialize_evidence(new_e),
                previous_value=None,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(new_e)
            return new_e
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def update_evidence(
        db: Session,
        evid_id: str,
        data: EvidenceUpdate,
        user_id: str = "System",
        reason: Optional[str] = "Evidence update via API"
    ) -> DBEvidence:
        e = EvidenceRepository.get_by_id(db, evid_id)
        if not e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence with ID '{evid_id}' not found."
            )

        prev_state = serialize_evidence(e)
        action = AuditAction.Update.value

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return e

        if "parent_verif_id" in update_dict and update_dict["parent_verif_id"] != e.parent_verif_id:
            parent = VerificationRepository.get_by_id(db, update_dict["parent_verif_id"])
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target parent verification '{update_dict['parent_verif_id']}' does not exist."
                )

        for k, val in update_dict.items():
            if val is not None:
                if k == "approval_status" and str(val) != e.approval_status:
                    action = AuditAction.State_Change.value
                val_to_set = val.value if hasattr(val, "value") else val
                setattr(e, k, val_to_set)

        try:
            db.flush()
            db.refresh(e)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Evidence.value,
                entity_id=e.evid_id,
                action=action,
                new_value=serialize_evidence(e),
                previous_value=prev_state,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(e)
            return e
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def delete_evidence(
        db: Session,
        evid_id: str,
        user_id: str = "System",
        reason: Optional[str] = "Evidence deletion via API"
    ) -> None:
        e = EvidenceRepository.get_by_id(db, evid_id)
        if not e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence with ID '{evid_id}' not found."
            )

        prev_state = serialize_evidence(e)

        try:
            EvidenceRepository.delete(db, e)
            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Evidence.value,
                entity_id=evid_id,
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
                detail=f"Cannot delete evidence '{evid_id}': {str(e)}"
            )

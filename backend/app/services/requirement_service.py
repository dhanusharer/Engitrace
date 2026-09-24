"""EngiTrace AI — Requirement Service (Phase 4)"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.app.models.db_models import DBRequirement
from backend.app.repositories.requirement_repo import RequirementRepository
from backend.app.schemas.requirements import RequirementCreate, RequirementUpdate
from backend.app.services.audit_service import AuditService
from backend.app.domain.models import TargetEntityType, AuditAction


def serialize_requirement(req: DBRequirement) -> Dict[str, Any]:
    return {
        "req_id": req.req_id,
        "version": req.version,
        "description": req.description,
        "category": req.category,
        "rationale": req.rationale,
        "source": req.source,
        "priority": req.priority,
        "owner": req.owner,
        "verification_method": req.verification_method,
        "acceptance_criteria": req.acceptance_criteria,
        "status": req.status,
        "created_date": req.created_date.isoformat() if req.created_date else None,
        "last_modified_date": req.last_modified_date.isoformat() if req.last_modified_date else None,
    }


class RequirementService:

    @staticmethod
    def get_requirement(db: Session, req_id: str) -> DBRequirement:
        req = RequirementRepository.get_by_id(db, req_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement with ID '{req_id}' not found."
            )
        return req

    @staticmethod
    def list_requirements(
        db: Session,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBRequirement]:
        return RequirementRepository.get_all(
            db, category=category, status=status_filter, limit=limit, offset=offset
        )

    @staticmethod
    def create_requirement(
        db: Session,
        data: RequirementCreate,
        user_id: str = "System",
        reason: Optional[str] = "Requirement creation via API"
    ) -> DBRequirement:
        existing = RequirementRepository.get_by_id(db, data.req_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Requirement with ID '{data.req_id}' already exists."
            )

        new_req = DBRequirement(
            req_id=data.req_id,
            version=data.version,
            description=data.description,
            category=data.category.value if hasattr(data.category, "value") else str(data.category),
            rationale=data.rationale,
            source=data.source,
            priority=data.priority.value if hasattr(data.priority, "value") else str(data.priority),
            owner=data.owner,
            verification_method=data.verification_method.value if hasattr(data.verification_method, "value") else str(data.verification_method),
            acceptance_criteria=data.acceptance_criteria,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            created_date=datetime.utcnow(),
            last_modified_date=datetime.utcnow()
        )

        try:
            db.add(new_req)
            db.flush()
            db.refresh(new_req)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Requirement.value,
                entity_id=new_req.req_id,
                action=AuditAction.Create.value,
                new_value=serialize_requirement(new_req),
                previous_value=None,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(new_req)
            return new_req
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def update_requirement(
        db: Session,
        req_id: str,
        data: RequirementUpdate,
        user_id: str = "System",
        reason: Optional[str] = "Requirement update via API"
    ) -> DBRequirement:
        req = RequirementRepository.get_by_id(db, req_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement with ID '{req_id}' not found."
            )

        prev_state = serialize_requirement(req)
        action = AuditAction.Update.value

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return req

        for k, v in update_dict.items():
            if v is not None:
                if k == "status" and str(v) != req.status:
                    action = AuditAction.State_Change.value
                val_to_set = v.value if hasattr(v, "value") else v
                setattr(req, k, val_to_set)

        req.last_modified_date = datetime.utcnow()

        try:
            db.flush()
            db.refresh(req)

            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Requirement.value,
                entity_id=req.req_id,
                action=action,
                new_value=serialize_requirement(req),
                previous_value=prev_state,
                user_id=user_id,
                reason=reason
            )
            db.commit()
            db.refresh(req)
            return req
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
            )

    @staticmethod
    def delete_requirement(
        db: Session,
        req_id: str,
        user_id: str = "System",
        reason: Optional[str] = "Requirement deletion via API"
    ) -> None:
        req = RequirementRepository.get_by_id(db, req_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement with ID '{req_id}' not found."
            )

        prev_state = serialize_requirement(req)

        try:
            RequirementRepository.delete(db, req)
            AuditService.log_mutation(
                db=db,
                entity_type=TargetEntityType.Requirement.value,
                entity_id=req_id,
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
                detail=f"Cannot delete requirement '{req_id}' because child records (Risks or Verifications) depend on it."
            )

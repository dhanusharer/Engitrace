"""EngiTrace AI — Traceability Service (Phase 4)

Delegates graph traversals and coverage analytics directly to Phase 3 TraceabilityEngine.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.services.compliance_service import ComplianceService
from backend.app.engine.traceability_engine import TraceabilityEngine


class TraceabilityService:

    def __init__(self):
        self.compliance_service = ComplianceService()

    def get_forward_traceability(self, db: Session, req_id: str) -> Dict[str, Any]:
        """Traverse forward from Requirement through the entire digital thread."""
        thread = self.compliance_service.load_from_db(db)
        if req_id not in thread.requirements:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement '{req_id}' not found."
            )

        res = TraceabilityEngine.trace_forward(
            req_id=req_id,
            requirements=thread.requirements,
            risks=thread.risks,
            controls=thread.controls,
            verifications=thread.verifications,
            evidence=thread.evidence
        )
        return res

    def get_backward_traceability(self, db: Session, evid_id: str) -> Dict[str, Any]:
        """Traverse backward from Evidence to its parent Verification, Control, Risk, and Requirement."""
        thread = self.compliance_service.load_from_db(db)
        if evid_id not in thread.evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence '{evid_id}' not found."
            )

        res = TraceabilityEngine.trace_backward(
            evid_id=evid_id,
            requirements=thread.requirements,
            risks=thread.risks,
            controls=thread.controls,
            verifications=thread.verifications,
            evidence=thread.evidence
        )
        return res

    def get_coverage_metrics(self, db: Session) -> Dict[str, Any]:
        """Computes coverage metrics across the active digital thread."""
        thread = self.compliance_service.load_from_db(db)
        return TraceabilityEngine.compute_coverage(
            requirements=thread.requirements,
            risks=thread.risks,
            controls=thread.controls,
            verifications=thread.verifications,
            evidence=thread.evidence
        )

"""EngiTrace AI — API Router Aggregator (Phase 4)

Mounts all v1 endpoints under /api/v1.
"""

from fastapi import APIRouter
from backend.app.api.routes import (
    requirements,
    risks,
    controls,
    verifications,
    evidence,
    compliance,
    findings,
    traceability,
    import_excel,
    audit,
)

api_router = APIRouter()

api_router.include_router(requirements.router)
api_router.include_router(risks.router)
api_router.include_router(controls.router)
api_router.include_router(verifications.router)
api_router.include_router(evidence.router)
api_router.include_router(compliance.router)
api_router.include_router(findings.router)
api_router.include_router(traceability.router)
api_router.include_router(import_excel.router)
api_router.include_router(audit.router)

"""EngiTrace AI — Health Check Endpoints (Phase 4)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="API Service Liveness Probe")
def health_check():
    """Liveness probe confirming the FastAPI service is active."""
    return {
        "status": "healthy",
        "service": "engitrace-api"
    }


@router.get("/health/db", summary="PostgreSQL Database Readiness Probe")
def db_health_check(db: Session = Depends(get_db)):
    """Readiness probe verifying physical connectivity to PostgreSQL.

    Executes a lightweight query (SELECT 1) without exposing database credentials.
    """
    try:
        res = db.execute(text("SELECT 1")).scalar()
        if res == 1:
            return {
                "status": "healthy",
                "database": "connected"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unexpected database response."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity probe failed."
        )

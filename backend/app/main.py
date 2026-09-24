"""EngiTrace AI — FastAPI Application Entrypoint (Phase 4)

Document Reference: DOC-ENG-DDICT-001 (Approved for Implementation)
Governing Axiom: "AI suggests. Rules validate. Humans approve. The system records."
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.api.routes import health
from backend.app.api.api import api_router

app = FastAPI(
    title="EngiTrace AI — Engineering Risk, Compliance & Traceability API",
    description=(
        "Production-grade backend integrating PostgreSQL 16, Excel ingestion, "
        "and the Phase 3 Deterministic Compliance & Traceability Engine for offshore wind turbine engineering."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation error handler providing clear engineering error feedback."""
    errors = []
    for err in exc.errors():
        field_loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append({
            "field": field_loc,
            "message": err.get("msg"),
            "type": err.get("type")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Global safe exception handler preventing leakage of database credentials or connection strings."""
    # Never leak internal stack traces or connection strings to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected server error occurred during processing."
        }
    )


# Mount Routers
# Liveness & Readiness Probes
app.include_router(health.router)

# Version 1 API Routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

"""EngiTrace AI — Excel Ingestion Endpoints (Phase 4)"""

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.excel_import import ImportExcelResponse
from backend.app.services.excel_import_service import ExcelImportService

router = APIRouter(prefix="/import", tags=["Ingestion"])


@router.post(
    "/excel",
    response_model=ImportExcelResponse,
    status_code=status.HTTP_200_OK,
    summary="Controlled Excel Workbook Ingestion"
)
async def import_excel(
    file: UploadFile = File(..., description="EngiTrace_Template.xlsx workbook file"),
    dry_run: bool = Query(True, description="When True, evaluates digital thread without persisting to database"),
    user_id: str = Query("System", description="ID of the user or pipeline triggering the import"),
    db: Session = Depends(get_db)
):
    """Safely ingests and validates an EngiTrace Excel template.

    Pipeline:
      1. Structural validation of sheets and headers
      2. Domain normalization
      3. Cross-entity referential integrity checks
      4. Deterministic engine dry-run evaluation
      5. Explicit transactional persistence with audit provenance (if dry_run=False).
    """
    # Validate file extension
    filename = file.filename or ""
    if not (filename.endswith(".xlsx") or filename.endswith(".xlsm")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .xlsx or .xlsm workbooks are accepted."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    service = ExcelImportService()
    result = service.process_excel(
        file_bytes=content,
        db=db,
        dry_run=dry_run,
        user_id=user_id
    )

    return result

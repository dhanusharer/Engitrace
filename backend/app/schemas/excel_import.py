"""EngiTrace AI — Excel Ingestion Schemas (Phase 4)"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.schemas.findings import FindingResponse


class ImportExcelResponse(BaseModel):
    success: bool
    dry_run: bool
    message: str
    rows_parsed: Dict[str, int]
    validation_errors: List[str]
    compliance_findings: List[FindingResponse]
    persisted_counts: Dict[str, int]

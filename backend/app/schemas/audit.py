"""EngiTrace AI — Audit Log Schemas (Phase 4)"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from backend.app.domain.models import AuditAction, TargetEntityType


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    log_id: str
    entity_type: str
    entity_id: str
    action: str
    field_name: Optional[str] = None
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Dict[str, Any]
    user_id: str
    reason: Optional[str] = None
    timestamp: datetime

"""EngiTrace AI — Compliance Finding Schemas (Phase 4)"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.domain.models import TargetEntityType, FindingSeverity, FindingStatus


class FindingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    target_entity_type: TargetEntityType
    target_entity_id: str = Field(..., max_length=32)
    rule_violated: str = Field(..., max_length=64)
    severity: FindingSeverity
    message: str = Field(..., min_length=15)
    finding_status: FindingStatus = Field(default=FindingStatus.Open)
    resolution: Optional[str] = None
    assigned_to: Optional[str] = Field(default=None, max_length=64)


class FindingCreate(FindingBase):
    finding_id: str = Field(..., pattern=r"^CMP-[A-Z]{3}-[0-9]{3,4}$")


class FindingUpdate(BaseModel):
    finding_status: Optional[FindingStatus] = None
    resolution: Optional[str] = None
    assigned_to: Optional[str] = Field(default=None, max_length=64)
    resolved_date: Optional[datetime] = None


class FindingResponse(FindingBase):
    finding_id: str
    created_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None

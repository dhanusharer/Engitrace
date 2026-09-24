"""EngiTrace AI — Requirement Schemas (Phase 4)"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.domain.models import (
    RequirementCategory, RequirementPriority, RequirementStatus, VerificationMethod
)


class RequirementBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    version: str = Field(default="v1.0", max_length=16)
    description: str = Field(..., min_length=20)
    category: RequirementCategory
    rationale: str = Field(..., min_length=15)
    source: str = Field(..., min_length=1, max_length=128)
    priority: RequirementPriority
    owner: Optional[str] = Field(default=None, max_length=64)
    verification_method: VerificationMethod
    acceptance_criteria: str = Field(..., min_length=1)
    status: RequirementStatus = Field(default=RequirementStatus.Draft)


class RequirementCreate(RequirementBase):
    req_id: str = Field(..., pattern=r"^REQ-[A-Z]{3}-[A-Z]{3}-[0-9]{3,4}$")


class RequirementUpdate(BaseModel):
    version: Optional[str] = Field(default=None, max_length=16)
    description: Optional[str] = Field(default=None, min_length=20)
    category: Optional[RequirementCategory] = None
    rationale: Optional[str] = Field(default=None, min_length=15)
    source: Optional[str] = Field(default=None, min_length=1, max_length=128)
    priority: Optional[RequirementPriority] = None
    owner: Optional[str] = Field(default=None, max_length=64)
    verification_method: Optional[VerificationMethod] = None
    acceptance_criteria: Optional[str] = Field(default=None, min_length=1)
    status: Optional[RequirementStatus] = None


class RequirementResponse(RequirementBase):
    req_id: str
    created_date: datetime
    last_modified_date: datetime

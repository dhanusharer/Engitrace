"""EngiTrace AI — Evidence Schemas (Phase 4)"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.domain.models import EvidenceType, EvidenceApprovalStatus


class EvidenceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    parent_verif_id: str = Field(..., max_length=32)
    evidence_type: EvidenceType
    file_name: str = Field(..., min_length=1, max_length=255)
    artifact_ref: str = Field(..., min_length=1, max_length=512)
    hash: Optional[str] = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    result_value: Optional[str] = None
    date_generated: datetime
    approval_status: EvidenceApprovalStatus = Field(default=EvidenceApprovalStatus.Uploaded)

    @field_validator("artifact_ref")
    @classmethod
    def validate_artifact_ref_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Artifact_Ref cannot be blank or whitespace-only.")
        return v


class EvidenceCreate(EvidenceBase):
    evid_id: str = Field(..., pattern=r"^EVD-[A-Z]{3}-[0-9]{3,4}$")


class EvidenceUpdate(BaseModel):
    parent_verif_id: Optional[str] = Field(default=None, max_length=32)
    evidence_type: Optional[EvidenceType] = None
    file_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    artifact_ref: Optional[str] = Field(default=None, min_length=1, max_length=512)
    hash: Optional[str] = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    result_value: Optional[str] = None
    date_generated: Optional[datetime] = None
    approval_status: Optional[EvidenceApprovalStatus] = None

    @field_validator("artifact_ref")
    @classmethod
    def validate_artifact_ref_nonempty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Artifact_Ref cannot be blank or whitespace-only.")
        return v


class EvidenceResponse(EvidenceBase):
    evid_id: str

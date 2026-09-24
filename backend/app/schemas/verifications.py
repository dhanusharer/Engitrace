"""EngiTrace AI — Verification Schemas (Phase 4)"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.app.domain.models import VerificationMethod, VerificationStatus, VerificationTargetType


class VerificationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    target_type: VerificationTargetType
    target_req_id: Optional[str] = Field(default=None, max_length=32)
    target_control_id: Optional[str] = Field(default=None, max_length=32)
    method: VerificationMethod
    acceptance_crit: str = Field(..., min_length=15)
    reviewer: Optional[str] = Field(default=None, max_length=64)
    status: VerificationStatus = Field(default=VerificationStatus.Planned)

    @model_validator(mode="after")
    def validate_single_target_architecture(self):
        req_present = self.target_req_id is not None and bool(str(self.target_req_id).strip())
        ctrl_present = self.target_control_id is not None and bool(str(self.target_control_id).strip())

        if (req_present and ctrl_present) or (not req_present and not ctrl_present):
            raise ValueError(
                "Dual-target constraint violation: Exactly one of Target_Req_ID or Target_Control_ID must be populated."
            )

        if self.target_type == VerificationTargetType.Requirement and not req_present:
            raise ValueError("Target consistency violation: Target_Type 'Requirement' requires Target_Req_ID to be populated.")

        if self.target_type == VerificationTargetType.Control and not ctrl_present:
            raise ValueError("Target consistency violation: Target_Type 'Control' requires Target_Control_ID to be populated.")

        return self


class VerificationCreate(VerificationBase):
    verif_id: str = Field(..., pattern=r"^VRF-[A-Z]{3}-[0-9]{3,4}$")


class VerificationUpdate(BaseModel):
    target_type: Optional[VerificationTargetType] = None
    target_req_id: Optional[str] = Field(default=None, max_length=32)
    target_control_id: Optional[str] = Field(default=None, max_length=32)
    method: Optional[VerificationMethod] = None
    acceptance_crit: Optional[str] = Field(default=None, min_length=15)
    reviewer: Optional[str] = Field(default=None, max_length=64)
    status: Optional[VerificationStatus] = None

    @model_validator(mode="after")
    def validate_update_target_architecture(self):
        # Only validate if both target IDs or target_type are being updated
        if self.target_req_id is not None or self.target_control_id is not None:
            req_present = self.target_req_id is not None and bool(str(self.target_req_id).strip())
            ctrl_present = self.target_control_id is not None and bool(str(self.target_control_id).strip())
            if req_present and ctrl_present:
                raise ValueError("Dual-target constraint violation: Cannot populate both Target_Req_ID and Target_Control_ID.")
        return self


class VerificationResponse(VerificationBase):
    verif_id: str

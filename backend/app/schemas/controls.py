"""EngiTrace AI — Control Schemas (Phase 4)"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.app.domain.models import ControlHierarchyType, ControlStatus


class ControlBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    parent_risk_id: str = Field(..., max_length=32)
    hierarchy_type: ControlHierarchyType
    description: str = Field(..., min_length=15)
    rationale: Optional[str] = None
    post_severity: int = Field(..., ge=1, le=5)
    post_likelihood: int = Field(..., ge=1, le=5)
    owner: Optional[str] = Field(default=None, max_length=64)
    status: ControlStatus = Field(default=ControlStatus.Proposed)
    implementation_date: Optional[datetime] = None


class ControlCreate(ControlBase):
    control_id: str = Field(..., pattern=r"^CTRL-[A-Z]{3}-[0-9]{3,4}$")
    residual_risk: Optional[int] = None

    @model_validator(mode="after")
    def validate_derived_residual_risk(self):
        calculated = self.post_severity * self.post_likelihood
        if self.residual_risk is not None and self.residual_risk != calculated:
            raise ValueError(
                f"Client cannot override calculated Residual_Risk. "
                f"Expected {calculated} (Post_Severity {self.post_severity} × Post_Likelihood {self.post_likelihood}), got {self.residual_risk}."
            )
        self.residual_risk = calculated
        return self


class ControlUpdate(BaseModel):
    parent_risk_id: Optional[str] = Field(default=None, max_length=32)
    hierarchy_type: Optional[ControlHierarchyType] = None
    description: Optional[str] = Field(default=None, min_length=15)
    rationale: Optional[str] = None
    post_severity: Optional[int] = Field(default=None, ge=1, le=5)
    post_likelihood: Optional[int] = Field(default=None, ge=1, le=5)
    residual_risk: Optional[int] = None
    owner: Optional[str] = Field(default=None, max_length=64)
    status: Optional[ControlStatus] = None
    implementation_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_derived_residual_risk(self):
        if self.post_severity is not None and self.post_likelihood is not None:
            calculated = self.post_severity * self.post_likelihood
            if self.residual_risk is not None and self.residual_risk != calculated:
                raise ValueError(
                    f"Client cannot override calculated Residual_Risk. "
                    f"Expected {calculated}, got {self.residual_risk}."
                )
            self.residual_risk = calculated
        return self


class ControlResponse(ControlBase):
    control_id: str
    residual_risk: int

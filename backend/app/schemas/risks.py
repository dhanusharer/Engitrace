"""EngiTrace AI — Risk Schemas (Phase 4)"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.app.domain.models import RiskCategory, RiskStatus


class RiskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    parent_req_id: str = Field(..., max_length=32)
    failure_mode: str = Field(..., min_length=1)
    cause: str = Field(..., min_length=1)
    effect: str = Field(..., min_length=1)
    pre_severity: int = Field(..., ge=1, le=5)
    pre_likelihood: int = Field(..., ge=1, le=5)
    detectability: Optional[int] = Field(default=None, ge=1, le=5)
    risk_category: RiskCategory
    owner: Optional[str] = Field(default=None, max_length=64)
    status: RiskStatus = Field(default=RiskStatus.Identified)


class RiskCreate(RiskBase):
    risk_id: str = Field(..., pattern=r"^RSK-[A-Z]{3}-[0-9]{3,4}$")
    risk_score: Optional[int] = None

    @model_validator(mode="after")
    def validate_derived_risk_score(self):
        calculated = self.pre_severity * self.pre_likelihood
        if self.risk_score is not None and self.risk_score != calculated:
            raise ValueError(
                f"Client cannot override calculated Risk_Score. "
                f"Expected {calculated} (Pre_Severity {self.pre_severity} × Pre_Likelihood {self.pre_likelihood}), got {self.risk_score}."
            )
        self.risk_score = calculated
        return self


class RiskUpdate(BaseModel):
    parent_req_id: Optional[str] = Field(default=None, max_length=32)
    failure_mode: Optional[str] = Field(default=None, min_length=1)
    cause: Optional[str] = Field(default=None, min_length=1)
    effect: Optional[str] = Field(default=None, min_length=1)
    pre_severity: Optional[int] = Field(default=None, ge=1, le=5)
    pre_likelihood: Optional[int] = Field(default=None, ge=1, le=5)
    detectability: Optional[int] = Field(default=None, ge=1, le=5)
    risk_score: Optional[int] = None
    risk_category: Optional[RiskCategory] = None
    owner: Optional[str] = Field(default=None, max_length=64)
    status: Optional[RiskStatus] = None

    @model_validator(mode="after")
    def validate_derived_risk_score(self):
        if self.pre_severity is not None and self.pre_likelihood is not None:
            calculated = self.pre_severity * self.pre_likelihood
            if self.risk_score is not None and self.risk_score != calculated:
                raise ValueError(
                    f"Client cannot override calculated Risk_Score. "
                    f"Expected {calculated}, got {self.risk_score}."
                )
            self.risk_score = calculated
        return self


class RiskResponse(RiskBase):
    risk_id: str
    risk_score: int

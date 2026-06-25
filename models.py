from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PurchaseRequest(BaseModel):
    """Validated input payload for a procurement purchase request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    request_id: str
    requestor: str
    cost_center_id: str
    vendor_name: str
    vendor_id: str
    category: str
    item_description: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    total_amount: float = Field(gt=0)


class ProcurementRecommendation(BaseModel):
    """Structured recommendation output produced by procurement pre-screening."""

    model_config = ConfigDict(str_strip_whitespace=True)

    request_id: str
    decision: Literal["approve", "deny", "escalate"]
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("rationale")
    @classmethod
    def rationale_non_empty(cls, value: str) -> str:
        """Enforce that recommendation rationale is not blank or whitespace-only."""
        if not value.strip():
            raise ValueError("rationale must be a non-empty string")
        return value


RiskLevel = Literal["low", "medium", "high", "critical"]
RiskErrorCode = Literal["vendor_not_found", "vendor_data_unavailable"]


class RiskAssessmentError(BaseModel):
    """Structured error payload for deterministic risk fallback behavior."""

    model_config = ConfigDict(str_strip_whitespace=True)

    code: RiskErrorCode
    message: str
    vendor_id: str | None = None


class RiskAssessmentResult(BaseModel):
    """Structured output contract for the assess_risk tool."""

    model_config = ConfigDict(str_strip_whitespace=True)

    vendor_id: str
    compliance_flag: bool
    compliance_notes: str
    contract_status: str
    risk_level: RiskLevel
    risk_summary: str
    error: RiskAssessmentError | None = None

    @field_validator("risk_summary")
    @classmethod
    def risk_summary_non_empty(cls, value: str) -> str:
        """Enforce that risk_summary is not blank or whitespace-only."""
        if not value.strip():
            raise ValueError("risk_summary must be a non-empty string")
        return value

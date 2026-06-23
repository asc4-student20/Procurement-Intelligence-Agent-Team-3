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

    @field_validator("rationale")
    @classmethod
    def rationale_non_empty(cls, value: str) -> str:
        """Enforce that recommendation rationale is not blank or whitespace-only."""
        if not value.strip():
            raise ValueError("rationale must be a non-empty string")
        return value

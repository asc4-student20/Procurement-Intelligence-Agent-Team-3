"""Risk-assessment tool for procurement pre-screening."""

from __future__ import annotations

from typing import Any

from data import loader
from models import RiskAssessmentError, RiskAssessmentResult, RiskLevel


def assess_risk(vendor_id: str) -> dict[str, Any]:
    """Assess vendor risk from compliance status and contract coverage.

    The tool returns deterministic, explainable risk output and a structured
    fallback when vendor data is unavailable or the vendor cannot be found.

    Args:
        vendor_id: Vendor identifier to evaluate (for example, ``V-006``).

    Returns:
        Structured result dictionary with:

        - ``vendor_id`` (str)
        - ``compliance_flag`` (bool)
        - ``compliance_notes`` (str)
        - ``contract_status`` (str)
        - ``risk_level`` (``low`` | ``medium`` | ``high`` | ``critical``)
        - ``risk_summary`` (str)
        - ``error`` (dict, optional): Includes machine-readable ``code`` and
          context for deterministic fallback outcomes.
    """
    try:
        vendors = loader.load_vendors()
    except FileNotFoundError as exc:
        result = RiskAssessmentResult(
            vendor_id=vendor_id,
            compliance_flag=False,
            compliance_notes="",
            contract_status="unknown",
            risk_level="high",
            risk_summary=(
                "Fallback risk applied because vendor data file is missing; "
                "escalate for manual procurement review."
            ),
            error=RiskAssessmentError(
                code="vendor_data_unavailable",
                message=f"file_not_found at load_vendors: {exc}",
                vendor_id=vendor_id,
            ),
        )
        return result.model_dump(exclude_none=True)
    except KeyError as exc:
        result = RiskAssessmentResult(
            vendor_id=vendor_id,
            compliance_flag=False,
            compliance_notes="",
            contract_status="unknown",
            risk_level="high",
            risk_summary=(
                "Fallback risk applied because vendor data keys are missing; "
                "escalate for manual procurement review."
            ),
            error=RiskAssessmentError(
                code="vendor_data_unavailable",
                message=f"key_error at load_vendors: {exc}",
                vendor_id=vendor_id,
            ),
        )
        return result.model_dump(exclude_none=True)
    except Exception as exc:  # pragma: no cover - defensive branch
        result = RiskAssessmentResult(
            vendor_id=vendor_id,
            compliance_flag=False,
            compliance_notes="",
            contract_status="unknown",
            risk_level="high",
            risk_summary=(
                "Fallback risk applied because vendor data is unavailable; "
                "escalate for manual procurement review."
            ),
            error=RiskAssessmentError(
                code="vendor_data_unavailable",
                message=f"unexpected_error at load_vendors: {exc}",
                vendor_id=vendor_id,
            ),
        )
        return result.model_dump(exclude_none=True)

    vendor = next(
        (row for row in vendors if str(row.get("vendor_id", "")) == vendor_id),
        None,
    )

    if vendor is None:
        result = RiskAssessmentResult(
            vendor_id=vendor_id,
            compliance_flag=False,
            compliance_notes="",
            contract_status="unknown",
            risk_level="high",
            risk_summary=(
                "Fallback risk applied because vendor record was not found; "
                "escalate for manual procurement review."
            ),
            error=RiskAssessmentError(
                code="vendor_not_found",
                message="Vendor ID does not exist in vendor data.",
                vendor_id=vendor_id,
            ),
        )
        return result.model_dump(exclude_none=True)

    compliance_flag = bool(vendor.get("compliance_flag", False))
    compliance_notes = str(vendor.get("compliance_notes", ""))
    contract_status = str(vendor.get("contract_status", "none")).strip().lower() or "none"

    risk_level = _compute_risk_level(compliance_flag, contract_status)
    risk_summary = _build_risk_summary(risk_level, compliance_flag, contract_status)

    result = RiskAssessmentResult(
        vendor_id=vendor_id,
        compliance_flag=compliance_flag,
        compliance_notes=compliance_notes,
        contract_status=contract_status,
        risk_level=risk_level,
        risk_summary=risk_summary,
    )
    return result.model_dump(exclude_none=True)


def _compute_risk_level(compliance_flag: bool, contract_status: str) -> RiskLevel:
    """Compute normalized risk level using deterministic precedence rules."""
    if compliance_flag:
        return "critical"
    if contract_status == "expired":
        return "high"
    if contract_status == "none":
        return "medium"
    return "low"


def _build_risk_summary(
    risk_level: RiskLevel,
    compliance_flag: bool,
    contract_status: str,
) -> str:
    """Build a concise explanation for the assigned risk level."""
    if compliance_flag:
        return (
            "Risk is critical because the vendor has an active compliance flag, "
            "which requires immediate escalation."
        )

    if contract_status == "expired":
        return (
            "Risk is high because the vendor contract is expired and must be "
            "renewed or replaced before approval."
        )

    if contract_status == "none":
        return (
            "Risk is medium because no active vendor contract is on file, "
            "requiring additional procurement review."
        )

    return (
        f"Risk is {risk_level} because the vendor has an active contract and no "
        "compliance issues."
    )

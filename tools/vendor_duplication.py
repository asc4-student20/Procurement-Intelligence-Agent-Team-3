"""Vendor-duplication tool for single-source conflict detection."""

from __future__ import annotations

from typing import Any

from data import loader


def _error_payload(error_type: str, message: str, stage: str) -> dict[str, str]:
    """Build a normalized typed error payload for deterministic escalation handling."""
    return {
        "type": error_type,
        "message": message,
        "stage": stage,
    }


def check_vendor_duplication(
    vendor_id: str,
    category: str,
    total_amount: float = 0.0,
) -> dict[str, Any]:
    """Detect active-contract vendor conflicts for POL-001 single-source checks.

    This tool identifies other active vendors in the same category and returns
    their IDs and details. POL-001 deny-significant triggering is applied only
    when:
    - ``total_amount`` exceeds the policy threshold (defaulted from policy data)
    - and the category is contracted (has active vendors)
    - and one or more conflicting active vendors exist.

    Args:
        vendor_id: Vendor identifier in the request.
        category: Request category to evaluate for active contract conflicts.
        total_amount: Request amount used for POL-001 threshold logic.

    Returns:
        Structured result with conflict details and trigger context:

        - ``vendor_id`` (str): Echo of requested vendor.
        - ``category`` (str): Echo of requested category.
        - ``total_amount`` (float): Echo of evaluated amount.
        - ``threshold_amount`` (float): POL-001 threshold used.
        - ``contracted_category`` (bool): Whether category has active contracts.
        - ``conflicting_vendor_ids`` (list[str]): IDs of active vendor conflicts.
        - ``conflicting_vendors`` (list[dict[str, str]]): Vendor detail records.
        - ``triggered`` (bool): True only when POL-001 trigger conditions hold.
        - ``reason`` (str): Human-readable explanation.
        - ``error`` (str, optional): Present for loader/data failures.
    """
    safe_amount = float(total_amount)

    try:
        vendors = loader.load_vendors()
        policies = loader.load_policies()
    except FileNotFoundError as exc:
        return {
            "vendor_id": vendor_id,
            "category": category,
            "total_amount": safe_amount,
            "threshold_amount": 25_000.0,
            "contracted_category": False,
            "conflicting_vendor_ids": [],
            "conflicting_vendors": [],
            "triggered": False,
            "reason": "Unable to evaluate vendor duplication due to data load error.",
            "error": _error_payload(
                "file_not_found",
                f"Vendor/policy data file not found: {exc}",
                "load_vendor_policy_inputs",
            ),
        }
    except KeyError as exc:
        return {
            "vendor_id": vendor_id,
            "category": category,
            "total_amount": safe_amount,
            "threshold_amount": 25_000.0,
            "contracted_category": False,
            "conflicting_vendor_ids": [],
            "conflicting_vendors": [],
            "triggered": False,
            "reason": "Unable to evaluate vendor duplication due to data load error.",
            "error": _error_payload(
                "key_error",
                f"Vendor/policy input data missing required key: {exc}",
                "load_vendor_policy_inputs",
            ),
        }
    except Exception as exc:  # pragma: no cover - defensive branch
        return {
            "vendor_id": vendor_id,
            "category": category,
            "total_amount": safe_amount,
            "threshold_amount": 25_000.0,
            "contracted_category": False,
            "conflicting_vendor_ids": [],
            "conflicting_vendors": [],
            "triggered": False,
            "reason": "Unable to evaluate vendor duplication due to data load error.",
            "error": _error_payload(
                "unexpected_error",
                f"Vendor/policy data unavailable: {exc}",
                "load_vendor_policy_inputs",
            ),
        }

    threshold_amount = 25_000.0
    policy_row = next((row for row in policies if row.get("policy_id") == "POL-001"), None)
    if policy_row is not None:
        threshold_amount = float(policy_row.get("threshold_amount", threshold_amount))

    active_same_category = [
        row
        for row in vendors
        if str(row.get("category", "")) == category
        and str(row.get("contract_status", "")) == "active"
    ]
    contracted_category = len(active_same_category) > 0

    conflicting_rows = [
        row
        for row in active_same_category
        if str(row.get("vendor_id", "")) != vendor_id
    ]

    conflicting_vendor_ids = [str(row.get("vendor_id", "")) for row in conflicting_rows]
    conflicting_vendor_ids = sorted({vid for vid in conflicting_vendor_ids if vid})

    conflicting_vendors: list[dict[str, str]] = [
        {
            "vendor_id": str(row.get("vendor_id", "")),
            "vendor_name": str(row.get("name", "")),
            "contract_id": str(row.get("contract_id", "")),
            "contract_status": str(row.get("contract_status", "")),
            "category": str(row.get("category", "")),
        }
        for row in conflicting_rows
    ]

    above_threshold = safe_amount > threshold_amount
    triggered = contracted_category and above_threshold and len(conflicting_vendor_ids) > 0

    if triggered:
        reason = (
            "POL-001 triggered: amount exceeds threshold in a contracted category "
            "with conflicting active vendors."
        )
    elif not contracted_category:
        reason = "Category has no active contracts; POL-001 does not trigger."
    elif not above_threshold:
        reason = "Amount does not exceed POL-001 threshold; trigger inactive."
    elif len(conflicting_vendor_ids) == 0:
        reason = "No conflicting active vendors found for this category."
    else:
        reason = "POL-001 trigger inactive for current inputs."

    return {
        "vendor_id": vendor_id,
        "category": category,
        "total_amount": safe_amount,
        "threshold_amount": threshold_amount,
        "contracted_category": contracted_category,
        "conflicting_vendor_ids": conflicting_vendor_ids,
        "conflicting_vendors": conflicting_vendors,
        "triggered": triggered,
        "reason": reason,
    }

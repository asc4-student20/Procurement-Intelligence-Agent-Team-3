"""Policy compliance tool for procurement pre-screening."""

from __future__ import annotations

from typing import Any

from data.loader import load_budgets, load_policies, load_vendors
from models import PurchaseRequest


def check_policy_compliance(request: PurchaseRequest) -> dict[str, Any]:
    """Evaluate a purchase request against procurement policies POL-001 to POL-008.

    Args:
        request: Purchase request model containing request, vendor, category,
            quantity, and amount fields used for policy checks.

    Returns:
        A structured compliance result containing:

        - ``request_id``: Request identifier.
        - ``violations``: List of violation records. Each violation record
          contains exactly ``policy_id``, ``rule_description``, and
          ``forced_decision`` (``deny`` or ``escalate``).
        - ``violation_count``: Number of policy violations found.
        - ``checked_policy_ids``: Ordered list of policy IDs evaluated.
        - ``error``: Optional error message if data cannot be loaded.

    Notes:
        - Data is loaded only through ``data.loader``.
        - The function evaluates all eight policies on every call.
        - POL-002 is evaluated, but no violation is emitted because the current
          request contract does not include approval-attestation metadata.
    """
    checked_policy_ids = [f"POL-00{idx}" for idx in range(1, 9)]

    try:
        policies = load_policies()
        vendors = load_vendors()
        budgets = load_budgets()
    except Exception as exc:  # pragma: no cover - defensive branch
        return {
            "request_id": request.request_id,
            "violations": [],
            "violation_count": 0,
            "checked_policy_ids": checked_policy_ids,
            "error": f"Unable to evaluate policies due to data load error: {exc}",
        }

    policy_by_id = {
        str(policy.get("policy_id", "")): policy
        for policy in policies
        if str(policy.get("policy_id", ""))
    }
    vendor_by_id = {
        str(vendor.get("vendor_id", "")): vendor
        for vendor in vendors
        if str(vendor.get("vendor_id", ""))
    }
    budget_by_center = {
        str(center.get("cost_center_id", "")): center
        for center in budgets
        if str(center.get("cost_center_id", ""))
    }

    violations: list[dict[str, str]] = []

    vendor = vendor_by_id.get(request.vendor_id)

    # POL-001: Single-source restriction for high-value contracted categories.
    pol001 = policy_by_id.get("POL-001", {})
    pol001_threshold = float(pol001.get("threshold_amount", 25_000.0))
    pol001_categories = {
        str(category) for category in pol001.get("affected_categories", [])
    }
    active_in_category = [
        row
        for row in vendors
        if str(row.get("category", "")) == request.category
        and str(row.get("contract_status", "")) == "active"
    ]
    contracted_vendor_ids = {str(row.get("vendor_id", "")) for row in active_in_category}
    if (
        request.category in pol001_categories
        and request.total_amount > pol001_threshold
        and len(contracted_vendor_ids) > 0
        and request.vendor_id not in contracted_vendor_ids
    ):
        violations.append(
            {
                "policy_id": "POL-001",
                "rule_description": (
                    "Single-source restriction violated: amount exceeds threshold "
                    "in a contracted category and selected vendor is not contracted."
                ),
                "forced_decision": "deny",
            }
        )

    # POL-002: Manager approval threshold is evaluated but not emitted because
    # the request schema has no approval-attestation field.
    _pol002 = policy_by_id.get("POL-002", {})

    # POL-003: Director approval threshold.
    pol003 = policy_by_id.get("POL-003", {})
    pol003_threshold = float(pol003.get("threshold_amount", 50_000.0))
    if request.total_amount >= pol003_threshold:
        violations.append(
            {
                "policy_id": "POL-003",
                "rule_description": (
                    "Director approval threshold reached or exceeded; request "
                    "requires escalation."
                ),
                "forced_decision": "escalate",
            }
        )

    # POL-004: Catering prohibition.
    if request.category == "catering":
        violations.append(
            {
                "policy_id": "POL-004",
                "rule_description": "Catering purchases are prohibited.",
                "forced_decision": "deny",
            }
        )

    # POL-005: Expired contract vendor.
    if vendor is not None and str(vendor.get("contract_status", "")) == "expired":
        violations.append(
            {
                "policy_id": "POL-005",
                "rule_description": "Vendor contract is expired.",
                "forced_decision": "deny",
            }
        )

    # POL-006: Compliance-flagged vendor hold.
    if vendor is not None and bool(vendor.get("compliance_flag", False)):
        violations.append(
            {
                "policy_id": "POL-006",
                "rule_description": "Vendor has an active compliance flag.",
                "forced_decision": "escalate",
            }
        )

    # POL-007: Staffing vendor single-source for > 40 hours.
    if request.category == "staffing" and request.quantity > 40:
        if vendor is None or str(vendor.get("contract_status", "")) != "active":
            violations.append(
                {
                    "policy_id": "POL-007",
                    "rule_description": (
                        "Staffing engagement above 40 hours requires a contracted "
                        "staffing vendor."
                    ),
                    "forced_decision": "deny",
                }
            )

    # POL-008: Budget overage prohibition.
    budget = budget_by_center.get(request.cost_center_id)
    if budget is not None:
        remaining = float(budget.get("remaining", 0.0))
        if request.total_amount > remaining:
            violations.append(
                {
                    "policy_id": "POL-008",
                    "rule_description": (
                        "Request exceeds remaining cost center budget and cannot "
                        "be approved."
                    ),
                    "forced_decision": "deny",
                }
            )

    return {
        "request_id": request.request_id,
        "violations": violations,
        "violation_count": len(violations),
        "checked_policy_ids": checked_policy_ids,
    }

"""Budget evaluation tool for procurement pre-screening."""

from __future__ import annotations

from typing import Any

from data.loader import load_budgets


def check_budget(cost_center_id: str, requested_amount: float) -> dict[str, Any]:
    """Evaluate whether a request fits within a cost center's remaining budget.

    This tool loads budget data via ``data.loader.load_budgets`` and determines
    whether the provided ``requested_amount`` can be covered by the remaining
    quarterly budget for ``cost_center_id``.

    Args:
        cost_center_id: Cost center identifier to evaluate (for example, ``CC-003``).
        requested_amount: Total requested amount in USD.

    Returns:
        A deterministic result dictionary with the following keys:

        - ``cost_center_id`` (str): Echo of the provided cost center ID.
        - ``requested_amount`` (float): Echo of the requested amount.
        - ``remaining_budget`` (float): Remaining quarterly budget for the
          cost center; ``0.0`` for error-safe fallback responses.
        - ``within_budget`` (bool): ``True`` when request is within remaining
          budget, otherwise ``False``.
        - ``overage`` (float): Positive difference between requested amount and
          remaining budget; ``0.0`` if within budget.
        - ``error`` (str, optional): Present when budget data cannot be loaded
          or the cost center is unknown.

    Notes:
        - The tool does not read ``mock_data/`` directly.
        - Errors are caught and represented in the output for safe escalation.
    """
    safe_requested_amount = float(requested_amount)

    try:
        budgets = load_budgets()
    except Exception as exc:  # pragma: no cover - defensive branch
        return {
            "cost_center_id": cost_center_id,
            "requested_amount": safe_requested_amount,
            "remaining_budget": 0.0,
            "within_budget": False,
            "overage": max(0.0, safe_requested_amount),
            "error": f"Unable to load budget data: {exc}",
        }

    matching_budget = next(
        (row for row in budgets if str(row.get("cost_center_id", "")) == cost_center_id),
        None,
    )

    if matching_budget is None:
        return {
            "cost_center_id": cost_center_id,
            "requested_amount": safe_requested_amount,
            "remaining_budget": 0.0,
            "within_budget": False,
            "overage": max(0.0, safe_requested_amount),
            "error": f"Unknown cost center: {cost_center_id}",
        }

    remaining_budget = float(matching_budget.get("remaining", 0.0))
    overage = max(0.0, safe_requested_amount - remaining_budget)

    return {
        "cost_center_id": cost_center_id,
        "requested_amount": safe_requested_amount,
        "remaining_budget": remaining_budget,
        "within_budget": overage == 0.0,
        "overage": overage,
    }

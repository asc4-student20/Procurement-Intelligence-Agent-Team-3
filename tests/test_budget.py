"""Tests for budget evaluation tool."""

from tools.budget import check_budget


def test_check_budget_cc003_within_and_over_budget() -> None:
    """Validate within-budget and over-budget outcomes for CC-003 using real data."""
    within_result = check_budget("CC-003", 6_900.0)
    assert within_result["within_budget"] is True
    assert within_result["remaining_budget"] == 6_900.0
    assert within_result["overage"] == 0.0
    assert "error" not in within_result

    over_result = check_budget("CC-003", 7_000.0)
    assert over_result["within_budget"] is False
    assert over_result["remaining_budget"] == 6_900.0
    assert over_result["overage"] == 100.0
    assert "error" not in over_result

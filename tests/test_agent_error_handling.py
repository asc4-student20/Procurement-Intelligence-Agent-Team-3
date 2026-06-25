"""Tests for agent-level error escalation behavior."""

from __future__ import annotations

import asyncio
from typing import Any

import agent
from models import ProcurementRecommendation, PurchaseRequest


def test_agent_escalates_when_budget_data_file_missing(monkeypatch: Any) -> None:
    """Budget loader FileNotFoundError should force escalate with error-aware rationale."""

    def _raise_missing_budget_file() -> list[dict[str, Any]]:
        raise FileNotFoundError("budgets.json was not found")

    monkeypatch.setattr("data.loader.load_budgets", _raise_missing_budget_file)

    class _DummyResult:
        def __init__(self) -> None:
            self.output = ProcurementRecommendation(
                request_id="REQ-DUMMY",
                decision="approve",
                rationale="",
                confidence=0.9,
            )

    async def _fake_run(_prompt: str) -> _DummyResult:
        return _DummyResult()

    monkeypatch.setattr(agent.procurement_agent, "run", _fake_run)

    request = PurchaseRequest(
        request_id="REQ-ERR-BUDGET-001",
        requestor="A. Analyst",
        cost_center_id="CC-001",
        vendor_name="BlueSky Cloud Solutions",
        vendor_id="V-002",
        category="software_licenses",
        item_description="Error handling verification",
        quantity=1,
        unit_price=500.0,
        total_amount=500.0,
    )

    recommendation = asyncio.run(agent.evaluate_purchase_request(request))

    assert recommendation.decision == "escalate"
    assert "budget check error" in recommendation.rationale.lower()
    assert "file_not_found" in recommendation.rationale.lower()
    assert "load_budgets" in recommendation.rationale.lower()

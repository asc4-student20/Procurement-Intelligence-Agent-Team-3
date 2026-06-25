"""Additional error-path tests for agent recommendation handling."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

# Allow agent module import in test environments without real model credentials.
os.environ.setdefault("OPENAI_API_KEY", "test-key")

import agent
from models import ProcurementRecommendation, PurchaseRequest


class _DummyResult:
    """Minimal result object used to stub procurement_agent.run."""

    def __init__(self) -> None:
        self.output = ProcurementRecommendation(
            request_id="REQ-DUMMY",
            decision="approve",
            rationale="placeholder rationale",
            confidence=0.9,
        )


async def _fake_run(_prompt: str) -> _DummyResult:
    """Stub model call so tests validate deterministic error handling only."""
    return _DummyResult()


def test_agent_handles_budget_loader_runtime_error_with_rationale() -> None:
    """RuntimeError in load_budgets should return recommendation with failure-aware rationale."""
    request = PurchaseRequest(
        request_id="REQ-ERR-BUDGET-RT-001",
        requestor="A. Analyst",
        cost_center_id="CC-001",
        vendor_name="BlueSky Cloud Solutions",
        vendor_id="V-002",
        category="software_licenses",
        item_description="RuntimeError handling verification",
        quantity=1,
        unit_price=500.0,
        total_amount=500.0,
    )

    with patch("data.loader.load_budgets", side_effect=RuntimeError("simulated budgets outage")):
        with patch.object(agent.procurement_agent, "run", _fake_run):
            recommendation = asyncio.run(agent.evaluate_purchase_request(request))

    assert recommendation.decision == "escalate"
    assert isinstance(recommendation.rationale, str)
    assert recommendation.rationale.strip()
    assert "budget" in recommendation.rationale.lower()
    assert "error" in recommendation.rationale.lower()


def test_agent_escalates_for_unknown_vendor_with_failure_context() -> None:
    """Unknown vendor_id should escalate with rationale that mentions vendor lookup failure."""
    request = PurchaseRequest(
        request_id="REQ-ERR-VENDOR-001",
        requestor="A. Analyst",
        cost_center_id="CC-001",
        vendor_name="Unknown Vendor Inc",
        vendor_id="V-999",
        category="software_licenses",
        item_description="Unknown vendor handling verification",
        quantity=1,
        unit_price=1200.0,
        total_amount=1200.0,
    )

    with patch.object(agent.procurement_agent, "run", _fake_run):
        recommendation = asyncio.run(agent.evaluate_purchase_request(request))

    rationale = recommendation.rationale.lower()

    assert recommendation.decision == "escalate"
    assert recommendation.rationale.strip()
    assert "vendor" in rationale
    assert (
        "not found" in rationale
        or "does not exist" in rationale
        or "vendor_not_found" in rationale
    )

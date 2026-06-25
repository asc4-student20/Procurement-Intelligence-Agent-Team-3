"""Async tests for end-to-end purchase request decisions."""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

import pytest

# Allow agent module import in test environments without real model credentials.
os.environ.setdefault("OPENAI_API_KEY", "test-key")

import agent as agent_module
from agent import evaluate_purchase_request
from data.loader import load_requests
from models import PurchaseRequest, ProcurementRecommendation


def _fixture_by_id(request_id: str) -> dict[str, Any]:
    """Return raw request fixture from mock_data/requests.json by request_id."""
    requests_data = load_requests()
    for request_data in requests_data:
        if request_data.get("request_id") == request_id:
            return request_data
    raise ValueError(f"Request ID {request_id} not found in mock_data/requests.json")


def _request_by_id(request_id: str) -> PurchaseRequest:
    """Return a typed request from mock_data/requests.json by request_id."""
    request_data = _fixture_by_id(request_id)
    payload = {
        key: value
        for key, value in request_data.items()
        if key in PurchaseRequest.model_fields
    }
    return PurchaseRequest(**payload)


async def _run_request(request_id: str) -> SimpleNamespace:
    """Evaluate a request and return a result-like object with .output."""
    recommendation = await evaluate_purchase_request(_request_by_id(request_id))
    return SimpleNamespace(output=recommendation)


@pytest.fixture(autouse=True)
def _stub_agent_run(monkeypatch: Any) -> None:
    """Stub external model call so tests validate deterministic decision logic only."""

    class _DummyResult:
        def __init__(self) -> None:
            self.output = ProcurementRecommendation(
                request_id="REQ-DUMMY",
                decision="approve",
                rationale=(
                    "The budget check, vendor duplication check, policy compliance check, "
                    "and risk assessment check were applied. "
                    "Evidence includes policy context POL-001 and amount $1.00."
                ),
            )

    async def _fake_run(_prompt: str) -> _DummyResult:
        return _DummyResult()

    monkeypatch.setattr(agent_module.procurement_agent, "run", _fake_run)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_id",
    [
        # deny-type
        "REQ-006",
        "REQ-007",
        "REQ-008",
        "REQ-009",
        # escalate-type
        "REQ-010",
        "REQ-011",
        # approve-type
        "REQ-001",
        "REQ-002",
        "REQ-003",
    ],
)
async def test_agent_matches_fixture_expected_outcome(request_id: str) -> None:
    """Decision should match expected_outcome from fixture for sampled requests."""
    fixture = _fixture_by_id(request_id)
    expected_outcome = str(fixture["expected_outcome"])

    result = await _run_request(request_id)
    recommendation: ProcurementRecommendation = result.output

    assert expected_outcome == recommendation.decision
    assert isinstance(recommendation.rationale, str)
    assert recommendation.rationale.strip()


@pytest.mark.asyncio
async def test_req_015_tight_budget_escalates() -> None:
    """REQ-015 should escalate when post-purchase budget is below the tight-budget threshold."""
    result = await _run_request("REQ-015")
    recommendation: ProcurementRecommendation = result.output

    assert recommendation.decision == "escalate"
    assert "remaining budget" in recommendation.rationale.lower()
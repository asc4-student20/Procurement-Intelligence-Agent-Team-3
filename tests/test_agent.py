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


def _request_by_id(request_id: str) -> PurchaseRequest:
    """Return a typed request from mock_data/requests.json by request_id."""
    requests_data = load_requests()
    for request_data in requests_data:
        if request_data.get("request_id") == request_id:
            payload = {
                key: value
                for key, value in request_data.items()
                if key in PurchaseRequest.model_fields
            }
            return PurchaseRequest(**payload)
    raise ValueError(f"Request ID {request_id} not found in mock_data/requests.json")


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


def _assert_recommendation(
    result: Any,
    expected_decision: str,
) -> None:
    """Assert decision and rationale output contract for a run result."""
    recommendation: ProcurementRecommendation = result.output
    assert recommendation.decision == expected_decision
    assert isinstance(recommendation.rationale, str)
    assert recommendation.rationale.strip()


@pytest.mark.asyncio
async def test_agent_req_001_approve() -> None:
    """REQ-001 should be approved."""
    result = await _run_request("REQ-001")
    _assert_recommendation(result, "approve")


@pytest.mark.asyncio
async def test_agent_req_006_deny_budget_overage() -> None:
    """REQ-006 should be denied for CC-003 budget overage."""
    result = await _run_request("REQ-006")
    _assert_recommendation(result, "deny")


@pytest.mark.asyncio
async def test_agent_req_009_policy_deny_catering() -> None:
    """REQ-009 should be denied due to POL-004 catering prohibition."""
    result = await _run_request("REQ-009")
    _assert_recommendation(result, "deny")


@pytest.mark.asyncio
async def test_agent_req_011_escalate_compliance_flag() -> None:
    """REQ-011 should be escalated for compliance-flagged vendor."""
    result = await _run_request("REQ-011")
    _assert_recommendation(result, "escalate")
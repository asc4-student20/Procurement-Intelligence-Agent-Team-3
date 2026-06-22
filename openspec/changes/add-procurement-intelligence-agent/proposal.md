## Why

FedEx procurement teams need a consistent pre-screening step so purchase requests are evaluated against the same budget, policy, and vendor risk criteria before human review. Defining this now reduces inconsistent decisions and provides a typed, auditable recommendation contract (`approve`, `deny`, `escalate`) for downstream workflows.

## What Changes

- Introduce a Pydantic AI procurement agent that evaluates purchase requests and returns a structured recommendation with a non-empty rationale.
- Define strict Pydantic v2 input/output contracts: `PurchaseRequest` and `ProcurementRecommendation`.
- Constrain recommendation decisions to exactly `approve`, `deny`, or `escalate`.
- Require the agent to run four checks for every request: budget, vendor duplication, policy compliance, and risk assessment.
- Enforce decision priority `escalate > deny > approve` across conflicting signals.
- Require tool failures to be captured and reflected in rationale, with escalation for safe handling.
- Standardize mock-data access through `data/loader.py` and prohibit direct reads from `mock_data/` in tool logic.

## Capabilities

### New Capabilities
- `procurement-pre-screening`: Evaluate purchase requests with four domain checks and produce a typed `approve`/`deny`/`escalate` recommendation with explicit rationale.

### Modified Capabilities
- None.

## Impact

- Affected code: `agent.py`, `models.py`, `tools/`, `data/loader.py`, and tests under `tests/`.
- API/contract impact: introduces and enforces structured input/output model contracts and decision enum restrictions.
- Operational impact: adds deterministic decision precedence and explicit tool-error escalation behavior.
- Dependency impact: relies on `pydantic-ai` and Pydantic v2 for model validation and structured output.

## Context

FedEx procurement requests are currently assessed with policy and budget knowledge that can vary by reviewer and timing. The target change introduces a pre-screening agent that standardizes recommendation generation while preserving human final approval authority. The implementation spans multiple modules (`agent.py`, `models.py`, `tools/`, and `data/loader.py`) and depends on deterministic decision precedence and structured output.

Constraints:
- Runtime contracts must be Pydantic v2 models.
- Agent construction must use `pydantic-ai` structured output.
- Tooling must read reference data through `data/loader.py`, not direct `mock_data/` access.
- Recommendation decision values must be exactly `approve`, `deny`, `escalate`.

Stakeholders:
- Procurement officers (consume recommendations and rationale)
- Engineering team (maintains checks and model contracts)
- Compliance and Legal teams (depend on escalation correctness)

## Goals / Non-Goals

**Goals:**
- Provide deterministic pre-screening recommendations from a typed input model.
- Enforce four mandatory checks for every request: budget, vendor duplication, policy compliance, and risk assessment.
- Produce structured output with constrained decision values and a non-empty rationale.
- Apply conflict resolution through strict priority `escalate > deny > approve`.
- Surface tool/data errors in rationale and escalate safely.

**Non-Goals:**
- Replace human procurement authority with automatic approvals.
- Add new external data sources or live API integrations.
- Redesign the policy catalog beyond current mocked policy set.
- Introduce UI or workflow orchestration outside the recommendation contract.

## Decisions

1. Use two Pydantic v2 models as hard I/O contracts.
- Decision: `PurchaseRequest` defines all required request fields; `ProcurementRecommendation` defines `request_id`, constrained `decision`, and non-empty `rationale`.
- Rationale: Typed contracts prevent schema drift and simplify testing and tool interoperability.
- Alternative considered: untyped dict input/output. Rejected due to weak validation and higher risk of malformed recommendations.

2. Configure the agent with structured output enforcement.
- Decision: Construct the agent with `output_type=ProcurementRecommendation`.
- Rationale: Guarantees output schema alignment and decision enum enforcement at runtime boundary.
- Alternative considered: free-form LLM output parsed post-hoc. Rejected due to parsing fragility and weaker safety guarantees.

3. Execute all four domain tools for every request.
- Decision: Always invoke budget, duplication, policy, and risk checks before final decision.
- Rationale: Full-check execution produces complete rationale and avoids hidden contradictions caused by short-circuiting.
- Alternative considered: stop after first hard violation. Rejected because it omits material findings needed by procurement reviewers.

4. Centralize reference-data reads through loader abstraction.
- Decision: Tools call `data/loader.py` only; direct `mock_data/` file reads are disallowed in tool code.
- Rationale: One access layer improves maintainability, testability, and future backend replacement.
- Alternative considered: each tool reading JSON directly. Rejected due to duplication and inconsistent error handling.

5. Apply strict recommendation precedence.
- Decision: Resolve mixed signals using `escalate > deny > approve`.
- Rationale: Compliance and uncertainty outcomes must dominate to avoid unsafe denials/approvals when higher-risk evidence exists.
- Alternative considered: deny-first priority. Rejected because it can mask conditions that must be escalated (for example compliance holds or tool failures).

6. Treat tool errors as escalation signals with explicit rationale text.
- Decision: Any tool error must be captured and reflected in recommendation rationale; decision escalates.
- Rationale: Missing or unavailable data is a safety condition requiring human review.
- Alternative considered: ignore errors and proceed with remaining checks. Rejected because it can produce false confidence.

## Risks / Trade-offs

- [Risk] Policy and tool logic diverge from sample expectation labels over time.
  - Mitigation: maintain scenario-based tests per tool and end-to-end recommendation fixtures.

- [Risk] Over-escalation reduces reviewer throughput.
  - Mitigation: make escalation triggers explicit and test near-threshold and error paths separately.

- [Risk] Data-shape mismatch between loader outputs and tool expectations.
  - Mitigation: validate loaded records and keep loader field contracts documented and tested.

- [Risk] Rationale quality may degrade while still non-empty.
  - Mitigation: enforce rationale content requirements in agent prompt and tests.

## Migration Plan

1. Introduce/confirm Pydantic models in `models.py` with required constraints.
2. Wire agent construction with structured output and required tool list.
3. Normalize tool data access through `data/loader.py`.
4. Add/update tests for each tool success path and decision-priority scenarios.
5. Run project test suite and capture results artifact before review.

Rollback approach:
- Revert to previous agent wiring and model definitions while preserving data files.
- Restore prior decision behavior if regression appears in recommendation outcomes.

## Open Questions

- Should strict regex validation be added for IDs (`REQ-*`, `CC-*`, `V-*`) in this change or deferred?
- Should `total_amount` be validated against `quantity * unit_price` inside the model with tolerance?
- Should medium-risk (`contract_status=none`) outcomes ever force escalation by policy rather than remain contextual?

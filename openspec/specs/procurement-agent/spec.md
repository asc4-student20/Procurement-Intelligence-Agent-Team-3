## Purpose
Define orchestration requirements for the procurement agent that evaluates requests and returns deterministic, typed recommendations.

## Requirements

### Requirement: agent.py SHALL use typed request and recommendation contracts from models.py
The `agent.py` implementation SHALL accept input validated as `PurchaseRequest` from `models.py` and SHALL return output validated as `ProcurementRecommendation` from `models.py`.

#### Scenario: Valid typed request produces typed recommendation
- **WHEN** `agent.py` receives a valid `PurchaseRequest`
- **THEN** it produces a `ProcurementRecommendation` with `request_id`, `decision`, and `rationale`

#### Scenario: Invalid request is rejected before decisioning
- **WHEN** input fails `PurchaseRequest` validation (for example, `quantity <= 0`)
- **THEN** tool execution and recommendation synthesis do not proceed with invalid data

### Requirement: agent.py SHALL execute all four domain tools for each evaluated request
For every valid request, `agent.py` SHALL execute all implemented checks: `check_budget`, `check_vendor_duplication`, `check_policy_compliance`, and `assess_risk`.

#### Scenario: Full tool coverage per request
- **WHEN** `agent.py` evaluates a valid `PurchaseRequest`
- **THEN** all four tool results are collected and made available to recommendation synthesis

#### Scenario: Tool arguments are mapped from request fields
- **WHEN** tools are invoked
- **THEN** `check_budget` receives `cost_center_id` and `total_amount`, `check_vendor_duplication` receives `vendor_id`, `category`, and `total_amount`, `check_policy_compliance` receives the full `PurchaseRequest`, and `assess_risk` receives `vendor_id`

### Requirement: Final decision logic SHALL be deterministic post-processing in agent.py
`agent.py` SHALL compute the final recommendation decision in deterministic post-processing logic using normalized tool outcomes, and SHALL NOT delegate final decision arbitration to prompt-only behavior.

#### Scenario: Deterministic arbiter used for final decision
- **WHEN** all tool outcomes are available
- **THEN** `agent.py` computes decision from explicit decision rules before final output is returned

### Requirement: Decision priority SHALL resolve conflicting tool outcomes
When multiple checks fire with conflicting outcomes, `agent.py` SHALL apply strict priority: `escalate` over `deny`, and `deny` over `approve`.

#### Scenario: Escalate overrides deny
- **WHEN** one or more escalation triggers and one or more deny triggers are both present
- **THEN** the final decision is `escalate`

#### Scenario: Deny applies when no escalation trigger exists
- **WHEN** one or more deny triggers are present and no escalation trigger exists
- **THEN** the final decision is `deny`

#### Scenario: Approve requires clean checks
- **WHEN** no escalation triggers and no deny triggers are present across all four tools
- **THEN** the final decision is `approve`

### Requirement: Tool errors SHALL be surfaced and handled safely without crashing recommendation flow
`agent.py` SHALL catch tool exceptions and tool-reported error conditions, include error context in recommendation rationale, and force a safe `escalate` decision rather than crashing or returning partial unvalidated output.

#### Scenario: Tool exception converted to safe escalation
- **WHEN** a tool raises an exception during execution
- **THEN** `agent.py` captures the error, records the failing tool context, and returns decision `escalate`

#### Scenario: Tool-reported error field forces escalation
- **WHEN** a tool returns an explicit error condition in its result payload
- **THEN** the final decision is `escalate` and rationale references the tool error context

#### Scenario: Recommendation remains schema-valid under error conditions
- **WHEN** one or more tool errors occur
- **THEN** returned output still conforms to `ProcurementRecommendation` with non-empty rationale

### Requirement: System prompt SHALL be constrained to evidence-grounded rationale generation
The system prompt used by `agent.py` SHALL constrain model behavior to use tool evidence only, produce no invented facts, and emit recommendations conforming to `ProcurementRecommendation` with decision restricted to `approve|deny|escalate` and non-empty rationale.

#### Scenario: Prompt enforces schema-aligned recommendation content
- **WHEN** recommendation text is generated
- **THEN** rationale references relevant tool findings and does not contradict deterministic decision arbitration

#### Scenario: Prompt encodes escalation-on-uncertainty safety posture
- **WHEN** evidence is incomplete, conflicting, or error-bearing
- **THEN** prompt guidance reinforces that unresolved risk and data uncertainty must support escalation-oriented rationale

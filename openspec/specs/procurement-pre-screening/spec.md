## Purpose
Define top-level procurement pre-screening behavior and output contracts.

## Requirements

### Requirement: Agent produces structured procurement recommendation
The system SHALL evaluate each valid purchase request and return a structured `ProcurementRecommendation` containing `request_id`, `decision`, and `rationale`.

#### Scenario: Structured recommendation returned
- **WHEN** the agent completes evaluation of a valid purchase request
- **THEN** it returns a response conforming to the `ProcurementRecommendation` schema

### Requirement: Decision values are constrained
The `decision` field SHALL be constrained to exactly one of `approve`, `deny`, or `escalate`.

#### Scenario: Invalid decision value rejected
- **WHEN** a recommendation contains a decision outside `approve|deny|escalate`
- **THEN** schema validation fails and the invalid recommendation is not accepted

### Requirement: Rationale is mandatory and non-empty
The recommendation `rationale` SHALL be a non-empty string after whitespace normalization.

#### Scenario: Blank rationale rejected
- **WHEN** a recommendation rationale is empty or whitespace-only
- **THEN** model validation fails with a rationale validation error

### Requirement: Request input uses validated Pydantic model
The system SHALL validate request payloads using the `PurchaseRequest` model with required fields and numeric constraints.

#### Scenario: Invalid quantity rejected
- **WHEN** a request is submitted with `quantity <= 0`
- **THEN** input validation fails before tool execution

### Requirement: Agent executes implemented domain checks for every request
The agent SHALL invoke implemented checks for each request: `check_budget`, `check_vendor_duplication`, and `check_policy_compliance`.

`assess_risk` MAY be invoked when the risk-assessment tool is implemented and wired.

#### Scenario: Full check coverage per request
- **WHEN** a purchase request is evaluated
- **THEN** budget, vendor-duplication, and policy-compliance checks are executed and available for decision synthesis

### Requirement: Decision precedence is deterministic
The system SHALL resolve conflicting check outcomes using strict precedence: `escalate` over `deny`, and `deny` over `approve`.

#### Scenario: Escalation overrides deny signal
- **WHEN** evaluation produces both an escalation-triggering condition and a deny-triggering condition
- **THEN** the final recommendation decision is `escalate`

### Requirement: Tool errors force escalation with error-aware rationale
If any domain check returns an error condition, the system SHALL set decision to `escalate` and SHALL include error context in rationale.

#### Scenario: Data access error handled safely
- **WHEN** one tool cannot load required data and returns an error
- **THEN** the recommendation decision is `escalate` and rationale references the tool error

### Requirement: Tool data access is centralized through loader
Tool implementations SHALL obtain reference data via `data/loader.py` and SHALL NOT directly read files from `mock_data/`.

#### Scenario: Tool reads through loader abstraction
- **WHEN** a domain tool performs budget, policy, vendor, or request data access
- **THEN** data is retrieved through loader functions rather than direct file reads

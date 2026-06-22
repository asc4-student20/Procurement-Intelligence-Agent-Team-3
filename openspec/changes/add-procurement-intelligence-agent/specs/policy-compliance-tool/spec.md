## ADDED Requirements

### Requirement: check_policy_compliance SHALL evaluate all eight policies
The system SHALL provide a tool named check_policy_compliance that accepts a purchase request and evaluates it against every policy in mock_data/policies.json (POL-001 through POL-008).

#### Scenario: Full policy sweep executes
- **WHEN** a valid purchase request is provided
- **THEN** policy evaluation includes all eight policies and does not stop after first violation

### Requirement: check_policy_compliance SHALL return structured violation records
For each violated policy, the tool SHALL return a violation record containing policy_id, violated_rule, and forced_decision.

#### Scenario: Multiple policy violations returned
- **WHEN** a request violates more than one policy
- **THEN** the result contains one violation record per violated policy

### Requirement: forced_decision MUST be constrained per violation
Each violation forced_decision MUST be one of deny or escalate only.

#### Scenario: Violation decision value constrained
- **WHEN** a violation is emitted
- **THEN** forced_decision is deny or escalate and never approve

### Requirement: no-violation requests SHALL return an empty violation list
If a request violates no policies, the tool SHALL return an empty violations list and zero violation count.

#### Scenario: Policy-compliant request
- **WHEN** the purchase request satisfies all policy rules
- **THEN** violations is empty and violation_count equals 0

### Requirement: check_policy_compliance MUST include deterministic error behavior
If policy or vendor data cannot be loaded, the tool MUST return a structured error field and MUST preserve a consistent response shape for callers.

#### Scenario: Policy data unavailable
- **WHEN** the policy dataset cannot be read
- **THEN** the result includes an error field and a safe default violations payload suitable for escalation handling

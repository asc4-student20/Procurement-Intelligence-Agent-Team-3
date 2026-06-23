## ADDED Requirements

### Requirement: Escalate outcomes SHALL take highest precedence
The system SHALL return decision=escalate when any escalation trigger is present, regardless of simultaneous deny signals.

#### Scenario: Tool error forces escalation
- **WHEN** any tool returns an error condition
- **THEN** final decision is escalate and rationale includes error context

#### Scenario: Compliance hold forces escalation
- **WHEN** policy compliance detects compliance-flagged vendor hold conditions
- **THEN** final decision is escalate

#### Scenario: Near director threshold escalation
- **WHEN** amount is within near-threshold escalation range below director threshold
- **THEN** final decision is escalate

### Requirement: Deny outcomes SHALL apply when no escalation trigger exists
The system SHALL return decision=deny when one or more deny triggers exist and no escalate trigger exists.

#### Scenario: Budget overage denies
- **WHEN** budget check returns within_budget=false and no escalation trigger exists
- **THEN** final decision is deny

#### Scenario: Prohibited category denies
- **WHEN** policy compliance identifies prohibited-category violation and no escalation trigger exists
- **THEN** final decision is deny

### Requirement: Approve outcomes SHALL require clean checks
The system SHALL return decision=approve only when no escalation trigger and no deny trigger are present.

#### Scenario: All checks pass
- **WHEN** budget, duplication, and policy checks are all non-violating
- **THEN** final decision is approve

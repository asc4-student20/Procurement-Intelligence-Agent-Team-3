## Purpose
Capture edge-case decisioning behavior visible in procurement sample data.

## Requirements

### Requirement: Mixed-signal requests SHALL resolve deterministically
Requests with both deny and escalate indicators SHALL resolve to escalate.

#### Scenario: Overage plus near-threshold signal
- **WHEN** a request exceeds remaining budget and also meets escalation conditions
- **THEN** final decision is escalate per precedence

### Requirement: Non-contracted vendors in unrestricted categories SHALL be handled explicitly
The system SHALL apply category-aware policy logic when vendor contract status is none.

#### Scenario: Unrestricted category with no direct violation
- **WHEN** vendor has no active contract but category is not covered by single-source deny policy and budget/policy/risk checks do not force deny or escalate
- **THEN** decision follows deterministic project rule and rationale explains why

### Requirement: Numeric decisioning SHALL use request/tool data over narrative labels
Decision logic SHALL use numeric fields and check results rather than free-text explanatory labels from sample fixtures.

#### Scenario: Narrative mismatch does not override computed rule
- **WHEN** narrative text conflicts with amount/threshold facts
- **THEN** recommendation follows computed policy and threshold logic

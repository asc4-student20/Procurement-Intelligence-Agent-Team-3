## ADDED Requirements

### Requirement: check_budget SHALL evaluate remaining cost center budget
The system SHALL provide a tool named check_budget that accepts cost_center_id and requested_amount and evaluates whether the request fits within the cost center's remaining quarterly budget.

#### Scenario: Request is within remaining budget
- **WHEN** requested_amount is less than or equal to the cost center's remaining budget
- **THEN** the tool returns within_budget=true and overage=0

#### Scenario: Request exceeds remaining budget
- **WHEN** requested_amount is greater than the cost center's remaining budget
- **THEN** the tool returns within_budget=false and a positive overage amount

### Requirement: check_budget SHALL return deterministic budget context fields
The tool SHALL return budget context fields required for downstream rationale generation, including cost_center_id, requested_amount, remaining_budget, within_budget, and overage.

#### Scenario: Response shape is stable
- **WHEN** check_budget completes evaluation
- **THEN** the response includes cost_center_id, requested_amount, remaining_budget, within_budget, and overage

### Requirement: check_budget SHALL support POL-008 deny significance
The tool SHALL indicate budget overage conditions in a way that allows policy enforcement of POL-008 (Budget Overage Prohibition).

#### Scenario: Overage condition signals policy violation context
- **WHEN** within_budget=false
- **THEN** the result exposes sufficient context for callers to apply POL-008 deny behavior

### Requirement: check_budget MUST include predictable error behavior
If budget data cannot be loaded or the cost center is unknown, the tool MUST return a structured error field and MUST preserve a non-crashing response shape suitable for escalation handling.

#### Scenario: Unknown cost center
- **WHEN** cost_center_id does not exist in budget data
- **THEN** the result includes an error field and default-safe budget context values

#### Scenario: Budget data unavailable
- **WHEN** budget dataset cannot be read
- **THEN** the result includes an error field and default-safe budget context values

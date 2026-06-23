## Purpose
Define canonical purchase request input fields and data-contract boundaries.

## Requirements

### Requirement: PurchaseRequest SHALL include the canonical request fields
The system SHALL require purchase request input fields: request_id, requestor, cost_center_id, vendor_name, vendor_id, category, item_description, quantity, unit_price, and total_amount.

#### Scenario: Valid request contains all required fields
- **WHEN** a request is submitted for pre-screening
- **THEN** all canonical request fields are present and validated before tool execution

### Requirement: Fixture-only fields SHALL NOT drive decisions
Fields used for dataset labeling (for example expected_outcome and outcome_reason) SHALL NOT be treated as operational decision inputs.

#### Scenario: Labeled fixture fields are ignored for decisioning
- **WHEN** fixture metadata appears alongside request fields
- **THEN** recommendation logic uses only validated operational input and tool outputs

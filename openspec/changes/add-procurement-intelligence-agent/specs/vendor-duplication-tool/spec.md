## ADDED Requirements

### Requirement: check_vendor_duplication SHALL detect active-contract vendor conflicts
The system SHALL provide a tool named check_vendor_duplication that accepts vendor_id, category, and total_amount and determines whether one or more different vendors hold active contracts in the same category.

#### Scenario: Conflicting active contract vendors exist
- **WHEN** the requested vendor is in category office_supplies and other vendors in office_supplies have active contracts
- **THEN** the tool returns conflict results for those other active-contract vendors

### Requirement: check_vendor_duplication SHALL return explicit conflict details
For each detected conflict, the tool SHALL return vendor-level contract detail records including at minimum vendor_id, vendor_name, contract_id, contract_status, and category.

#### Scenario: Conflict details are returned in structured form
- **WHEN** one or more conflicting active-contract vendors are found
- **THEN** each conflict entry includes vendor_id, vendor_name, contract_id, contract_status, and category

### Requirement: check_vendor_duplication SHALL return conflicting vendor ID list
The tool SHALL return a top-level list of conflicting vendor IDs to support policy reasoning and rationale generation.

#### Scenario: Conflicting vendor IDs provided
- **WHEN** conflicts are found
- **THEN** conflicting_vendor_ids contains each conflicting vendor's ID exactly once

### Requirement: POL-001 threshold SHALL govern deny-trigger significance
The tool SHALL reference POL-001 threshold amount from policy data and SHALL indicate that conflicts above threshold are deny-significant under single-source restrictions.

#### Scenario: Amount above POL-001 threshold with conflicts
- **WHEN** total_amount is greater than the POL-001 threshold and conflicting active contracts exist
- **THEN** the result indicates a deny-significant POL-001 conflict condition

#### Scenario: Amount at or below POL-001 threshold
- **WHEN** total_amount is at or below the POL-001 threshold
- **THEN** the result indicates POL-001 deny trigger is not active even if same-category vendors exist

### Requirement: check_vendor_duplication MUST include predictable error behavior
If vendor or policy data cannot be loaded, the tool MUST return a structured error field and MUST return a non-crashing response shape that callers can escalate.

#### Scenario: Data source unavailable
- **WHEN** vendor or policy data load fails
- **THEN** the tool returns an error message and safe default conflict fields without raising an unhandled exception

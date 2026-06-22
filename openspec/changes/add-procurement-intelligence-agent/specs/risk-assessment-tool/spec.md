## ADDED Requirements

### Requirement: assess_risk SHALL return vendor compliance and contract status
The system SHALL provide a tool named assess_risk that accepts vendor_id and returns the vendor's compliance flag status and contract status.

#### Scenario: Vendor record found
- **WHEN** vendor_id exists in vendor data
- **THEN** the result includes compliance_flag, compliance_notes, and contract_status fields

### Requirement: assess_risk SHALL compute normalized risk level
The tool SHALL compute a normalized risk_level constrained to one of low, medium, high, or critical.

#### Scenario: Compliance flag produces critical risk
- **WHEN** compliance_flag is true
- **THEN** risk_level is critical

#### Scenario: Expired contract produces high risk
- **WHEN** contract_status is expired and compliance_flag is false
- **THEN** risk_level is high

#### Scenario: No contract produces medium risk
- **WHEN** contract_status is none and compliance_flag is false
- **THEN** risk_level is medium

#### Scenario: Active contract without compliance issues produces low risk
- **WHEN** contract_status is active and compliance_flag is false
- **THEN** risk_level is low

### Requirement: assess_risk SHALL return explainable risk context
The tool SHALL include a human-readable risk_summary describing why the computed risk level was assigned.

#### Scenario: Risk summary accompanies result
- **WHEN** a risk_level is returned
- **THEN** risk_summary provides an explanation tied to vendor status inputs

### Requirement: assess_risk MUST include deterministic error behavior
If vendor data cannot be loaded or the vendor_id is unknown, the tool MUST return a structured error field and MUST return a safe high-scrutiny risk result for escalation.

#### Scenario: Unknown vendor
- **WHEN** vendor_id is not found
- **THEN** the result includes error context and a risk result that signals elevated review requirement

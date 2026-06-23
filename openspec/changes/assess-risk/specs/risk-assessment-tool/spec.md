## MODIFIED Requirements

### Requirement: assess_risk MUST include deterministic error behavior
If vendor data cannot be loaded or the vendor_id is unknown, the tool MUST return a structured
`error` object containing machine-readable error context and MUST return a safe high-scrutiny risk
result for escalation.

#### Scenario: Unknown vendor
- **WHEN** vendor_id is not found
- **THEN** the result includes `error.code = "vendor_not_found"` and `error.vendor_id`
- **AND** `risk_level` is `high` or `critical` to signal elevated review
- **AND** `risk_summary` clearly states the risk result is fallback-driven due to missing vendor data

#### Scenario: Vendor data load failure
- **WHEN** vendor data cannot be loaded from the configured data source
- **THEN** the result includes `error.code = "vendor_data_unavailable"`
- **AND** `risk_level` is `high` or `critical` to prevent auto-approval
- **AND** `risk_summary` instructs escalation because risk could not be reliably computed

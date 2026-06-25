## ADDED Requirements

### Requirement: ProcurementRecommendation SHALL include a bounded confidence score
The system SHALL include `confidence` in `ProcurementRecommendation` as a floating-point value in the inclusive range `0.0` to `1.0`.

#### Scenario: Recommendation includes valid confidence
- **WHEN** a recommendation is generated for a valid request
- **THEN** output includes `request_id`, `decision`, `rationale`, and `confidence`
- **AND** `confidence` is between `0.0` and `1.0` inclusive

#### Scenario: Unambiguous single-check decision has very high confidence
- **WHEN** only one check fires and the outcome is unambiguous (for example, sole catering prohibition)
- **THEN** confidence is high (at least `0.9`)

#### Scenario: Low-confidence uncertainty escalates
- **WHEN** the recommendation confidence is below `0.5`
- **THEN** final decision is `escalate`

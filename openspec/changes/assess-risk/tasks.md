## 1. Risk Tool Foundations

- [x] 1.1 Add `assess_risk` tool module under `tools/` with loader-backed vendor lookup
- [x] 1.2 Define or update structured output models for risk level, risk summary, and error context
- [x] 1.3 Export and document the tool so it is discoverable by the procurement agent workflow

## 2. Deterministic Risk Logic

- [x] 2.1 Implement risk precedence mapping for compliance and contract status
- [x] 2.2 Implement deterministic fallback behavior for unknown vendors and loader failures
- [x] 2.3 Ensure fallback output includes machine-readable error code and escalation-oriented summary

## 3. Verification

- [x] 3.1 Add pytest coverage for success-path risk classification outcomes
- [x] 3.2 Add pytest coverage for unknown vendor and vendor-data-unavailable fallback scenarios
- [x] 3.3 Run `pytest tests/ -v --tb=short --junitxml=docs/test-results.xml` and confirm green status

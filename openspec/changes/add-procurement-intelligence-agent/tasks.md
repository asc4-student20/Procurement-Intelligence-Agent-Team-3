## 1. Model Contracts

- [ ] 1.1 Define or confirm `PurchaseRequest` in `models.py` with required request fields and positive numeric constraints.
- [ ] 1.2 Define or confirm `ProcurementRecommendation` in `models.py` with `decision` constrained to `approve|deny|escalate` and non-empty `rationale` validation.

## 2. Agent Assembly and Decision Logic

- [ ] 2.1 Configure the Pydantic AI agent with `output_type=ProcurementRecommendation` and procurement system prompt expectations.
- [ ] 2.2 Implement or confirm deterministic recommendation precedence `escalate > deny > approve` when check outcomes conflict.
- [ ] 2.3 Ensure tool errors are treated as escalation conditions and are reflected in rationale text.

## 3. Tooling and Data Access

- [ ] 3.1 Implement or confirm `check_budget` behavior for within-budget and overage outcomes with cost center context.
- [ ] 3.2 Implement or confirm `check_vendor_duplication` behavior for POL-001 threshold and contracted-vendor conflicts.
- [ ] 3.3 Implement or confirm `check_policy_compliance` behavior for policy-triggered deny/escalate outcomes.
- [ ] 3.4 Implement or confirm `assess_risk` behavior for low/medium/high/critical vendor risk outcomes.
- [ ] 3.5 Ensure all tool data reads are routed through `data/loader.py` and no tool reads `mock_data/` directly.

## 4. Validation and Test Coverage

- [ ] 4.1 Add or update tests to verify model validation constraints for both input and output contracts.
- [ ] 4.2 Add or update tests confirming all four tools are used and decision precedence is enforced for mixed signals.
- [ ] 4.3 Add or update tests for tool-error escalation and rationale error-context inclusion.
- [ ] 4.4 Run `pytest tests/ -v --tb=short --junitxml=docs/test-results.xml` and verify green status before review.

## 5. Readiness and Traceability

- [ ] 5.1 Confirm implementation aligns with `specs/procurement-pre-screening/spec.md` scenarios.
- [ ] 5.2 Prepare final review notes summarizing behavior coverage, risks, and any deferred questions.

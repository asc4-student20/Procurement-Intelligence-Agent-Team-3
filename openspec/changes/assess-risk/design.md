## Context

The project defines risk-assessment requirements in OpenSpec, but the current implementation lacks
a concrete `assess_risk` tool wired to loader-backed vendor data. Procurement recommendations need
a deterministic risk signal and explainable rationale so approval decisions remain consistent,
traceable, and safe under error conditions.

## Goals / Non-Goals

**Goals:**
- Deliver a deterministic `assess_risk` evaluation path based on vendor compliance and contract
  status.
- Ensure output is normalized (`low`, `medium`, `high`, `critical`) and includes a clear summary.
- Standardize error behavior for unknown vendors and data access failures to force elevated review.
- Provide tests that lock expected outcomes for success and error paths.

**Non-Goals:**
- Introducing external scoring services or machine-learning risk models.
- Changing the approval recommendation taxonomy (`approve`, `deny`, `escalate`).
- Modifying mock fixture files directly.

## Decisions

1. Implement a dedicated `tools/risk_assessment.py` module for `assess_risk`.
   - Rationale: keeps risk logic isolated and testable like existing tool modules.
   - Alternative considered: embedding risk logic in the main agent flow; rejected because it
     reduces reusability and makes focused unit testing harder.

2. Use explicit precedence rules for risk classification.
   - Rule order: compliance flag => `critical`; expired contract => `high`; no contract =>
     `medium`; active contract without compliance issue => `low`.
   - Rationale: deterministic mapping aligns with current spec expectations.

3. Return a structured fallback object on failures.
   - For unknown vendor or data load errors, include an `error` object plus a high-scrutiny risk
     result to support escalation.
   - Alternative considered: raising exceptions to caller; rejected because tool-level structured
     responses are easier for the agent to reason over.

4. Validate behavior via targeted pytest coverage.
   - Include at least one success-path test and dedicated edge/error tests.
   - Rationale: risk classification drift is high-impact and should be guarded by stable tests.

## Risks / Trade-offs

- [Risk] Existing calling code may assume exception-based failure handling. → Mitigation: document
  and test structured error outputs and keep field names stable.
- [Risk] Vendor data schema drift can break mapping assumptions. → Mitigation: access data through
  `data/loader.py` only and guard missing fields with safe defaults.
- [Risk] New output fields may require follow-on updates in downstream code. → Mitigation: add
  compatibility checks in tests and keep output contract explicit in models.

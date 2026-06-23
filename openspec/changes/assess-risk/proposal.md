## Why

The procurement workflow depends on vendor risk checks, but there is no implemented `assess_risk`
tool in the current codebase. Adding and hardening this capability now closes a critical gap in
pre-screening decisions and reduces inconsistent manual risk interpretation.

## What Changes

- Add an `assess_risk` tool that evaluates vendor compliance and contract status from loader-backed
  vendor data.
- Return a normalized risk level (`low`, `medium`, `high`, `critical`) with a human-readable risk
  summary for explainability.
- Add deterministic, structured error handling for unknown vendors and data-load failures that
  returns an escalation-safe risk result.
- Add tests for the primary success path and edge/error behavior to keep risk outcomes stable.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `risk-assessment-tool`: clarify and enforce deterministic fallback output for unknown vendor IDs
  and data loading errors, including explicit structured error context.

## Impact

- Affected specs: `risk-assessment-tool`
- Affected code: `tools/` risk assessment module, `models.py` output contracts, and tests in
  `tests/`
- Operational impact: procurement recommendations get consistent, explainable risk signals for
  safer approve/deny/escalate decisions

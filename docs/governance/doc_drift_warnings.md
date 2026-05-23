# Documentation Drift Warnings

Append-only log for failed documentation update validations.

## Entry Template

- Timestamp (UTC):
- Session/Task:
- File:
- Validation rule failed:
- Action taken: rollback doc patch, continue code task
- Short diff summary:
- Next attempt recommendation:

## Entries

- 2026-05-23 10:20 UTC:
  - Session/Task: Wave C governance alignment
  - File: `tests/integration/api/test_api_routes_smoke.py`
  - Validation rule failed: scope discipline drift (health test expanded beyond runtime contract needs)
  - Action taken: reduced to minimal readiness/lifecycle contract assertions and proceeded with targeted verification
  - Short diff summary: removed oversized policy-assert surface from health smoke test; retained runtime contract assertions
  - Next attempt recommendation: constrain smoke test additions to endpoint contract objectives only

- No drift warnings recorded yet.

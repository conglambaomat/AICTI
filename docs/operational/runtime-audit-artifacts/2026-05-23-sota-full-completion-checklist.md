# SOTA Core v2 Full Completion Checklist

| Item ID | Layer | Requirement | Verification command | Expected pass marker | Evidence artifact/path | Status | Blocker if fail | Next action |
|---|---|---|---|---|---|---|---|---|
| A1 | Plan | Foundation plan complete | `git log --oneline --reverse -- src/de_forge tests` + targeted replay tests | foundation-expected commit chain present and tests green | commits: `071f698`..`4f4f8a9`, `6e62782`; global suite 169 passed | PASS | - | Keep foundation regression bundle in CI |
| A2 | Plan | Compiler plan complete | `git log --oneline --reverse -- src/de_forge tests` + compiler/integration tests | compiler-related commits present and tests green | commits: `6e62782`, `3ef8798`, `a94b862`, `344f22a`; `tests/integration/services/test_rule_generation_service.py` pass | PASS | - | Keep compiler-path tests mandatory |
| A3 | Plan | Validation-oracle-regression plan complete | `git log --oneline --reverse -- src/de_forge tests` + validation/regression tests | validation+regression commits present and tests green | commits: `b9db12d`, `eaa2f4b`, `ae3b6d3`, `4b12ec7`; validation/retrieval/refinement tests pass | PASS | - | Preserve regression and robustness test gates |
| A4 | Plan | Agents plan complete | `git log --oneline --reverse -- src/de_forge tests` + agent/review/audit tests | controlled-agent and audit commits present with passing tests | commits: `13ed366`, `260cdd3`, `549f036`; agent/review/audit integration tests pass | PASS | - | Keep agent audit + review gates enforced |
| A5 | Plan | Orchestrator-UI-dashboard plan complete | `git log --oneline --reverse -- src/de_forge tests` + API/E2E/runtime tests | orchestrator+api+dashboard-surface commits present and tests green | commits: `cf1cf79`, `21efe1b`, `7e7af4c`, `12c9bd8`, `814fef8`, `ad1d2f1`; strict E2E bundle 17 passed | PASS | - | Maintain runtime API and orchestration gates |
| B1 | Invariant | No raw-report-to-production-rule shortcut | `python -m uv run pytest tests/e2e/test_pipeline_e2e.py -q` | all relevant tests pass | docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md | PASS | - | Keep regression suite in gate bundle |
| B2 | Invariant | DetectionSpec-first mandatory | `python -m uv run pytest tests/e2e/test_api_schema_validation.py -q` | tests pass | docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md | PASS | - | Keep schema validation tests mandatory |
| B3 | Invariant | Citation integrity hard gate | `python -m uv run pytest tests/integration/services/test_retrieval_faithfulness.py -q` | tests pass | tests/integration/services/test_retrieval_faithfulness.py | PASS | - | Maintain faithfulness checks in CI |
| B4 | Invariant | ATT&CK modeling chain correctness | `python -m uv run pytest tests/integration/services/test_attack_mapping_service.py -q` | tests pass | tests/integration/services/test_attack_mapping_service.py | PASS | - | Maintain ATT&CK mapping tests |
| B5 | Invariant | Required proof obligations enforced | `python -m uv run pytest tests/integration/services/test_static_validation_service.py tests/integration/services/test_dynamic_validation_service.py -q` | tests pass | respective integration tests | PASS | - | Keep static/dynamic validation gates |
| B6 | Invariant | Detection AST/compiler preferred source | `python -m uv run pytest tests/integration/services/test_rule_generation_service.py -q` | tests pass | tests/integration/services/test_rule_generation_service.py | PASS | - | Keep compiler path as default route |
| B7 | Invariant | Human review before export mandatory | `python -m uv run pytest tests/e2e/test_api_review_and_export.py -q` | pre-approval blocked + post-approval success | tests/e2e/test_api_review_and_export.py | PASS | - | Keep review/export e2e gate |
| B8 | Invariant | Agent/refinement loops bounded | `python -m uv run pytest tests/integration/services/test_refinement_limits.py -q` | tests pass | tests/integration/services/test_refinement_limits.py | PASS | - | Preserve hard loop limits |
| B9 | Invariant | Feedback -> regression protection | `python -m uv run pytest tests/integration/services/test_review_gate.py tests/integration/services/test_orchestrator_state_transitions.py -q` | tests pass | integration regression tests | PASS | - | Continue regression expansion |
| B10 | Invariant | Full lineage/auditability preserved | `python -m uv run pytest tests/e2e/test_api_run_status.py -q` | tests pass | tests/e2e/test_api_run_status.py | PASS | - | Keep run-status lineage contract |
| C1 | Gate | docs preflight passes | `python scripts/docs_preflight.py` | `DOCS_PREFLIGHT: PASS` | command output | PASS | - | Keep as startup gate |
| C2 | Gate | full tests pass | `python -m uv run pytest tests/ -q` | `169 passed` | command output | PASS | - | Continue full-suite gate |
| C3 | Gate | mypy passes | `python -m uv run mypy src/` | `Success: no issues found` | command output | PASS | - | Keep strict typing gate |
| C4 | Gate | ruff check passes | `python -m uv run ruff check src/ tests/` | `All checks passed` | command output | PASS | - | Keep lint gate |
| C5 | Gate | format check passes | `python -m uv run ruff format --check src/ tests/` | `already formatted` | command output | PASS | - | Keep format gate |
| C6 | Gate | strict runtime E2E bundle passes | `python -m uv run pytest tests/e2e/test_api_health_and_contracts.py tests/e2e/test_api_schema_validation.py tests/e2e/test_api_abstain_vs_hard_fail.py tests/e2e/test_api_review_and_export.py tests/e2e/test_api_run_status.py tests/e2e/test_pipeline_e2e.py -q` | `17 passed` | command output | PASS | - | Keep strict runtime bundle |

## Final Verdict
- Verdict: DONE
- PASS count: 21
- FAIL count: 0
- MISSING count: 0

## P0 Blockers (if NOT DONE)
- None.

## Ordered Next Actions
1. Preserve current gate bundle as mandatory pre-release checklist.
2. Keep runtime strict E2E and invariant-linked tests green on every integration wave.
3. Re-run Layer C gates fresh before any release cut.

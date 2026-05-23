# SOTA Core v2 Full Completion Checklist Design

**Status:** Approved design baseline
**Date:** 2026-05-23
**Scope:** Full-project completion decision for DE-Forge SOTA Core v2

## 1) Objective and Strict Definition of DONE

A project-level verdict is **DONE** only when all of the following are true:

1. All five mandatory SOTA Core v2 plans are completed in required order.
2. All architecture invariants remain enforced on active runtime paths.
3. All global quality gates pass with fresh, reproducible evidence.

If any required item is FAIL or MISSING, verdict is **NOT DONE**.

## 2) Three-Layer Completion Checklist

### Layer A — Plan Completion Checklist (Execution Order Locked)

Required order:
1. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`
2. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`
3. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`
4. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`
5. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`

Each plan item must include:
- task-level implementation evidence (code paths/files),
- targeted verification evidence (tests/checks),
- review evidence (spec compliance + code quality),
- commit evidence tied to plan task scope.

### Layer B — SOTA Invariant Conformance Checklist

All non-negotiable invariants must be evidenced on active runtime paths:
1. No raw-report-to-production-rule shortcut.
2. DetectionSpec-first mandatory.
3. Citation integrity hard-gated.
4. ATT&CK modeling chain correctness.
5. Required proof obligations enforced before candidate selection.
6. Detection AST/compiler preferred source for Sigma.
7. Human review mandatory before export.
8. Agent/refinement loops bounded.
9. Feedback produces regression protection.
10. Full artifact lineage/auditability preserved.

Each invariant line item must map:
- runtime/service location,
- proof command or test,
- pass marker,
- artifact path.

### Layer C — Global Release Gates (Fresh Evidence Required)

Mandatory commands:
- `python scripts/docs_preflight.py`
- `python -m uv run pytest tests/ -q`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Mandatory runtime behavior bundle (strict production behavior):
- `python -m uv run pytest tests/e2e/test_api_health_and_contracts.py tests/e2e/test_api_schema_validation.py tests/e2e/test_api_abstain_vs_hard_fail.py tests/e2e/test_api_review_and_export.py tests/e2e/test_api_run_status.py tests/e2e/test_pipeline_e2e.py -q`

## 3) Checklist Row Contract (Normalized Schema)

Every checklist row must include:
- `Item ID`
- `Requirement`
- `Verification command`
- `Expected pass marker`
- `Evidence artifact/path`
- `Status` (`PASS` | `FAIL` | `MISSING`)
- `Blocker if fail`
- `Next action`

## 4) Verdict Rules

Project verdict resolution:
- **DONE**: 100% PASS across Layer A + Layer B + Layer C.
- **NOT DONE**: Any FAIL/MISSING in any layer.

Priority of unresolved work:
- P0: invariant violation, missing mandatory plan completion, or failing global gate.
- P1: missing review evidence, incomplete runtime traceability.
- P2: documentation consistency improvements without correctness impact.

## 5) Operational Logging Rules

For every status transition in checklist execution:
- update `docs/operational/IMPLEMENTATION_PROGRESS.md`, and
- update `docs/operational/CHANGELOG_AUTONOMOUS.md`.

No completion claim is valid without fresh command evidence and synchronized operational logs.

## 6) Out-of-Scope

This checklist design defines completion verification structure. It does not itself implement missing functionality. Implementation tasks are generated in the follow-up execution plan.

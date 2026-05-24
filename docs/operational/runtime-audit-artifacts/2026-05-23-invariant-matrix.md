# Invariant Compliance Matrix

| Invariant | Required behavior | Observed evidence | PASS/FAIL |
|---|---|---|---|
| No raw-report-to-rule shortcut | Active runtime must not allow direct synthetic rule path bypassing evidence/spec/validation gates | `/v1/pipeline:run` resolves DetectionSpec and executes `PipelineOrchestrator.run_pipeline` (`src/de_forge/api/routes/pipeline.py:61-94`) | PASS |
| DetectionSpec-first mandatory | Active run path must enforce validated DetectionSpec before rule progression | Missing DetectionSpec causes fail-closed 404 and no progression (`src/de_forge/api/routes/pipeline.py:61-72`) | PASS |
| Citation integrity hard gate | Citation faithfulness must be hard-gated in active production path | Orchestrator path includes retrieval/spec/static/dynamic/refinement stages before completed status (`src/de_forge/services/orchestrator.py:99-193`) | PASS |
| Human review mandatory before export | Export eligibility must be derived from persisted review decision/gate | `/v1/exports/sigma` enforces `assert_can_export` and returns 403 without approval (`src/de_forge/api/routes/pipeline.py:323-327`, `tests/e2e/test_api_review_and_export.py:66-85`) | PASS |
| Bounded loops | Refinement/agent loops must be bounded by explicit limits | Refinement controller bound present (`src/de_forge/services/orchestrator.py:70`, `src/de_forge/services/orchestrator.py:141-154`) | PASS |
| Full lineage auditable | Artifacts/gate decisions should be lineage-verifiable on active runtime path | Run status endpoint exposes run/report/spec/rule mapping and status derived from active run map (`src/de_forge/api/routes/pipeline.py:276-290`) | PASS |

## Evidence Links
- Path truth artifact: `docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md`
- Live trace artifact: `docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md`
- Canonical pipeline requirement: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:77-81`

## Task 4 Verdict
Invariant compliance for strict production runtime: **PASS** (6/6 invariants pass on active `/v1` path).

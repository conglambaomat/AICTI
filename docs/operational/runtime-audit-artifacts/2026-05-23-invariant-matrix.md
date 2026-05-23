# Invariant Compliance Matrix

| Invariant | Required behavior | Observed evidence | PASS/FAIL |
|---|---|---|---|
| No raw-report-to-rule shortcut | Active runtime must not allow direct synthetic rule path bypassing evidence/spec/validation gates | `/v1/pipeline:run` returns synthetic branch outcomes and does not invoke orchestrator-gated flow (`src/de_forge/api/routes/pipeline.py:36-64`) | FAIL |
| DetectionSpec-first mandatory | Active run path must enforce validated DetectionSpec before rule progression | DetectionSpec-first gate exists in orchestrator (`src/de_forge/services/orchestrator.py:45-49`) but active `/v1` run path bypasses orchestrator (`src/de_forge/api/routes/pipeline.py:36-64`) | FAIL |
| Citation integrity hard gate | Citation faithfulness must be hard-gated in active production path | Citation requirements defined canonically, but active `/v1` run path is synthetic and does not execute evidence/citation validation chain (`src/de_forge/api/routes/pipeline.py:36-64`) | FAIL |
| Human review mandatory before export | Export eligibility must be derived from persisted review decision/gate | `/v1/exports/sigma` allows export only by literal run id `run_approved` (`src/de_forge/api/routes/pipeline.py:91-99`); persisted review check exists separately under `/review/assert-export` (`src/de_forge/api/routes/review.py:34-41`, `src/de_forge/services/review.py:50-57`) | FAIL |
| Bounded loops | Refinement/agent loops must be bounded by explicit limits | Refinement controller bound present (`src/de_forge/services/orchestrator.py:70`, `src/de_forge/services/orchestrator.py:141-154`) | PASS |
| Full lineage auditable | Artifacts/gate decisions should be lineage-verifiable on active runtime path | Active `/v1` synthetic path returns generated ids/status without persistence-backed lineage chain (`src/de_forge/api/routes/pipeline.py:24-33`, `src/de_forge/api/routes/pipeline.py:36-64`) | FAIL |

## Evidence Links
- Path truth artifact: `docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md`
- Live trace artifact: `docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md`
- Canonical pipeline requirement: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:77-81`

## Task 4 Verdict
Invariant compliance for strict production runtime: **FAIL** (5/6 invariants fail on active `/v1` path).

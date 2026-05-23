# Live Runtime Trace Evidence

## Required stage evidence
- [x] ingest response captured
- [x] pipeline run response captured
- [x] gate/decision metadata captured
- [x] review/export gate behavior captured

## Command Evidence
- `python -m uv run pytest tests/e2e/test_pipeline_e2e.py::test_e2e_positive_pipeline_reaches_awaiting_review -v` -> PASS
  - Marker: `PASSED [100%]`
- `python -m uv run pytest tests/e2e/test_pipeline_e2e.py::test_e2e_ambiguous_report_abstains -v` -> PASS
  - Marker: `PASSED [100%]`
- `python -m uv run pytest tests/e2e/test_pipeline_e2e.py::test_deterministic_replay_same_input_same_transitions_and_idempotency -v` -> PASS
  - Marker: `PASSED [100%]`

## Runtime Interpretation
- Stage coverage observed by tests:
  - Positive flow reaches `awaiting_review` status at API contract level.
  - Ambiguous input returns abstain contract.
  - Deterministic replay behavior is stable for same input.
- Gate behavior observed:
  - Tests validate behavior exposed by active API route contracts.
- Mismatch vs canonical path:
  - Active `/v1/pipeline:run` route contains synthetic branch logic and does not invoke orchestrator hard gates (`src/de_forge/api/routes/pipeline.py:36-64`).
  - Export gate in `/v1/exports/sigma` uses literal `run_id == "run_approved"`, not persisted review decision checks (`src/de_forge/api/routes/pipeline.py:91-99`).
  - Canonical hard-gated flow exists in orchestrator service but is not the active `/v1` path (`src/de_forge/services/orchestrator.py:33-63`, `src/de_forge/services/orchestrator.py:65-193`).

## Task 3 Verdict
- Live runtime trace tests: PASS
- Production-strict runtime-path conformance: FAIL (route-level stub mismatch remains critical).

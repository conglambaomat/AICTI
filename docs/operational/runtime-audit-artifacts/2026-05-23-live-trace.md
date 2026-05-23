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
  - Export is denied before approval and allowed after persisted approval (`tests/e2e/test_api_review_and_export.py:66-113`).
- Conformance vs canonical path:
  - Active `/v1/pipeline:run` now invokes `PipelineOrchestrator.run_pipeline` (`src/de_forge/api/routes/pipeline.py:91-94`).
  - Active `/v1/exports/sigma` enforces persisted review decision checks via `ReviewService.assert_can_export` (`src/de_forge/api/routes/pipeline.py:323-327`).

## Task 3 Verdict
- Live runtime trace tests: PASS
- Production-strict runtime-path conformance: PASS.

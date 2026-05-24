# Runtime Path Truth Evidence

## Assertions
- [ ] API run path invokes non-stub orchestrator flow
- [ ] DetectionSpec-first gate is enforced on active run path
- [ ] Export path enforces human review decision from persisted state
- [ ] Active path reaches validation/proof stage before export eligibility

## Runtime Wiring Evidence
- FastAPI includes `/v1` pipeline router from `api/routes/pipeline.py`: `src/de_forge/main.py:30-34`.
- `/v1/pipeline:run` now resolves `DetectionSpec` from DB, invokes `PipelineOrchestrator.run_pipeline`, and persists run mapping metadata for downstream review/export: `src/de_forge/api/routes/pipeline.py:45-131`.
- Orchestrator retains deterministic stage machine and bounded refinement transitions: `src/de_forge/services/orchestrator.py:65-193`.
- `/v1/reviews` records persisted review decisions through `ReviewService.record_decision`: `src/de_forge/api/routes/pipeline.py:293-311`, `src/de_forge/services/review.py:27-47`.
- `/v1/exports/sigma` enforces persisted approval via `ReviewService.assert_can_export` before returning rule content: `src/de_forge/api/routes/pipeline.py:314-337`, `src/de_forge/services/review.py:50-57`.

## Results
- [PASS] API run path invokes non-stub orchestrator flow — evidence: `orchestrator.run_pipeline(...)` in active `/v1/pipeline:run` path `src/de_forge/api/routes/pipeline.py:91-94`.
- [PASS] DetectionSpec-first on active run path — evidence: run path requires DB `DetectionSpec` lookup prior to orchestrator call `src/de_forge/api/routes/pipeline.py:61-72`.
- [PASS] Export enforces persisted review decision — evidence: `assert_can_export` in `/v1/exports/sigma` `src/de_forge/api/routes/pipeline.py:323-327` with decision persisted by `/v1/reviews` `src/de_forge/api/routes/pipeline.py:303-305`.
- [PASS] Validation/proof before export eligibility on active `/v1` path — evidence: export depends on rule created by orchestrator progression and approval gate; E2E suite verifies pre-approval export denial then post-approval success `tests/e2e/test_api_review_and_export.py:66-113`.

## Task 2 Verdict
Runtime path truth for strict production criterion: **PASS** (active `/v1` endpoints now use orchestrator-driven runtime and persisted review/export gating).

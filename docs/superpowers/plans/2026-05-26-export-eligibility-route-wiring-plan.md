# Export Eligibility Route Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire Sigma export through the production ExportEligibilityService using a SQLAlchemy repository adapter.

**Architecture:** Keep policy in `ExportEligibilityService`; add a SQLAlchemy adapter in the same service module to translate persisted rows into the existing pure service protocol. Update the `/v1/exports/sigma` route to check eligibility before fetching and returning rule content, preserving existing response content after all gates pass.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy ORM, pytest, TestClient.

---

## File Structure

- Modify `tests/integration/api/test_export_production_gates.py`: new isolated in-memory API integration test proving missing compiler provenance blocks export even when run mapping, proof rows, and approval exist.
- Modify `src/de_forge/services/export_eligibility.py`: add `SqlAlchemyExportEligibilityRepository` with the existing protocol methods.
- Modify `src/de_forge/api/routes/pipeline.py`: import repository/service/error and use them in `export_sigma`.
- Potentially modify existing export success tests only if they legitimately rely on successful export without persisted proof coverage or compiler provenance.

## Task 1: Missing compiler provenance export gate test

**Files:**
- Create/modify: `tests/integration/api/test_export_production_gates.py`

- [ ] **Step 1: Write failing test**

Add a TestClient test that overrides `get_db` with an in-memory SQLite session, creates schema with `Base.metadata.create_all`, inserts a validated `DetectionSpec`, a manual/default `GeneratedRule` with no compiler provenance, a matching `PipelineRunRecord`, all eight required `ProofObligationRecord` rows with status `proven`, and an approved `ReviewDecision` through `ReviewService`. POST `/v1/exports/sigma` with `run_id`; assert HTTP 403 and `detail == "COMPILER_PROVENANCE_MISSING"`.

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py::test_export_blocks_manual_rule_without_compiler_provenance -v
```

Expected before implementation: FAIL because the old route only checks `ReviewService.assert_can_export` and returns 200 or a different detail.

## Task 2: SQLAlchemy export eligibility repository and route wiring

**Files:**
- Modify: `src/de_forge/services/export_eligibility.py`
- Modify: `src/de_forge/api/routes/pipeline.py`

- [ ] **Step 1: Implement repository**

Add `SqlAlchemyExportEligibilityRepository` with constructor `__init__(self, db: Session)`. Implement:

- `get_run(run_id)` using `PipelineRunRecord` by `run_id`.
- `get_rule(rule_id)` using `db.get(GeneratedRule, rule_id)`.
- `get_detection_spec(spec_id)` returning `None` if `spec_id is None`, otherwise `db.get(DetectionSpec, spec_id)`.
- `get_proof_rows(run_id, rule_id)` querying `ProofObligationRecord` by `run_id` and `rule_candidate_id`, returning list of mapping dictionaries with `run_id`, `rule_candidate_id`, `claim_type`, `status`, and `justification`.
- `latest_review_decision(run_id, rule_id)` using `ReviewService(db)._get_latest_decision(rule_id, run_id=run_id)`.

- [ ] **Step 2: Wire route**

In `src/de_forge/api/routes/pipeline.py`, import `ExportBlockedReason`, `ExportEligibilityService`, and `SqlAlchemyExportEligibilityRepository`. In `export_sigma`, keep the initial run mapping 404. Replace `ReviewService.assert_can_export(...)` with:

```python
try:
    ExportEligibilityService(
        SqlAlchemyExportEligibilityRepository(db)
    ).assert_exportable(run_id=payload.run_id, rule_id=rule_id)
except ExportBlockedReason as exc:
    return JSONResponse(status_code=403, content={"detail": str(exc)})
```

Keep the generated rule fetch and `ExportSigmaResponse` after eligibility passes.

- [ ] **Step 3: Verify GREEN targeted test**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py::test_export_blocks_manual_rule_without_compiler_provenance -v
```

Expected: PASS.

## Task 3: Existing success tests compatibility

**Files:**
- Modify only legitimate existing export success tests if required.

- [ ] **Step 1: Run integration export gate tests**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py -v
```

If a success test fails because it lacks compiler provenance or complete proof rows, update its fixture to set `generation_source="compiler"`, non-empty `detection_ast_id`, non-empty `compiled_sigma_id`, and all required proof obligations.

- [ ] **Step 2: Re-run integration export gate tests**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py -v
```

Expected: PASS.

## Task 4: Required verification and commit

**Files:**
- Stage only files changed for this task.

- [ ] **Step 1: Run requested verification**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py -v
pytest tests/unit/services/test_export_eligibility.py tests/unit/services/test_proof_coverage.py tests/unit/services/test_compiler_provenance.py -v
pytest tests/integration/api/test_api_routes.py tests/integration/e2e/test_sota_pipeline_e2e.py -v
```

If a pre-existing local DB schema failure unrelated to this task occurs, capture the exact command and error and report it.

- [ ] **Step 2: Commit**

Run status and diff checks, then stage only task files and commit:

```bash
git status --short
git diff -- tests/integration/api/test_export_production_gates.py src/de_forge/services/export_eligibility.py src/de_forge/api/routes/pipeline.py
git add tests/integration/api/test_export_production_gates.py src/de_forge/services/export_eligibility.py src/de_forge/api/routes/pipeline.py
git commit -m "$(cat <<'EOF'
fix(export): enforce production eligibility gates

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds. Do not stage `.claude/`, `de_forge.db`, or unrelated files.

## Self-Review

- Spec coverage: all user requirements map to Tasks 1-4.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: repository method names match `ExportEligibilityRepository` protocol and route uses `assert_exportable(run_id=..., rule_id=...)`.

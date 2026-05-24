# DE-Forge UI Dashboard Enhancements Implementation Plan

> Required workflow: implement task-by-task with TDD, verification, spec compliance review, code quality review, and task-scoped commits. Do not touch Claude settings files.

## Goal

Implement the low-risk deferred UI/dashboard add-on from `docs/superpowers/specs/2026-05-22-de-forge-ui-dashboard-enhancements-design.md`.

## File structure map

- `src/de_forge/ui_support/review_view.py` — deterministic review/evidence/dashboard view models.
- `src/de_forge/api/routes/ui.py` — richer server-rendered UI pages.
- `src/de_forge/api/routes/metrics.py` — historical quality snapshot endpoint.
- `tests/unit/ui_support/test_review_view.py` — UI support unit tests.
- `tests/integration/api/test_api_routes.py` — API/UI route integration tests.

---

### Task 1: UI support view models

**Files:**
- Create: `src/de_forge/ui_support/review_view.py`
- Test: `tests/unit/ui_support/test_review_view.py`

Steps:

1. Write failing tests for a deterministic review view model containing evidence quote, graph path, DetectionSpec summary, Sigma YAML, proof status, validation score, and quality history snapshots.
2. Run targeted test and observe expected import failure.
3. Implement minimal dataclasses/Pydantic models and factory functions.
4. Run targeted test and observe pass.
5. Run spec compliance review against the design.
6. Run code quality review.
7. Commit only task files with message `feat(ui): add review view models`.

Verification commands:

```bash
python -m pytest tests/unit/ui_support/test_review_view.py -v
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
```

---

### Task 2: Rich trust-oriented review page

**Files:**
- Modify: `src/de_forge/api/routes/ui.py`
- Modify: `tests/integration/api/test_api_routes.py`

Steps:

1. Write failing integration tests asserting `/api/ui/review` includes Evidence Graph Path, DetectionSpec, editable Sigma textarea, review controls, proof status, and validation score.
2. Run targeted test and observe expected content failure.
3. Render the richer review page from `ui_support.review_view` while preserving existing headers.
4. Run targeted test and observe pass.
5. Run spec compliance review.
6. Run code quality review.
7. Commit only task files with message `feat(ui): expand trust review page`.

Verification commands:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_review_ui_page_contains_trust_columns tests/integration/api/test_api_routes.py::test_review_ui_page_contains_lineage_and_edit_controls -v
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
```

---

### Task 3: Evidence graph and dashboard UI pages

**Files:**
- Modify: `src/de_forge/api/routes/ui.py`
- Modify: `tests/integration/api/test_api_routes.py`

Steps:

1. Write failing integration tests for `/api/ui/evidence-graph` and `/api/ui/dashboard`.
2. Run targeted tests and observe expected 404 failures.
3. Add simple server-rendered evidence graph and quality dashboard pages.
4. Run targeted tests and observe pass.
5. Run spec compliance review.
6. Run code quality review.
7. Commit only task files with message `feat(ui): add graph and dashboard pages`.

Verification commands:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_evidence_graph_ui_page_renders_graph_path tests/integration/api/test_api_routes.py::test_dashboard_ui_page_renders_quality_history -v
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
```

---

### Task 4: Historical metrics endpoint

**Files:**
- Modify: `src/de_forge/api/routes/metrics.py`
- Modify: `tests/integration/api/test_api_routes.py`

Steps:

1. Write failing integration test for `/api/metrics/history` returning ordered quality snapshots.
2. Run targeted test and observe expected 404.
3. Add endpoint backed by UI support quality history sample data.
4. Run targeted test and observe pass.
5. Run spec compliance review.
6. Run code quality review.
7. Commit only task files with message `feat(metrics): add quality history endpoint`.

Verification commands:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_metrics_history_endpoint_returns_quality_snapshots -v
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
```

---

### Task 5: Final UI/dashboard verification

**Files:**
- Modify only if verification finds issues.

Steps:

1. Run all UI/API tests.
2. Run full test suite with coverage.
3. Run mypy.
4. Run Ruff lint and format check.
5. Manual smoke test `/api/ui/review`, `/api/ui/evidence-graph`, and `/api/ui/dashboard`.
6. Commit verification fixes only if needed; do not create an empty commit.

Verification commands:

```bash
python -m pytest tests/unit/ui_support tests/integration/api/test_api_routes.py -v
python -m pytest tests/ -v --cov=src --cov-report=term-missing
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
```

Manual smoke URLs:

```text
http://127.0.0.1:8000/api/ui/review
http://127.0.0.1:8000/api/ui/evidence-graph
http://127.0.0.1:8000/api/ui/dashboard
```

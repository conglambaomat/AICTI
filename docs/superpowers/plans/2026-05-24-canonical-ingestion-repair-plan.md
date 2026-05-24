# Canonical Ingestion Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/v1/reports:ingest` real, deterministic, persisted, and aligned with the existing ingestion service while preserving SOTA Core v2 fail-closed boundaries.

**Architecture:** Route handlers stay thin and delegate TXT ingestion to `IngestionService`, which remains the canonical persistence/chunking boundary. PDF input is explicitly rejected with a stable unsupported error until a real PDF extraction path exists. `/v1/pipeline:run` must verify that the requested `report_id` exists in persisted `reports` before looking up or running any `DetectionSpec`.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest, SQLite test database, existing `IngestionService` and ORM models.

---

## File Structure

- Modify `src/de_forge/api/routes/pipeline.py`
  - Replace fake `/v1/reports:ingest` implementation with `IngestionService` delegation.
  - Add explicit PDF rejection for canonical JSON ingest and legacy file ingest.
  - Add persisted-report guard in `/v1/pipeline:run` before DetectionSpec lookup.
  - Forward DB sessions through legacy wrappers where needed.
- Modify `src/de_forge/api/routes/ingestion.py`
  - Align existing `/ingest` file upload behavior with canonical unsupported-PDF policy.
- Modify `src/de_forge/schemas/api_pipeline.py`
  - Add stable `chunk_count` to `ReportIngestResponse` so canonical and legacy ingestion can report persisted chunking evidence.
- Modify `tests/e2e/test_api_health_and_contracts.py`
  - Strengthen `/v1/reports:ingest` endpoint existence test into real persistence/shape coverage.
- Modify `tests/e2e/test_api_schema_validation.py`
  - Add canonical ingest validation/idempotency/PDF tests and pipeline persisted-report guard tests.
- Modify `tests/integration/api/test_api_routes_smoke.py`
  - Add smoke coverage for `/ingest` PDF unsupported behavior without changing existing missing-file validation.

---

### Task 1: Canonical TXT ingest persists reports and chunks

**Files:**
- Modify: `tests/e2e/test_api_health_and_contracts.py:17-32`
- Modify: `src/de_forge/schemas/api_pipeline.py`
- Modify: `src/de_forge/api/routes/pipeline.py:37-44`

- [ ] **Step 1: Write the failing test**

Replace `test_post_reports_ingest_endpoint_exists` in `tests/e2e/test_api_health_and_contracts.py` with this stronger test:

```python
def test_post_reports_ingest_persists_txt_report_and_chunks() -> None:
    content = "PowerShell launch behavior observed\n\nEncoded command spawned child process"
    response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": content,
            "external_ref": "r-001",
            "metadata": {"title": "sample"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["report_id"].startswith("report_")
    assert body["status"] == "ingested"
    assert body["chunk_count"] == 2
    assert "trace_id" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_health_and_contracts.py::test_post_reports_ingest_persists_txt_report_and_chunks -q
```

Expected: FAIL because current `/v1/reports:ingest` returns a fake `rep_...` ID and no `chunk_count`.

- [ ] **Step 3: Add `chunk_count` to response schema**

In `src/de_forge/schemas/api_pipeline.py`, change `ReportIngestResponse` to include `chunk_count`:

```python
class ReportIngestResponse(BaseModel):
    """Response schema for POST /v1/reports:ingest."""

    report_id: str = Field(description="Generated report ID")
    status: Literal["ingested"] = Field(description="Ingestion status")
    trace_id: str = Field(description="Trace ID for observability")
    chunk_count: int = Field(description="Number of persisted report chunks")
```

- [ ] **Step 4: Implement canonical route through `IngestionService`**

In `src/de_forge/api/routes/pipeline.py`, add imports:

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from de_forge.models import Report as ReportModel
from de_forge.services.ingestion import IngestionService
```

Replace `/v1/reports:ingest` with:

```python
@router.post("/reports:ingest", response_model=ReportIngestResponse, status_code=201)
async def ingest_report(
    payload: ReportIngestRequest, db: Session = Depends(get_db)
) -> ReportIngestResponse:
    assert_schema_contract_current(db)
    if payload.source_type == "pdf":
        raise HTTPException(status_code=415, detail="PDF ingestion is not supported")

    service = IngestionService(db)
    try:
        result = service.ingest(
            source_type=payload.source_type,
            filename=payload.external_ref or "inline-report.txt",
            content_bytes=payload.content.encode("utf-8"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportIngestResponse(
        report_id=result.report_id,
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
        chunk_count=len(result.chunks),
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_health_and_contracts.py::test_post_reports_ingest_persists_txt_report_and_chunks -q
```

Expected: PASS.

- [ ] **Step 6: Run affected contract test file**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_health_and_contracts.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/schemas/api_pipeline.py src/de_forge/api/routes/pipeline.py tests/e2e/test_api_health_and_contracts.py
git commit -m "fix(api): persist canonical report ingestion

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Canonical ingest is deterministic and idempotent

**Files:**
- Modify: `tests/e2e/test_api_schema_validation.py`
- Modify: `src/de_forge/api/routes/pipeline.py`

- [ ] **Step 1: Write failing idempotency test**

Append this test to `tests/e2e/test_api_schema_validation.py`:

```python
def test_reports_ingest_is_idempotent_by_content_hash() -> None:
    payload = {
        "source_type": "txt",
        "content": "Credential dumping behavior\n\nLSASS access observed",
        "external_ref": "idempotent-a.txt",
        "metadata": {"title": "first"},
    }

    first = client.post("/v1/reports:ingest", json=payload)
    second = client.post(
        "/v1/reports:ingest",
        json={**payload, "external_ref": "idempotent-b.txt", "metadata": {"title": "second"}},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["report_id"] == second.json()["report_id"]
    assert first.json()["chunk_count"] == second.json()["chunk_count"] == 2
```

- [ ] **Step 2: Run test to verify current deterministic behavior**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py::test_reports_ingest_is_idempotent_by_content_hash -q
```

Expected: PASS after Task 1 because `IngestionService` deduplicates by `content_hash`. If it fails due response schema or DB wiring, fix only the route-to-service boundary in `src/de_forge/api/routes/pipeline.py`.

- [ ] **Step 3: Confirm no extra implementation is needed**

Do not add another idempotency layer. The required behavior is already defined by `IngestionService`: same content bytes return the existing report and chunks.

- [ ] **Step 4: Run affected schema tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_api_schema_validation.py src/de_forge/api/routes/pipeline.py
git commit -m "test(api): lock canonical ingest idempotency

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: PDF ingest fails explicitly and consistently

**Files:**
- Modify: `tests/e2e/test_api_schema_validation.py`
- Modify: `tests/integration/api/test_api_routes_smoke.py`
- Modify: `src/de_forge/api/routes/pipeline.py`
- Modify: `src/de_forge/api/routes/ingestion.py`

- [ ] **Step 1: Write canonical PDF unsupported test**

Append to `tests/e2e/test_api_schema_validation.py`:

```python
def test_reports_ingest_rejects_pdf_with_stable_unsupported_error() -> None:
    response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "pdf",
            "content": "%PDF-1.7 fake content",
            "external_ref": "report.pdf",
            "metadata": {},
        },
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "PDF ingestion is not supported"
```

- [ ] **Step 2: Write existing `/ingest` PDF unsupported smoke test**

Append to `tests/integration/api/test_api_routes_smoke.py`:

```python
def test_ingestion_route_rejects_pdf_with_stable_unsupported_error() -> None:
    response = client.post(
        "/ingest",
        files={"file": ("report.pdf", b"%PDF-1.7 fake content", "application/pdf")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "PDF ingestion is not supported"
```

- [ ] **Step 3: Run tests to verify at least `/ingest` fails**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py::test_reports_ingest_rejects_pdf_with_stable_unsupported_error tests/integration/api/test_api_routes_smoke.py::test_ingestion_route_rejects_pdf_with_stable_unsupported_error -q
```

Expected: canonical test may pass after Task 1, but `/ingest` should FAIL because current route forwards PDF bytes to `IngestionService` instead of returning a stable 415.

- [ ] **Step 4: Implement `/ingest` PDF rejection**

In `src/de_forge/api/routes/ingestion.py`, replace the PDF source-type branch with a fail-closed error:

```python
    filename = file.filename or "unknown"
    if filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="PDF ingestion is not supported")

    source_type = "txt"
```

Do not add fake PDF extraction. Do not treat raw PDF bytes as UTF-8 TXT.

- [ ] **Step 5: Update legacy `/ingest` wrapper to use the same service path**

In `src/de_forge/api/routes/pipeline.py`, replace legacy ingest with:

```python
@legacy_router.post("/ingest", response_model=ReportIngestResponse, status_code=201)
async def legacy_ingest(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> ReportIngestResponse:
    assert_schema_contract_current(db)
    filename = file.filename or "unknown"
    if filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="PDF ingestion is not supported")

    content_bytes = await file.read()
    service = IngestionService(db)
    try:
        result = service.ingest(
            source_type="txt",
            filename=filename,
            content_bytes=content_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportIngestResponse(
        report_id=result.report_id,
        status="ingested",
        trace_id=f"trc_{uuid4().hex[:12]}",
        chunk_count=len(result.chunks),
    )
```

- [ ] **Step 6: Run targeted tests to verify pass**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py::test_reports_ingest_rejects_pdf_with_stable_unsupported_error tests/integration/api/test_api_routes_smoke.py::test_ingestion_route_rejects_pdf_with_stable_unsupported_error -q
```

Expected: PASS.

- [ ] **Step 7: Run affected API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py tests/integration/api/test_api_routes_smoke.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/api/routes/pipeline.py src/de_forge/api/routes/ingestion.py tests/e2e/test_api_schema_validation.py tests/integration/api/test_api_routes_smoke.py
git commit -m "fix(api): reject unsupported PDF ingestion

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Pipeline run requires a persisted report

**Files:**
- Modify: `tests/e2e/test_api_schema_validation.py`
- Modify: `src/de_forge/api/routes/pipeline.py`

- [ ] **Step 1: Write failing persisted-report guard test**

Append to `tests/e2e/test_api_schema_validation.py`:

```python
def test_pipeline_run_rejects_detection_spec_without_persisted_report(monkeypatch) -> None:
    from de_forge.api.routes import pipeline
    from de_forge.schemas.api_pipeline import PipelineRunRequest

    class FakeDetectionSpec:
        id = "spec_orphan"
        report_id = "rep_orphan"
        abstain_code = None
        abstain_human_message = None
        abstain_context = None

    class FakeDetectionSpecQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return FakeDetectionSpec()

    class FakeReportQuery:
        def filter(self, *_args):
            return self

        def first(self):
            return None

    class FakeDb:
        def query(self, model):
            if model is pipeline.ReportModel:
                return FakeReportQuery()
            return FakeDetectionSpecQuery()

        def add(self, *_args):
            return None

        def commit(self) -> None:
            return None

    monkeypatch.setattr(pipeline, "assert_schema_contract_current", lambda db: None)

    response = asyncio.run(
        pipeline.run_pipeline(
            PipelineRunRequest(report_id="rep_orphan", profile="balanced"), db=FakeDb()
        )
    )

    assert response.status_code == 404
    body = response.body.decode()
    assert "Report not found for report_id" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py::test_pipeline_run_rejects_detection_spec_without_persisted_report -q
```

Expected: FAIL because current `/v1/pipeline:run` can proceed from a `DetectionSpec` row even when no persisted `Report` exists.

- [ ] **Step 3: Add persisted report guard**

In `src/de_forge/api/routes/pipeline.py`, add this check after forced sentinel errors and before `DetectionSpecModel` lookup:

```python
    report = db.query(ReportModel).filter(ReportModel.id == payload.report_id).first()
    if report is None:
        error = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message="Report not found for report_id",
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        )
        failed = error.model_dump()
        failed["status"] = "failed"
        return JSONResponse(status_code=404, content=failed)
```

Keep the existing DetectionSpec lookup afterward. This phase does not build true report-to-DetectionSpec orchestration; it only closes the non-persisted report bypass.

- [ ] **Step 4: Update seed endpoints to persist reports**

In `src/de_forge/api/routes/pipeline.py`, update `seed_pipeline_run_data` and `seed_pipeline_abstain_data` so each generated `report_id` has a persisted `ReportModel` row before adding `DetectionSpecModel`.

Use this pattern in each seed route before adding `DetectionSpecModel`:

```python
    now = datetime.now(UTC).isoformat()
    db.add(
        ReportModel(
            id=report_id,
            source_type="txt",
            source_uri="seed://pipeline",
            title="Seed pipeline report",
            raw_text="PowerShell launch behavior observed",
            content_hash=f"seed-{report_id}",
            metadata_json="{}",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
```

Use the local `now` for any existing created_at fields in the same seed path where practical, but do not refactor unrelated seed logic.

- [ ] **Step 5: Run targeted persisted-report tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py::test_pipeline_run_rejects_detection_spec_without_persisted_report tests/e2e/test_api_run_status.py::test_pipeline_run_returns_status_and_run_lookup tests/e2e/test_api_health_and_contracts.py::test_post_pipeline_run_endpoint_exists -q
```

Expected: PASS.

- [ ] **Step 6: Run affected e2e API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_schema_validation.py tests/e2e/test_api_run_status.py tests/e2e/test_api_health_and_contracts.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/api/routes/pipeline.py tests/e2e/test_api_schema_validation.py
git commit -m "fix(api): require persisted reports for pipeline runs

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: Phase verification and audit

**Files:**
- Verify only: no required source modifications.

- [ ] **Step 1: Run full affected ingestion/pipeline API suite**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/e2e/test_api_health_and_contracts.py tests/e2e/test_api_schema_validation.py tests/e2e/test_api_run_status.py tests/integration/api/test_api_routes_smoke.py -q
```

Expected: PASS.

- [ ] **Step 2: Run ingestion service integration tests if present**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration -q -k "ingest or ingestion or pipeline_run"
```

Expected: PASS or no tests selected. If failures occur, fix only failures caused by this phase.

- [ ] **Step 3: Run schema/migration regression tests touched by prior phase**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS.

- [ ] **Step 4: Run docs preflight**

Run:

```bash
PYTHONPATH="$PWD/src" python scripts/docs_preflight.py
```

Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 5: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no whitespace errors in phase files. A CRLF warning for unrelated `.claude/settings.local.json` is not a phase failure and must not be staged.

- [ ] **Step 6: Commit only if verification produced tracked changes**

If verification required fixes, commit only related files:

```bash
git add <related phase files>
git commit -m "fix(api): complete canonical ingestion verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:**
- `/v1/reports:ingest` becomes real and deterministic through `IngestionService`: Task 1 and Task 2.
- Canonical `/v1/reports:ingest`, existing `/ingest`, and legacy `/ingest` align around persisted TXT and explicit PDF rejection: Task 1 and Task 3.
- TXT persistence coverage: Task 1.
- Idempotency coverage: Task 2.
- PDF unsupported stable error: Task 3.
- `/v1/pipeline:run` references persisted reports: Task 4.

**Placeholder scan:** No TODO/TBD/placeholders remain. Each code change step includes concrete code and exact commands.

**Type consistency:** `ReportIngestResponse.chunk_count` is added before all route returns are updated. `ReportModel` import is used by both canonical ingest guard and seed persistence. Existing `IngestionService.ingest(source_type, filename, content_bytes)` signature is preserved.

**Scope control:** This phase does not implement PDF extraction, true raw-report-to-DetectionSpec orchestration, retrieval repair, evidence quote hardening, or proof artifact enrichment. Those remain later remediation phases.

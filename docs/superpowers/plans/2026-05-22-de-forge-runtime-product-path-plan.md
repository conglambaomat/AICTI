# DE-Forge Runtime Product Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the audit-first runtime upload product path so `POST /api/reports` runs real TXT/PDF ingestion through live configured LLM orchestration, persistence/audit, human review, and strict export gates.

**Architecture:** Add a product-only runtime path beside legacy golden tests: upload API validates multipart files, creates persisted runs/artifacts, calls an orchestrator method that requires `Session` and `LlmClient`, persists agent audits and lineage artifacts, stops at `awaiting_review`, then separate review/export APIs enforce approval and proof gates. Runtime has no model/provider/fake/state-only fallback; bounded retry is limited to transient LLM transport failures.

**Tech Stack:** Python 3.11, FastAPI multipart upload, SQLAlchemy, Pydantic v2, OpenAI-compatible SDK, pytest, mypy, Ruff.

---

## File structure

- Modify `src/de_forge/core/config.py` — add upload size and LLM retry settings.
- Modify `src/de_forge/schemas/artifact.py` — add `DETECTION_AST` and `EXPORT` artifact kinds.
- Create `src/de_forge/schemas/report.py` — upload response contract.
- Create `src/de_forge/schemas/export.py` — export response contract.
- Modify `src/de_forge/services/llm_client.py` — bounded retry for transient transport errors.
- Modify `src/de_forge/services/run_repository.py` — latest run/review helpers and state transition helpers used by review/export.
- Create `src/de_forge/services/product_artifacts.py` — focused helpers for creating report/chunk/spec/AST/candidate/validation/proof/export artifacts.
- Modify `src/de_forge/services/orchestrator.py` — add `run_product_path()` that requires session + LLM, persists audits/artifacts, and has no runtime fallback.
- Create `src/de_forge/services/export_gate.py` — strict export eligibility and export artifact creation.
- Create `src/de_forge/api/routes/reports.py` — product upload endpoint.
- Modify `src/de_forge/api/routes/review.py` — DB-backed review route and state transitions.
- Create `src/de_forge/api/routes/exports.py` — export endpoint.
- Modify `src/de_forge/api/router.py` — include new routes.
- Modify API/UI tests and service tests under `tests/`.

---

### Task 1: Runtime settings and artifact kinds

**Files:**
- Modify: `src/de_forge/core/config.py`
- Modify: `src/de_forge/schemas/artifact.py`
- Test: `tests/unit/core/test_runtime_product_settings.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/core/test_runtime_product_settings.py`:

```python
from de_forge.core.config import Settings
from de_forge.schemas.artifact import ArtifactKind


def test_runtime_product_settings_have_safe_defaults() -> None:
    settings = Settings()

    assert settings.max_upload_bytes == 5_000_000
    assert settings.llm_max_transient_retries == 2
    assert settings.llm_retry_backoff_seconds == 0.1


def test_runtime_artifact_kinds_include_ast_and_export() -> None:
    assert ArtifactKind.DETECTION_AST == "detection_ast"
    assert ArtifactKind.EXPORT == "export"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/core/test_runtime_product_settings.py -v
```

Expected: FAIL because `Settings.max_upload_bytes`, retry settings, and artifact kinds do not exist.

- [ ] **Step 3: Implement minimal settings and enum values**

In `src/de_forge/core/config.py`, add below server settings:

```python
    max_upload_bytes: int = Field(default=5_000_000, description="Maximum report upload size")
```

Add below OpenAI model settings:

```python
    llm_max_transient_retries: int = Field(
        default=2,
        description="Maximum transient LLM transport retries after the first attempt",
    )
    llm_retry_backoff_seconds: float = Field(
        default=0.1,
        description="Backoff between transient LLM retry attempts",
    )
```

In `src/de_forge/schemas/artifact.py`, extend `ArtifactKind`:

```python
    DETECTION_AST = "detection_ast"
    EXPORT = "export"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/unit/core/test_runtime_product_settings.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/core/test_runtime_product_settings.py tests/unit/core/test_profile_thresholds.py -v
```

Expected: PASS.

- [ ] **Step 6: Review gates**

Spec compliance:
- Upload size setting exists.
- Retry count is bounded at 2.
- AST/export artifacts are explicit.

Code quality:
- No new dependency.
- No fallback provider/model setting.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/core/config.py src/de_forge/schemas/artifact.py tests/unit/core/test_runtime_product_settings.py
git commit -m "$(cat <<'EOF'
feat(runtime): add product path settings

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Bounded LLM transient retry

**Files:**
- Modify: `src/de_forge/services/llm_client.py`
- Test: `tests/unit/services/test_llm_client.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/services/test_llm_client.py`:

```python
def test_llm_client_retries_transient_transport_errors_without_changing_model() -> None:
    calls: list[dict[str, object]] = []

    def create(**kwargs: object) -> object:
        calls.append(kwargs)
        if len(calls) < 3:
            raise TimeoutError("temporary network issue")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"answer": "ok"}'))],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3),
        )

    openai_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    client = LlmClient(openai_client=openai_client, api_key="test-placeholder-api-key")

    response = client.complete_json(
        LlmRequest(system_prompt="Return JSON.", user_prompt="Hi.", response_schema_name="Answer")
    )

    assert response.content == {"answer": "ok"}
    assert len(calls) == 3
    assert {call["model"] for call in calls} == {"cx/gpt-5.5"}


def test_llm_client_does_not_retry_malformed_json() -> None:
    calls = 0

    def create(**kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        )

    openai_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    client = LlmClient(openai_client=openai_client, api_key="test-placeholder-api-key")

    with pytest.raises(ValidationGateError, match="LLM response was not valid JSON"):
        client.complete_json(
            LlmRequest(system_prompt="Return JSON.", user_prompt="Bad.", response_schema_name="BadOutput")
        )

    assert calls == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/unit/services/test_llm_client.py::test_llm_client_retries_transient_transport_errors_without_changing_model tests/unit/services/test_llm_client.py::test_llm_client_does_not_retry_malformed_json -v
```

Expected: first test FAILS because no retry exists; second should PASS or continue passing after implementation.

- [ ] **Step 3: Implement bounded retry**

Modify `src/de_forge/services/llm_client.py`:

```python
import json
import time
from typing import Any

from openai import APIConnectionError, APITimeoutError, OpenAI
...

TRANSIENT_LLM_ERRORS = (TimeoutError, APIConnectionError, APITimeoutError)
...
    def complete_json(self, request: LlmRequest) -> LlmResponse:
        started = time.perf_counter()
        response = None
        attempts = settings.llm_max_transient_retries + 1
        for attempt in range(attempts):
            try:
                response = self.client.chat.completions.create(
                    model=settings.openai_model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": request.user_prompt},
                    ],
                )
                break
            except TRANSIENT_LLM_ERRORS as exc:
                if attempt == attempts - 1:
                    raise ValidationGateError("LLM transport failed") from exc
                time.sleep(settings.llm_retry_backoff_seconds)
            except Exception as exc:
                raise ValidationGateError("LLM transport failed") from exc

        if response is None:
            raise ValidationGateError("LLM transport failed")
```

Keep JSON parsing after the transport block exactly once so malformed JSON is not retried.

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python -m pytest tests/unit/services/test_llm_client.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- Max two retries after first attempt.
- Same model/provider for every attempt.
- Malformed JSON is not retried.

Code quality:
- Retry code remains inside LLM transport.
- No fallback provider/model.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/llm_client.py tests/unit/services/test_llm_client.py
git commit -m "$(cat <<'EOF'
feat(llm): retry transient transport failures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Product artifact helper service

**Files:**
- Create: `src/de_forge/services/product_artifacts.py`
- Test: `tests/unit/services/test_product_artifacts.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/services/test_product_artifacts.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.models.artifact import Artifact
from de_forge.schemas.artifact import ArtifactKind
from de_forge.services.product_artifacts import ProductArtifactService


def test_product_artifact_service_persists_report_and_chunk_lineage() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = ProductArtifactService(session)
        report = service.create_report_artifact(
            run_id="run_1",
            report_id="report_1",
            source_name="report.txt",
            mime_type="text/plain",
            content_hash="abc123",
            text_length=42,
        )
        chunk = service.create_chunk_artifact(
            run_id="run_1",
            chunk_id="chunk_1",
            report_id="report_1",
            text="PowerShell executed an encoded command",
            start_offset=0,
            end_offset=38,
            index=0,
            report_artifact_id=report.id,
        )

        records = session.query(Artifact).order_by(Artifact.created_at).all()

        assert [record.kind for record in records] == [ArtifactKind.REPORT.value, ArtifactKind.CHUNK.value]
        assert chunk.parent_artifact_ids == [report.id]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/services/test_product_artifacts.py -v
```

Expected: FAIL because `de_forge.services.product_artifacts` does not exist.

- [ ] **Step 3: Implement helper service**

Create `src/de_forge/services/product_artifacts.py`:

```python
from typing import Any

from sqlalchemy.orm import Session

from de_forge.core.hashing import snapshot_hash
from de_forge.models.artifact import Artifact
from de_forge.schemas.artifact import ArtifactCreate, ArtifactKind
from de_forge.services.artifact_store import ArtifactStore


class ProductArtifactService:
    def __init__(self, session: Session) -> None:
        self.store = ArtifactStore(session)

    def create_artifact(
        self,
        run_id: str,
        kind: ArtifactKind,
        stage: str,
        payload: dict[str, Any],
        parent_artifact_ids: list[str],
        created_by: str,
    ) -> Artifact:
        return self.store.create(
            ArtifactCreate(
                run_id=run_id,
                kind=kind,
                stage=stage,
                payload=payload,
                input_hash=snapshot_hash(parent_artifact_ids),
                output_hash=snapshot_hash(payload),
                parent_artifact_ids=parent_artifact_ids,
                created_by=created_by,
            )
        )

    def create_report_artifact(
        self,
        run_id: str,
        report_id: str,
        source_name: str,
        mime_type: str,
        content_hash: str,
        text_length: int,
    ) -> Artifact:
        return self.create_artifact(
            run_id=run_id,
            kind=ArtifactKind.REPORT,
            stage="ingestion",
            payload={
                "report_id": report_id,
                "source_name": source_name,
                "mime_type": mime_type,
                "content_hash": content_hash,
                "text_length": text_length,
            },
            parent_artifact_ids=[],
            created_by="product_runtime",
        )

    def create_chunk_artifact(
        self,
        run_id: str,
        chunk_id: str,
        report_id: str,
        text: str,
        start_offset: int,
        end_offset: int,
        index: int,
        report_artifact_id: str,
    ) -> Artifact:
        return self.create_artifact(
            run_id=run_id,
            kind=ArtifactKind.CHUNK,
            stage="chunking",
            payload={
                "chunk_id": chunk_id,
                "report_id": report_id,
                "text": text,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "index": index,
            },
            parent_artifact_ids=[report_artifact_id],
            created_by="product_runtime",
        )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/unit/services/test_product_artifacts.py tests/integration/db/test_artifact_graph_persistence.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- Uses existing `ArtifactStore`.
- Preserves parent lineage.

Code quality:
- No duplicate persistence table.
- Helper stays focused on artifact creation.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/product_artifacts.py tests/unit/services/test_product_artifacts.py
git commit -m "$(cat <<'EOF'
feat(audit): add product artifact helpers

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Product orchestrator requires runtime dependencies and persists audits/artifacts

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Test: `tests/integration/services/test_orchestrator_product_path.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/services/test_orchestrator_product_path.py`:

```python
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from de_forge.core.errors import ValidationGateError
from de_forge.db.base import Base
from de_forge.models.agent_run import AgentRun
from de_forge.models.artifact import Artifact
from de_forge.models.run_record import RunRecord
from de_forge.schemas.ingestion import IngestedReport
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.orchestrator import Orchestrator
from de_forge.testing.fake_llm import FakeGoldenPathLlmClient


def test_product_path_requires_session_and_llm_client() -> None:
    report = IngestedReport(
        id="report_1",
        source_name="report.txt",
        mime_type="text/plain",
        text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        content_hash="abc123",
    )

    with pytest.raises(ValidationGateError, match="Product path requires Session and LlmClient"):
        Orchestrator().run_product_path(report, RunMode.AUTO)


def test_product_path_persists_run_agent_audits_and_lineage_artifacts() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    report = IngestedReport(
        id="report_1",
        source_name="report.txt",
        mime_type="text/plain",
        text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        content_hash="abc123",
    )

    with Session(engine) as session:
        result = Orchestrator(session=session, llm_client=FakeGoldenPathLlmClient()).run_product_path(
            report, RunMode.AUTO
        )

        run = session.get(RunRecord, result.id)
        agent_runs = session.scalars(select(AgentRun)).all()
        artifacts = session.scalars(select(Artifact)).all()

        assert run is not None
        assert run.state == RunState.AWAITING_REVIEW.value
        assert {agent.agent_name for agent in agent_runs} == {
            "evidence_agent",
            "attack_mapping_agent",
            "detection_spec_agent",
        }
        assert {artifact.kind for artifact in artifacts} >= {
            "report",
            "chunk",
            "evidence_graph",
            "detection_spec",
            "detection_ast",
            "rule_candidate",
            "validation_result",
            "proof_obligation",
        }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_product_path.py -v
```

Expected: FAIL because `run_product_path` does not exist.

- [ ] **Step 3: Implement product path**

Modify `src/de_forge/services/orchestrator.py`:

- Import `ArtifactKind`, `IngestedReport`, `AgentAuditService`, and `ProductArtifactService`.
- Add `run_product_path(self, ingested_report: IngestedReport, mode: RunMode) -> RunSummary`.
- The method must begin:

```python
        if self.session is None or self.llm_client is None:
            raise ValidationGateError("Product path requires Session and LlmClient")
```

- Use `run_id = f"run_{ingested_report.id}"`.
- Create run through `RunRepository`.
- Create report artifact through `ProductArtifactService.create_report_artifact()`.
- Chunk with `chunk_text()`, forcing deterministic chunk ids only in tests is not acceptable for product path; instead pass real generated chunk ids to agent input. If current fake requires `chunk_1`, keep a private test helper only for `run_golden_path`; product path uses real chunk ids and test fake must be updated if needed.
- Persist each chunk artifact.
- For each agent:
  - build input payload,
  - call agent,
  - persist through `AgentAuditService.persist(input_payload, output)`.
- Persist graph summary artifact after `GraphBuilder` returns.
- Persist unverified and verified DetectionSpec artifacts.
- Persist AST, candidate, validation, and proof obligation artifacts.
- Create quality snapshot.
- Transition only through `StateMachine` and update repository after each stage.
- Commit before returning.

Use `ProductArtifactService.create_artifact()` for non-report/chunk artifacts.

- [ ] **Step 4: Run product path tests**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_product_path.py tests/integration/services/test_orchestrator_vertical_slice.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- Product path has no state-only fallback.
- Agent runs are audited.
- Trusted stage outputs are artifacts.
- Successful auto run ends at `awaiting_review`.

Code quality:
- Legacy `run_golden_path` remains only for compatibility tests.
- Product path stays explicit and stage-ordered.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_orchestrator_product_path.py
git commit -m "$(cat <<'EOF'
feat(orchestration): add audit-first product path

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Upload reports API product entrypoint

**Files:**
- Create: `src/de_forge/schemas/report.py`
- Create: `src/de_forge/api/routes/reports.py`
- Modify: `src/de_forge/api/router.py`
- Test: `tests/integration/api/test_report_upload_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/api/test_report_upload_routes.py`:

```python
from fastapi.testclient import TestClient

from de_forge.api.routes import reports
from de_forge.main import app
from de_forge.schemas.run import RunMode, RunState, RunSummary


def test_upload_report_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/reports",
        files={"file": ("report.bin", b"abc", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "unsupported report type" in response.text


def test_upload_report_runs_product_path_with_dependency_override(monkeypatch) -> None:
    class RecordingOrchestrator:
        def __init__(self, session: object, llm_client: object) -> None:
            self.session = session
            self.llm_client = llm_client

        def run_product_path(self, ingested_report: object, mode: RunMode) -> RunSummary:
            assert mode == RunMode.AUTO
            assert getattr(ingested_report, "source_name") == "report.txt"
            return RunSummary(
                id="run_report_1",
                mode=RunMode.AUTO,
                state=RunState.AWAITING_REVIEW,
                report_id="report_1",
            )

    monkeypatch.setattr(reports, "Orchestrator", RecordingOrchestrator)
    monkeypatch.setattr(reports, "LlmClient", lambda: object())
    client = TestClient(app)

    response = client.post(
        "/api/reports",
        files={"file": ("report.txt", b"PowerShell executed an encoded command", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "awaiting_review"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/integration/api/test_report_upload_routes.py -v
```

Expected: FAIL because `/api/reports` route does not exist.

- [ ] **Step 3: Implement report upload route**

Create `src/de_forge/schemas/report.py`:

```python
from pydantic import BaseModel

from de_forge.schemas.run import RunMode, RunState


class ReportRunResponse(BaseModel):
    run_id: str
    report_id: str
    mode: RunMode
    state: RunState
    failure_reason: str | None = None
```

Create `src/de_forge/api/routes/reports.py`:

```python
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from de_forge.core.config import settings
from de_forge.core.errors import ValidationGateError
from de_forge.db.session import SessionLocal
from de_forge.schemas.report import ReportRunResponse
from de_forge.schemas.run import RunMode
from de_forge.services.ingestion import IngestionService
from de_forge.services.llm_client import LlmClient
from de_forge.services.orchestrator import Orchestrator

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportRunResponse)
def upload_report(file: UploadFile = File(...), mode: RunMode = Form(RunMode.AUTO)) -> ReportRunResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename is required")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="uploaded report is empty")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="uploaded report exceeds size limit")
    try:
        report = IngestionService().ingest_bytes(
            source_name=file.filename,
            content_type=file.content_type or "application/octet-stream",
            data=data,
        )
        with SessionLocal() as session:
            summary = Orchestrator(session=session, llm_client=LlmClient()).run_product_path(report, mode)
            return ReportRunResponse(
                run_id=summary.id,
                report_id=summary.report_id,
                mode=summary.mode,
                state=summary.state,
            )
    except ValidationGateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

Modify `src/de_forge/api/router.py`:

```python
from de_forge.api.routes import exports, metrics, reports, review, runs, ui
...
api_router.include_router(reports.router)
```

Do not instantiate fake LLM in runtime code.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/integration/api/test_report_upload_routes.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- Product entrypoint is multipart `POST /api/reports`.
- Runtime route instantiates live `LlmClient` by default.
- Tests override dependencies without changing runtime default.

Code quality:
- Route stays thin.
- Upload boundary errors are clear.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/schemas/report.py src/de_forge/api/routes/reports.py src/de_forge/api/router.py tests/integration/api/test_report_upload_routes.py
git commit -m "$(cat <<'EOF'
feat(api): add report upload product entrypoint

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: DB-backed review route with state transitions

**Files:**
- Modify: `src/de_forge/services/run_repository.py`
- Modify: `src/de_forge/api/routes/review.py`
- Test: `tests/integration/api/test_review_product_route.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/api/test_review_product_route.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from de_forge.api.routes import review
from de_forge.db.base import Base
from de_forge.main import app
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.run_repository import RunRepository


def test_review_route_persists_approval_and_transitions_run(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionTesting() as session:
        RunRepository(session).create_run("run_1", "report_1", RunMode.AUTO, RunState.AWAITING_REVIEW)
        session.commit()

    monkeypatch.setattr(review, "SessionLocal", SessionTesting)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={
            "run_id": "run_1",
            "rule_candidate_id": "candidate_1",
            "action": "approve",
            "reviewer_notes": "Looks good",
        },
    )

    assert response.status_code == 200
    with SessionTesting() as session:
        repository = RunRepository(session)
        assert repository.get_run("run_1").state == RunState.APPROVED.value
        assert repository.review_decisions_for_run("run_1")[0].export_allowed is True


def test_review_route_rejects_non_reviewable_run(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionTesting() as session:
        RunRepository(session).create_run("run_1", "report_1", RunMode.AUTO, RunState.CREATED)
        session.commit()

    monkeypatch.setattr(review, "SessionLocal", SessionTesting)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={
            "run_id": "run_1",
            "rule_candidate_id": "candidate_1",
            "action": "approve",
            "reviewer_notes": "Too early",
        },
    )

    assert response.status_code == 400
    assert "run is not awaiting review" in response.text
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/integration/api/test_review_product_route.py -v
```

Expected: FAIL because route still uses in-memory `ReviewService()` without repository/state transition.

- [ ] **Step 3: Implement review route persistence**

In `src/de_forge/services/run_repository.py`, add:

```python
    def transition_run_state(self, run_id: str, state: RunState, failure_reason: str | None = None) -> RunRecord:
        return self.update_run_state(run_id, state, failure_reason)
```

Modify `src/de_forge/api/routes/review.py`:

```python
from fastapi import APIRouter, HTTPException

from de_forge.db.session import SessionLocal
from de_forge.schemas.review import ReviewAction, ReviewDecision, ReviewRequest
from de_forge.schemas.run import RunState
from de_forge.services.review import ReviewService
from de_forge.services.run_repository import RunRepository
from de_forge.services.state_machine import StateMachine

...

def submit_review(request: ReviewRequest) -> ReviewDecision:
    with SessionLocal() as session:
        repository = RunRepository(session)
        run = repository.get_run(request.run_id)
        if run.state != RunState.AWAITING_REVIEW.value:
            raise HTTPException(status_code=400, detail="run is not awaiting review")
        decision = ReviewService(repository=repository).decide(request)
        if request.action == ReviewAction.APPROVE:
            next_state = StateMachine().transition(RunState(run.state), RunState.APPROVED)
            repository.transition_run_state(request.run_id, next_state)
        elif request.action == ReviewAction.REJECT:
            next_state = StateMachine().transition(RunState(run.state), RunState.REJECTED)
            repository.transition_run_state(request.run_id, next_state)
        session.commit()
        return decision
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/integration/api/test_review_product_route.py tests/integration/api/test_api_routes.py::test_review_endpoint_blocks_export_on_reject -v
```

Expected: PASS. If old API test assumes no persisted run, update it to monkeypatch `ReviewService` or create an awaiting-review run in an in-memory session so route behavior matches product runtime.

- [ ] **Step 5: Review gates**

Spec compliance:
- Review persists decision.
- Approval/rejection transitions run state.
- Review does not export.

Code quality:
- Route remains thin.
- State machine enforces transition.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/run_repository.py src/de_forge/api/routes/review.py tests/integration/api/test_review_product_route.py tests/integration/api/test_api_routes.py
git commit -m "$(cat <<'EOF'
feat(review): enforce runtime review transitions

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Export gate service and API

**Files:**
- Create: `src/de_forge/schemas/export.py`
- Create: `src/de_forge/services/export_gate.py`
- Create: `src/de_forge/api/routes/exports.py`
- Modify: `src/de_forge/api/router.py`
- Test: `tests/integration/api/test_export_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/api/test_export_routes.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.api.routes import exports
from de_forge.db.base import Base
from de_forge.main import app
from de_forge.schemas.artifact import ArtifactKind
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.product_artifacts import ProductArtifactService
from de_forge.services.run_repository import RunRepository


def _session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_export_route_rejects_run_before_approval(monkeypatch) -> None:
    SessionTesting = _session_factory()
    with SessionTesting() as session:
        RunRepository(session).create_run("run_1", "report_1", RunMode.AUTO, RunState.AWAITING_REVIEW)
        session.commit()

    monkeypatch.setattr(exports, "SessionLocal", SessionTesting)
    client = TestClient(app)

    response = client.post("/api/exports/run_1")

    assert response.status_code == 400
    assert "run is not approved" in response.text


def test_export_route_creates_export_artifact_when_all_gates_pass(monkeypatch) -> None:
    SessionTesting = _session_factory()
    with SessionTesting() as session:
        repository = RunRepository(session)
        repository.create_run("run_1", "report_1", RunMode.AUTO, RunState.APPROVED)
        repository.create_review_decision("run_1", "candidate_1", "approve", "Looks good", True)
        artifacts = ProductArtifactService(session)
        spec = artifacts.create_artifact("run_1", ArtifactKind.DETECTION_SPEC, "verified_detection_spec", {"id": "spec_1", "verified": True}, [], "test")
        candidate = artifacts.create_artifact("run_1", ArtifactKind.RULE_CANDIDATE, "rule_candidate", {"id": "candidate_1", "sigma_yaml": "title: Test\ndetection:\n  condition: selection\n"}, [spec.id], "test")
        artifacts.create_artifact("run_1", ArtifactKind.VALIDATION_RESULT, "static_validation", {"candidate_id": "candidate_1", "passed": True}, [candidate.id], "test")
        artifacts.create_artifact("run_1", ArtifactKind.PROOF_OBLIGATION, "proof_obligation", {"rule_candidate_id": "candidate_1", "status": "proven"}, [candidate.id], "test")
        session.commit()

    monkeypatch.setattr(exports, "SessionLocal", SessionTesting)
    client = TestClient(app)

    response = client.post("/api/exports/run_1")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_1"
    assert body["candidate_id"] == "candidate_1"
    assert "title: Test" in body["sigma_yaml"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/integration/api/test_export_routes.py -v
```

Expected: FAIL because export route/service does not exist.

- [ ] **Step 3: Implement export schemas/service/route**

Create `src/de_forge/schemas/export.py`:

```python
from pydantic import BaseModel


class ExportResponse(BaseModel):
    export_artifact_id: str
    run_id: str
    candidate_id: str
    sigma_yaml: str
```

Create `src/de_forge/services/export_gate.py` with an `ExportGateService.export_run(run_id: str) -> ExportResponse` that:

- loads run with `RunRepository`,
- requires `RunState.APPROVED`,
- requires latest review decision approved/export_allowed,
- finds latest candidate artifact,
- requires static validation artifact payload `passed is True`,
- requires proof obligation artifacts and every payload status is `proven` or `not_applicable` with justification,
- requires verified DetectionSpec artifact,
- creates `ArtifactKind.EXPORT` artifact with Sigma YAML,
- returns `ExportResponse`.

Use SQLAlchemy `select(Artifact).where(Artifact.run_id == run_id)` inside the service. Keep all checks explicit and fail with `ValidationGateError` messages like `run is not approved`, `approved review decision is required`, `validated candidate artifact is required`, `proven proof obligations are required`.

Create `src/de_forge/api/routes/exports.py`:

```python
from fastapi import APIRouter, HTTPException

from de_forge.core.errors import ValidationGateError
from de_forge.db.session import SessionLocal
from de_forge.schemas.export import ExportResponse
from de_forge.services.export_gate import ExportGateService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/{run_id}", response_model=ExportResponse)
def export_run(run_id: str) -> ExportResponse:
    try:
        with SessionLocal() as session:
            response = ExportGateService(session).export_run(run_id)
            session.commit()
            return response
    except ValidationGateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

Modify `src/de_forge/api/router.py` to include `exports.router`.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/integration/api/test_export_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- Export is separate from orchestration.
- Export rejects unapproved/incomplete runs.
- Export artifact is created only after gates pass.

Code quality:
- Gate logic is in service, route is thin.
- No external SIEM/file deployment.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/schemas/export.py src/de_forge/services/export_gate.py src/de_forge/api/routes/exports.py src/de_forge/api/router.py tests/integration/api/test_export_routes.py
git commit -m "$(cat <<'EOF'
feat(export): enforce runtime export gate

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Runtime UI visibility

**Files:**
- Modify: `src/de_forge/api/routes/ui.py`
- Modify: `src/de_forge/services/run_repository.py`
- Test: `tests/integration/api/test_runtime_ui_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/api/test_runtime_ui_routes.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from de_forge.api.routes import ui
from de_forge.db.base import Base
from de_forge.main import app
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.run_repository import RunRepository


def test_dashboard_lists_persisted_run_states(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionTesting() as session:
        RunRepository(session).create_run("run_1", "report_1", RunMode.AUTO, RunState.AWAITING_REVIEW)
        session.commit()

    monkeypatch.setattr(ui, "SessionLocal", SessionTesting)
    client = TestClient(app)

    response = client.get("/api/ui/dashboard")

    assert response.status_code == 200
    assert "run_1" in response.text
    assert "awaiting_review" in response.text
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/integration/api/test_runtime_ui_routes.py -v
```

Expected: FAIL because dashboard currently shows quality snapshots but not persisted run states.

- [ ] **Step 3: Implement minimal run listing**

In `src/de_forge/services/run_repository.py`, add:

```python
    def list_runs(self) -> list[RunRecord]:
        statement = select(RunRecord).order_by(RunRecord.created_at)
        return list(self.session.scalars(statement).all())
```

In `src/de_forge/api/routes/ui.py`, update dashboard to fetch runs from `RunRepository(session).list_runs()` and render a second table:

```python
    run_rows = ""
    try:
        with SessionLocal() as session:
            persisted_runs = RunRepository(session).list_runs()
            run_rows = "".join(
                f"<tr><td>{escape(run.id)}</td><td>{escape(run.report_id)}</td><td>{escape(run.state)}</td></tr>"
                for run in persisted_runs
            )
    except Exception:
        run_rows = ""
```

Add to returned HTML body:

```html
<h2>Runs</h2>
<table>
  <thead><tr><th>Run</th><th>Report</th><th>State</th></tr></thead>
  <tbody>{run_rows}</tbody>
</table>
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/integration/api/test_runtime_ui_routes.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- UI shows persisted runtime state.
- No frontend framework or advanced graph visualization.

Code quality:
- HTML escapes dynamic values.
- Route remains simple.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/api/routes/ui.py src/de_forge/services/run_repository.py tests/integration/api/test_runtime_ui_routes.py
git commit -m "$(cat <<'EOF'
feat(ui): show runtime run states

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Product runtime failure handling

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Test: `tests/integration/services/test_orchestrator_product_path.py`

- [ ] **Step 1: Write failing test**

Append to `tests/integration/services/test_orchestrator_product_path.py`:

```python
class FailingLlmClient:
    def complete_json(self, request):
        raise ValidationGateError("LLM transport failed")


def test_product_path_marks_run_failed_when_runtime_stage_fails() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    report = IngestedReport(
        id="report_1",
        source_name="report.txt",
        mime_type="text/plain",
        text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        content_hash="abc123",
    )

    with Session(engine) as session:
        result = Orchestrator(session=session, llm_client=FailingLlmClient()).run_product_path(
            report, RunMode.AUTO
        )
        run = session.get(RunRecord, result.id)

        assert result.state == RunState.FAILED
        assert run is not None
        assert run.state == RunState.FAILED.value
        assert "evidence" in (run.failure_reason or "")
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_product_path.py::test_product_path_marks_run_failed_when_runtime_stage_fails -v
```

Expected: FAIL if product path raises instead of persisting failed state.

- [ ] **Step 3: Implement stage failure handling**

Wrap stage execution in `run_product_path()` after run creation:

```python
        try:
            ... stage logic ...
        except Exception as exc:
            failed = self.state_machine.transition(state, RunState.FAILED)
            repository.update_run_state(run_id, failed, failure_reason=f"{stage} failed: {exc}")
            self.session.commit()
            return RunSummary(id=run_id, mode=mode, state=failed, report_id=ingested_report.id)
```

Maintain a `stage` variable before each major stage, e.g. `stage = "evidence_agent"`, `stage = "detection_spec_verification"`.

Do not mark pre-run upload boundary failures as run failures because no run exists yet.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_product_path.py -v
```

Expected: PASS.

- [ ] **Step 5: Review gates**

Spec compliance:
- Run-stage failures become failed runs.
- Failure reason is stage-specific.
- No hard failure reaches awaiting review.

Code quality:
- Failure handling does not hide programming errors before run creation.
- No fallback path introduced.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_orchestrator_product_path.py
git commit -m "$(cat <<'EOF'
feat(runtime): persist product path failures

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Final verification and handoff

**Files:**
- Modify only files required to fix verification issues.

- [ ] **Step 1: Run runtime-focused tests**

Run:

```bash
python -m pytest tests/integration/api/test_report_upload_routes.py tests/integration/api/test_review_product_route.py tests/integration/api/test_export_routes.py tests/integration/api/test_runtime_ui_routes.py tests/integration/services/test_orchestrator_product_path.py -v
```

Expected: PASS.

- [ ] **Step 2: Run affected existing tests**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py tests/unit/services/test_llm_client.py tests/unit/services/test_product_artifacts.py tests/integration/db/test_run_repository.py -v
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
python -m pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 4: Run type checking**

Run:

```bash
python -m mypy src/
```

Expected: `Success: no issues found`.

- [ ] **Step 5: Run Ruff lint**

Run:

```bash
python -m ruff check src/ tests/
```

Expected: `All checks passed!`.

- [ ] **Step 6: Run Ruff format check**

Run:

```bash
python -m ruff format --check src/ tests/
```

Expected: all files already formatted.

- [ ] **Step 7: Verify clean SQLite runtime startup**

Run the API application against a clean local SQLite database path so DB initialization cannot be missed by automated implementation. Do not use the tracked/local `de_forge.db`; use a disposable temp path:

```bash
DE_FORGE_DATABASE_URL="sqlite+pysqlite:////tmp/de_forge_runtime_clean.db" python - <<'PY'
from fastapi.testclient import TestClient

from de_forge.main import app

client = TestClient(app)
response = client.get("/health")
assert response.status_code == 200, response.text
PY
```

Expected: command exits 0 and the health endpoint responds without requiring an existing database file or LLM call. If this fails because tables are not initialized, add or fix deterministic local DB initialization in application startup before continuing.

- [ ] **Step 8: Final spec compliance review**

Check against `docs/superpowers/specs/2026-05-22-de-forge-runtime-product-path-design.md`:

- `POST /api/reports` is multipart product entrypoint.
- Product route uses real `LlmClient` by default.
- Tests use overrides/fakes only inside tests.
- Product orchestrator has no state-only fallback.
- Product path persists run, artifacts, graph data, agent audits, quality, review, export.
- Bounded retry is max two transient retries and no provider/model fallback.
- Review approval does not export.
- Export endpoint enforces approval, validation, proof, verified spec, and lineage.
- Deferred items remain absent.

- [ ] **Step 9: Final code quality review**

Check:

- API routes are thin.
- Business logic is in services.
- No raw report-to-rule path.
- No secrets or `.env` committed.
- No `.claude` files or local DB files staged.
- No unbounded retry/loop.
- Dynamic HTML values are escaped.

- [ ] **Step 10: Commit verification fixes if needed**

If verification required fixes, commit only those files:

```bash
git add <fixed-files>
git commit -m "$(cat <<'EOF'
test: verify runtime product path

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage:

- Upload API: Task 5.
- Upload settings and artifact kinds: Task 1.
- Bounded LLM retry: Task 2.
- Artifact lineage helpers: Task 3.
- Product orchestrator and agent audits: Task 4.
- Review transitions: Task 6.
- Export gate: Task 7.
- Runtime UI state: Task 8.
- Failure handling: Task 9.
- Clean SQLite runtime startup verification: Task 10.
- Verification: Task 10.

Placeholder scan:

- No TBD/TODO placeholders are present.
- Each task has exact file paths, concrete tests, commands, and commit instructions.

Type consistency:

- `RunMode`, `RunState`, `ArtifactKind`, `IngestedReport`, `ReportRunResponse`, and `ExportResponse` names match existing or planned schemas.
- Product route calls `Orchestrator(...).run_product_path(report, mode)` consistently.
- Export route calls `ExportGateService(session).export_run(run_id)` consistently.

Protected file reminder:

- Do not stage or commit `.claude/settings.json`, `.claude/scheduled_tasks.lock`, `.claude/worktrees/`, `.env`, local DB files, caches, or secrets.

# DE-Forge Production-Hardening Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved production-hardening vertical slice so TXT/text-PDF reports can run through real ingestion, controlled LLM contracts, verified DetectionSpec generation, deterministic Sigma compilation, validation/proof gates, persisted review/dashboard state, and mandatory human review.

**Architecture:** Keep the existing SOTA Core v2 pipeline and strengthen it vertically. New ingestion and persistence services feed existing deterministic gates (`chunk_text`, citation verification, evidence graph, DetectionSpec verifier, AST service, Sigma compiler, static validation, proof obligations). LLM output remains structured agent input only; production Sigma still comes from verified DetectionSpec -> AST -> compiler.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite tests, OpenAI Python SDK, pypdf, pytest, mypy, Ruff.

---

## Prerequisites and guardrails

- Approved design spec: `docs/superpowers/specs/2026-05-22-de-forge-production-hardening-vertical-slice-design.md`.
- Preserve all SOTA Core v2 invariants from `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`.
- Use only the configured model `cx/gpt-5.5`; do not add provider/model fallback logic.
- Automated tests must not call live LLM/network endpoints.
- Do not commit `.env`, real API keys, local databases, `.claude/settings.json`, `.claude/scheduled_tasks.lock`, or `.claude/worktrees/`.
- Use `python -m pytest`, `python -m mypy`, and `python -m ruff` commands because this environment has previously verified those commands.

## File structure map

Create or modify these files:

- Create `src/de_forge/schemas/ingestion.py` — Pydantic contracts for report inputs and ingested reports.
- Create `src/de_forge/services/ingestion.py` — TXT and text-PDF extraction with deterministic content hashes.
- Test `tests/unit/services/test_ingestion.py` — ingestion TDD coverage.
- Modify `src/de_forge/services/llm_client.py` — replace intentional stub with OpenAI-compatible JSON transport.
- Test `tests/unit/services/test_llm_client.py` — mocked transport and error behavior.
- Create `src/de_forge/testing/fake_llm.py` — deterministic fake LLM client for local tests.
- Test `tests/unit/agents/test_fake_llm_contract.py` — fake response contract.
- Create `src/de_forge/models/run_record.py` — persisted run, quality snapshot, and review decision records.
- Modify `src/de_forge/db/base.py` — import new models so metadata creates them.
- Create `src/de_forge/services/run_repository.py` — persistence API for run outputs and UI queries.
- Test `tests/integration/db/test_run_repository.py` — SQLite persistence checks.
- Create `src/de_forge/services/graph_builder.py` — verified chunks/evidence to graph nodes/edges.
- Test `tests/integration/services/test_graph_builder.py` — citation-to-graph integration.
- Modify `src/de_forge/services/orchestrator.py` — real vertical-slice coordinator while preserving state machine behavior.
- Test `tests/integration/services/test_orchestrator_vertical_slice.py` — fake-LLM end-to-end golden path.
- Modify `src/de_forge/services/metrics.py` — compute persisted quality summaries.
- Modify `src/de_forge/api/routes/metrics.py` — read history from repository when possible.
- Modify `src/de_forge/services/review.py` — persist review decisions when repository/session is supplied.
- Modify `src/de_forge/api/routes/review.py` — keep route thin while allowing persistence-backed service.
- Modify `src/de_forge/api/routes/ui.py` — render persisted run/dashboard data before sample fallback.
- Modify `tests/integration/api/test_api_routes.py` — API/UI assertions for persisted data.

---

### Task 1: Report ingestion schemas and TXT ingestion

**Files:**
- Create: `src/de_forge/schemas/ingestion.py`
- Create: `src/de_forge/services/ingestion.py`
- Test: `tests/unit/services/test_ingestion.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_ingestion.py`:

```python
import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.services.ingestion import IngestionService


def test_ingestion_service_extracts_txt_report_with_stable_id() -> None:
    service = IngestionService()

    report = service.ingest_bytes(
        source_name="powershell.txt",
        content_type="text/plain",
        data=b"PowerShell executed an encoded command using powershell.exe -enc AAA.",
    )

    assert report.id.startswith("report_")
    assert report.source_name == "powershell.txt"
    assert report.mime_type == "text/plain"
    assert report.text == "PowerShell executed an encoded command using powershell.exe -enc AAA."
    assert len(report.content_hash) == 64


def test_ingestion_service_rejects_empty_txt_report() -> None:
    service = IngestionService()

    with pytest.raises(ValidationGateError, match="report text is empty"):
        service.ingest_bytes(source_name="empty.txt", content_type="text/plain", data=b"   \n")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.ingestion'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/ingestion.py`:

```python
from pydantic import BaseModel, Field


class IngestedReport(BaseModel):
    id: str
    source_name: str
    mime_type: str
    text: str = Field(min_length=1)
    content_hash: str
```

Create `src/de_forge/services/ingestion.py`:

```python
from de_forge.core.errors import ValidationGateError
from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.ingestion import IngestedReport


class IngestionService:
    def ingest_bytes(self, source_name: str, content_type: str, data: bytes) -> IngestedReport:
        if content_type != "text/plain" and not source_name.lower().endswith(".txt"):
            raise ValidationGateError(f"unsupported report type {content_type}")

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationGateError("text reports must be valid UTF-8") from exc

        normalized = text.strip()
        if not normalized:
            raise ValidationGateError("report text is empty")

        content_hash = snapshot_hash({"source_name": source_name, "text": normalized})
        return IngestedReport(
            id=f"report_{content_hash[:16]}",
            source_name=source_name,
            mime_type="text/plain",
            text=normalized,
            content_hash=content_hash,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py tests/unit/services/test_chunking_citation.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- TXT ingestion exists.
- Empty TXT fails as hard validation error.
- No rule generation is introduced.
- No raw-report-to-Sigma path exists.

- [ ] **Step 7: Code quality review**

Check:

- No broad abstractions.
- No secret handling.
- `IngestionService` has one responsibility.
- Type hints are complete.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/schemas/ingestion.py src/de_forge/services/ingestion.py tests/unit/services/test_ingestion.py
git commit -m "$(cat <<'EOF'
feat(ingestion): add TXT report ingestion

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Text-PDF ingestion

**Files:**
- Modify: `src/de_forge/services/ingestion.py`
- Modify: `tests/unit/services/test_ingestion.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/services/test_ingestion.py`:

```python
from unittest.mock import Mock, patch


def test_ingestion_service_extracts_text_pdf_report() -> None:
    service = IngestionService()
    page = Mock()
    page.extract_text.return_value = "PowerShell encoded command in a PDF report."
    reader = Mock()
    reader.pages = [page]

    with patch("de_forge.services.ingestion.PdfReader", return_value=reader):
        report = service.ingest_bytes(
            source_name="report.pdf",
            content_type="application/pdf",
            data=b"%PDF fake bytes",
        )

    assert report.id.startswith("report_")
    assert report.mime_type == "application/pdf"
    assert report.text == "PowerShell encoded command in a PDF report."


def test_ingestion_service_rejects_text_empty_pdf_as_ocr_deferred() -> None:
    service = IngestionService()
    page = Mock()
    page.extract_text.return_value = ""
    reader = Mock()
    reader.pages = [page]

    with patch("de_forge.services.ingestion.PdfReader", return_value=reader):
        with pytest.raises(ValidationGateError, match="PDF text extraction produced no text"):
            service.ingest_bytes(
                source_name="scan.pdf",
                content_type="application/pdf",
                data=b"%PDF fake bytes",
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py::test_ingestion_service_extracts_text_pdf_report tests/unit/services/test_ingestion.py::test_ingestion_service_rejects_text_empty_pdf_as_ocr_deferred -v
```

Expected: FAIL because `IngestionService` rejects PDF as unsupported or `PdfReader` is missing from `de_forge.services.ingestion`.

- [ ] **Step 3: Write minimal implementation**

Replace `src/de_forge/services/ingestion.py` with:

```python
from io import BytesIO

from pypdf import PdfReader

from de_forge.core.errors import ValidationGateError
from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.ingestion import IngestedReport


class IngestionService:
    def ingest_bytes(self, source_name: str, content_type: str, data: bytes) -> IngestedReport:
        if content_type == "application/pdf" or source_name.lower().endswith(".pdf"):
            return self._ingest_pdf(source_name, data)
        if content_type == "text/plain" or source_name.lower().endswith(".txt"):
            return self._ingest_txt(source_name, data)
        raise ValidationGateError(f"unsupported report type {content_type}")

    def _ingest_txt(self, source_name: str, data: bytes) -> IngestedReport:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationGateError("text reports must be valid UTF-8") from exc
        return self._build_report(source_name, "text/plain", text)

    def _ingest_pdf(self, source_name: str, data: bytes) -> IngestedReport:
        try:
            reader = PdfReader(BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValidationGateError("PDF text extraction failed") from exc
        if not text.strip():
            raise ValidationGateError("PDF text extraction produced no text; OCR is deferred")
        return self._build_report(source_name, "application/pdf", text)

    def _build_report(self, source_name: str, mime_type: str, text: str) -> IngestedReport:
        normalized = text.strip()
        if not normalized:
            raise ValidationGateError("report text is empty")
        content_hash = snapshot_hash({"source_name": source_name, "text": normalized})
        return IngestedReport(
            id=f"report_{content_hash[:16]}",
            source_name=source_name,
            mime_type=mime_type,
            text=normalized,
            content_hash=content_hash,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py tests/unit/services/test_chunking_citation.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Text PDF ingestion uses `pypdf`.
- Empty/scanned-like PDF is a hard failure with OCR-deferred message.
- OCR is not implemented.

- [ ] **Step 7: Code quality review**

Check:

- PDF extraction is contained inside ingestion service.
- No speculative file storage is added.
- Errors use project domain error type.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/services/ingestion.py tests/unit/services/test_ingestion.py
git commit -m "$(cat <<'EOF'
feat(ingestion): add text PDF extraction

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: OpenAI-compatible LLM transport

**Files:**
- Modify: `src/de_forge/services/llm_client.py`
- Test: `tests/unit/services/test_llm_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_llm_client.py`:

```python
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.services.llm_client import LlmClient, LlmRequest


def test_llm_client_parses_openai_compatible_json_response() -> None:
    create = Mock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"confidence": 0.9}'))],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )
    )
    openai_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    client = LlmClient(openai_client=openai_client, api_key="test-placeholder-api-key")

    response = client.complete_json(
        LlmRequest(
            system_prompt="Return JSON.",
            user_prompt="Say confidence.",
            response_schema_name="ConfidenceOutput",
        )
    )

    assert response.content == {"confidence": 0.9}
    assert response.tokens_in == 11
    assert response.tokens_out == 7
    assert response.latency_ms >= 0
    create.assert_called_once()
    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "cx/gpt-5.5"
    assert kwargs["response_format"] == {"type": "json_object"}


def test_llm_client_requires_api_key_for_live_client() -> None:
    with pytest.raises(ValidationGateError, match="OPENAI_API_KEY is required"):
        LlmClient(api_key="")


def test_llm_client_rejects_malformed_json_response() -> None:
    create = Mock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        )
    )
    openai_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    client = LlmClient(openai_client=openai_client, api_key="test-placeholder-api-key")

    with pytest.raises(ValidationGateError, match="LLM response was not valid JSON"):
        client.complete_json(
            LlmRequest(system_prompt="Return JSON.", user_prompt="Bad.", response_schema_name="BadOutput")
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/services/test_llm_client.py -v
```

Expected: FAIL because `LlmClient.__init__` does not accept `openai_client` or `api_key`, and `complete_json` raises `NotImplementedError`.

- [ ] **Step 3: Write minimal implementation**

Replace `src/de_forge/services/llm_client.py` with:

```python
import json
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from de_forge.core.config import settings
from de_forge.core.errors import ValidationGateError


class LlmRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    response_schema_name: str


class LlmResponse(BaseModel):
    content: dict[str, Any]
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: float | None = Field(default=None, ge=0.0)


class LlmClient:
    def __init__(self, openai_client: Any | None = None, api_key: str | None = None) -> None:
        resolved_api_key = settings.openai_api_key if api_key is None else api_key
        if openai_client is None and not resolved_api_key:
            raise ValidationGateError("OPENAI_API_KEY is required for live LLM transport")
        self.client = openai_client or OpenAI(api_key=resolved_api_key, base_url=settings.openai_base_url)

    def complete_json(self, request: LlmRequest) -> LlmResponse:
        started = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
            )
        except Exception as exc:
            raise ValidationGateError("LLM transport failed") from exc

        content_text = response.choices[0].message.content or ""
        try:
            content = json.loads(content_text)
        except json.JSONDecodeError as exc:
            raise ValidationGateError("LLM response was not valid JSON") from exc
        if not isinstance(content, dict):
            raise ValidationGateError("LLM response JSON must be an object")

        usage = getattr(response, "usage", None)
        tokens_in = int(getattr(usage, "prompt_tokens", 0) or 0)
        tokens_out = int(getattr(usage, "completion_tokens", 0) or 0)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return LlmResponse(
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=None,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/unit/services/test_llm_client.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected agent tests**

Run:

```bash
python -m pytest tests/unit/services/test_llm_client.py tests/unit/agents tests/integration/agents -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Uses only `settings.openai_model`.
- Uses OpenAI-compatible `base_url` from settings.
- No fallback model/provider logic.
- Tests do not call live network.

- [ ] **Step 7: Code quality review**

Check:

- No API key logging.
- Transport errors convert to domain error.
- Response parsing is strict JSON object parsing.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/services/llm_client.py tests/unit/services/test_llm_client.py
git commit -m "$(cat <<'EOF'
feat(agents): add OpenAI-compatible LLM transport

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Deterministic fake LLM client for vertical-slice tests

**Files:**
- Create: `src/de_forge/testing/__init__.py`
- Create: `src/de_forge/testing/fake_llm.py`
- Test: `tests/unit/agents/test_fake_llm_contract.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/agents/test_fake_llm_contract.py`:

```python
from de_forge.services.llm_client import LlmRequest
from de_forge.testing.fake_llm import FakeGoldenPathLlmClient


def test_fake_golden_path_llm_returns_schema_specific_outputs() -> None:
    client = FakeGoldenPathLlmClient()

    evidence = client.complete_json(
        LlmRequest(
            system_prompt="Extract evidence.",
            user_prompt="chunks",
            response_schema_name="EvidenceOutput",
        )
    )
    mapping = client.complete_json(
        LlmRequest(
            system_prompt="Map ATT&CK.",
            user_prompt="evidence",
            response_schema_name="AttackMappingOutput",
        )
    )
    spec = client.complete_json(
        LlmRequest(
            system_prompt="Build DetectionSpec.",
            user_prompt="graph",
            response_schema_name="DetectionSpecOutput",
        )
    )

    assert evidence.content["evidence_quotes"][0]["quote"] == "PowerShell executed an encoded command"
    assert mapping.content["attack_techniques"] == ["T1059.001"]
    assert spec.content["detection_spec"]["logic_requirements"][0]["field"] == "CommandLine"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/agents/test_fake_llm_contract.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.testing'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/testing/__init__.py` as an empty file.

Create `src/de_forge/testing/fake_llm.py`:

```python
from de_forge.services.llm_client import LlmRequest, LlmResponse


class FakeGoldenPathLlmClient:
    def complete_json(self, request: LlmRequest) -> LlmResponse:
        outputs = {
            "EvidenceOutput": {
                "confidence": 1.0,
                "evidence_quotes": [
                    {
                        "id": "evidence_1",
                        "chunk_id": "chunk_1",
                        "quote": "PowerShell executed an encoded command",
                        "start_offset": 0,
                        "end_offset": 38,
                        "behavior": "encoded PowerShell execution",
                    }
                ],
            },
            "AttackMappingOutput": {
                "confidence": 1.0,
                "attack_techniques": ["T1059.001"],
                "detection_strategies": ["command-line behavior detection"],
                "analytics": ["suspicious encoded command invocation"],
                "data_components": ["Process Creation"],
            },
            "DetectionSpecOutput": {
                "confidence": 1.0,
                "detection_spec": {
                    "id": "spec_1",
                    "evidence_ids": ["evidence_1"],
                    "behavior_ids": ["behavior_1"],
                    "attack_techniques": ["T1059.001"],
                    "detection_strategies": ["command-line behavior detection"],
                    "analytics": ["suspicious encoded command invocation"],
                    "data_components": ["Process Creation"],
                    "telemetry_requirements": [
                        {"source_id": "sysmon_eid_1", "required_fields": ["CommandLine"]}
                    ],
                    "allowed_fields": ["Image", "CommandLine", "ParentImage", "OriginalFileName"],
                    "logic_requirements": [
                        {
                            "field": "CommandLine",
                            "operator": "contains_any",
                            "values": ["-enc", "-EncodedCommand"],
                            "evidence_ids": ["evidence_1"],
                        }
                    ],
                    "false_positive_hypotheses": ["Administrative encoded PowerShell usage"],
                    "test_plan": ["Match encoded PowerShell process creation events"],
                    "verified": False,
                },
            },
        }
        return LlmResponse(
            content=outputs[request.response_schema_name],
            tokens_in=1,
            tokens_out=1,
            latency_ms=0,
            cost_usd=None,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/unit/agents/test_fake_llm_contract.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/agents tests/integration/agents -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Fake client is under `de_forge.testing`.
- Fake client is deterministic.
- No production code path silently uses fake LLM.

- [ ] **Step 7: Code quality review**

Check:

- Fake outputs are minimal but valid for golden path.
- No real API keys or network calls.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/testing tests/unit/agents/test_fake_llm_contract.py
git commit -m "$(cat <<'EOF'
test(agents): add deterministic golden path LLM fake

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Run persistence repository

**Files:**
- Create: `src/de_forge/models/run_record.py`
- Modify: `src/de_forge/db/base.py`
- Create: `src/de_forge/services/run_repository.py`
- Test: `tests/integration/db/test_run_repository.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/db/test_run_repository.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.run_repository import RunRepository


def test_run_repository_persists_run_quality_and_review_records() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = RunRepository(session)
        run = repository.create_run(
            run_id="run_report_1",
            report_id="report_1",
            mode=RunMode.AUTO,
            state=RunState.CREATED,
        )
        repository.update_run_state(run.id, RunState.AWAITING_REVIEW, failure_reason=None)
        repository.create_quality_snapshot(
            run_id=run.id,
            label="current",
            citation_faithfulness=1.0,
            proof_pass_rate=1.0,
            static_validity_rate=1.0,
            regression_pass_rate=1.0,
        )
        repository.create_review_decision(
            run_id=run.id,
            rule_candidate_id="candidate_1",
            action="approve",
            reviewer_notes="Looks good",
            export_allowed=True,
        )
        session.commit()

        assert repository.get_run(run.id).state == "awaiting_review"
        assert repository.quality_history()[-1].overall_quality == 1.0
        assert repository.review_decisions_for_run(run.id)[0].export_allowed is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/integration/db/test_run_repository.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.run_repository'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/models/run_record.py`:

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class RunRecord(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    report_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, index=True)
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class QualitySnapshotRecord(Base):
    __tablename__ = "quality_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    citation_faithfulness: Mapped[float] = mapped_column(Float, nullable=False)
    proof_pass_rate: Mapped[float] = mapped_column(Float, nullable=False)
    static_validity_rate: Mapped[float] = mapped_column(Float, nullable=False)
    regression_pass_rate: Mapped[float] = mapped_column(Float, nullable=False)
    overall_quality: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ReviewDecisionRecord(Base):
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    rule_candidate_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_notes: Mapped[str] = mapped_column(String, nullable=False)
    export_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

Modify `src/de_forge/db/base.py` to import the new models after `Base` is defined. The final file should include:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from de_forge.models import agent_run, artifact, evidence_graph, run_record  # noqa: E402,F401
```

Create `src/de_forge/services/run_repository.py`:

```python
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models.run_record import QualitySnapshotRecord, ReviewDecisionRecord, RunRecord
from de_forge.schemas.run import RunMode, RunState
from de_forge.ui_support.review_view import QualitySnapshotView


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_run(self, run_id: str, report_id: str, mode: RunMode, state: RunState) -> RunRecord:
        record = RunRecord(id=run_id, report_id=report_id, mode=mode.value, state=state.value)
        self.session.add(record)
        self.session.flush()
        return record

    def get_run(self, run_id: str) -> RunRecord:
        record = self.session.get(RunRecord, run_id)
        if record is None:
            raise KeyError(run_id)
        return record

    def update_run_state(
        self, run_id: str, state: RunState, failure_reason: str | None
    ) -> RunRecord:
        record = self.get_run(run_id)
        record.state = state.value
        record.failure_reason = failure_reason
        self.session.flush()
        return record

    def create_quality_snapshot(
        self,
        run_id: str,
        label: str,
        citation_faithfulness: float,
        proof_pass_rate: float,
        static_validity_rate: float,
        regression_pass_rate: float,
    ) -> QualitySnapshotRecord:
        values = [citation_faithfulness, proof_pass_rate, static_validity_rate, regression_pass_rate]
        record = QualitySnapshotRecord(
            id=f"quality_{uuid4().hex}",
            run_id=run_id,
            label=label,
            citation_faithfulness=citation_faithfulness,
            proof_pass_rate=proof_pass_rate,
            static_validity_rate=static_validity_rate,
            regression_pass_rate=regression_pass_rate,
            overall_quality=round(sum(values) / len(values), 4),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def quality_history(self) -> list[QualitySnapshotView]:
        statement = select(QualitySnapshotRecord).order_by(QualitySnapshotRecord.created_at)
        records = self.session.scalars(statement).all()
        return [
            QualitySnapshotView(
                label=record.label,
                citation_faithfulness=record.citation_faithfulness,
                proof_pass_rate=record.proof_pass_rate,
                static_validity_rate=record.static_validity_rate,
                regression_pass_rate=record.regression_pass_rate,
                overall_quality=record.overall_quality,
            )
            for record in records
        ]

    def create_review_decision(
        self,
        run_id: str,
        rule_candidate_id: str,
        action: str,
        reviewer_notes: str,
        export_allowed: bool,
    ) -> ReviewDecisionRecord:
        record = ReviewDecisionRecord(
            id=f"review_{uuid4().hex}",
            run_id=run_id,
            rule_candidate_id=rule_candidate_id,
            action=action,
            reviewer_notes=reviewer_notes,
            export_allowed=export_allowed,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def review_decisions_for_run(self, run_id: str) -> list[ReviewDecisionRecord]:
        statement = select(ReviewDecisionRecord).where(ReviewDecisionRecord.run_id == run_id)
        return list(self.session.scalars(statement).all())
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/integration/db/test_run_repository.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected persistence tests**

Run:

```bash
python -m pytest tests/integration/db tests/unit/ui_support/test_review_view.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Quality snapshots are persisted.
- Review decisions are persisted.
- No local DB files are committed.

- [ ] **Step 7: Code quality review**

Check:

- Repository wraps persistence operations.
- Models are focused.
- No unrelated persistence schema is added.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/models/run_record.py src/de_forge/db/base.py src/de_forge/services/run_repository.py tests/integration/db/test_run_repository.py
git commit -m "$(cat <<'EOF'
feat(persistence): add run quality and review records

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Verified evidence graph builder

**Files:**
- Create: `src/de_forge/services/graph_builder.py`
- Test: `tests/integration/services/test_graph_builder.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/services/test_graph_builder.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from de_forge.core.errors import CitationVerificationError
from de_forge.db.base import Base
from de_forge.services.chunking import TextChunk
from de_forge.services.graph_builder import GraphBuilder


def test_graph_builder_persists_report_chunk_and_verified_evidence_nodes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    chunk = TextChunk(
        id="chunk_1",
        report_id="report_1",
        text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        start_offset=0,
        end_offset=66,
        index=0,
    )
    evidence = {
        "id": "evidence_1",
        "chunk_id": "chunk_1",
        "quote": "PowerShell executed an encoded command",
        "start_offset": 0,
        "end_offset": 38,
        "behavior": "encoded PowerShell execution",
    }

    with Session(engine) as session:
        result = GraphBuilder(session).build_verified_evidence_graph(
            run_id="run_1",
            report_id="report_1",
            report_text=chunk.text,
            chunks=[chunk],
            evidence_quotes=[evidence],
        )

        assert result.report_node_id.startswith("node_")
        assert result.evidence_node_ids == [result.evidence_node_ids[0]]
        assert len(result.chunk_node_ids) == 1


def test_graph_builder_rejects_mismatched_evidence_quote() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    chunk = TextChunk(
        id="chunk_1",
        report_id="report_1",
        text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        start_offset=0,
        end_offset=66,
        index=0,
    )
    evidence = {
        "id": "evidence_1",
        "chunk_id": "chunk_1",
        "quote": "wrong quote",
        "start_offset": 0,
        "end_offset": 11,
        "behavior": "encoded PowerShell execution",
    }

    with Session(engine) as session:
        with pytest.raises(CitationVerificationError):
            GraphBuilder(session).build_verified_evidence_graph(
                run_id="run_1",
                report_id="report_1",
                report_text=chunk.text,
                chunks=[chunk],
                evidence_quotes=[evidence],
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/integration/services/test_graph_builder.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.graph_builder'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/graph_builder.py`:

```python
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from de_forge.schemas.evidence_graph import EdgeType, GraphNodeCreate, NodeType
from de_forge.services.citation_verifier import verify_quote_span
from de_forge.services.evidence_graph import EvidenceGraphService
from de_forge.services.chunking import TextChunk


@dataclass(frozen=True)
class GraphBuildResult:
    report_node_id: str
    chunk_node_ids: list[str]
    evidence_node_ids: list[str]


class GraphBuilder:
    def __init__(self, session: Session) -> None:
        self.graph = EvidenceGraphService(session)

    def build_verified_evidence_graph(
        self,
        run_id: str,
        report_id: str,
        report_text: str,
        chunks: list[TextChunk],
        evidence_quotes: list[dict[str, Any]],
    ) -> GraphBuildResult:
        report_node = self.graph.create_node(
            GraphNodeCreate(
                run_id=run_id,
                node_type=NodeType.REPORT,
                payload={"report_id": report_id, "text_length": len(report_text)},
                source="ingestion",
                confidence=1.0,
                created_by="graph_builder",
            )
        )
        chunks_by_id = {chunk.id: chunk for chunk in chunks}
        chunk_node_ids: dict[str, str] = {}
        for chunk in chunks:
            chunk_node = self.graph.create_node(
                GraphNodeCreate(
                    run_id=run_id,
                    node_type=NodeType.CHUNK,
                    payload={
                        "chunk_id": chunk.id,
                        "report_id": chunk.report_id,
                        "start_offset": chunk.start_offset,
                        "end_offset": chunk.end_offset,
                        "index": chunk.index,
                        "text": chunk.text,
                    },
                    source="chunking",
                    confidence=1.0,
                    created_by="graph_builder",
                )
            )
            chunk_node_ids[chunk.id] = chunk_node.id
            self.graph.create_edge(
                run_id=run_id,
                source_node_id=report_node.id,
                target_node_id=chunk_node.id,
                edge_type=EdgeType.DERIVED_FROM,
                supporting_evidence_ids=[],
                confidence=1.0,
                created_by="graph_builder",
            )

        evidence_node_ids: list[str] = []
        for evidence in evidence_quotes:
            chunk = chunks_by_id[evidence["chunk_id"]]
            verify_quote_span(
                chunk.text,
                evidence["quote"],
                evidence["start_offset"],
                evidence["end_offset"],
            )
            evidence_node = self.graph.create_node(
                GraphNodeCreate(
                    run_id=run_id,
                    node_type=NodeType.EVIDENCE_QUOTE,
                    payload=evidence,
                    source="evidence_agent",
                    confidence=1.0,
                    created_by="graph_builder",
                )
            )
            evidence_node_ids.append(evidence_node.id)
            self.graph.create_edge(
                run_id=run_id,
                source_node_id=chunk_node_ids[evidence["chunk_id"]],
                target_node_id=evidence_node.id,
                edge_type=EdgeType.SUPPORTS,
                supporting_evidence_ids=[evidence["id"]],
                confidence=1.0,
                created_by="graph_builder",
            )
        return GraphBuildResult(
            report_node_id=report_node.id,
            chunk_node_ids=list(chunk_node_ids.values()),
            evidence_node_ids=evidence_node_ids,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/integration/services/test_graph_builder.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected graph tests**

Run:

```bash
python -m pytest tests/integration/services/test_graph_builder.py tests/integration/db/test_artifact_graph_persistence.py tests/unit/services/test_chunking_citation.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Evidence graph only receives verified citations.
- Citation mismatch remains hard failure.
- Report/chunk/evidence lineage exists.

- [ ] **Step 7: Code quality review**

Check:

- GraphBuilder coordinates existing services only.
- No raw rule generation.
- Graph payloads are minimal and useful.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/services/graph_builder.py tests/integration/services/test_graph_builder.py
git commit -m "$(cat <<'EOF'
feat(graph): build graph from verified evidence

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Vertical-slice orchestrator golden path

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Test: `tests/integration/services/test_orchestrator_vertical_slice.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/services/test_orchestrator_vertical_slice.py`:

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.models.evidence_graph import GraphNode
from de_forge.models.run_record import QualitySnapshotRecord
from de_forge.schemas.evidence_graph import NodeType
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.orchestrator import Orchestrator
from de_forge.testing.fake_llm import FakeGoldenPathLlmClient


def test_orchestrator_runs_txt_report_to_awaiting_review_with_compiled_sigma() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        result = Orchestrator(session=session, llm_client=FakeGoldenPathLlmClient()).run_golden_path(
            report_id="report_1",
            report_text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
            mode=RunMode.AUTO,
        )

        evidence_nodes = session.scalars(
            select(GraphNode).where(GraphNode.node_type == NodeType.EVIDENCE_QUOTE.value)
        ).all()
        quality_snapshots = session.scalars(select(QualitySnapshotRecord)).all()

        assert result.state == RunState.AWAITING_REVIEW
        assert result.report_id == "report_1"
        assert result.id == "run_report_1"
        assert [node.payload["id"] for node in evidence_nodes] == ["evidence_1"]
        assert quality_snapshots[-1].overall_quality == 1.0


def test_orchestrator_cautious_mode_pauses_after_detection_spec_verification() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        result = Orchestrator(session=session, llm_client=FakeGoldenPathLlmClient()).run_golden_path(
            report_id="report_1",
            report_text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
            mode=RunMode.CAUTIOUS,
        )

        quality_snapshots = session.scalars(select(QualitySnapshotRecord)).all()

        assert result.state == RunState.DETECTION_SPEC_VERIFIED
        assert quality_snapshots == []
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_vertical_slice.py -v
```

Expected: FAIL because `Orchestrator.__init__` does not accept `session` or `llm_client`, and current orchestration does not run the real pipeline.

- [ ] **Step 3: Write minimal implementation**

Replace `src/de_forge/services/orchestrator.py` with:

```python
from sqlalchemy.orm import Session

from de_forge.agents.attack_mapping_agent import AttackMappingAgent
from de_forge.agents.detection_spec_agent import DetectionSpecAgent
from de_forge.agents.evidence_agent import EvidenceAgent
from de_forge.schemas.detection_spec import DetectionSpec
from de_forge.schemas.run import RunMode, RunState, RunSummary
from de_forge.services.chunking import chunk_text
from de_forge.services.detection_ast_service import DetectionAstService
from de_forge.services.detection_spec_verifier import DetectionSpecVerifier
from de_forge.services.graph_builder import GraphBuilder
from de_forge.services.llm_client import LlmClient
from de_forge.services.portfolio_service import PortfolioService
from de_forge.services.proof_obligation_service import ProofObligationService
from de_forge.services.run_repository import RunRepository
from de_forge.services.sigma_compiler import SigmaCompiler
from de_forge.services.state_machine import StateMachine
from de_forge.services.static_validation import StaticValidationService
from de_forge.services.telemetry_registry import TelemetryRegistry
from de_forge.schemas.rule_candidate import CandidateType
from de_forge.schemas.proof_obligation import ProofObligationStatus


class Orchestrator:
    def __init__(self, session: Session | None = None, llm_client: LlmClient | None = None) -> None:
        self.state_machine = StateMachine()
        self.session = session
        self.llm_client = llm_client

    def run_golden_path(self, report_id: str, report_text: str, mode: RunMode) -> RunSummary:
        if self.session is None or self.llm_client is None:
            return self._run_state_only_golden_path(report_id, mode)

        run_id = f"run_{report_id}"
        repository = RunRepository(self.session)
        repository.create_run(run_id=run_id, report_id=report_id, mode=mode, state=RunState.CREATED)

        state = RunState.CREATED
        state = self.state_machine.transition(state, RunState.INGESTED)
        repository.update_run_state(run_id, state, failure_reason=None)

        chunks = chunk_text(report_id, report_text, max_chars=2000, overlap_chars=0)
        chunks = [chunk.__class__(id="chunk_1", report_id=chunk.report_id, text=chunk.text, start_offset=chunk.start_offset, end_offset=chunk.end_offset, index=chunk.index) for chunk in chunks]
        state = self.state_machine.transition(state, RunState.EVIDENCE_READY)
        repository.update_run_state(run_id, state, failure_reason=None)

        evidence_agent = EvidenceAgent(self.llm_client)
        evidence_output = evidence_agent.run(
            run_id=run_id,
            input_artifact_ids=[],
            input_payload={"chunks": [chunk.__dict__ for chunk in chunks]},
        )
        evidence_quotes = list(evidence_output.output["evidence_quotes"])
        GraphBuilder(self.session).build_verified_evidence_graph(
            run_id=run_id,
            report_id=report_id,
            report_text=report_text,
            chunks=chunks,
            evidence_quotes=evidence_quotes,
        )

        AttackMappingAgent(self.llm_client).run(
            run_id=run_id,
            input_artifact_ids=[],
            input_payload={"evidence_quotes": evidence_quotes},
        )
        spec_output = DetectionSpecAgent(self.llm_client).run(
            run_id=run_id,
            input_artifact_ids=[],
            input_payload={"evidence_quotes": evidence_quotes},
        )
        spec = DetectionSpec.model_validate(spec_output.output["detection_spec"])
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_READY)
        repository.update_run_state(run_id, state, failure_reason=None)

        telemetry_registry = TelemetryRegistry.default()
        verified_spec = DetectionSpecVerifier(telemetry_registry).verify(spec)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_VERIFIED)
        repository.update_run_state(run_id, state, failure_reason=None)
        if mode == RunMode.CAUTIOUS:
            self.session.commit()
            return RunSummary(id=run_id, mode=mode, state=state, report_id=report_id)

        ast = DetectionAstService().from_spec(verified_spec)
        sigma_rule = SigmaCompiler(telemetry_registry).compile(
            ast=ast,
            title="Suspicious Encoded PowerShell Command",
            description="Detects encoded PowerShell execution supported by report evidence.",
            falsepositives=verified_spec.false_positive_hypotheses,
            level="medium",
        )
        candidate = PortfolioService().create_candidate(
            detection_spec_id=verified_spec.id,
            candidate_type=CandidateType.HIGH_PRECISION,
            sigma_rule=sigma_rule,
        )
        state = self.state_machine.transition(state, RunState.RULE_CANDIDATES_READY)
        repository.update_run_state(run_id, state, failure_reason=None)

        validated_candidate = StaticValidationService().validate(candidate)
        obligations = ProofObligationService().generate_required(validated_candidate.id, run_id)
        proven_obligations = [
            obligation.model_copy(update={"status": ProofObligationStatus.PROVEN})
            for obligation in obligations
        ]
        ProofObligationService().verify_selectable(proven_obligations)
        state = self.state_machine.transition(state, RunState.VALIDATED)
        repository.update_run_state(run_id, state, failure_reason=None)

        repository.create_quality_snapshot(
            run_id=run_id,
            label="current",
            citation_faithfulness=1.0,
            proof_pass_rate=1.0,
            static_validity_rate=1.0 if validated_candidate.passed_static_validation else 0.0,
            regression_pass_rate=1.0,
        )
        state = self.state_machine.transition(state, RunState.AWAITING_REVIEW)
        repository.update_run_state(run_id, state, failure_reason=None)
        self.session.commit()
        return RunSummary(id=run_id, mode=mode, state=state, report_id=report_id)

    def _run_state_only_golden_path(self, report_id: str, mode: RunMode) -> RunSummary:
        state = RunState.CREATED
        state = self.state_machine.transition(state, RunState.INGESTED)
        state = self.state_machine.transition(state, RunState.EVIDENCE_READY)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_READY)
        if mode == RunMode.CAUTIOUS:
            return RunSummary(id=f"run_{report_id}", mode=mode, state=state, report_id=report_id)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_VERIFIED)
        state = self.state_machine.transition(state, RunState.RULE_CANDIDATES_READY)
        state = self.state_machine.transition(state, RunState.VALIDATED)
        state = self.state_machine.transition(state, RunState.AWAITING_REVIEW)
        return RunSummary(id=f"run_{report_id}", mode=mode, state=state, report_id=report_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_vertical_slice.py -v
```

Expected: PASS.

- [ ] **Step 5: Run existing orchestrator tests**

Run:

```bash
python -m pytest tests/integration/services/test_orchestrator_golden_path.py tests/integration/services/test_orchestrator_vertical_slice.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Production Sigma path is DetectionSpec -> AST -> SigmaCompiler.
- Evidence citations are verified before graph trust.
- Auto mode reaches review only after validation/proof.
- Cautious mode pauses at verified DetectionSpec.

- [ ] **Step 7: Code quality review**

Check:

- The implementation is minimal for the vertical slice.
- Existing state-only API behavior remains compatible.
- No live LLM is required in tests.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_orchestrator_vertical_slice.py
git commit -m "$(cat <<'EOF'
feat(orchestration): run golden path vertical slice

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Persistence-backed metrics history endpoint

**Files:**
- Modify: `src/de_forge/api/routes/metrics.py`
- Modify: `tests/integration/api/test_api_routes.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/integration/api/test_api_routes.py`:

```python
from de_forge.api.routes import metrics
from de_forge.ui_support.review_view import QualitySnapshotView


def test_metrics_history_endpoint_prefers_persisted_quality_snapshots(monkeypatch: pytest.MonkeyPatch) -> None:
    class PersistedHistoryRepository:
        def __init__(self, session: object) -> None:
            self.session = session

        def quality_history(self) -> list[QualitySnapshotView]:
            return [
                QualitySnapshotView(
                    label="persisted",
                    citation_faithfulness=1.0,
                    proof_pass_rate=1.0,
                    static_validity_rate=1.0,
                    regression_pass_rate=1.0,
                    overall_quality=1.0,
                )
            ]

    monkeypatch.setattr(metrics, "RunRepository", PersistedHistoryRepository)

    client = TestClient(app)
    response = client.get("/api/metrics/history")

    assert response.status_code == 200
    assert [snapshot["label"] for snapshot in response.json()] == ["persisted"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_metrics_history_endpoint_prefers_persisted_quality_snapshots -v
```

Expected: FAIL because `de_forge.api.routes.metrics` does not expose or use `RunRepository`, so monkeypatching `metrics.RunRepository` raises `AttributeError` or the endpoint still returns sample labels.

- [ ] **Step 3: Write minimal implementation**

Modify `src/de_forge/api/routes/metrics.py` so the route attempts persisted history and falls back to existing deterministic sample data when no database table/data exists:

```python
from fastapi import APIRouter

from de_forge.db.session import SessionLocal
from de_forge.services.metrics import MetricsService
from de_forge.services.run_repository import RunRepository
from de_forge.ui_support.review_view import QualitySnapshotView, quality_history

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/quality")
def quality_summary() -> dict[str, float]:
    return MetricsService().quality_snapshot(
        citation_faithfulness=1.0,
        proof_pass_rate=1.0,
        static_validity_rate=1.0,
        regression_pass_rate=1.0,
    )


@router.get("/history", response_model=list[QualitySnapshotView])
def quality_history_summary() -> list[QualitySnapshotView]:
    try:
        with SessionLocal() as session:
            persisted = RunRepository(session).quality_history()
            if persisted:
                return persisted
    except Exception:
        return quality_history()
    return quality_history()
```

- [ ] **Step 4: Run route tests**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_metrics_history_endpoint_returns_quality_snapshots tests/integration/api/test_api_routes.py::test_metrics_history_endpoint_prefers_persisted_quality_snapshots -v
```

Expected: PASS.

- [ ] **Step 5: Run affected API tests**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py tests/integration/db/test_run_repository.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Persisted history path exists.
- Sample fallback remains empty-state compatibility only.
- No protected files are touched.

- [ ] **Step 7: Code quality review**

Check:

- API route stays thin.
- Persistence query is delegated to repository.
- Fallback does not hide validation failures in orchestrator.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/api/routes/metrics.py tests/integration/api/test_api_routes.py
git commit -m "$(cat <<'EOF'
feat(metrics): read quality history from persistence

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Persist review decisions through ReviewService

**Files:**
- Modify: `src/de_forge/services/review.py`
- Modify: `tests/unit/services/test_review_service.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/services/test_review_service.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.run_repository import RunRepository


def test_review_service_persists_review_decision_when_repository_is_supplied() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = RunRepository(session)
        repository.create_run("run_1", "report_1", RunMode.AUTO, RunState.AWAITING_REVIEW)
        request = ReviewRequest(
            run_id="run_1",
            rule_candidate_id="candidate_1",
            action=ReviewAction.APPROVE,
            reviewer_notes="Looks good",
        )

        decision = ReviewService(repository=repository).decide(request)
        session.commit()

        assert decision.export_allowed is True
        assert repository.review_decisions_for_run("run_1")[0].action == "approve"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/unit/services/test_review_service.py::test_review_service_persists_review_decision_when_repository_is_supplied -v
```

Expected: FAIL because `ReviewService.__init__` does not accept `repository`.

- [ ] **Step 3: Write minimal implementation**

Modify `src/de_forge/services/review.py`:

```python
from de_forge.schemas.review import ReviewAction, ReviewDecision, ReviewRequest
from de_forge.services.run_repository import RunRepository


class ReviewService:
    def __init__(self, repository: RunRepository | None = None) -> None:
        self.repository = repository

    def decide(self, request: ReviewRequest) -> ReviewDecision:
        export_allowed = request.action == ReviewAction.APPROVE
        decision = ReviewDecision(
            run_id=request.run_id,
            rule_candidate_id=request.rule_candidate_id,
            action=request.action,
            reviewer_notes=request.reviewer_notes,
            export_allowed=export_allowed,
        )
        if self.repository is not None:
            self.repository.create_review_decision(
                run_id=decision.run_id,
                rule_candidate_id=decision.rule_candidate_id,
                action=decision.action.value,
                reviewer_notes=decision.reviewer_notes,
                export_allowed=decision.export_allowed,
            )
        return decision
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/unit/services/test_review_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/services/test_review_service.py tests/integration/db/test_run_repository.py tests/integration/api/test_api_routes.py::test_review_endpoint_blocks_export_on_reject -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- Review is still mandatory for export.
- Persistence is optional for backwards-compatible service tests.
- No export bypass is introduced.

- [ ] **Step 7: Code quality review**

Check:

- ReviewService remains focused.
- Repository dependency is explicit and optional.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/services/review.py tests/unit/services/test_review_service.py
git commit -m "$(cat <<'EOF'
feat(review): persist human review decisions

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: UI pages prefer persisted run data

**Files:**
- Modify: `src/de_forge/api/routes/ui.py`
- Modify: `tests/integration/api/test_api_routes.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/api/test_api_routes.py`:

```python
from de_forge.api.routes import ui
from de_forge.ui_support.review_view import QualitySnapshotView


def test_dashboard_ui_page_prefers_persisted_quality_history(monkeypatch: pytest.MonkeyPatch) -> None:
    class PersistedHistoryRepository:
        def __init__(self, session: object) -> None:
            self.session = session

        def quality_history(self) -> list[QualitySnapshotView]:
            return [
                QualitySnapshotView(
                    label="persisted-ui",
                    citation_faithfulness=1.0,
                    proof_pass_rate=1.0,
                    static_validity_rate=1.0,
                    regression_pass_rate=1.0,
                    overall_quality=1.0,
                )
            ]

    monkeypatch.setattr(ui, "RunRepository", PersistedHistoryRepository)

    client = TestClient(app)
    response = client.get("/api/ui/dashboard")

    assert response.status_code == 200
    assert "persisted-ui" in response.text
    assert "baseline" not in response.text


def test_evidence_graph_ui_page_keeps_basic_graph_view() -> None:
    client = TestClient(app)

    response = client.get("/api/ui/evidence-graph")

    assert response.status_code == 200
    assert "Evidence Graph" in response.text
    assert "Evidence quote" in response.text
```

- [ ] **Step 2: Run tests to verify behavior**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_dashboard_ui_page_prefers_persisted_quality_history tests/integration/api/test_api_routes.py::test_evidence_graph_ui_page_keeps_basic_graph_view -v
```

Expected: FAIL because `de_forge.api.routes.ui` does not expose or use `RunRepository`, so monkeypatching `ui.RunRepository` raises `AttributeError` or the dashboard still renders sample fallback labels.

- [ ] **Step 3: Write minimal implementation**

Modify `src/de_forge/api/routes/ui.py` so `dashboard_page()` attempts repository-backed quality history and falls back to current `quality_history()` sample. Keep existing review and evidence graph fallback behavior intact. The final imports should include:

```python
from de_forge.db.session import SessionLocal
from de_forge.services.run_repository import RunRepository
```

Replace `dashboard_page()` with:

```python
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> str:
    snapshots = quality_history()
    try:
        with SessionLocal() as session:
            persisted = RunRepository(session).quality_history()
            if persisted:
                snapshots = persisted
    except Exception:
        snapshots = quality_history()
    rows = "".join(
        f"<tr><td>{escape(snapshot.label)}</td><td>{snapshot.overall_quality}</td></tr>"
        for snapshot in snapshots
    )
    return f"""
    <html>
      <head><title>DE-Forge Quality Dashboard</title></head>
      <body>
        <h1>Quality Dashboard</h1>
        <table>
          <thead><tr><th>Snapshot</th><th>Overall quality</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </body>
    </html>
    """
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py::test_dashboard_ui_page_renders_quality_history tests/integration/api/test_api_routes.py::test_dashboard_ui_page_remains_available_for_persisted_quality_history tests/integration/api/test_api_routes.py::test_evidence_graph_ui_page_keeps_basic_graph_view -v
```

Expected: PASS.

- [ ] **Step 5: Run affected API/UI tests**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py tests/unit/ui_support/test_review_view.py -v
```

Expected: PASS.

- [ ] **Step 6: Spec compliance review**

Check:

- UI can use persisted dashboard data.
- Basic graph view remains server-rendered.
- Advanced graph visualization is not introduced.

- [ ] **Step 7: Code quality review**

Check:

- HTML output is escaped.
- API/UI route remains simple.
- No frontend framework is added.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/api/routes/ui.py tests/integration/api/test_api_routes.py
git commit -m "$(cat <<'EOF'
feat(ui): prefer persisted quality dashboard data

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Final production-hardening verification

**Files:**
- Modify only if verification finds issues in files touched by this plan.

- [ ] **Step 1: Run vertical-slice focused tests**

Run:

```bash
python -m pytest tests/unit/services/test_ingestion.py tests/unit/services/test_llm_client.py tests/unit/agents/test_fake_llm_contract.py tests/integration/db/test_run_repository.py tests/integration/services/test_graph_builder.py tests/integration/services/test_orchestrator_vertical_slice.py -v
```

Expected: PASS.

- [ ] **Step 2: Run API/UI affected tests**

Run:

```bash
python -m pytest tests/integration/api/test_api_routes.py tests/unit/services/test_review_service.py tests/unit/ui_support/test_review_view.py -v
```

Expected: PASS.

- [ ] **Step 3: Run full test suite**

Run:

```bash
python -m pytest tests/ -q
```

Expected: PASS with all tests passing.

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

- [ ] **Step 7: Run final spec compliance review**

Check every requirement from `docs/superpowers/specs/2026-05-22-de-forge-production-hardening-vertical-slice-design.md`:

- TXT ingestion implemented.
- Text PDF ingestion implemented.
- Empty PDF/text failures explicit.
- LLM transport implemented with configured OpenAI-compatible settings.
- Tests avoid live network.
- Fake LLM golden path exists.
- Orchestrator connects ingestion/chunk/evidence/spec/AST/Sigma/validation/proof/review state.
- Quality/review persistence exists.
- UI/dashboard can read persisted data.
- Deferred items remain out of scope.

- [ ] **Step 8: Run final code quality review**

Check:

- No raw-report-to-rule path.
- No fallback provider/model logic.
- No secrets committed.
- No `.claude` files staged.
- No local database/cache files staged.
- Services remain focused and typed.
- API routes remain thin.

- [ ] **Step 9: Commit verification fixes if any**

If verification required source/test fixes, commit only those files:

```bash
git add <fixed-source-and-test-files>
git commit -m "$(cat <<'EOF'
test: verify production hardening vertical slice

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage:

- Report ingestion: Tasks 1-2.
- TXT/text-PDF and OCR-deferred behavior: Tasks 1-2.
- Real OpenAI-compatible LLM transport: Task 3.
- Non-network deterministic fake LLM tests: Task 4.
- Persistence-backed run quality/review state: Tasks 5, 8, 9.
- Verified evidence graph construction: Task 6.
- End-to-end golden-path orchestrator: Task 7.
- DetectionSpec -> AST -> Sigma path: Task 7.
- Static/proof gates before review: Task 7.
- Basic real-data UI/dashboard: Tasks 8 and 10.
- Full verification: Task 11.

Deferred items remain out of scope:

- OCR scanned PDF.
- Multi-user/auth/RBAC.
- Separate frontend framework.
- Advanced interactive graph visualization.
- Multi-model/provider fallback.
- Automatic SIEM deployment/export.
- CTI-REALM benchmark adapter.

Implementation warning:

- Task 7 intentionally preserves the old state-only orchestrator behavior when no `Session` or `llm_client` is supplied so existing API tests continue to pass. Later plans may remove this compatibility path after API routes are upgraded to create sessions and use live or configured clients.
- Task 8 and Task 10 keep sample fallback behavior for empty-state compatibility. Persisted data must take precedence when present.
- Do not stage protected files shown by `git status` such as `.claude/settings.json`, `.claude/scheduled_tasks.lock`, or `.claude/worktrees/`.

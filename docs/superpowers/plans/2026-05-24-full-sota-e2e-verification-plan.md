# Full SOTA End-to-End Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the completed DE-Forge SOTA Core v2 production path end-to-end through HTTP/API and service-level regression tests.

**Architecture:** Add final verification tests after Phases 4–8 are implemented. The E2E suite should exercise TXT ingest, persisted evidence/retrieval lineage, DetectionSpec-gated AST/compiler rule generation, validation/proof persistence, human review, export, runtime APIs, health, and metrics. Adversarial tests must prove fail-closed behavior for missing or invalid state.

**Tech Stack:** Python 3.11, FastAPI TestClient, SQLAlchemy SQLite StaticPool, pytest, existing API routers and persistence services.

---

## File Structure

- Create `tests/integration/e2e/test_sota_pipeline_e2e.py`
  - Successful canonical SOTA flow.
  - Missing report and missing proof/evidence fail-closed flows.
  - Latest rejected review blocks export after prior approval.
- Create `tests/integration/e2e/test_sota_runtime_truth_e2e.py`
  - Runtime `/runs`, `/metrics`, `/dashboard`, and `/health` truthfulness after a completed run.
- Modify no production code unless E2E tests expose a regression from Phases 4–8.
- Verify docs preflight, schema/migration, core service suites, and API suites.

---

### Task 1: Add successful canonical SOTA HTTP E2E test

**Files:**
- Create: `tests/integration/e2e/test_sota_pipeline_e2e.py`

- [ ] **Step 1: Write successful E2E test**

Create `tests/integration/e2e/test_sota_pipeline_e2e.py` with:

```python
import json
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import DetectionSpec, ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()
    app = FastAPI()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(pipeline_router)
    return TestClient(app), db


def _persist_validated_spec(db: Session, report_id: str, evidence_id: str) -> str:
    spec_payload = {
        "report_id": report_id,
        "behavior_rules": [
            {
                "evidence": [evidence_id],
                "attack_ids": ["T1059.001"],
                "required_telemetry": ["process_creation"],
                "detection_logic": "CommandLine contains 'powershell'",
            }
        ],
        "false_positive_hypotheses": ["administrative scripts"],
        "test_plan": "validate against process creation logs",
        "evidence_ids": [evidence_id],
        "behavior_ids": ["behavior-1"],
        "detection_strategy": "detect encoded powershell",
        "analytic": "powershell command line analytic",
        "data_component": "process creation",
        "allowed_telemetry_fields": ["CommandLine", "Image"],
        "rationale_traceability": [evidence_id],
    }
    spec = DetectionSpec(
        id="spec-e2e",
        report_id=report_id,
        spec_payload=json.dumps(spec_payload),
        is_validated=True,
    )
    db.add(spec)
    db.commit()
    return spec.id


def test_successful_sota_pipeline_ingest_run_review_export() -> None:
    client, db = _build_client()

    ingest_response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "powershell encoded command",
            "external_ref": "e2e-report.txt",
            "metadata": {},
        },
    )
    assert ingest_response.status_code == 201
    report_id = ingest_response.json()["report_id"]
    chunk = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).one()

    RetrievalAuditService(db).record_retrieval(
        run_id="run-evidence-e2e",
        report_id=report_id,
        query_text="powershell encoded command",
        retrieval_mode="hybrid_rrf_stub",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id=chunk.id,
                text=chunk.chunk_text,
                score_sparse=1.0,
                score_dense=1.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-evidence-e2e",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-e2e",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )
    _persist_validated_spec(db, report_id, "evidence-e2e")

    run_response = client.post("/v1/pipeline:run", json={"report_id": report_id})
    assert run_response.status_code == 200
    run_body = run_response.json()
    assert run_body["status"] == "ok"
    assert run_body["stage"] == "awaiting_review"
    assert run_body["detection_spec_id"] == "spec-e2e"
    assert run_body["rule_id"]

    review_response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_body["run_id"],
            "decision": "approved",
            "reviewer": "analyst@example.com",
            "comments": "E2E approved.",
        },
    )
    assert review_response.status_code == 201

    export_response = client.post("/v1/exports/sigma", json={"run_id": run_body["run_id"]})
    assert export_response.status_code == 200
    export_body = export_response.json()
    assert export_body["rule_id"] == run_body["rule_id"]
    assert "CommandLine|contains" in export_body["content"]
    assert "powershell" in export_body["content"]
```

- [ ] **Step 2: Run successful E2E test**

Run after Phases 4–8 are implemented:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/e2e/test_sota_pipeline_e2e.py::test_successful_sota_pipeline_ingest_run_review_export -q
```

Expected: PASS. If it fails, fix only the phase regression exposed by the E2E test.

- [ ] **Step 3: Commit if fixes or test file added**

```bash
git add tests/integration/e2e/test_sota_pipeline_e2e.py <related fix files>
git commit -m "test(e2e): verify canonical sota pipeline

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Add fail-closed adversarial E2E tests

**Files:**
- Modify: `tests/integration/e2e/test_sota_pipeline_e2e.py`

- [ ] **Step 1: Add adversarial E2E tests**

Append to `tests/integration/e2e/test_sota_pipeline_e2e.py`:

```python
def test_pipeline_run_missing_report_fails_closed() -> None:
    client, _ = _build_client()

    response = client.post("/v1/pipeline:run", json={"report_id": "missing-report"})

    assert response.status_code == 404
    assert response.json()["status"] == "failed"
    assert "Report not found" in response.json()["message"]


def test_export_requires_latest_approved_review() -> None:
    client, db = _build_client()
    ingest_response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "powershell encoded command",
            "external_ref": "review-e2e-report.txt",
            "metadata": {},
        },
    )
    report_id = ingest_response.json()["report_id"]
    chunk = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).one()
    RetrievalAuditService(db).record_retrieval(
        run_id="run-review-evidence",
        report_id=report_id,
        query_text="powershell encoded command",
        retrieval_mode="hybrid_rrf_stub",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id=chunk.id,
                text=chunk.chunk_text,
                score_sparse=1.0,
                score_dense=1.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-review-evidence",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-review-e2e",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )
    _persist_validated_spec(db, report_id, "evidence-review-e2e")
    run_body = client.post("/v1/pipeline:run", json={"report_id": report_id}).json()

    approved = client.post(
        "/v1/reviews",
        json={
            "run_id": run_body["run_id"],
            "decision": "approved",
            "reviewer": "analyst@example.com",
            "comments": "Initial approval.",
        },
    )
    assert approved.status_code == 201

    rejected = client.post(
        "/v1/reviews",
        json={
            "run_id": run_body["run_id"],
            "decision": "rejected",
            "reviewer": "analyst@example.com",
            "comments": "Reject after review.",
        },
    )
    assert rejected.status_code == 201

    export_response = client.post("/v1/exports/sigma", json={"run_id": run_body["run_id"]})
    assert export_response.status_code == 403
    assert "latest review decision is not approved" in export_response.json()["detail"]


def test_pipeline_fails_closed_when_detection_spec_missing_after_evidence() -> None:
    client, db = _build_client()
    ingest_response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "powershell encoded command",
            "external_ref": "missing-spec-e2e-report.txt",
            "metadata": {},
        },
    )
    report_id = ingest_response.json()["report_id"]
    chunk = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).one()
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-missing-spec-evidence",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-missing-spec-e2e",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )

    response = client.post("/v1/pipeline:run", json={"report_id": report_id})

    assert response.status_code == 400
    assert response.json()["status"] == "failed"
    assert "validated DetectionSpec required" in response.json()["message"]
```

- [ ] **Step 2: Run adversarial E2E tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/e2e/test_sota_pipeline_e2e.py::test_pipeline_run_missing_report_fails_closed tests/integration/e2e/test_sota_pipeline_e2e.py::test_export_requires_latest_approved_review tests/integration/e2e/test_sota_pipeline_e2e.py::test_pipeline_fails_closed_when_detection_spec_missing_after_evidence -q
```

Expected: PASS. If failures expose a bypass, fix the production gate rather than weakening the test.

- [ ] **Step 3: Run full SOTA pipeline E2E file**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/e2e/test_sota_pipeline_e2e.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/e2e/test_sota_pipeline_e2e.py <related fix files>
git commit -m "test(e2e): verify sota fail-closed gates

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Add runtime truth E2E tests

**Files:**
- Create: `tests/integration/e2e/test_sota_runtime_truth_e2e.py`

- [ ] **Step 1: Write runtime truth E2E tests**

Create `tests/integration/e2e/test_sota_runtime_truth_e2e.py` with:

```python
from tests.integration.e2e.test_sota_pipeline_e2e import (
    _build_client,
    _persist_validated_spec,
)

from de_forge.models import ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService


def test_runtime_apis_reflect_completed_pipeline_state() -> None:
    client, db = _build_client()
    ingest_response = client.post(
        "/v1/reports:ingest",
        json={
            "source_type": "txt",
            "content": "powershell encoded command",
            "external_ref": "runtime-e2e-report.txt",
            "metadata": {},
        },
    )
    report_id = ingest_response.json()["report_id"]
    chunk = db.query(ReportChunk).filter(ReportChunk.report_id == report_id).one()
    RetrievalAuditService(db).record_retrieval(
        run_id="run-runtime-evidence",
        report_id=report_id,
        query_text="powershell encoded command",
        retrieval_mode="hybrid_rrf_stub",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id=chunk.id,
                text=chunk.chunk_text,
                score_sparse=1.0,
                score_dense=1.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-runtime-evidence",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-runtime-e2e",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )
    _persist_validated_spec(db, report_id, "evidence-runtime-e2e")

    run_body = client.post("/v1/pipeline:run", json={"report_id": report_id}).json()
    run_id = run_body["run_id"]

    runs = client.get("/api/runs").json()
    assert any(item["run_id"] == run_id for item in runs["items"])

    run_detail = client.get(f"/api/runs/{run_id}").json()
    assert run_detail["stage"] == "awaiting_review"
    assert run_detail["rule_id"] == run_body["rule_id"]

    validation = client.get(f"/api/runs/{run_id}/validation").json()
    assert validation["items"]
    assert validation["items"][0]["status"] == "passed"

    ops = client.get("/api/metrics/ops").json()
    assert ops["total_runs"] == 1
    assert ops["run_counts"] == {"ok": 1}

    quality = client.get("/api/metrics/quality").json()
    assert quality["overall_quality"] is not None

    dashboard = client.get("/api/dashboard/summary").json()
    assert dashboard["queue"]["total_runs"] == 1

    health = client.get("/health").json()
    assert "checks" in health
    assert "policy" in health
```

- [ ] **Step 2: Run runtime truth E2E test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/e2e/test_sota_runtime_truth_e2e.py -q
```

Expected: PASS. If `/api` route mounting differs in the active branch, adjust only the test route paths to match `src/de_forge/api/router.py` and `src/de_forge/main.py`.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/e2e/test_sota_runtime_truth_e2e.py <related fix files>
git commit -m "test(e2e): verify runtime truth surfaces

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Final full SOTA verification suite

**Files:**
- Verify only unless a regression fix is required.

- [ ] **Step 1: Run E2E suite**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/e2e -q
```

Expected: PASS.

- [ ] **Step 2: Run core integration service suites**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services -q -k "evidence or retrieval or validation or proof or orchestrator or review"
```

Expected: PASS.

- [ ] **Step 3: Run runtime API suites**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api -q
```

Expected: PASS.

- [ ] **Step 4: Run schema/migration contract suites**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Run unit tests for touched deterministic services**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/unit -q
```

Expected: PASS.

- [ ] **Step 6: Run docs preflight**

Run:

```bash
PYTHONPATH="$PWD/src" python scripts/docs_preflight.py
```

Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 7: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no whitespace errors in phase files. CRLF warnings for unrelated local Claude settings are not phase failures and must not be staged.

- [ ] **Step 8: Review final commit boundary**

Run:

```bash
git status --short
git diff --stat
git log --oneline -12
```

Expected: no uncommitted implementation changes except unrelated local artifacts. Do not stage or commit `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/scheduled_tasks.lock`, `de_forge.db`, `.env`, cache files, or unrelated docs.

- [ ] **Step 9: Commit only if final verification required a tracked fix**

If verification required a fix, commit only related files:

```bash
git add <related final verification files>
git commit -m "fix(e2e): complete sota verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:** Phase 9 covers successful canonical HTTP flow, fail-closed adversarial paths, runtime truth APIs, metrics/dashboard/health truthfulness, and final full regression commands.

**Placeholder scan:** No TODO/TBD/placeholders remain. Each test includes concrete code and exact commands.

**Type consistency:** Test helpers use the same persisted models and API routes introduced or hardened in Phases 4–8. E2E tests depend on `RetrievalAuditService`, `ValidationProofPersistenceService` through orchestration, and DB-backed `/api` runtime routes.

**Scope control:** This phase does not introduce new product features, providers, deployment automation, or PR creation. It only verifies the implemented SOTA path and fixes regressions discovered by verification.

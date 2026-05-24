# Runtime API Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove misleading placeholder production state from runtime APIs and ensure run/spec/portfolio/validation endpoints are DB-derived or explicitly marked non-authoritative.

**Architecture:** Introduce a small `RunStateService` that reads persisted `PipelineRunRecord`, `DetectionSpec`, `GeneratedRule`, `ValidationResult`, and `ProofObligationRecord` rows. Replace hardcoded `/runs/*` responses with service-backed responses, while leaving HTML UI shells static but adding visible non-authoritative labels until they are wired to live data.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy ORM, Pydantic-compatible dict responses, pytest, SQLite integration tests.

---

## File Structure

- Create `src/de_forge/services/run_state.py`
  - DB-backed run listing/detail/spec/portfolio/validation methods.
- Modify `src/de_forge/api/routes/runs.py`
  - Add DB session dependency.
  - Replace placeholder responses for list/detail/spec/portfolio/validation.
  - Use Phase 4 `RetrievalAuditService.get_run_evidence_lineage()` for evidence route if not already changed.
- Create `tests/integration/api/test_runtime_runs_api.py`
  - Verify endpoints return empty/not-found instead of placeholders.
  - Verify populated DB state drives responses.
- Modify `src/de_forge/api/routes/ui.py`
  - Add visible non-authoritative labels to static HTML shells so they cannot be mistaken for production state.
- Create `tests/unit/api/test_ui_non_authoritative.py`
  - Verify UI pages include non-authoritative/static-shell labeling.
- Verify pipeline/review/export API regressions.

---

### Task 1: Add DB-backed run state service

**Files:**
- Create: `src/de_forge/services/run_state.py`
- Create: `tests/integration/services/test_run_state.py`

- [ ] **Step 1: Write failing run state service tests**

Create `tests/integration/services/test_run_state.py` with:

```python
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    ProofObligationRecord,
    Report,
    ValidationResult,
)
from de_forge.services.run_state import RunStateService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_run(db: Session) -> None:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    db.add(
        Report(
            id="report-1",
            source_type="txt",
            source_uri="report.txt",
            title="report.txt",
            raw_text="powershell behavior",
            content_hash="hash-1",
            metadata_json="{}",
            status="ingested",
            created_at=created_at,
            updated_at=created_at,
        )
    )
    db.add(
        DetectionSpec(
            id="spec-1",
            report_id="report-1",
            spec_payload='{"telemetry": "process_creation"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRule(
            id="rule-1",
            detection_spec_id="spec-1",
            query_candidate_id=None,
            rule_content="title: persisted rule",
        )
    )
    db.add(
        PipelineRunRecord(
            id="pipeline-1",
            run_id="run-1",
            report_id="report-1",
            status="ok",
            stage="awaiting_review",
            detection_spec_id="spec-1",
            rule_id="rule-1",
            created_at=created_at,
        )
    )
    db.add(
        ValidationResult(
            id="validation-1",
            rule_id="rule-1",
            run_id="run-1",
            status="passed",
            details_json='{"validation_type":"static"}',
            created_at=created_at,
        )
    )
    db.add(
        ProofObligationRecord(
            id="proof-1",
            run_id="run-1",
            rule_candidate_id="rule-1",
            claim_type="citation_faithful",
            claim_text="Citations are faithful.",
            required_artifact_types='["static_validation"]',
            status="proven",
            justification="derived",
        )
    )
    db.commit()


def test_list_runs_returns_persisted_runs_not_placeholders() -> None:
    db = _build_session()
    service = RunStateService(db)
    assert service.list_runs() == {"items": []}

    _seed_run(db)

    assert service.list_runs() == {
        "items": [
            {
                "run_id": "run-1",
                "report_id": "report-1",
                "status": "ok",
                "stage": "awaiting_review",
                "detection_spec_id": "spec-1",
                "rule_id": "rule-1",
                "created_at": db.get(PipelineRunRecord, "pipeline-1").created_at,
            }
        ]
    }


def test_run_detail_returns_none_for_missing_and_persisted_detail_for_existing() -> None:
    db = _build_session()
    service = RunStateService(db)
    assert service.get_run_detail("missing") is None

    _seed_run(db)

    assert service.get_run_detail("run-1") == {
        "run_id": "run-1",
        "report_id": "report-1",
        "status": "ok",
        "stage": "awaiting_review",
        "detection_spec_id": "spec-1",
        "rule_id": "rule-1",
        "created_at": db.get(PipelineRunRecord, "pipeline-1").created_at,
    }


def test_run_spec_portfolio_and_validation_are_db_backed() -> None:
    db = _build_session()
    _seed_run(db)
    service = RunStateService(db)

    assert service.get_run_spec("run-1") == {
        "run_id": "run-1",
        "detection_spec_id": "spec-1",
        "is_validated": True,
        "abstain_code": None,
        "spec_payload": {"telemetry": "process_creation"},
    }
    assert service.get_run_portfolio("run-1") == {
        "run_id": "run-1",
        "items": [
            {
                "rule_id": "rule-1",
                "detection_spec_id": "spec-1",
                "proof_status": "proven",
            }
        ],
    }
    assert service.get_run_validation("run-1") == {
        "run_id": "run-1",
        "items": [
            {
                "validation_id": "validation-1",
                "rule_id": "rule-1",
                "status": "passed",
                "details": {"validation_type": "static"},
            }
        ],
    }
```

- [ ] **Step 2: Run failing service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_run_state.py -q
```

Expected: FAIL because `de_forge.services.run_state` does not exist.

- [ ] **Step 3: Implement run state service**

Create `src/de_forge/services/run_state.py` with:

```python
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    ProofObligationRecord,
    ValidationResult,
)


class RunStateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_runs(self) -> dict[str, list[dict[str, object]]]:
        rows = (
            self.db.execute(select(PipelineRunRecord).order_by(PipelineRunRecord.created_at))
            .scalars()
            .all()
        )
        return {"items": [self._run_record_payload(row) for row in rows]}

    def get_run_detail(self, run_id: str) -> dict[str, object] | None:
        record = self._get_run(run_id)
        if record is None:
            return None
        return self._run_record_payload(record)

    def get_run_spec(self, run_id: str) -> dict[str, object] | None:
        record = self._get_run(run_id)
        if record is None or record.detection_spec_id is None:
            return None
        spec = self.db.get(DetectionSpec, record.detection_spec_id)
        if spec is None:
            return None
        return {
            "run_id": run_id,
            "detection_spec_id": spec.id,
            "is_validated": spec.is_validated,
            "abstain_code": spec.abstain_code,
            "spec_payload": self._parse_json(spec.spec_payload),
        }

    def get_run_portfolio(self, run_id: str) -> dict[str, object] | None:
        record = self._get_run(run_id)
        if record is None or record.rule_id is None:
            return None
        rule = self.db.get(GeneratedRule, record.rule_id)
        if rule is None:
            return None
        obligations = (
            self.db.execute(
                select(ProofObligationRecord)
                .where(ProofObligationRecord.run_id == run_id)
                .where(ProofObligationRecord.rule_candidate_id == rule.id)
            )
            .scalars()
            .all()
        )
        statuses = {obligation.status for obligation in obligations}
        proof_status = "missing"
        if statuses == {"proven"}:
            proof_status = "proven"
        elif statuses:
            proof_status = "blocked"
        return {
            "run_id": run_id,
            "items": [
                {
                    "rule_id": rule.id,
                    "detection_spec_id": rule.detection_spec_id,
                    "proof_status": proof_status,
                }
            ],
        }

    def get_run_validation(self, run_id: str) -> dict[str, object] | None:
        record = self._get_run(run_id)
        if record is None:
            return None
        rows = (
            self.db.execute(
                select(ValidationResult)
                .where(ValidationResult.run_id == run_id)
                .order_by(ValidationResult.id)
            )
            .scalars()
            .all()
        )
        return {
            "run_id": run_id,
            "items": [
                {
                    "validation_id": row.id,
                    "rule_id": row.rule_id,
                    "status": row.status,
                    "details": self._parse_json(row.details_json),
                }
                for row in rows
            ],
        }

    def _get_run(self, run_id: str) -> PipelineRunRecord | None:
        return self.db.execute(
            select(PipelineRunRecord).where(PipelineRunRecord.run_id == run_id)
        ).scalar_one_or_none()

    def _run_record_payload(self, record: PipelineRunRecord) -> dict[str, object]:
        return {
            "run_id": record.run_id,
            "report_id": record.report_id,
            "status": record.status,
            "stage": record.stage,
            "detection_spec_id": record.detection_spec_id,
            "rule_id": record.rule_id,
            "created_at": record.created_at,
        }

    def _parse_json(self, value: str | None) -> Any:
        if value is None:
            return None
        return json.loads(value)
```

- [ ] **Step 4: Run service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_run_state.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/run_state.py tests/integration/services/test_run_state.py
git commit -m "feat(api): add db-backed run state service

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Replace hardcoded `/runs` endpoints with DB-backed responses

**Files:**
- Modify: `src/de_forge/api/routes/runs.py`
- Create: `tests/integration/api/test_runtime_runs_api.py`

- [ ] **Step 1: Write failing runtime runs API tests**

Create `tests/integration/api/test_runtime_runs_api.py` with:

```python
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.dependencies import get_db
from de_forge.api.routes.runs import router as runs_router
from de_forge.db.base import Base
from de_forge.models import DetectionSpec, GeneratedRule, PipelineRunRecord, Report, ValidationResult


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
    app.include_router(runs_router)
    return TestClient(app), db


def _seed_run(db: Session) -> None:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    db.add(
        Report(
            id="report-api",
            source_type="txt",
            source_uri="report.txt",
            title="report.txt",
            raw_text="api behavior",
            content_hash="hash-api",
            metadata_json="{}",
            status="ingested",
            created_at=created_at,
            updated_at=created_at,
        )
    )
    db.add(
        DetectionSpec(
            id="spec-api",
            report_id="report-api",
            spec_payload='{"telemetry":"process_creation"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRule(
            id="rule-api",
            detection_spec_id="spec-api",
            query_candidate_id=None,
            rule_content="title: api rule",
        )
    )
    db.add(
        PipelineRunRecord(
            id="pipeline-api",
            run_id="run-api",
            report_id="report-api",
            status="ok",
            stage="awaiting_review",
            detection_spec_id="spec-api",
            rule_id="rule-api",
            created_at=created_at,
        )
    )
    db.add(
        ValidationResult(
            id="validation-api",
            rule_id="rule-api",
            run_id="run-api",
            status="passed",
            details_json='{"validation_type":"static"}',
            created_at=created_at,
        )
    )
    db.commit()


def test_runs_endpoints_return_empty_or_404_instead_of_placeholders() -> None:
    client, _ = _build_client()

    assert client.get("/runs").json() == {"items": []}
    assert client.get("/runs/missing").status_code == 404
    assert client.get("/runs/missing/spec").status_code == 404
    assert client.get("/runs/missing/portfolio").status_code == 404
    assert client.get("/runs/missing/validation").status_code == 404


def test_runs_endpoints_return_persisted_state() -> None:
    client, db = _build_client()
    _seed_run(db)

    listed = client.get("/runs")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["run_id"] == "run-api"
    assert listed.json()["items"][0]["stage"] == "awaiting_review"

    detail = client.get("/runs/run-api")
    assert detail.status_code == 200
    assert detail.json()["rule_id"] == "rule-api"

    spec = client.get("/runs/run-api/spec")
    assert spec.status_code == 200
    assert spec.json()["detection_spec_id"] == "spec-api"
    assert spec.json()["spec_payload"] == {"telemetry": "process_creation"}

    validation = client.get("/runs/run-api/validation")
    assert validation.status_code == 200
    assert validation.json()["items"] == [
        {
            "validation_id": "validation-api",
            "rule_id": "rule-api",
            "status": "passed",
            "details": {"validation_type": "static"},
        }
    ]
```

- [ ] **Step 2: Run failing API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_runtime_runs_api.py -q
```

Expected: FAIL because `/runs` endpoints return hardcoded placeholder payloads.

- [ ] **Step 3: Replace route implementations**

Update imports in `src/de_forge/api/routes/runs.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from de_forge.api.dependencies import get_db
from de_forge.services.retrieval_audit import RetrievalAuditService
from de_forge.services.run_state import RunStateService
```

Replace route functions with:

```python
@router.get("")
def list_runs(db: Session = Depends(get_db)) -> dict[str, list[dict[str, object]]]:
    return RunStateService(db).list_runs()


@router.get("/{run_id}")
def run_detail(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    detail = RunStateService(db).get_run_detail(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return detail


@router.get("/{run_id}/evidence")
def run_evidence(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return RetrievalAuditService(db).get_run_evidence_lineage(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{run_id}/spec")
def run_spec(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    spec = RunStateService(db).get_run_spec(run_id)
    if spec is None:
        raise HTTPException(status_code=404, detail="Run spec not found")
    return spec


@router.get("/{run_id}/portfolio")
def run_portfolio(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    portfolio = RunStateService(db).get_run_portfolio(run_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Run portfolio not found")
    return portfolio


@router.get("/{run_id}/validation")
def run_validation(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    validation = RunStateService(db).get_run_validation(run_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="Run validation not found")
    return validation
```

Keep `/runs/golden` unchanged in this task.

- [ ] **Step 4: Run API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_runtime_runs_api.py -q
```

Expected: PASS.

- [ ] **Step 5: Run affected runtime API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_run_state.py tests/integration/api/test_runtime_runs_api.py tests/integration/api/test_runs_lineage.py -q
```

Expected: PASS. If `test_runs_lineage.py` does not exist yet because Phase 4 is not implemented in this worktree, run only the existing files and record that Phase 4 will add the lineage test.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/api/routes/runs.py tests/integration/api/test_runtime_runs_api.py
git commit -m "fix(api): replace run placeholders with persisted state

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Label static UI shells as non-authoritative

**Files:**
- Modify: `src/de_forge/api/routes/ui.py`
- Create: `tests/unit/api/test_ui_non_authoritative.py`

- [ ] **Step 1: Write failing UI labeling tests**

Create `tests/unit/api/test_ui_non_authoritative.py` with:

```python
from de_forge.api.routes.ui import dashboard_page, evidence_spec_page, portfolio_review_page, review_page


def test_static_ui_pages_are_labeled_non_authoritative() -> None:
    pages = [
        review_page(),
        evidence_spec_page("run-1"),
        portfolio_review_page("run-1"),
        dashboard_page(),
    ]

    for page in pages:
        assert "Non-authoritative static UI shell" in page
        assert "Use API responses for production state" in page
```

- [ ] **Step 2: Run failing UI test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/unit/api/test_ui_non_authoritative.py -q
```

Expected: FAIL because UI shells do not include non-authoritative labeling.

- [ ] **Step 3: Add label to UI shell wrapper**

Modify `_page()` in `src/de_forge/api/routes/ui.py`:

```python
def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html>
  <head><meta charset="utf-8"><title>{title}</title></head>
  <body>
    <h1>DE-Forge UI</h1>
    <aside><strong>Non-authoritative static UI shell.</strong> Use API responses for production state.</aside>
    {body}
  </body>
</html>"""
```

- [ ] **Step 4: Run UI test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/unit/api/test_ui_non_authoritative.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/api/routes/ui.py tests/unit/api/test_ui_non_authoritative.py
git commit -m "fix(ui): label static pages as non-authoritative

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Phase verification and audit

**Files:**
- Verify only unless a regression fix is required.

- [ ] **Step 1: Run runtime API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_run_state.py tests/integration/api/test_runtime_runs_api.py tests/unit/api/test_ui_non_authoritative.py -q
```

Expected: PASS.

- [ ] **Step 2: Run pipeline/review/export regressions**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api -q -k "pipeline or runs or review or export"
```

Expected: PASS or only unrelated failures with documented evidence.

- [ ] **Step 3: Run service regressions for run lineage and proof gates**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services -q -k "run_state or retrieval_audit or validation_proof or review_gate"
```

Expected: PASS or only missing-test selections for phases not yet implemented in the active branch.

- [ ] **Step 4: Run schema/migration regressions**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Run docs preflight**

Run:

```bash
PYTHONPATH="$PWD/src" python scripts/docs_preflight.py
```

Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 6: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no whitespace errors in phase files. CRLF warnings for unrelated local Claude settings are not phase failures and must not be staged.

- [ ] **Step 7: Review commit boundary**

Run:

```bash
git status --short
git diff --stat
```

Expected: no uncommitted Phase 7 changes. Do not stage or commit `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/scheduled_tasks.lock`, `de_forge.db`, `.env`, cache files, or unrelated docs.

- [ ] **Step 8: Commit only if verification required a tracked fix**

If verification required a fix, commit only related Phase 7 files:

```bash
git add <related phase 7 files>
git commit -m "fix(api): complete runtime hardening verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:** Phase 7 requirements are covered: hardcoded `/runs` placeholders are replaced by DB-derived state, missing runs return not-found/empty responses, validation/spec/portfolio are persisted-state driven, and static UI shells are explicitly non-authoritative.

**Placeholder scan:** No TODO/TBD/placeholders remain. Dashboard and metrics hardcoding are intentionally deferred to Phase 8 where DB-derived health/metrics are handled together.

**Type consistency:** `RunStateService` returns JSON-compatible dictionaries used directly by FastAPI routes. Route responses match test expectations and persisted model fields.

**Scope control:** This phase does not implement metrics truthfulness, dashboard DB summaries, authentication, frontend redesign, or orchestration repairs. Those are handled in adjacent phase plans.

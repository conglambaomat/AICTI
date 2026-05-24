# Health Metrics Truthfulness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make health, metrics, and dashboard summaries report database-derived runtime truth instead of optimistic constants or hardcoded production state.

**Architecture:** Extend `MetricsService` to accept a SQLAlchemy session and compute quality/ops/dashboard summaries from persisted records. Update metric/dashboard routes to inject the DB session. Simplify health output so measured checks are separated from static policy declarations and no measured runtime field is hardcoded as healthy when the DB/schema check fails.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy ORM, existing persistence models, pytest, SQLite integration/API tests.

---

## File Structure

- Modify `src/de_forge/services/metrics.py`
  - Add DB-derived `quality_summary()`, `ops_summary()`, and `dashboard_summary()` methods.
  - Keep pure `quality_snapshot(...)` helper if existing tests depend on it.
- Modify `src/de_forge/api/routes/metrics.py`
  - Inject DB session and return service-derived values.
- Modify `src/de_forge/api/routes/dashboard.py`
  - Inject DB session and return service-derived dashboard summary.
- Modify `src/de_forge/main.py`
  - Separate measured health checks from static policy declarations.
  - Remove long hardcoded invariant mirror from measured health checks.
- Create `tests/integration/services/test_metrics_truthfulness.py`
  - Cover empty and populated DB metrics.
- Create `tests/integration/api/test_metrics_dashboard_truthfulness.py`
  - Cover route-level DB-derived metrics/dashboard.
- Modify or create `tests/integration/api/test_health_truthfulness.py`
  - Cover health measured/static separation.

---

### Task 1: Add DB-derived metrics service summaries

**Files:**
- Modify: `src/de_forge/services/metrics.py`
- Create: `tests/integration/services/test_metrics_truthfulness.py`

- [ ] **Step 1: Write failing metrics service tests**

Create `tests/integration/services/test_metrics_truthfulness.py` with:

```python
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import (
    PipelineRunRecord,
    ProofObligationRecord,
    RegressionRun,
    Report,
    ReviewDecision,
    ValidationResult,
)
from de_forge.services.metrics import MetricsService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_metrics(db: Session) -> None:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    db.add(
        Report(
            id="report-1",
            source_type="txt",
            source_uri="report.txt",
            title="report.txt",
            raw_text="behavior",
            content_hash="hash-1",
            metadata_json="{}",
            status="ingested",
            created_at=created_at,
            updated_at=created_at,
        )
    )
    db.add_all(
        [
            PipelineRunRecord(
                id="pipeline-1",
                run_id="run-ok",
                report_id="report-1",
                status="ok",
                stage="awaiting_review",
                detection_spec_id="spec-1",
                rule_id="rule-1",
                created_at=created_at,
            ),
            PipelineRunRecord(
                id="pipeline-2",
                run_id="run-failed",
                report_id="report-1",
                status="failed",
                stage="static_validation_failed",
                detection_spec_id="spec-2",
                rule_id="rule-2",
                created_at=created_at,
            ),
        ]
    )
    db.add_all(
        [
            ValidationResult(
                id="validation-1",
                rule_id="rule-1",
                run_id="run-ok",
                status="passed",
                details_json="{}",
                created_at=created_at,
            ),
            ValidationResult(
                id="validation-2",
                rule_id="rule-2",
                run_id="run-failed",
                status="failed",
                details_json="{}",
                created_at=created_at,
            ),
        ]
    )
    db.add_all(
        [
            ProofObligationRecord(
                id="proof-1",
                run_id="run-ok",
                rule_candidate_id="rule-1",
                claim_type="citation_faithful",
                claim_text="Citations are faithful.",
                required_artifact_types='["static_validation"]',
                status="proven",
                justification="derived",
            ),
            ProofObligationRecord(
                id="proof-2",
                run_id="run-failed",
                rule_candidate_id="rule-2",
                claim_type="not_overbroad",
                claim_text="Rule is not overbroad.",
                required_artifact_types='["static_validation"]',
                status="unknown",
                justification=None,
            ),
        ]
    )
    db.add(
        RegressionRun(
            id="regression-1",
            rule_id="rule-1",
            run_id="run-ok",
            status="passed",
            result_json="{}",
            created_at=created_at,
        )
    )
    db.add(
        ReviewDecision(
            id="review-1",
            rule_id="rule-1",
            run_id="run-ok",
            decision="approved",
            reviewer="analyst@example.com",
            comments="approved",
            created_at=created_at,
        )
    )
    db.commit()


def test_quality_summary_returns_no_data_for_empty_database() -> None:
    db = _build_session()

    assert MetricsService(db).quality_summary() == {
        "citation_faithfulness": None,
        "proof_pass_rate": None,
        "static_validity_rate": None,
        "regression_pass_rate": None,
        "overall_quality": None,
        "sample_counts": {
            "proof_obligations": 0,
            "static_validations": 0,
            "regression_runs": 0,
        },
    }


def test_quality_summary_is_derived_from_persisted_records() -> None:
    db = _build_session()
    _seed_metrics(db)

    assert MetricsService(db).quality_summary() == {
        "citation_faithfulness": 0.5,
        "proof_pass_rate": 0.5,
        "static_validity_rate": 0.5,
        "regression_pass_rate": 1.0,
        "overall_quality": 0.625,
        "sample_counts": {
            "proof_obligations": 2,
            "static_validations": 2,
            "regression_runs": 1,
        },
    }


def test_ops_summary_is_derived_from_pipeline_runs() -> None:
    db = _build_session()
    assert MetricsService(db).ops_summary() == {
        "queue_depth": 0,
        "run_success_rate": None,
        "run_counts": {},
        "total_runs": 0,
    }

    _seed_metrics(db)

    assert MetricsService(db).ops_summary() == {
        "queue_depth": 1,
        "run_success_rate": 0.5,
        "run_counts": {"failed": 1, "ok": 1},
        "total_runs": 2,
    }
```

- [ ] **Step 2: Run failing metrics service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_metrics_truthfulness.py -q
```

Expected: FAIL because `MetricsService` has no DB-backed `quality_summary()` or `ops_summary()`.

- [ ] **Step 3: Implement DB-derived metrics service methods**

Replace `src/de_forge/services/metrics.py` with:

```python
from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import PipelineRunRecord, ProofObligationRecord, RegressionRun, ValidationResult


class MetricsService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def quality_snapshot(
        self,
        citation_faithfulness: float,
        proof_pass_rate: float,
        static_validity_rate: float,
        regression_pass_rate: float,
    ) -> dict[str, float]:
        values = [
            citation_faithfulness,
            proof_pass_rate,
            static_validity_rate,
            regression_pass_rate,
        ]
        return {
            "citation_faithfulness": citation_faithfulness,
            "proof_pass_rate": proof_pass_rate,
            "static_validity_rate": static_validity_rate,
            "regression_pass_rate": regression_pass_rate,
            "overall_quality": round(sum(values) / len(values), 4),
        }

    def quality_summary(self) -> dict[str, Any]:
        if self.db is None:
            raise ValueError("database session required")

        proof_rows = self.db.execute(select(ProofObligationRecord)).scalars().all()
        validation_rows = self.db.execute(select(ValidationResult)).scalars().all()
        regression_rows = self.db.execute(select(RegressionRun)).scalars().all()

        citation_rows = [row for row in proof_rows if row.claim_type == "citation_faithful"]
        citation_faithfulness = self._rate(citation_rows, "proven")
        proof_pass_rate = self._rate(proof_rows, "proven")
        static_validity_rate = self._rate(validation_rows, "passed")
        regression_pass_rate = self._rate(regression_rows, "passed")
        available_values = [
            value
            for value in [
                citation_faithfulness,
                proof_pass_rate,
                static_validity_rate,
                regression_pass_rate,
            ]
            if value is not None
        ]
        return {
            "citation_faithfulness": citation_faithfulness,
            "proof_pass_rate": proof_pass_rate,
            "static_validity_rate": static_validity_rate,
            "regression_pass_rate": regression_pass_rate,
            "overall_quality": round(sum(available_values) / len(available_values), 4)
            if available_values
            else None,
            "sample_counts": {
                "proof_obligations": len(proof_rows),
                "static_validations": len(validation_rows),
                "regression_runs": len(regression_rows),
            },
        }

    def ops_summary(self) -> dict[str, Any]:
        if self.db is None:
            raise ValueError("database session required")
        runs = self.db.execute(select(PipelineRunRecord)).scalars().all()
        counts = Counter(run.status for run in runs)
        terminal = [run for run in runs if run.status in {"ok", "failed", "abstain"}]
        success_count = sum(1 for run in terminal if run.status == "ok")
        return {
            "queue_depth": sum(1 for run in runs if run.status not in {"ok", "failed", "abstain"}),
            "run_success_rate": round(success_count / len(terminal), 4) if terminal else None,
            "run_counts": dict(sorted(counts.items())),
            "total_runs": len(runs),
        }

    def dashboard_summary(self) -> dict[str, Any]:
        return {
            "queue": self.ops_summary(),
            "quality": self.quality_summary(),
        }

    def _rate(self, rows: list[object], passing_status: str) -> float | None:
        if not rows:
            return None
        passed = sum(1 for row in rows if getattr(row, "status") == passing_status)
        return round(passed / len(rows), 4)
```

- [ ] **Step 4: Run metrics service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_metrics_truthfulness.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/metrics.py tests/integration/services/test_metrics_truthfulness.py
git commit -m "fix(metrics): derive quality and ops from database

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Wire metrics and dashboard routes to DB-derived summaries

**Files:**
- Modify: `src/de_forge/api/routes/metrics.py`
- Modify: `src/de_forge/api/routes/dashboard.py`
- Create: `tests/integration/api/test_metrics_dashboard_truthfulness.py`

- [ ] **Step 1: Write failing route tests**

Create `tests/integration/api/test_metrics_dashboard_truthfulness.py` with:

```python
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.dashboard import router as dashboard_router
from de_forge.api.routes.metrics import router as metrics_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import PipelineRunRecord, Report


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
    app.include_router(metrics_router)
    app.include_router(dashboard_router)
    return TestClient(app), db


def _seed_run(db: Session) -> None:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    db.add(
        Report(
            id="report-1",
            source_type="txt",
            source_uri="report.txt",
            title="report.txt",
            raw_text="behavior",
            content_hash="hash-1",
            metadata_json="{}",
            status="ingested",
            created_at=created_at,
            updated_at=created_at,
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
    db.commit()


def test_metrics_routes_return_empty_truth_not_optimistic_constants() -> None:
    client, _ = _build_client()

    assert client.get("/metrics/quality").json() == {
        "citation_faithfulness": None,
        "proof_pass_rate": None,
        "static_validity_rate": None,
        "regression_pass_rate": None,
        "overall_quality": None,
        "sample_counts": {
            "proof_obligations": 0,
            "static_validations": 0,
            "regression_runs": 0,
        },
    }
    assert client.get("/metrics/ops").json() == {
        "queue_depth": 0,
        "run_success_rate": None,
        "run_counts": {},
        "total_runs": 0,
    }


def test_metrics_and_dashboard_routes_use_persisted_runs() -> None:
    client, db = _build_client()
    _seed_run(db)

    assert client.get("/metrics/ops").json() == {
        "queue_depth": 0,
        "run_success_rate": 1.0,
        "run_counts": {"ok": 1},
        "total_runs": 1,
    }
    dashboard = client.get("/dashboard/summary").json()
    assert dashboard["queue"]["total_runs"] == 1
    assert dashboard["queue"]["run_counts"] == {"ok": 1}
    assert dashboard["quality"]["overall_quality"] is None
```

- [ ] **Step 2: Run failing route tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_metrics_dashboard_truthfulness.py -q
```

Expected: FAIL because routes still return constants.

- [ ] **Step 3: Wire metrics route to DB session**

Replace `src/de_forge/api/routes/metrics.py` with:

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/quality")
def quality_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return MetricsService(db).quality_summary()


@router.get("/ops")
def ops_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return MetricsService(db).ops_summary()
```

- [ ] **Step 4: Wire dashboard route to DB session**

Replace `src/de_forge/api/routes/dashboard.py` with:

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.services.metrics import MetricsService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return MetricsService(db).dashboard_summary()
```

- [ ] **Step 5: Run route tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_metrics_dashboard_truthfulness.py -q
```

Expected: PASS.

- [ ] **Step 6: Run metrics service and route tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_metrics_truthfulness.py tests/integration/api/test_metrics_dashboard_truthfulness.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/api/routes/metrics.py src/de_forge/api/routes/dashboard.py tests/integration/api/test_metrics_dashboard_truthfulness.py
git commit -m "fix(api): serve truthful metrics summaries

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Separate measured health checks from static policy declarations

**Files:**
- Modify: `src/de_forge/main.py`
- Create: `tests/integration/api/test_health_truthfulness.py`

- [ ] **Step 1: Write failing health truthfulness test**

Create `tests/integration/api/test_health_truthfulness.py` with:

```python
from fastapi.testclient import TestClient

from de_forge.main import app


def test_health_separates_measured_checks_from_policy_declarations() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert "checks" in body
    assert "policy" in body
    assert "details" in body
    assert "policy" not in body["details"]
    assert set(body["checks"]).issuperset({"api", "database", "schema"})
    assert body["policy"] == {
        "human_review_required_for_export": True,
        "detection_spec_required": True,
        "proof_obligation_required": True,
        "citation_exact_required": True,
        "raw_report_to_rule_forbidden": True,
        "agent_loops_bounded": True,
    }
```

- [ ] **Step 2: Run failing health test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_health_truthfulness.py -q
```

Expected: FAIL because health currently nests a very large hardcoded policy map under `details.policy`.

- [ ] **Step 3: Simplify health response**

In `src/de_forge/main.py`, replace the `details` and policy portion of the health return with this top-level structure:

```python
        "checks": {
            "api": "ok",
            "database": database_check,
            "schema": schema_check,
        },
        "errors": errors,
        "run_id": run_id,
        "trace_id": trace_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "uptime_seconds": int(monotonic() - _started_at),
        "policy": {
            "human_review_required_for_export": True,
            "detection_spec_required": True,
            "proof_obligation_required": True,
            "citation_exact_required": True,
            "raw_report_to_rule_forbidden": True,
            "agent_loops_bounded": True,
        },
        "details": {
            "db_probe": "select_1" if database_check == "ok" else None,
            "schema_guard": "current" if schema_check == "ok" else "drift_or_unavailable",
        },
```

Keep status/readiness/ready/ok behavior unchanged.

- [ ] **Step 4: Run health test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_health_truthfulness.py -q
```

Expected: PASS.

- [ ] **Step 5: Run existing health/API regressions**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api -q -k "health or metrics or dashboard"
```

Expected: PASS or only unrelated failures with documented evidence.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/main.py tests/integration/api/test_health_truthfulness.py
git commit -m "fix(health): separate measured checks from policy

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Phase verification and audit

**Files:**
- Verify only unless a regression fix is required.

- [ ] **Step 1: Run health/metrics tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_metrics_truthfulness.py tests/integration/api/test_metrics_dashboard_truthfulness.py tests/integration/api/test_health_truthfulness.py -q
```

Expected: PASS.

- [ ] **Step 2: Run runtime API regression selection**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api -q -k "health or metrics or dashboard or runs or pipeline"
```

Expected: PASS or only unrelated failures with documented evidence.

- [ ] **Step 3: Run service regression selection**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services -q -k "metrics or run_state or validation_proof or retrieval_audit"
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

Expected: no uncommitted Phase 8 changes. Do not stage or commit `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/scheduled_tasks.lock`, `de_forge.db`, `.env`, cache files, or unrelated docs.

- [ ] **Step 8: Commit only if verification required a tracked fix**

If verification required a fix, commit only related Phase 8 files:

```bash
git add <related phase 8 files>
git commit -m "fix(metrics): complete truthfulness verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:** Phase 8 requirements are covered: metrics are DB-derived, empty datasets return no-data values, dashboard summary is derived from metrics, health separates measured checks from static policy, and schema/database failures remain degraded/not-ready.

**Placeholder scan:** No TODO/TBD/placeholders remain. All code-changing steps include exact code and commands.

**Type consistency:** Metrics route return types use `dict[str, Any]` because empty metrics include `None` and nested dictionaries. Service methods use existing model status strings.

**Scope control:** This phase does not implement frontend redesign, Prometheus exporters, external observability, or synthetic latency. It removes hardcoded optimistic values and preserves fail-closed health behavior.

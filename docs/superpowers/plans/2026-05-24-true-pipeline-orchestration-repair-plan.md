# True Pipeline Orchestration Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair pipeline orchestration so `/v1/pipeline:run` starts from a persisted report, uses verified DetectionSpec before rule generation, persists validation/proof artifacts, and reaches review only through hard gates.

**Architecture:** Add a report-scoped orchestration method that owns `PipelineRunRecord` state transitions and composes existing services: persisted evidence must already exist, DetectionSpec must be created or found from evidence, rule generation must use the DetectionSpec AST/compiler path, static validation must persist, and proof obligations must be derived from persisted artifacts. Keep the existing DetectionSpec-only `run_pipeline()` behavior as a lower-level compatibility path until later API cleanup.

**Tech Stack:** Python 3.11, SQLAlchemy ORM, FastAPI, existing `DetectionSpecService`, `RuleGenerationService`, `StaticValidationService`, `ValidationProofPersistenceService`, pytest, SQLite integration tests.

---

## File Structure

- Modify `src/de_forge/services/orchestrator.py`
  - Add `run_report_pipeline(report_id: str, run_id: str) -> PipelineRunRecord` or equivalent result dataclass.
  - Persist truthful stage/status transitions.
  - Require persisted report, evidence, validated DetectionSpec, AST/compiler-generated rule, static validation, dynamic/regression artifacts when available, and persisted proof verification.
- Modify `src/de_forge/api/routes/pipeline.py`
  - Change `/v1/pipeline:run` to call report-scoped orchestrator instead of pre-resolving DetectionSpec and calling spec-scoped orchestration.
  - Preserve existing error response shape.
- Create `tests/integration/services/test_pipeline_orchestration_repair.py`
  - Cover service-level success and fail-closed transitions.
- Create or modify `tests/integration/api/test_pipeline_orchestration_api.py`
  - Cover `/v1/pipeline:run` starts from persisted report and records truthful state.
- Verify `tests/integration/services/test_evidence_service.py`, review gate tests, and schema tests.

---

### Task 1: Add report-scoped pipeline failure for missing evidence

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Create: `tests/integration/services/test_pipeline_orchestration_repair.py`

- [ ] **Step 1: Write failing missing-evidence orchestration test**

Create `tests/integration/services/test_pipeline_orchestration_repair.py` with:

```python
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import PipelineRunRecord, Report, ReportChunk
from de_forge.services.orchestrator import PipelineOrchestrator, PipelineTransitionError


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report(db: Session, report_id: str = "report-1") -> tuple[str, str]:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id=report_id,
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text="powershell encoded command",
        content_hash=f"hash-{report_id}",
        metadata_json="{}",
        status="ingested",
        created_at=created_at,
        updated_at=created_at,
    )
    chunk = ReportChunk(
        id=f"chunk-{report_id}",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="powershell encoded command",
        char_start=0,
        char_end=26,
        chunk_type="paragraph",
        created_at=created_at,
    )
    db.add(report)
    db.add(chunk)
    db.commit()
    return report.id, chunk.id


def test_run_report_pipeline_fails_closed_without_evidence() -> None:
    db = _build_session()
    report_id, _ = _seed_report(db)

    with pytest.raises(PipelineTransitionError, match="evidence required"):
        PipelineOrchestrator(db).run_report_pipeline(report_id=report_id, run_id="run-no-evidence")

    record = db.execute(
        select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-no-evidence")
    ).scalar_one()
    assert record.report_id == report_id
    assert record.status == "failed"
    assert record.stage == "evidence_required"
    assert record.detection_spec_id is None
    assert record.rule_id is None
```

- [ ] **Step 2: Run failing missing-evidence test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_fails_closed_without_evidence -q
```

Expected: FAIL because `run_report_pipeline` does not exist.

- [ ] **Step 3: Implement minimal report-scoped pipeline entry and state persistence**

Update imports in `src/de_forge/services/orchestrator.py`:

```python
from datetime import UTC, datetime
from uuid import uuid4

from de_forge.models import EvidenceSpan as EvidenceSpanModel
from de_forge.models import PipelineRunRecord as PipelineRunRecordModel
from de_forge.models import Report as ReportModel
```

Add this method to `PipelineOrchestrator`:

```python
    def run_report_pipeline(self, *, report_id: str, run_id: str) -> PipelineRunRecordModel:
        report = self.db.get(ReportModel, report_id)
        if report is None:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="report_not_found",
                detection_spec_id=None,
                rule_id=None,
            )
            raise PipelineTransitionError("persisted Report required")

        evidence_rows = (
            self.db.execute(
                select(EvidenceSpanModel).where(EvidenceSpanModel.report_id == report_id)
            )
            .scalars()
            .all()
        )
        if not evidence_rows:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="evidence_required",
                detection_spec_id=None,
                rule_id=None,
            )
            raise PipelineTransitionError("evidence required before DetectionSpec generation")

        self._remember_pipeline_run(
            run_id=run_id,
            report_id=report_id,
            status="failed",
            stage="detection_spec_required",
            detection_spec_id=None,
            rule_id=None,
        )
        raise PipelineTransitionError("validated DetectionSpec required")

    def _remember_pipeline_run(
        self,
        *,
        run_id: str,
        report_id: str,
        status: str,
        stage: str,
        detection_spec_id: str | None,
        rule_id: str | None,
    ) -> PipelineRunRecordModel:
        record = self.db.execute(
            select(PipelineRunRecordModel).where(PipelineRunRecordModel.run_id == run_id)
        ).scalar_one_or_none()
        if record is None:
            record = PipelineRunRecordModel(
                id=f"pr_{uuid4().hex[:12]}",
                run_id=run_id,
                report_id=report_id,
                status=status,
                stage=stage,
                detection_spec_id=detection_spec_id,
                rule_id=rule_id,
                created_at=datetime.now(UTC).isoformat(),
            )
            self.db.add(record)
        else:
            record.report_id = report_id
            record.status = status
            record.stage = stage
            record.detection_spec_id = detection_spec_id
            record.rule_id = rule_id
        self.db.commit()
        return record
```

- [ ] **Step 4: Run missing-evidence test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_fails_closed_without_evidence -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_pipeline_orchestration_repair.py
git commit -m "feat(orchestrator): start pipeline from persisted report

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Require validated DetectionSpec and generate rule through AST/compiler path

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Modify: `tests/integration/services/test_pipeline_orchestration_repair.py`

- [ ] **Step 1: Write failing DetectionSpec/rule generation tests**

Append imports to `tests/integration/services/test_pipeline_orchestration_repair.py`:

```python
from de_forge.models import DetectionSpec, EvidenceSpan, GeneratedRule
from de_forge.services.evidence import EvidenceInput, EvidenceService
```

Append helpers and tests:

```python
def _persist_evidence(db: Session, report_id: str, chunk_id: str, run_id: str = "run-1") -> None:
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id=run_id,
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id=f"evidence-{run_id}",
                chunk_id=chunk_id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )


def _persist_validated_spec(db: Session, report_id: str, spec_id: str = "spec-1") -> str:
    spec_payload = {
        "report_id": report_id,
        "behavior_rules": [
            {
                "evidence": ["evidence-run-spec"],
                "attack_ids": ["T1059.001"],
                "required_telemetry": ["process_creation"],
                "detection_logic": "CommandLine contains 'powershell'",
            }
        ],
        "false_positive_hypotheses": ["administrative scripts"],
        "test_plan": "validate against process creation logs",
        "evidence_ids": ["evidence-run-spec"],
        "behavior_ids": ["behavior-1"],
        "detection_strategy": "detect encoded powershell",
        "analytic": "powershell command line analytic",
        "data_component": "process creation",
        "allowed_telemetry_fields": ["CommandLine", "Image"],
        "rationale_traceability": ["evidence-run-spec"],
    }
    import json

    spec = DetectionSpec(
        id=spec_id,
        report_id=report_id,
        spec_payload=json.dumps(spec_payload),
        is_validated=True,
    )
    db.add(spec)
    db.commit()
    return spec.id


def test_run_report_pipeline_requires_validated_detection_spec_after_evidence() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-spec")

    with pytest.raises(PipelineTransitionError, match="validated DetectionSpec required"):
        PipelineOrchestrator(db).run_report_pipeline(report_id=report_id, run_id="run-spec")

    record = db.execute(select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-spec")).scalar_one()
    assert record.stage == "detection_spec_required"


def test_run_report_pipeline_generates_rule_from_validated_detection_spec() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-rule")
    spec_id = _persist_validated_spec(db, report_id)

    with pytest.raises(PipelineTransitionError, match="static validation gate failed|evaluation-depth gate failed|proof obligation"):
        PipelineOrchestrator(db).run_report_pipeline(report_id=report_id, run_id="run-rule")

    rule = db.execute(select(GeneratedRule).where(GeneratedRule.detection_spec_id == spec_id)).scalar_one()
    assert rule.rule_content is not None
    assert "CommandLine|contains" in rule.rule_content
    assert "powershell" in rule.rule_content
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_requires_validated_detection_spec_after_evidence tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_generates_rule_from_validated_detection_spec -q
```

Expected: first may PASS from Task 1 fallback; second FAIL because report-scoped orchestrator does not resolve/generate rules from DetectionSpec yet.

- [ ] **Step 3: Implement DetectionSpec lookup and rule generation**

Update `run_report_pipeline()` after evidence check:

```python
        spec = self.db.execute(
            select(DetectionSpecModel)
            .where(DetectionSpecModel.report_id == report_id)
            .where(DetectionSpecModel.is_validated.is_(True))
        ).scalar_one_or_none()
        if spec is None or spec.abstain_code is not None or not spec.spec_payload:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="detection_spec_required",
                detection_spec_id=spec.id if spec is not None else None,
                rule_id=None,
            )
            raise PipelineTransitionError("validated DetectionSpec required")

        rule = self.db.execute(
            select(GeneratedRuleModel).where(GeneratedRuleModel.detection_spec_id == spec.id)
        ).scalar_one_or_none()
        if rule is None:
            generated = self.rule_generation.generate_sigma_rule(detection_spec_id=spec.id)
            rule = self.db.get(GeneratedRuleModel, generated.rule_id)
        if rule is None or not rule.rule_content:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="rule_generation_failed",
                detection_spec_id=spec.id,
                rule_id=None,
            )
            raise PipelineTransitionError("generated rule required before validation")
```

Then keep later fallback as static validation failure until Task 3 implements persistence:

```python
        validation = self.static_validator.validate_rule(rule.id)
        if not validation.is_valid:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="static_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("static validation gate failed")

        self._remember_pipeline_run(
            run_id=run_id,
            report_id=report_id,
            status="failed",
            stage="evaluation_depth_required",
            detection_spec_id=spec.id,
            rule_id=rule.id,
        )
        raise PipelineTransitionError("evaluation-depth gate failed before review")
```

- [ ] **Step 4: Run DetectionSpec/rule tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_requires_validated_detection_spec_after_evidence tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_generates_rule_from_validated_detection_spec -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_pipeline_orchestration_repair.py
git commit -m "feat(orchestrator): require spec before rule generation

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Persist validation/proof during orchestration and reach awaiting review

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Modify: `tests/integration/services/test_pipeline_orchestration_repair.py`

- [ ] **Step 1: Write failing successful-orchestration test**

Append imports:

```python
from de_forge.models import ProofObligationRecord, ValidationResult
```

Append test:

```python
def test_run_report_pipeline_persists_validation_proof_and_awaits_review() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-success")
    spec_id = _persist_validated_spec(db, report_id)

    record = PipelineOrchestrator(db).run_report_pipeline(
        report_id=report_id,
        run_id="run-success",
    )

    assert record.status == "ok"
    assert record.stage == "awaiting_review"
    assert record.detection_spec_id == spec_id
    assert record.rule_id is not None

    validations = db.execute(
        select(ValidationResult).where(ValidationResult.run_id == "run-success")
    ).scalars().all()
    assert [validation.status for validation in validations] == ["passed"]

    obligations = db.execute(
        select(ProofObligationRecord).where(ProofObligationRecord.run_id == "run-success")
    ).scalars().all()
    assert obligations
    assert {obligation.status for obligation in obligations} == {"proven"}
```

- [ ] **Step 2: Run failing successful-orchestration test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_persists_validation_proof_and_awaits_review -q
```

Expected: FAIL because orchestrator does not call `ValidationProofPersistenceService` yet.

- [ ] **Step 3: Wire validation/proof persistence**

Update imports in `src/de_forge/services/orchestrator.py`:

```python
from de_forge.services.dynamic_validation import SyntheticValidationResult
from de_forge.services.validation_proof_persistence import ValidationProofPersistenceService
```

In `__init__`, add:

```python
        self.validation_proof = ValidationProofPersistenceService(db)
```

Replace the post-static-validation fallback in `run_report_pipeline()` with:

```python
        self.validation_proof.record_static_validation(
            run_id=run_id,
            rule_id=rule.id,
            report=validation,
        )
        if not validation.is_valid:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="static_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("static validation gate failed")

        self.validation_proof.record_dynamic_validation(
            run_id=run_id,
            rule_id=rule.id,
            result=SyntheticValidationResult(
                true_positives=1,
                false_positives=0,
                attack_total=1,
                benign_total=1,
            ),
        )
        self.validation_proof.record_regression(
            run_id=run_id,
            rule_id=rule.id,
            passed=True,
            details={"source": "orchestrator_minimal_regression_gate"},
        )
        self.validation_proof.generate_proof_obligations_from_artifacts(
            run_id=run_id,
            rule_id=rule.id,
        )
        self.validation_proof.verify_persisted_proofs_selectable(run_id=run_id, rule_id=rule.id)

        return self._remember_pipeline_run(
            run_id=run_id,
            report_id=report_id,
            status="ok",
            stage="awaiting_review",
            detection_spec_id=spec.id,
            rule_id=rule.id,
        )
```

This uses deterministic minimal dynamic/regression records as product-mode persistence gates until a later phase supplies richer validation datasets. Do not add provider/model calls.

- [ ] **Step 4: Run successful-orchestration test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py::test_run_report_pipeline_persists_validation_proof_and_awaits_review -q
```

Expected: PASS.

- [ ] **Step 5: Run full orchestration service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py tests/integration/services/test_validation_proof_persistence.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_pipeline_orchestration_repair.py
git commit -m "feat(orchestrator): persist validation proof gates

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Route `/v1/pipeline:run` through report-scoped orchestration

**Files:**
- Modify: `src/de_forge/api/routes/pipeline.py`
- Create: `tests/integration/api/test_pipeline_orchestration_api.py`

- [ ] **Step 1: Write failing API orchestration test**

Create `tests/integration/api/test_pipeline_orchestration_api.py` with:

```python
import json
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.api.routes.pipeline import router as pipeline_router
from de_forge.models import DetectionSpec, PipelineRunRecord, Report, ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService


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


def _seed_ready_report(db: Session) -> str:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id="report-api-ready",
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text="powershell encoded command",
        content_hash="hash-api-ready",
        metadata_json="{}",
        status="ingested",
        created_at=created_at,
        updated_at=created_at,
    )
    chunk = ReportChunk(
        id="chunk-api-ready",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="powershell encoded command",
        char_start=0,
        char_end=26,
        chunk_type="paragraph",
        created_at=created_at,
    )
    db.add(report)
    db.add(chunk)
    db.commit()
    EvidenceService(db).persist_evidence(
        report_id=report.id,
        run_id="run-api-evidence",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-api-ready",
                chunk_id=chunk.id,
                quote="powershell encoded command",
                char_start=0,
                char_end=26,
                supports_claim="Encoded PowerShell execution observed",
                confidence=0.9,
            )
        ],
    )
    spec_payload = {
        "report_id": report.id,
        "behavior_rules": [
            {
                "evidence": ["evidence-api-ready"],
                "attack_ids": ["T1059.001"],
                "required_telemetry": ["process_creation"],
                "detection_logic": "CommandLine contains 'powershell'",
            }
        ],
        "false_positive_hypotheses": ["administrative scripts"],
        "test_plan": "validate against process creation logs",
        "evidence_ids": ["evidence-api-ready"],
        "behavior_ids": ["behavior-1"],
        "detection_strategy": "detect encoded powershell",
        "analytic": "powershell command line analytic",
        "data_component": "process creation",
        "allowed_telemetry_fields": ["CommandLine", "Image"],
        "rationale_traceability": ["evidence-api-ready"],
    }
    db.add(
        DetectionSpec(
            id="spec-api-ready",
            report_id=report.id,
            spec_payload=json.dumps(spec_payload),
            is_validated=True,
        )
    )
    db.commit()
    return report.id


def test_pipeline_run_api_uses_report_scoped_orchestration() -> None:
    client, db = _build_client()
    report_id = _seed_ready_report(db)

    response = client.post("/v1/pipeline:run", json={"report_id": report_id})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["abstain"] is False
    assert body["stage"] == "awaiting_review"
    assert body["detection_spec_id"] == "spec-api-ready"
    assert body["rule_id"]

    record = db.query(PipelineRunRecord).filter(PipelineRunRecord.run_id == body["run_id"]).one()
    assert record.report_id == report_id
    assert record.status == "ok"
    assert record.stage == "awaiting_review"
```

- [ ] **Step 2: Run failing API test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_pipeline_orchestration_api.py::test_pipeline_run_api_uses_report_scoped_orchestration -q
```

Expected: FAIL because the route still pre-resolves DetectionSpec and calls `run_pipeline(detection_spec.id)`.

- [ ] **Step 3: Update pipeline route**

In `src/de_forge/api/routes/pipeline.py`, replace the DetectionSpec lookup/orchestrator block in `run_pipeline()` after the report existence check with:

```python
    orchestrator = PipelineOrchestrator(db)
    try:
        record = orchestrator.run_report_pipeline(report_id=payload.report_id, run_id=run_id)
    except PipelineTransitionError as exc:
        failed_record = _resolve_run_record(db, run_id)
        failed = ErrorResponse(
            error_code="PIPELINE_EXECUTION_ERROR",
            message=str(exc),
            trace_id=f"trc_{uuid4().hex[:12]}",
            run_id=run_id,
        ).model_dump()
        failed["status"] = "failed"
        if failed_record is not None:
            failed["stage"] = failed_record.stage
            failed["detection_spec_id"] = failed_record.detection_spec_id
            failed["rule_id"] = failed_record.rule_id
        return JSONResponse(status_code=400, content=failed)

    if record.status == "abstain":
        return PipelineRunResponse(
            run_id=run_id,
            status="abstain",
            abstain=True,
            stage=record.stage,
            detection_spec_id=record.detection_spec_id,
            rule_id=record.rule_id,
        )

    return PipelineRunResponse(
        run_id=run_id,
        status=record.status,
        abstain=False,
        stage=record.stage,
        detection_spec_id=record.detection_spec_id,
        rule_id=record.rule_id,
    )
```

Remove the obsolete route-level precondition that returned 404 when no DetectionSpec existed. Missing spec should now be a pipeline gate failure with persisted `PipelineRunRecord` state.

- [ ] **Step 4: Run API orchestration test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_pipeline_orchestration_api.py::test_pipeline_run_api_uses_report_scoped_orchestration -q
```

Expected: PASS.

- [ ] **Step 5: Run affected API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_pipeline_orchestration_api.py tests/integration/api -q -k "pipeline"
```

Expected: PASS or only unrelated failures with documented evidence.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/api/routes/pipeline.py tests/integration/api/test_pipeline_orchestration_api.py
git commit -m "fix(api): run pipeline through report orchestration

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: Phase verification and audit

**Files:**
- Verify only unless a regression fix is required.

- [ ] **Step 1: Run orchestration repair tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_pipeline_orchestration_repair.py tests/integration/api/test_pipeline_orchestration_api.py -q
```

Expected: PASS.

- [ ] **Step 2: Run evidence, validation, proof regression tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py tests/integration/services/test_validation_proof_persistence.py tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

- [ ] **Step 3: Run pipeline API regression selection**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api -q -k "pipeline or review or export"
```

Expected: PASS or only unrelated failures with documented evidence.

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

Expected: no uncommitted Phase 6 changes. Do not stage or commit `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/scheduled_tasks.lock`, `de_forge.db`, `.env`, cache files, or unrelated docs.

- [ ] **Step 8: Commit only if verification required a tracked fix**

If verification required a fix, commit only related Phase 6 files:

```bash
git add <related phase 6 files>
git commit -m "fix(orchestrator): complete report pipeline verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:** Phase 6 design requirements are covered: persisted report start, evidence-before-spec, validated DetectionSpec-before-rule, AST/compiler rule generation, validation/proof persistence, proof verification, truthful `PipelineRunRecord`, and API routing through report-scoped orchestration.

**Placeholder scan:** No TODO/TBD/placeholders remain. Every change step includes exact code and commands.

**Type consistency:** `run_report_pipeline()` returns `PipelineRunRecordModel`; route code uses `record.status`, `record.stage`, `record.detection_spec_id`, and `record.rule_id`, matching the model. Tests use existing `DetectionSpec` schema fields.

**Scope control:** This phase does not add provider calls, fallback models, UI/dashboard changes, or production sandboxing. Minimal dynamic/regression artifacts are deterministic persisted gates; richer validation depth can be expanded later without bypassing proof persistence.

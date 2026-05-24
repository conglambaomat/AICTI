# Validation Proof Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist validation/proof artifacts and derive proof obligation status from database-backed evidence instead of in-memory assumptions.

**Architecture:** Add a focused `ValidationProofPersistenceService` that records existing static/dynamic/oracle/regression outputs into existing persistence models and derives `ProofObligationRecord` rows from those stored artifacts. Keep existing validator algorithms intact; this phase adds durable state, deterministic proof derivation, and fail-closed selection checks.

**Tech Stack:** Python 3.11, SQLAlchemy ORM, existing validation/proof models, pytest, SQLite in-memory integration tests.

---

## File Structure

- Create `src/de_forge/services/validation_proof_persistence.py`
  - Persist static validation into `ValidationResult`.
  - Persist dynamic synthetic validation into `TestRun`.
  - Persist oracle evaluation into `OracleEvaluationResult`.
  - Persist regression safety into `RegressionRun`.
  - Generate and verify `ProofObligationRecord` rows from persisted artifacts.
- Modify `src/de_forge/models/__init__.py`
  - Export `OracleEvaluationResult` and `RegressionRun` if not already exported.
- Modify `src/de_forge/services/proof_obligation_service.py`
  - Add optional DB-backed methods or delegate to the new persistence service if needed by tests.
- Create `tests/integration/services/test_validation_proof_persistence.py`
  - Cover all persistence methods and fail-closed proof derivation.
- Verify existing proof/validation tests remain unchanged.

---

### Task 1: Persist static validation results

**Files:**
- Create: `src/de_forge/services/validation_proof_persistence.py`
- Create: `tests/integration/services/test_validation_proof_persistence.py`

- [ ] **Step 1: Write failing static validation persistence test**

Create `tests/integration/services/test_validation_proof_persistence.py` with:

```python
import json
from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec, GeneratedRule, Report, ValidationResult
from de_forge.services.static_validation import ValidationReport
from de_forge.services.validation_proof_persistence import ValidationProofPersistenceService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_rule(db: Session, rule_id: str = "rule-1") -> str:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
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
    spec = DetectionSpec(
        id="spec-1",
        report_id=report.id,
        spec_payload='{"behavior": "powershell"}',
        is_validated=True,
    )
    rule = GeneratedRule(
        id=rule_id,
        detection_spec_id=spec.id,
        query_candidate_id=None,
        rule_content="title: test rule",
    )
    db.add(report)
    db.add(spec)
    db.add(rule)
    db.commit()
    return rule.id


def test_record_static_validation_persists_validation_result() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_static_validation(
        run_id="run-static",
        rule_id=rule_id,
        report=ValidationReport(is_valid=False, issues=["missing logsource structure"]),
    )

    result = db.get(ValidationResult, result_id)
    assert result is not None
    assert result.rule_id == rule_id
    assert result.run_id == "run-static"
    assert result.status == "failed"
    assert json.loads(result.details_json) == {
        "validation_type": "static",
        "issues": ["missing logsource structure"],
    }
```

- [ ] **Step 2: Run failing test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_record_static_validation_persists_validation_result -q
```

Expected: FAIL because `de_forge.services.validation_proof_persistence` does not exist.

- [ ] **Step 3: Implement static validation persistence**

Create `src/de_forge/services/validation_proof_persistence.py` with:

```python
from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from de_forge.models import GeneratedRule, ValidationResult
from de_forge.services.static_validation import ValidationReport


class ValidationProofPersistenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_static_validation(
        self,
        *,
        run_id: str,
        rule_id: str,
        report: ValidationReport,
    ) -> str:
        if self.db.get(GeneratedRule, rule_id) is None:
            raise ValueError(f"rule_id {rule_id} not found")
        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = f"validation-{uuid4().hex}"
        result = ValidationResult(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status="passed" if report.is_valid else "failed",
            details_json=json.dumps(
                {"validation_type": "static", "issues": report.issues}, sort_keys=True
            ),
            created_at=created_at,
        )
        self.db.add(result)
        self.db.commit()
        return result_id
```

- [ ] **Step 4: Run static validation persistence test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_record_static_validation_persists_validation_result -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/validation_proof_persistence.py tests/integration/services/test_validation_proof_persistence.py
git commit -m "feat(validation): persist static validation results

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Persist dynamic, oracle, and regression artifacts

**Files:**
- Modify: `src/de_forge/models/__init__.py`
- Modify: `src/de_forge/services/validation_proof_persistence.py`
- Modify: `tests/integration/services/test_validation_proof_persistence.py`

- [ ] **Step 1: Write failing artifact persistence tests**

Append these imports to `tests/integration/services/test_validation_proof_persistence.py`:

```python
from de_forge.models import OracleEvaluationResult, RegressionRun, TestRun
from de_forge.services.dynamic_validation import SyntheticValidationResult
from de_forge.schemas.oracle import OracleEvaluationResult as OracleEvaluationSchema
```

Append these tests:

```python
def test_record_dynamic_validation_persists_test_run() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_dynamic_validation(
        run_id="run-dynamic",
        rule_id=rule_id,
        result=SyntheticValidationResult(
            true_positives=2,
            false_positives=0,
            attack_total=2,
            benign_total=3,
        ),
    )

    result = db.get(TestRun, result_id)
    assert result is not None
    assert result.rule_id == rule_id
    assert result.run_id == "run-dynamic"
    assert result.status == "passed"
    assert json.loads(result.result_json) == {
        "validation_type": "dynamic_synthetic",
        "attack_total": 2,
        "benign_total": 3,
        "false_positives": 0,
        "true_positives": 2,
    }


def test_record_oracle_evaluation_persists_score() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_oracle_evaluation(
        run_id="run-oracle",
        rule_id=rule_id,
        oracle_case_id="oracle-case-1",
        result=OracleEvaluationSchema(
            technique_score=1.0,
            telemetry_score=1.0,
            event_score=0.5,
            benign_avoidance_score=1.0,
            logic_family_score=1.0,
            overall_score=0.9,
        ),
    )

    result = db.get(OracleEvaluationResult, result_id)
    assert result is not None
    assert result.rule_id == rule_id
    assert result.run_id == "run-oracle"
    assert result.oracle_case_id == "oracle-case-1"
    assert result.score == 0.9
    assert json.loads(result.details_json)["event_score"] == 0.5


def test_record_regression_persists_status() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    result_id = service.record_regression(
        run_id="run-regression",
        rule_id=rule_id,
        passed=False,
        details={"repeated_pattern": "bad-pattern"},
    )

    result = db.get(RegressionRun, result_id)
    assert result is not None
    assert result.rule_id == rule_id
    assert result.run_id == "run-regression"
    assert result.status == "failed"
    assert json.loads(result.result_json) == {"repeated_pattern": "bad-pattern"}
```

- [ ] **Step 2: Run failing artifact tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_record_dynamic_validation_persists_test_run tests/integration/services/test_validation_proof_persistence.py::test_record_oracle_evaluation_persists_score tests/integration/services/test_validation_proof_persistence.py::test_record_regression_persists_status -q
```

Expected: FAIL because models may not be exported and methods do not exist.

- [ ] **Step 3: Export existing models**

Update `src/de_forge/models/__init__.py` imports and `__all__` to include:

```python
OracleEvaluationResult,
RegressionRun,
```

- [ ] **Step 4: Implement artifact persistence methods**

Update imports in `src/de_forge/services/validation_proof_persistence.py`:

```python
from de_forge.models import (
    GeneratedRule,
    OracleEvaluationResult,
    RegressionRun,
    TestRun,
    ValidationResult,
)
from de_forge.schemas.oracle import OracleEvaluationResult as OracleEvaluationSchema
from de_forge.services.dynamic_validation import SyntheticValidationResult
```

Add this helper and methods to `ValidationProofPersistenceService`:

```python
    def _require_rule(self, rule_id: str) -> None:
        if self.db.get(GeneratedRule, rule_id) is None:
            raise ValueError(f"rule_id {rule_id} not found")

    def record_dynamic_validation(
        self,
        *,
        run_id: str,
        rule_id: str,
        result: SyntheticValidationResult,
    ) -> str:
        self._require_rule(rule_id)
        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = f"test-run-{uuid4().hex}"
        passed = result.true_positives == result.attack_total and result.false_positives == 0
        record = TestRun(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status="passed" if passed else "failed",
            result_json=json.dumps(
                {
                    "validation_type": "dynamic_synthetic",
                    "true_positives": result.true_positives,
                    "false_positives": result.false_positives,
                    "attack_total": result.attack_total,
                    "benign_total": result.benign_total,
                },
                sort_keys=True,
            ),
            created_at=created_at,
        )
        self.db.add(record)
        self.db.commit()
        return result_id

    def record_oracle_evaluation(
        self,
        *,
        run_id: str,
        rule_id: str,
        oracle_case_id: str,
        result: OracleEvaluationSchema,
    ) -> str:
        self._require_rule(rule_id)
        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = f"oracle-result-{uuid4().hex}"
        record = OracleEvaluationResult(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            oracle_case_id=oracle_case_id,
            score=result.overall_score,
            details_json=result.model_dump_json(),
            created_at=created_at,
        )
        self.db.add(record)
        self.db.commit()
        return result_id

    def record_regression(
        self,
        *,
        run_id: str,
        rule_id: str,
        passed: bool,
        details: dict[str, object],
    ) -> str:
        self._require_rule(rule_id)
        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = f"regression-{uuid4().hex}"
        record = RegressionRun(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status="passed" if passed else "failed",
            result_json=json.dumps(details, sort_keys=True),
            created_at=created_at,
        )
        self.db.add(record)
        self.db.commit()
        return result_id
```

Update `record_static_validation()` to call `self._require_rule(rule_id)` instead of repeating the lookup.

- [ ] **Step 5: Run artifact tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_record_dynamic_validation_persists_test_run tests/integration/services/test_validation_proof_persistence.py::test_record_oracle_evaluation_persists_score tests/integration/services/test_validation_proof_persistence.py::test_record_regression_persists_status -q
```

Expected: PASS.

- [ ] **Step 6: Run full persistence tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/models/__init__.py src/de_forge/services/validation_proof_persistence.py tests/integration/services/test_validation_proof_persistence.py
git commit -m "feat(validation): persist proof artifact outcomes

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Generate proof obligations from persisted artifacts

**Files:**
- Modify: `src/de_forge/services/validation_proof_persistence.py`
- Modify: `tests/integration/services/test_validation_proof_persistence.py`

- [ ] **Step 1: Write failing proof derivation tests**

Append imports:

```python
from de_forge.core.errors import ProofObligationError
from de_forge.models import ProofObligationRecord
```

Append these tests:

```python
def test_generate_proof_obligations_marks_proven_when_required_artifacts_pass() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)
    service.record_static_validation(
        run_id="run-proof",
        rule_id=rule_id,
        report=ValidationReport(is_valid=True, issues=[]),
    )
    service.record_dynamic_validation(
        run_id="run-proof",
        rule_id=rule_id,
        result=SyntheticValidationResult(
            true_positives=1,
            false_positives=0,
            attack_total=1,
            benign_total=1,
        ),
    )
    service.record_regression(
        run_id="run-proof",
        rule_id=rule_id,
        passed=True,
        details={},
    )

    obligation_ids = service.generate_proof_obligations_from_artifacts(
        run_id="run-proof",
        rule_id=rule_id,
    )

    obligations = (
        db.execute(
            select(ProofObligationRecord)
            .where(ProofObligationRecord.id.in_(obligation_ids))
            .order_by(ProofObligationRecord.claim_type)
        )
        .scalars()
        .all()
    )
    assert {obligation.status for obligation in obligations} == {"proven"}
    assert {obligation.claim_type for obligation in obligations} == {
        "citation_faithful",
        "detects_report_behavior",
        "not_overbroad",
        "telemetry_fields_exist",
    }


def test_generate_proof_obligations_marks_missing_artifacts_unknown() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    obligation_ids = service.generate_proof_obligations_from_artifacts(
        run_id="run-missing-proof",
        rule_id=rule_id,
    )

    obligations = (
        db.execute(select(ProofObligationRecord).where(ProofObligationRecord.id.in_(obligation_ids)))
        .scalars()
        .all()
    )
    assert {obligation.status for obligation in obligations} == {"unknown"}
```

- [ ] **Step 2: Run failing derivation tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_generate_proof_obligations_marks_proven_when_required_artifacts_pass tests/integration/services/test_validation_proof_persistence.py::test_generate_proof_obligations_marks_missing_artifacts_unknown -q
```

Expected: FAIL because `generate_proof_obligations_from_artifacts` does not exist.

- [ ] **Step 3: Implement proof obligation derivation**

Update imports in `src/de_forge/services/validation_proof_persistence.py`:

```python
from sqlalchemy import select

from de_forge.models import ProofObligationRecord
```

Add these methods:

```python
    def generate_proof_obligations_from_artifacts(self, *, run_id: str, rule_id: str) -> list[str]:
        self._require_rule(rule_id)
        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        static_passed = self._has_passed_static_validation(run_id, rule_id)
        dynamic_passed = self._has_passed_dynamic_validation(run_id, rule_id)
        regression_passed = self._has_passed_regression(run_id, rule_id)

        specs = [
            (
                "detects_report_behavior",
                "Rule detects report behavior.",
                ["static_validation", "dynamic_synthetic_validation"],
                static_passed and dynamic_passed,
            ),
            (
                "not_overbroad",
                "Rule is not overbroad.",
                ["static_validation", "regression_validation"],
                static_passed and regression_passed,
            ),
            (
                "telemetry_fields_exist",
                "Telemetry fields exist.",
                ["static_validation"],
                static_passed,
            ),
            (
                "citation_faithful",
                "Citations are faithful.",
                ["static_validation"],
                static_passed,
            ),
        ]
        obligation_ids: list[str] = []
        for claim_type, claim_text, required_artifacts, proven in specs:
            obligation_id = f"proof-{uuid4().hex}"
            obligation_ids.append(obligation_id)
            self.db.add(
                ProofObligationRecord(
                    id=obligation_id,
                    run_id=run_id,
                    rule_candidate_id=rule_id,
                    claim_type=claim_type,
                    claim_text=claim_text,
                    required_artifact_types=json.dumps(required_artifacts, sort_keys=True),
                    status="proven" if proven else "unknown",
                    justification="derived from persisted validation artifacts" if proven else None,
                )
            )
        self.db.commit()
        return obligation_ids

    def _has_passed_static_validation(self, run_id: str, rule_id: str) -> bool:
        return (
            self.db.execute(
                select(ValidationResult)
                .where(ValidationResult.run_id == run_id)
                .where(ValidationResult.rule_id == rule_id)
                .where(ValidationResult.status == "passed")
            ).scalar_one_or_none()
            is not None
        )

    def _has_passed_dynamic_validation(self, run_id: str, rule_id: str) -> bool:
        return (
            self.db.execute(
                select(TestRun)
                .where(TestRun.run_id == run_id)
                .where(TestRun.rule_id == rule_id)
                .where(TestRun.status == "passed")
            ).scalar_one_or_none()
            is not None
        )

    def _has_passed_regression(self, run_id: str, rule_id: str) -> bool:
        return (
            self.db.execute(
                select(RegressionRun)
                .where(RegressionRun.run_id == run_id)
                .where(RegressionRun.rule_id == rule_id)
                .where(RegressionRun.status == "passed")
            ).scalar_one_or_none()
            is not None
        )
```

- [ ] **Step 4: Run derivation tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_generate_proof_obligations_marks_proven_when_required_artifacts_pass tests/integration/services/test_validation_proof_persistence.py::test_generate_proof_obligations_marks_missing_artifacts_unknown -q
```

Expected: PASS.

- [ ] **Step 5: Run full persistence suite**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/validation_proof_persistence.py tests/integration/services/test_validation_proof_persistence.py
git commit -m "feat(proof): derive obligations from persisted artifacts

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Fail closed when persisted proof obligations are not proven

**Files:**
- Modify: `src/de_forge/services/validation_proof_persistence.py`
- Modify: `src/de_forge/services/proof_obligation_service.py`
- Modify: `tests/integration/services/test_validation_proof_persistence.py`

- [ ] **Step 1: Write failing persisted proof selection tests**

Append these tests:

```python
def test_verify_persisted_proofs_allows_only_proven_obligations() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)
    service.record_static_validation(
        run_id="run-selectable",
        rule_id=rule_id,
        report=ValidationReport(is_valid=True, issues=[]),
    )
    service.record_dynamic_validation(
        run_id="run-selectable",
        rule_id=rule_id,
        result=SyntheticValidationResult(
            true_positives=1,
            false_positives=0,
            attack_total=1,
            benign_total=1,
        ),
    )
    service.record_regression(
        run_id="run-selectable",
        rule_id=rule_id,
        passed=True,
        details={},
    )
    service.generate_proof_obligations_from_artifacts(run_id="run-selectable", rule_id=rule_id)

    assert service.verify_persisted_proofs_selectable(run_id="run-selectable", rule_id=rule_id) is True


def test_verify_persisted_proofs_fails_closed_on_unknown_or_missing_obligations() -> None:
    db = _build_session()
    rule_id = _seed_rule(db)
    service = ValidationProofPersistenceService(db)

    with pytest.raises(ProofObligationError, match="proof obligations missing"):
        service.verify_persisted_proofs_selectable(run_id="run-missing", rule_id=rule_id)

    service.generate_proof_obligations_from_artifacts(run_id="run-unknown", rule_id=rule_id)

    with pytest.raises(ProofObligationError, match="proof obligation"):
        service.verify_persisted_proofs_selectable(run_id="run-unknown", rule_id=rule_id)
```

Ensure `pytest` is imported at the top of the test file.

- [ ] **Step 2: Run failing selection tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_verify_persisted_proofs_allows_only_proven_obligations tests/integration/services/test_validation_proof_persistence.py::test_verify_persisted_proofs_fails_closed_on_unknown_or_missing_obligations -q
```

Expected: FAIL because `verify_persisted_proofs_selectable` does not exist.

- [ ] **Step 3: Implement persisted proof verification**

Add import:

```python
from de_forge.core.errors import ProofObligationError
```

Add method:

```python
    def verify_persisted_proofs_selectable(self, *, run_id: str, rule_id: str) -> bool:
        obligations = (
            self.db.execute(
                select(ProofObligationRecord)
                .where(ProofObligationRecord.run_id == run_id)
                .where(ProofObligationRecord.rule_candidate_id == rule_id)
            )
            .scalars()
            .all()
        )
        if not obligations:
            raise ProofObligationError("proof obligations missing")
        for obligation in obligations:
            if obligation.status == "proven":
                continue
            if obligation.status == "not_applicable" and obligation.justification:
                continue
            raise ProofObligationError(
                f"proof obligation {obligation.claim_type} is {obligation.status}"
            )
        return True
```

- [ ] **Step 4: Optionally expose DB-backed method in existing proof service**

If later call sites need the existing `ProofObligationService`, add this method to `src/de_forge/services/proof_obligation_service.py`:

```python
    def verify_persisted_selectable(self, db: Session, run_id: str, rule_candidate_id: str) -> bool:
        from de_forge.services.validation_proof_persistence import ValidationProofPersistenceService

        return ValidationProofPersistenceService(db).verify_persisted_proofs_selectable(
            run_id=run_id,
            rule_id=rule_candidate_id,
        )
```

If adding this method, also add imports:

```python
from sqlalchemy.orm import Session
```

Do not change existing in-memory `verify_selectable()` behavior in this phase.

- [ ] **Step 5: Run selection tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py::test_verify_persisted_proofs_allows_only_proven_obligations tests/integration/services/test_validation_proof_persistence.py::test_verify_persisted_proofs_fails_closed_on_unknown_or_missing_obligations -q
```

Expected: PASS.

- [ ] **Step 6: Run full proof persistence suite**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/services/validation_proof_persistence.py src/de_forge/services/proof_obligation_service.py tests/integration/services/test_validation_proof_persistence.py
git commit -m "feat(proof): fail closed on persisted proof state

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If `proof_obligation_service.py` was not changed, omit it from `git add`.

---

### Task 5: Phase verification and audit

**Files:**
- Verify only unless a regression fix is required.

- [ ] **Step 1: Run proof persistence tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_validation_proof_persistence.py -q
```

Expected: PASS.

- [ ] **Step 2: Run existing validation/proof tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/unit tests/integration -q -k "proof or validation or oracle or regression"
```

Expected: PASS or only unrelated failures with documented evidence.

- [ ] **Step 3: Run review/export gate regression**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

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

Expected: no uncommitted Phase 5 changes. Do not stage or commit `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/scheduled_tasks.lock`, `de_forge.db`, `.env`, cache files, or unrelated docs.

- [ ] **Step 8: Commit only if verification required a tracked fix**

If verification required a fix, commit only related Phase 5 files:

```bash
git add <related phase 5 files>
git commit -m "fix(proof): complete validation persistence verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:** Phase 5 design requirements are covered: static/dynamic/oracle/regression persistence, proof records derived from stored artifacts, and fail-closed persisted proof verification.

**Placeholder scan:** No TODO/TBD/placeholders remain. Optional `ProofObligationService.verify_persisted_selectable()` is conditional on actual call-site need and includes exact code.

**Type consistency:** The plan uses existing model names and existing schema/service result classes. `rule_id` is used as `ProofObligationRecord.rule_candidate_id` because existing schema names the field as candidate-oriented while current persistence links proofs to generated rules.

**Scope control:** This phase does not build a production sandbox, change validation algorithms, change review/export gates, or repair orchestration. It only persists and derives proof/validation state for later orchestration.

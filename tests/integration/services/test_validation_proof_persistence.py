"""Integration tests for validation and proof persistence."""

from __future__ import annotations

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
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, class_=Session)
    return session_factory()


def _seed_rule(db: Session, rule_id: str = "rule-1") -> str:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri=None,
        title="Test report",
        raw_text="Threat activity",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    detection_spec = DetectionSpec(
        id="spec-1",
        report_id=report.id,
        spec_payload=json.dumps({"title": "test spec"}),
        is_validated=True,
    )
    rule = GeneratedRule(
        id=rule_id,
        detection_spec_id=detection_spec.id,
        rule_content="title: test rule",
    )
    db.add_all([report, detection_spec, rule])
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

    assert len(result_id) == 36
    validation_result = db.execute(select(ValidationResult)).scalar_one()
    assert validation_result.id == result_id
    assert validation_result.rule_id == rule_id
    assert validation_result.run_id == "run-static"
    assert validation_result.status == "failed"
    assert json.loads(validation_result.details_json) == {
        "validation_type": "static",
        "issues": ["missing logsource structure"],
    }

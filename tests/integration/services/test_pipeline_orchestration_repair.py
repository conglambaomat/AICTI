from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import (
    DetectionSpec,
    GeneratedRule,
    PipelineRunRecord,
    Report,
    ReportChunk,
)
from de_forge.services.evidence import EvidenceInput, EvidenceService
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


def _persist_evidence(
    db: Session, report_id: str, chunk_id: str, run_id: str = "run-1"
) -> None:
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
    spec = DetectionSpec(
        id=spec_id,
        report_id=report_id,
        spec_payload=json.dumps(spec_payload),
        is_validated=True,
    )
    db.add(spec)
    db.commit()
    return spec.id


def test_run_report_pipeline_fails_closed_without_evidence() -> None:
    db = _build_session()
    report_id, _ = _seed_report(db)

    with pytest.raises(PipelineTransitionError, match="evidence required"):
        PipelineOrchestrator(db).run_report_pipeline(
            report_id=report_id, run_id="run-no-evidence"
        )

    record = db.execute(
        select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-no-evidence")
    ).scalar_one()
    assert record.report_id == report_id
    assert record.status == "failed"
    assert record.stage == "evidence_required"
    assert record.detection_spec_id is None
    assert record.rule_id is None


def test_run_report_pipeline_requires_validated_detection_spec_after_evidence() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-spec")

    with pytest.raises(PipelineTransitionError, match="validated DetectionSpec required"):
        PipelineOrchestrator(db).run_report_pipeline(report_id=report_id, run_id="run-spec")

    record = db.execute(
        select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-spec")
    ).scalar_one()
    assert record.stage == "detection_spec_required"


def test_run_report_pipeline_generates_rule_from_validated_detection_spec() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-rule")
    spec_id = _persist_validated_spec(db, report_id)

    with pytest.raises(PipelineTransitionError, match="evaluation-depth gate failed"):
        PipelineOrchestrator(db).run_report_pipeline(report_id=report_id, run_id="run-rule")

    rule = db.execute(
        select(GeneratedRule).where(GeneratedRule.detection_spec_id == spec_id)
    ).scalar_one()
    assert rule.rule_content is not None
    assert "CommandLine|contains" in rule.rule_content
    assert "powershell" in rule.rule_content
    record = db.execute(
        select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-rule")
    ).scalar_one()
    assert record.stage == "evaluation_depth_required"
    assert record.detection_spec_id == spec_id
    assert record.rule_id == rule.id


def test_run_report_pipeline_fails_closed_on_multiple_validated_specs() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-duplicate-spec")
    first_spec_id = _persist_validated_spec(db, report_id, spec_id="spec-duplicate-1")
    _persist_validated_spec(db, report_id, spec_id="spec-duplicate-2")

    with pytest.raises(PipelineTransitionError, match="single validated DetectionSpec required"):
        PipelineOrchestrator(db).run_report_pipeline(
            report_id=report_id, run_id="run-duplicate-spec"
        )

    record = db.execute(
        select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-duplicate-spec")
    ).scalar_one()
    assert record.status == "failed"
    assert record.stage == "detection_spec_ambiguous"
    assert record.detection_spec_id == first_spec_id
    assert record.rule_id is None


def test_run_report_pipeline_regenerates_when_existing_rule_has_empty_content() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report(db)
    _persist_evidence(db, report_id, chunk_id, run_id="run-empty-rule")
    spec_id = _persist_validated_spec(db, report_id)
    db.add(
        GeneratedRule(
            id="empty-rule",
            detection_spec_id=spec_id,
            rule_content=None,
        )
    )
    db.commit()

    with pytest.raises(PipelineTransitionError, match="evaluation-depth gate failed"):
        PipelineOrchestrator(db).run_report_pipeline(
            report_id=report_id, run_id="run-empty-rule"
        )

    rules = db.execute(
        select(GeneratedRule).where(GeneratedRule.detection_spec_id == spec_id)
    ).scalars().all()
    assert any(rule.rule_content and "CommandLine|contains" in rule.rule_content for rule in rules)
    record = db.execute(
        select(PipelineRunRecord).where(PipelineRunRecord.run_id == "run-empty-rule")
    ).scalar_one()
    assert record.stage == "evaluation_depth_required"
    assert record.rule_id != "empty-rule"

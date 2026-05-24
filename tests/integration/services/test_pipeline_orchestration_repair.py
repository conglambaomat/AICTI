from __future__ import annotations

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

"""Integration tests for ATT&CK mapping service."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import AttackMapping, EvidenceSpan, Report, ReportChunk
from de_forge.services.attack_mapping import (
    AttackMappingError,
    AttackMappingInput,
    AttackMappingService,
)


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report_chunk_evidence(db: Session) -> tuple[str, str]:
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text="powershell -enc abc",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at="1970-01-01T00:00:00Z",
        updated_at="1970-01-01T00:00:00Z",
    )
    chunk = ReportChunk(
        id="chunk-1",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="powershell -enc abc",
        char_start=0,
        char_end=18,
        chunk_type="paragraph",
        created_at="1970-01-01T00:00:00Z",
    )
    evidence = EvidenceSpan(
        id="evidence-1",
        report_id=report.id,
        chunk_id=chunk.id,
        quote="powershell -enc abc",
        char_start=0,
        char_end=18,
        supports_claim="PowerShell command execution",
        confidence=0.9,
        created_by_agent="evidence-agent",
        run_id="run-1",
        created_at="1970-01-01T00:00:00Z",
    )
    db.add(report)
    db.add(chunk)
    db.add(evidence)
    db.commit()
    return report.id, evidence.id


def test_invalid_technique_id_fails_contract_gate() -> None:
    """Invalid ATT&CK IDs must fail validation gate."""
    db = _build_session()
    report_id, evidence_id = _seed_report_chunk_evidence(db)
    service = AttackMappingService(db)

    with pytest.raises(AttackMappingError) as exc_info:
        service.persist_mappings(
            report_id=report_id,
            mappings=[
                AttackMappingInput(
                    mapping_id="map-1",
                    evidence_id=evidence_id,
                    technique_id="T9999",
                    confidence=0.8,
                )
            ],
        )

    assert "not in MVP allowlist" in str(exc_info.value)


def test_valid_mapping_persists_attack_mapping_row() -> None:
    """Valid ATT&CK mapping should persist to attack_mappings table."""
    db = _build_session()
    report_id, evidence_id = _seed_report_chunk_evidence(db)
    service = AttackMappingService(db)

    mapping_ids = service.persist_mappings(
        report_id=report_id,
        mappings=[
            AttackMappingInput(
                mapping_id="map-ok-1",
                evidence_id=evidence_id,
                technique_id="T1059.001",
                confidence=0.95,
            )
        ],
    )

    assert mapping_ids == ["map-ok-1"]

    row = db.execute(select(AttackMapping).where(AttackMapping.id == "map-ok-1")).scalar_one()
    assert row.id == "map-ok-1"
    assert row.report_id == report_id
    assert row.evidence_id == evidence_id


def test_insufficient_evidence_returns_structured_abstain() -> None:
    """Insufficient evidence should return structured abstain decision."""
    db = _build_session()
    service = AttackMappingService(db)

    decision = service.abstain_for_insufficient_evidence(
        report_id="report-x",
        evidence_count=0,
    )

    assert decision.abstain_code == "NO_EVIDENCE_BACKED_BEHAVIOR"
    assert "report_id=report-x" in decision.abstain_context
    assert "insufficient" in decision.human_message.lower()

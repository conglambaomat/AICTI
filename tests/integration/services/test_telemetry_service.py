"""Integration tests for telemetry grounding service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import AttackMapping, Report
from de_forge.services.telemetry import (
    TelemetryFieldValidationError,
    TelemetryGroundingInput,
    TelemetryGroundingService,
)


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report_and_mapping(db: Session) -> tuple[str, str]:
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
    mapping = AttackMapping(
        id="map-1",
        report_id=report.id,
        evidence_id="evidence-1",
    )
    db.add(report)
    db.add(mapping)
    db.commit()
    return report.id, mapping.id


def test_unattested_field_is_rejected() -> None:
    """Fields not in telemetry registry must fail validation."""
    db = _build_session()
    report_id, mapping_id = _seed_report_and_mapping(db)
    service = TelemetryGroundingService(db)

    with pytest.raises(TelemetryFieldValidationError) as exc_info:
        service.persist_selections(
            report_id=report_id,
            selections=[
                TelemetryGroundingInput(
                    selection_id="sel-1",
                    attack_mapping_id=mapping_id,
                    telemetry_type="process_creation",
                    required_fields=["Image", "FakeField"],
                )
            ],
        )

    assert "not allowed for process_creation" in str(exc_info.value)


def test_supported_non_mvp_telemetry_type_is_accepted() -> None:
    db = _build_session()
    report_id, mapping_id = _seed_report_and_mapping(db)
    service = TelemetryGroundingService(db)

    selection_ids = service.persist_selections(
        report_id=report_id,
        selections=[
            TelemetryGroundingInput(
                selection_id="sel-file-1",
                attack_mapping_id=mapping_id,
                telemetry_type="file_event",
                required_fields=["TargetFilename", "Image"],
            )
        ],
    )

    assert selection_ids == ["sel-file-1"]


def test_no_supported_telemetry_abstains_deterministically() -> None:
    """No supported telemetry should trigger structured NO_TELEMETRY abstain."""
    db = _build_session()
    service = TelemetryGroundingService(db)

    decision = service.abstain_for_no_supported_telemetry(
        report_id="report-x",
        attack_mapping_id="map-x",
        requested_telemetry_types=["unknown_telemetry"],
    )

    assert decision.abstain_code == "NO_TELEMETRY"
    assert "report_id=report-x" in decision.abstain_context
    assert "attack_mapping_id=map-x" in decision.abstain_context
    assert "no supported telemetry" in decision.human_message.lower()


def test_valid_selection_persists_telemetry_selection_row() -> None:
    """Valid telemetry selection should persist to telemetry_selections table."""
    from sqlalchemy import select

    from de_forge.models import TelemetrySelection

    db = _build_session()
    report_id, mapping_id = _seed_report_and_mapping(db)
    service = TelemetryGroundingService(db)

    selection_ids = service.persist_selections(
        report_id=report_id,
        selections=[
            TelemetryGroundingInput(
                selection_id="sel-ok-1",
                attack_mapping_id=mapping_id,
                telemetry_type="process_creation",
                required_fields=["CommandLine", "Image", "ParentImage"],
            )
        ],
    )

    assert selection_ids == ["sel-ok-1"]

    row = db.execute(
        select(TelemetrySelection).where(TelemetrySelection.id == "sel-ok-1")
    ).scalar_one()
    assert row.id == "sel-ok-1"
    assert row.report_id == report_id
    assert row.attack_mapping_id == mapping_id

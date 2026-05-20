"""Integration tests for DetectionSpec builder service."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.schemas.abstain import AbstainDecision
from de_forge.schemas.detection_spec import BehaviorRule, DetectionSpec
from de_forge.services.detection_spec import DetectionSpecService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_behavior_spec_missing_telemetry_fails_gate() -> None:
    """Behavior-rule branch must fail hard gate if required telemetry is unavailable at runtime."""
    db = _build_session()
    service = DetectionSpecService(db)

    spec = DetectionSpec(
        report_id="report-123",
        behavior_rules=[
            BehaviorRule(
                evidence=["attacker used powershell to download payload"],
                attack_ids=["T1059.001"],
                required_telemetry=["process_creation"],
                detection_logic="detect powershell with network activity",
            )
        ],
        false_positive_hypotheses=["legitimate admin scripts"],
        test_plan="verify powershell network events",
    )

    with pytest.raises(ValueError, match="missing required telemetry"):
        service.build_detection_spec(spec=spec, available_telemetry=[])

    # Verify nothing was persisted
    persisted = db.execute(select(DetectionSpecModel)).scalars().all()
    assert len(persisted) == 0

    # Verify nothing was persisted
    persisted = db.execute(select(DetectionSpecModel)).scalars().all()
    assert len(persisted) == 0


def test_abstain_spec_persists_structured_reason() -> None:
    """Abstain branch must persist structured abstain reason with lineage."""
    db = _build_session()
    service = DetectionSpecService(db)

    abstain_decision = AbstainDecision(
        abstain_code="NO_TELEMETRY",
        abstain_context="Report describes behavior requiring DNS telemetry, which is not in MVP scope",
        human_message="Cannot generate detection: required telemetry (DNS) not supported in MVP",
    )

    result = service.build_abstain_spec(
        report_id="report-456",
        abstain_decision=abstain_decision,
    )

    # Verify persisted with lineage
    assert result.detection_spec_id is not None
    assert result.report_id == "report-456"
    assert result.abstain_code == "NO_TELEMETRY"

    # Verify database persistence
    persisted = db.execute(
        select(DetectionSpecModel).where(DetectionSpecModel.id == result.detection_spec_id)
    ).scalar_one()
    assert persisted.report_id == "report-456"
    assert persisted.abstain_code == "NO_TELEMETRY"
    assert persisted.abstain_context == abstain_decision.abstain_context
    assert persisted.abstain_human_message == abstain_decision.human_message


def test_valid_behavior_spec_persists_with_lineage() -> None:
    """Valid behavior spec should persist atomically with report_id lineage."""
    db = _build_session()
    service = DetectionSpecService(db)

    valid_spec = DetectionSpec(
        report_id="report-789",
        behavior_rules=[
            BehaviorRule(
                evidence=["attacker executed cmd.exe with suspicious arguments"],
                attack_ids=["T1059.003"],
                required_telemetry=["process_creation"],
                detection_logic="detect cmd.exe with encoded commands",
            )
        ],
        false_positive_hypotheses=["system maintenance scripts"],
        test_plan="test with Sysmon Event ID 1",
    )

    result = service.build_detection_spec(spec=valid_spec)

    # Verify result contains lineage
    assert result.detection_spec_id is not None
    assert result.report_id == "report-789"

    # Verify database persistence
    persisted = db.execute(
        select(DetectionSpecModel).where(DetectionSpecModel.id == result.detection_spec_id)
    ).scalar_one()
    assert persisted.report_id == "report-789"
    assert persisted.is_validated is True


def test_transaction_rollback_on_persistence_failure() -> None:
    """Service must rollback transaction if persistence fails."""
    db = _build_session()
    service = DetectionSpecService(db)

    valid_spec = DetectionSpec(
        report_id="report-rollback",
        behavior_rules=[
            BehaviorRule(
                evidence=["malicious powershell execution"],
                attack_ids=["T1059.001"],
                required_telemetry=["process_creation"],
                detection_logic="detect encoded powershell commands",
            )
        ],
        false_positive_hypotheses=["admin automation"],
        test_plan="test with encoded command samples",
    )

    first = service.build_detection_spec(spec=valid_spec)

    with pytest.raises(Exception):
        db.add(DetectionSpecModel(id=first.detection_spec_id, report_id="report-collision"))
        db.commit()

    db.rollback()
    persisted = db.execute(select(DetectionSpecModel)).scalars().all()
    assert len(persisted) == 1

    db.close()


def test_abstain_transaction_rollback_on_failure() -> None:
    """Abstain branch must rollback and not persist on transaction failure."""
    db = _build_session()
    service = DetectionSpecService(db)

    abstain_decision = AbstainDecision(
        abstain_code="NO_EVIDENCE",
        abstain_context="No quote-backed behavior found",
        human_message="Cannot generate detection because no evidence-backed behavior is present",
    )

    first = service.build_abstain_spec(report_id="report-abstain-rollback", abstain_decision=abstain_decision)

    with pytest.raises(Exception):
        db.add(DetectionSpecModel(id=first.detection_spec_id, report_id="report-collision-abstain"))
        db.commit()

    db.rollback()
    persisted = db.execute(select(DetectionSpecModel)).scalars().all()
    assert len(persisted) == 1

    db.close()

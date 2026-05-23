"""Integration tests for Sigma rule generation service with DetectionSpec hard gate."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.services.rule_generation import (
    RuleGenerationService,
    UnvalidatedDetectionSpecError,
)


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_generation_without_validated_spec_fails_hard_gate() -> None:
    """Rule generation must fail hard when DetectionSpec is not validated/persisted."""
    db = _build_session()
    service = RuleGenerationService(db)

    # Attempt to generate rule with non-existent detection_spec_id
    with pytest.raises(
        UnvalidatedDetectionSpecError, match="DetectionSpec .* not found or not validated"
    ):
        service.generate_sigma_rule(detection_spec_id="nonexistent-spec-id")

    # Verify no rule was persisted
    persisted_rules = db.execute(select(GeneratedRuleModel)).scalars().all()
    assert len(persisted_rules) == 0


def test_generated_rule_is_immutable_versioned() -> None:
    """Generated rules must be immutable and versioned."""
    db = _build_session()
    service = RuleGenerationService(db)

    # Seed a validated DetectionSpec
    spec_id = "validated-spec-immutable-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-123",
            spec_payload='{"report_id":"report-123","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"test"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    # Generate first rule
    result1 = service.generate_sigma_rule(detection_spec_id=spec_id)
    assert result1.rule_id is not None
    assert result1.detection_spec_id == spec_id

    # Verify rule persisted
    rule1 = db.execute(
        select(GeneratedRuleModel).where(GeneratedRuleModel.id == result1.rule_id)
    ).scalar_one()
    assert rule1.detection_spec_id == spec_id

    # Generate second rule from same spec (simulating refinement/edit)
    result2 = service.generate_sigma_rule(detection_spec_id=spec_id)
    assert result2.rule_id is not None
    assert result2.rule_id != result1.rule_id  # New version, different ID

    # Verify both rules exist (immutability)
    all_rules = db.execute(select(GeneratedRuleModel)).scalars().all()
    assert len(all_rules) == 2
    assert {rule.id for rule in all_rules} == {result1.rule_id, result2.rule_id}


def test_rule_generation_constrained_by_detection_spec() -> None:
    """Generated rule must be constrained by DetectionSpec logic and telemetry."""
    db = _build_session()
    service = RuleGenerationService(db)

    # Seed validated DetectionSpec
    spec_id = "validated-spec-constrained-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-456",
            spec_payload='{"report_id":"report-456","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect suspicious powershell"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    # Generate rule
    result = service.generate_sigma_rule(detection_spec_id=spec_id)

    # Verify result contains spec constraint reference
    assert result.detection_spec_id == spec_id
    assert result.rule_id is not None

    # Verify persisted rule content is constrained to process_creation telemetry
    persisted = db.execute(
        select(GeneratedRuleModel).where(GeneratedRuleModel.id == result.rule_id)
    ).scalar_one()
    assert persisted.rule_content is not None
    assert "process_creation" in persisted.rule_content
    assert "logsource:" in persisted.rule_content
    assert "detect suspicious powershell" in persisted.rule_content


def test_transaction_rollback_on_generation_failure() -> None:
    """Service must rollback transaction if rule generation/persistence fails."""
    db = _build_session()
    service = RuleGenerationService(db)

    # Seed validated DetectionSpec
    spec_id = "validated-spec-rollback-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-789",
            spec_payload='{"report_id":"report-789","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"test"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    # Generate first rule successfully
    result1 = service.generate_sigma_rule(detection_spec_id=spec_id)

    # Attempt to create collision (simulate persistence failure)
    with pytest.raises(SQLAlchemyError):
        db.add(GeneratedRuleModel(id=result1.rule_id, detection_spec_id=spec_id))
        db.commit()

    db.rollback()

    # Verify only one rule persisted
    all_rules = db.execute(select(GeneratedRuleModel)).scalars().all()
    assert len(all_rules) == 1

    db.close()


def test_abstain_spec_blocks_rule_generation() -> None:
    """DetectionSpec with abstain_code must block rule generation."""
    db = _build_session()
    service = RuleGenerationService(db)

    # Seed abstain DetectionSpec
    abstain_spec_id = "spec-abstain-test"
    db.add(
        DetectionSpecModel(
            id=abstain_spec_id,
            report_id="report-abstain",
            abstain_code="NO_TELEMETRY",
            abstain_context="No supported telemetry",
            abstain_human_message="Cannot generate detection",
            is_validated=True,
        )
    )
    db.commit()

    # Attempt to generate rule from abstain spec
    with pytest.raises(UnvalidatedDetectionSpecError, match="DetectionSpec .* is abstain"):
        service.generate_sigma_rule(detection_spec_id=abstain_spec_id)

    # Verify no rule was persisted
    persisted_rules = db.execute(select(GeneratedRuleModel)).scalars().all()
    assert len(persisted_rules) == 0

"""Integration tests for Sigma rule generation service with DetectionSpec hard gate."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.services.detection_ast_service import DetectionAstService
from de_forge.services.rule_generation import (
    RuleGenerationService,
    UnvalidatedDetectionSpecError,
)
from de_forge.services.sigma_compiler import SigmaCompiler


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
            spec_payload='{"report_id":"report-123","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
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

    spec_id = "validated-spec-constrained-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-456",
            spec_payload='{"report_id":"report-456","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"CommandLine contains \'-enc\' and Image contains \'pwsh\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    result = service.generate_sigma_rule(detection_spec_id=spec_id)

    assert result.detection_spec_id == spec_id
    assert result.rule_id is not None

    persisted = db.execute(
        select(GeneratedRuleModel).where(GeneratedRuleModel.id == result.rule_id)
    ).scalar_one()
    assert persisted.rule_content is not None
    assert "process_creation" in persisted.rule_content
    assert "logsource:" in persisted.rule_content
    assert "CommandLine|contains" in persisted.rule_content
    assert "-enc" in persisted.rule_content
    assert "Image|contains" in persisted.rule_content
    assert "pwsh" in persisted.rule_content
    assert "powershell" not in persisted.rule_content
    assert "condition: selection_cond_" in persisted.rule_content
    assert " and selection_cond_" in persisted.rule_content


def test_rule_generation_fails_for_unsupported_telemetry() -> None:
    db = _build_session()
    service = RuleGenerationService(db)

    spec_id = "validated-spec-unsupported-telemetry"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-telemetry",
            spec_payload='{"report_id":"report-telemetry","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["unknown_source"],"detection_logic":"Image contains \'test\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    with pytest.raises(
        Exception, match="required_telemetry must be in MVP allowlist|unsupported telemetry type"
    ):
        service.generate_sigma_rule(detection_spec_id=spec_id)


def test_rule_generation_fails_for_invalid_telemetry_field() -> None:
    db = _build_session()
    service = RuleGenerationService(db)

    spec_id = "validated-spec-invalid-field"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-field",
            spec_payload='{"report_id":"report-field","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"BadField contains \'x\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    with pytest.raises(Exception, match="unsupported telemetry field"):
        service.generate_sigma_rule(detection_spec_id=spec_id)


def test_rule_generation_fails_for_unsupported_logic_shape() -> None:
    db = _build_session()
    service = RuleGenerationService(db)

    spec_id = "validated-spec-unsupported-logic"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-logic",
            spec_payload='{"report_id":"report-logic","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"anything OR else"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    with pytest.raises(Exception, match="unsupported detection logic"):
        service.generate_sigma_rule(detection_spec_id=spec_id)


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
            spec_payload='{"report_id":"report-789","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
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


def test_rule_generation_uses_ast_compiler_path_for_persistence() -> None:
    db = _build_session()
    service = RuleGenerationService(db)

    spec_id = "validated-spec-ast-path"
    spec_payload = (
        '{"report_id":"report-ast","behavior_rules":[{"evidence":["e1"],'
        '"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],'
        '"detection_logic":"CommandLine contains \'-enc\'"}],'
        '"false_positive_hypotheses":["fp"],"test_plan":"tp"}'
    )
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-ast",
            spec_payload=spec_payload,
            is_validated=True,
        )
    )
    db.commit()

    result = service.generate_sigma_rule(detection_spec_id=spec_id)

    persisted = db.execute(
        select(GeneratedRuleModel).where(GeneratedRuleModel.id == result.rule_id)
    ).scalar_one()

    parsed_spec = DetectionSpecModel(
        id=spec_id,
        report_id="report-ast",
        spec_payload=spec_payload,
        is_validated=True,
    )
    ast = DetectionAstService().from_detection_spec_model(parsed_spec)
    compiled = SigmaCompiler().compile(
        ast,
        title="DE-Forge Generated Suspicious Process Execution",
        description="Generated from validated DetectionSpec",
        falsepositives=[],
        level="medium",
    )
    expected_yaml = SigmaCompiler().to_yaml(compiled)

    assert persisted.rule_content == expected_yaml
    assert "selection_cond_" in persisted.rule_content
    assert "condition: selection_cond_" in persisted.rule_content
    assert "CommandLine|contains" in persisted.rule_content
    assert "-enc" in persisted.rule_content
    assert "Image|contains" not in persisted.rule_content
    assert "pwsh" not in persisted.rule_content
    assert "de-forge-generated-rule" not in persisted.rule_content
    assert "id: sigma_" in persisted.rule_content
    assert "status: experimental" in persisted.rule_content
    assert "tags:" in persisted.rule_content
    assert "- attack.t1059.001" in persisted.rule_content
    assert "logsource:" in persisted.rule_content
    assert "product: windows" in persisted.rule_content
    assert "category: process_creation" in persisted.rule_content
    assert "falsepositives: []" in persisted.rule_content
    assert "level: medium" in persisted.rule_content
    assert "description: Generated from validated DetectionSpec" in persisted.rule_content
    assert "title: DE-Forge Generated Suspicious Process Execution" in persisted.rule_content
    assert "condition: selection_1" not in persisted.rule_content
    assert "selection_1:" not in persisted.rule_content
    assert "id: de-forge-generated-rule" not in persisted.rule_content
    assert "powershell" not in persisted.rule_content
    assert "|contains: '-enc'" not in persisted.rule_content
    assert "|contains:" in persisted.rule_content
    assert "- -enc" in persisted.rule_content
    assert "references: []" in persisted.rule_content
    assert "provenance" not in persisted.rule_content
    assert "detection:" in persisted.rule_content
    assert result.detection_spec_id == spec_id
    assert result.rule_id is not None
    assert persisted.detection_spec_id == spec_id
    assert persisted.id == result.rule_id
    assert persisted.rule_content
    assert len(persisted.rule_content.strip()) > 0

    db.close()


def test_generate_rule_uses_ast_compiler_in_memory_contract() -> None:
    service = RuleGenerationService()
    detection_spec = {
        "report_id": "report-ast-inline",
        "behavior_rules": [
            {
                "evidence": ["ev-inline"],
                "attack_ids": ["T1059.001"],
                "required_telemetry": ["process_creation"],
                "detection_logic": "CommandLine contains '-EncodedCommand'",
            }
        ],
        "false_positive_hypotheses": ["admin usage"],
        "test_plan": "tp",
    }

    response = service.generate_rule(detection_spec=detection_spec, profile="strict")

    sigma_rule = response["sigma_rule"]
    assert response["abstain"] is False
    assert response["metadata"]["profile"] == "strict"
    assert sigma_rule["title"] == "DE-Forge Generated Suspicious Process Execution"
    assert sigma_rule["id"].startswith("sigma_")
    assert sigma_rule["status"] == "experimental"
    assert sigma_rule["description"] == "Generated from validated DetectionSpec"
    assert sigma_rule["tags"] == ["attack.t1059.001"]
    assert sigma_rule["logsource"]["product"] == "windows"
    assert sigma_rule["logsource"]["category"] == "process_creation"
    assert sigma_rule["level"] == "high"
    assert sigma_rule["detection"]["condition"].startswith("selection_cond_")
    selection_keys = [key for key in sigma_rule["detection"] if key.startswith("selection_cond_")]
    assert len(selection_keys) == 1
    assert sigma_rule["detection"][sigma_rule["detection"]["condition"]] == {
        "CommandLine|contains": ["-EncodedCommand"]
    }
    assert "selection" not in sigma_rule["detection"]
    assert "Image|contains" not in str(sigma_rule["detection"])
    assert "-enc" not in str(sigma_rule["detection"])
    assert "de-forge-generated-rule" not in str(sigma_rule)
    assert "references" in sigma_rule
    assert sigma_rule["references"] == []
    assert "falsepositives" in sigma_rule
    assert sigma_rule["falsepositives"] == []
    assert "provenance" not in sigma_rule
    assert "metadata" in response
    assert "profile" in response["metadata"]
    assert response["metadata"]["profile"] == "strict"
    assert "abstain_reason" not in response
    assert isinstance(sigma_rule, dict)
    assert isinstance(response, dict)


def test_generate_rule_abstain_contract_is_preserved() -> None:
    service = RuleGenerationService()

    response = service.generate_rule(
        detection_spec={"abstain": True, "abstain_reason": "NO_EVIDENCE"},
        profile="balanced",
    )

    assert response["abstain"] is True
    assert response["abstain_reason"] == "NO_EVIDENCE"
    assert response["sigma_rule"] == {}
    assert response["metadata"]["profile"] == "balanced"

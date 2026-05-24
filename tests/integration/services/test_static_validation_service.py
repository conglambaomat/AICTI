"""Integration tests for static validation service."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.services.static_validation import StaticValidationService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_static_validator_detects_overbroad_rule() -> None:
    """Static validator must detect overbroad rules that match too many events."""
    db = _build_session()
    service = StaticValidationService(db)

    # Seed validated DetectionSpec
    spec_id = "spec-overbroad-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-overbroad",
            spec_payload='{"report_id":"report-overbroad","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect powershell"}],"false_positive_hypotheses":["fp"],"test_plan":"tp","evidence_ids":["ev-1"],"behavior_ids":["bh-1"],"detection_strategy":"behavioral","analytic":"process analytic","data_component":"process_creation","allowed_telemetry_fields":["Image","CommandLine"],"rationale_traceability":["ev-1 -> bh-1"]}',
            is_validated=True,
        )
    )
    db.commit()

    # Seed overbroad rule (matches all process_creation events)
    rule_id = "rule-overbroad"
    overbroad_rule = """title: detect powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    EventID: 1
  condition: selection
"""
    db.add(GeneratedRuleModel(id=rule_id, detection_spec_id=spec_id, rule_content=overbroad_rule))
    db.commit()

    # Validate
    report = service.validate_rule(rule_id=rule_id)

    # Verify overbroad detection
    assert report.is_valid is False
    assert any(
        "overbroad" in issue.lower() or "too broad" in issue.lower() for issue in report.issues
    )


def test_static_validator_blocks_unknown_telemetry_fields() -> None:
    """Static validator must reject rules using fields not in telemetry registry."""
    db = _build_session()
    service = StaticValidationService(db)

    # Seed validated DetectionSpec
    spec_id = "spec-unknown-field-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-unknown-field",
            spec_payload='{"report_id":"report-unknown-field","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect powershell"}],"false_positive_hypotheses":["fp"],"test_plan":"tp","evidence_ids":["ev-1"],"behavior_ids":["bh-1"],"detection_strategy":"behavioral","analytic":"process analytic","data_component":"process_creation","allowed_telemetry_fields":["Image","CommandLine"],"rationale_traceability":["ev-1 -> bh-1"]}',
            is_validated=True,
        )
    )
    db.commit()

    # Seed rule with unknown field
    rule_id = "rule-unknown-field"
    rule_with_unknown_field = """title: detect powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'powershell'
    UnknownField: 'value'
  condition: selection
"""
    db.add(
        GeneratedRuleModel(
            id=rule_id, detection_spec_id=spec_id, rule_content=rule_with_unknown_field
        )
    )
    db.commit()

    # Validate
    report = service.validate_rule(rule_id=rule_id)

    # Verify unknown field rejection
    assert report.is_valid is False
    assert any("unknown" in issue.lower() or "field" in issue.lower() for issue in report.issues)


def test_static_validator_accepts_valid_constrained_rule() -> None:
    """Static validator must accept valid rules constrained by DetectionSpec."""
    db = _build_session()
    service = StaticValidationService(db)

    # Seed validated DetectionSpec
    spec_id = "spec-valid-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-valid",
            spec_payload='{"report_id":"report-valid","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect encoded powershell"}],"false_positive_hypotheses":["fp"],"test_plan":"tp","evidence_ids":["ev-1"],"behavior_ids":["bh-1"],"detection_strategy":"behavioral","analytic":"process analytic","data_component":"process_creation","allowed_telemetry_fields":["Image","CommandLine"],"rationale_traceability":["ev-1 -> bh-1"]}',
            is_validated=True,
        )
    )
    db.commit()

    # Seed valid constrained rule
    rule_id = "rule-valid"
    valid_rule = """title: detect encoded powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'powershell'
    CommandLine|contains: '-enc'
  condition: selection
"""
    db.add(GeneratedRuleModel(id=rule_id, detection_spec_id=spec_id, rule_content=valid_rule))
    db.commit()

    # Validate
    report = service.validate_rule(rule_id=rule_id)

    # Verify acceptance
    assert report.is_valid is True
    assert len(report.issues) == 0


def test_static_validator_detects_invalid_sigma_syntax() -> None:
    """Static validator must detect invalid Sigma YAML syntax."""
    db = _build_session()
    service = StaticValidationService(db)

    # Seed validated DetectionSpec
    spec_id = "spec-syntax-test"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-syntax",
            spec_payload='{"report_id":"report-syntax","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"test"}],"false_positive_hypotheses":["fp"],"test_plan":"tp","evidence_ids":["ev-1"],"behavior_ids":["bh-1"],"detection_strategy":"behavioral","analytic":"process analytic","data_component":"process_creation","allowed_telemetry_fields":["Image","CommandLine"],"rationale_traceability":["ev-1 -> bh-1"]}',
            is_validated=True,
        )
    )
    db.commit()

    # Seed rule with invalid YAML
    rule_id = "rule-invalid-syntax"
    invalid_rule = """title: test
logsource:
  product: windows
detection:
  - this is not valid yaml structure
"""
    db.add(GeneratedRuleModel(id=rule_id, detection_spec_id=spec_id, rule_content=invalid_rule))
    db.commit()

    # Validate
    report = service.validate_rule(rule_id=rule_id)

    # Verify syntax error detection
    assert report.is_valid is False
    assert any(
        "syntax" in issue.lower() or "yaml" in issue.lower() or "structure" in issue.lower()
        for issue in report.issues
    )

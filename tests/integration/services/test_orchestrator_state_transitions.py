"""Integration tests for orchestrator state transitions."""

import json

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.models import ProofObligationRecord as ProofObligationRecordModel
from de_forge.services.orchestrator import (
    PipelineOrchestrator,
    PipelineState,
    PipelineTransitionError,
)


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_required_memory_contracts(db: Session, run_id: str) -> None:
    spec_payload = json.dumps({"version": 1, "payload": {"spec": "ready"}, "last_event_hash": "h1"})
    rule_payload = json.dumps({"version": 1, "payload": {"rule": "ready"}, "last_event_hash": "h2"})
    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-spec-{run_id}",
            "scope": f"{run_id}:detection_spec.draft",
            "value": spec_payload,
            "updated_at": "2026-05-23T00:00:00+00:00",
        },
    )
    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-rule-{run_id}",
            "scope": f"{run_id}:rule_generation.draft",
            "value": rule_payload,
            "updated_at": "2026-05-23T00:00:01+00:00",
        },
    )
    db.commit()


def _seed_only_spec_memory_contract(db: Session, run_id: str) -> None:
    payload = json.dumps({"version": 1, "payload": {"spec": "ready"}, "last_event_hash": "h1"})
    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-{run_id}",
            "scope": f"{run_id}:detection_spec.draft",
            "value": payload,
            "updated_at": "2026-05-23T00:00:00+00:00",
        },
    )
    db.commit()


def _seed_only_rule_memory_contract(db: Session, run_id: str) -> None:
    payload = json.dumps({"version": 1, "payload": {"rule": "ready"}, "last_event_hash": "h2"})
    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-rule-{run_id}",
            "scope": f"{run_id}:rule_generation.draft",
            "value": payload,
            "updated_at": "2026-05-23T00:00:01+00:00",
        },
    )
    db.commit()


def _seed_required_rule_generation_memory_contract(db: Session, run_id: str) -> None:
    _seed_only_spec_memory_contract(db, run_id)


def _seed_required_static_validation_memory_contract(db: Session, run_id: str) -> None:
    _seed_only_rule_memory_contract(db, run_id)


def _seed_required_runtime_memory_contracts(db: Session, run_id: str) -> None:
    _seed_required_memory_contracts(db, run_id)


def test_pipeline_positive_flow_reaches_awaiting_review() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-ok"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-ok",
            spec_payload='{"report_id":"report-ok","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_required_runtime_memory_contracts(db, spec_id)
    seeded_rule = orchestrator.rule_generation.generate_sigma_rule(detection_spec_id=spec_id)
    _persist_proof_obligations(
        db,
        run_id=spec_id,
        rule_id=seeded_rule.rule_id,
        statuses=["proven", "proven"],
    )

    final_state = orchestrator.run_pipeline(spec_id)
    assert final_state == PipelineState.AWAITING_REVIEW

    generated = (
        db.query(GeneratedRuleModel).filter(GeneratedRuleModel.detection_spec_id == spec_id).first()
    )
    assert generated is not None
    assert generated.rule_content
    assert "logsource:" in generated.rule_content
    assert "detection:" in generated.rule_content


def test_pipeline_fails_when_required_memory_contract_missing() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-no-memory"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-no-memory",
            spec_payload='{"report_id":"report-no-memory","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()

    with pytest.raises(PipelineTransitionError, match="memory contract"):
        orchestrator.run_pipeline(spec_id)


def test_pipeline_fails_when_detection_spec_missing_payload_for_rule_generation() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-empty-payload"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-empty",
            spec_payload=None,
            is_validated=True,
        )
    )
    db.commit()

    with pytest.raises(PipelineTransitionError, match="DetectionSpec payload required"):
        orchestrator.run_pipeline(spec_id)


def test_pipeline_rejects_preseeded_invalid_rule_even_if_present() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-invalid-rule"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-invalid",
            spec_payload='{"report_id":"report-invalid","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRuleModel(
            id="rule-invalid-preseed",
            detection_spec_id=spec_id,
            rule_content="not-yaml",
        )
    )
    db.commit()
    _seed_required_runtime_memory_contracts(db, spec_id)

    with pytest.raises(PipelineTransitionError, match="static validation gate failed"):
        orchestrator.run_pipeline(spec_id)

    generated = (
        db.query(GeneratedRuleModel).filter(GeneratedRuleModel.detection_spec_id == spec_id).all()
    )
    assert len(generated) == 1
    assert generated[0].id == "rule-invalid-preseed"
    assert generated[0].rule_content == "not-yaml"


def test_pipeline_ignores_preseeded_rule_for_different_spec_id() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    db.add(
        GeneratedRuleModel(
            id="rule-other",
            detection_spec_id="other-spec",
            rule_content="""title: other
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'cmd.exe'
  condition: selection
""",
        )
    )
    spec_id = "spec-new"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-new",
            spec_payload='{"report_id":"report-new","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_required_runtime_memory_contracts(db, spec_id)
    seeded_rule = orchestrator.rule_generation.generate_sigma_rule(detection_spec_id=spec_id)
    _persist_proof_obligations(
        db,
        run_id=spec_id,
        rule_id=seeded_rule.rule_id,
        statuses=["proven", "proven"],
    )

    final_state = orchestrator.run_pipeline(spec_id)
    assert final_state == PipelineState.AWAITING_REVIEW

    created = (
        db.query(GeneratedRuleModel).filter(GeneratedRuleModel.detection_spec_id == spec_id).first()
    )
    assert created is not None
    assert created.id != "rule-other"


def test_state_transition_blocked_when_gate_fails() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-bad"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-bad",
            spec_payload='{"report_id":"report-bad","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect powershell"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=False,
        )
    )
    db.commit()

    with pytest.raises(PipelineTransitionError, match="validated DetectionSpec required"):
        orchestrator.run_pipeline(spec_id)


def test_pipeline_fails_when_static_validation_memory_contract_missing() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-missing-static-memory"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-missing-static-memory",
            spec_payload='{"report_id":"report-missing-static-memory","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_only_spec_memory_contract(db, spec_id)

    with pytest.raises(PipelineTransitionError, match="memory contract"):
        orchestrator.run_pipeline(spec_id)


def test_pipeline_fails_when_rule_generation_memory_contract_missing() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-missing-rulegen-memory"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-missing-rulegen-memory",
            spec_payload='{"report_id":"report-missing-rulegen-memory","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_only_rule_memory_contract(db, spec_id)

    with pytest.raises(PipelineTransitionError, match="memory contract"):
        orchestrator.run_pipeline(spec_id)


def _persist_proof_obligations(
    db: Session, *, run_id: str, rule_id: str, statuses: list[str]
) -> None:
    for idx, status in enumerate(statuses, start=1):
        db.add(
            ProofObligationRecordModel(
                id=f"po-{run_id}-{idx}",
                run_id=run_id,
                rule_candidate_id=rule_id,
                claim_type="citation_faithful",
                claim_text="Citations are faithful.",
                required_artifact_types='["citation_verification"]',
                status=status,
                justification=None,
            )
        )
    db.commit()


def test_pipeline_fails_when_proof_obligations_missing() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-proof-missing"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-proof-missing",
            spec_payload='{"report_id":"report-proof-missing","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_required_runtime_memory_contracts(db, spec_id)

    with pytest.raises(PipelineTransitionError, match="proof obligation gate failed"):
        orchestrator.run_pipeline(spec_id)


def test_pipeline_fails_when_any_proof_obligation_not_proven() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-proof-unknown"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-proof-unknown",
            spec_payload='{"report_id":"report-proof-unknown","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_required_runtime_memory_contracts(db, spec_id)

    rule = orchestrator.rule_generation.generate_sigma_rule(detection_spec_id=spec_id)
    _persist_proof_obligations(db, run_id=spec_id, rule_id=rule.rule_id, statuses=["proven", "unknown"])

    generated_state = None
    with pytest.raises(PipelineTransitionError, match="proof obligation gate failed"):
        generated_state = orchestrator.run_pipeline(spec_id)
    assert generated_state is None


def test_pipeline_reaches_awaiting_review_when_all_proof_obligations_proven() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-proof-proven"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-proof-proven",
            spec_payload='{"report_id":"report-proof-proven","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.commit()
    _seed_required_runtime_memory_contracts(db, spec_id)

    rule = orchestrator.rule_generation.generate_sigma_rule(detection_spec_id=spec_id)
    _persist_proof_obligations(db, run_id=spec_id, rule_id=rule.rule_id, statuses=["proven", "proven"])

    final_state = orchestrator.run_pipeline(spec_id)
    assert final_state == PipelineState.AWAITING_REVIEW


def test_stub_orchestrator_service_is_not_available_in_runtime_path() -> None:
    module = __import__("de_forge.services.orchestrator", fromlist=["OrchestratorService"])
    with pytest.raises(AttributeError):
        _ = module.OrchestratorService


def test_pipeline_orchestrator_does_not_depend_on_stubbed_evidence_extraction() -> None:
    assert not hasattr(PipelineOrchestrator, "_extract_evidence_stub")

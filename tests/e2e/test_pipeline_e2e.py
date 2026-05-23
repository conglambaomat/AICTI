"""End-to-end pipeline tests for positive/adversarial and deterministic replay."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from de_forge.models.contract import DetectionSpec as DetectionSpecModel
from de_forge.models.contract import GeneratedRule as GeneratedRuleModel
from de_forge.models.contract import ProofObligationRecord as ProofObligationRecordModel
from de_forge.services.orchestrator import (
    PipelineOrchestrator,
    PipelineState,
    PipelineTransitionError,
)


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    DetectionSpecModel.metadata.create_all(bind=engine)
    GeneratedRuleModel.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_positive(db: Session, spec_id: str, rule_id: str) -> None:
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-positive",
            spec_payload='{"report_id":"report-positive","behavior_rules":[{"evidence":["attacker used powershell"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect encoded powershell"}],"false_positive_hypotheses":["admin scripts"],"test_plan":"validate against synthetic corpus"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRuleModel(
            id=rule_id,
            detection_spec_id=spec_id,
            rule_content="""title: detect encoded powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'powershell'
    CommandLine|contains: '-enc'
  condition: selection
""",
        )
    )
    db.execute(
        text(
            """
            INSERT INTO memory_views (id, scope, key, value, updated_at)
            VALUES (:id, :scope, 'latest', :value, :updated_at)
            """
        ),
        {
            "id": f"mv-{spec_id}",
            "scope": f"{spec_id}:detection_spec.draft",
            "value": '{"version": 1, "payload": {"spec": "ready"}, "last_event_hash": "h1"}',
            "updated_at": "2026-05-23T00:00:00Z",
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
            "id": f"mv-rule-{spec_id}",
            "scope": f"{spec_id}:rule_generation.draft",
            "value": '{"version": 1, "payload": {"rule": "ready"}, "last_event_hash": "h2"}',
            "updated_at": "2026-05-23T00:00:01Z",
        },
    )
    db.add(
        ProofObligationRecordModel(
            id=f"po-{spec_id}-1",
            run_id=spec_id,
            rule_candidate_id=rule_id,
            claim_type="citation_faithful",
            claim_text="Citations are faithful.",
            required_artifact_types='["citation_verification"]',
            status="proven",
            justification=None,
        )
    )
    db.add(
        ProofObligationRecordModel(
            id=f"po-{spec_id}-2",
            run_id=spec_id,
            rule_candidate_id=rule_id,
            claim_type="not_overbroad",
            claim_text="Rule is not overbroad.",
            required_artifact_types='["false_positive_analysis"]',
            status="proven",
            justification=None,
        )
    )
    db.commit()


def _seed_ambiguous_abstain(db: Session, spec_id: str) -> None:
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-ambiguous",
            abstain_code="NO_EVIDENCE",
            abstain_context="No quote-backed behavior found",
            abstain_human_message="Cannot generate detection",
            is_validated=True,
        )
    )
    db.commit()


def test_e2e_positive_pipeline_reaches_awaiting_review() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "e2e-spec-positive"
    _seed_positive(db, spec_id=spec_id, rule_id="e2e-rule-positive")

    final_state = orchestrator.run_pipeline(spec_id)
    assert final_state == PipelineState.AWAITING_REVIEW


def test_e2e_ambiguous_report_abstains() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "e2e-spec-ambiguous"
    _seed_ambiguous_abstain(db, spec_id=spec_id)

    with pytest.raises(PipelineTransitionError, match="abstain"):
        orchestrator.run_pipeline(spec_id)


def test_deterministic_replay_same_input_same_transitions_and_idempotency() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "e2e-spec-replay"
    _seed_positive(db, spec_id=spec_id, rule_id="e2e-rule-replay")

    first = orchestrator.run_pipeline(spec_id)
    second = orchestrator.run_pipeline(spec_id)

    assert first == PipelineState.AWAITING_REVIEW
    assert second == PipelineState.AWAITING_REVIEW
    assert first == second

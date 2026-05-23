"""Integration tests for agent audit integrity verification."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from de_forge.core.hashing import snapshot_hash
from de_forge.db.base import Base
from de_forge.models import AgentRun as AgentRunModel
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.models import RefinementIteration as RefinementIterationModel
from de_forge.services.agent_audit import AgentAuditService, IntegrityError
from de_forge.services.orchestrator import PipelineOrchestrator, PipelineTransitionError


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_agent_run_read_fails_on_hash_mismatch() -> None:
    """Agent run read must fail when stored hash does not match snapshot content."""
    db = _build_session()
    service = AgentAuditService(db)

    # Seed agent run with mismatched hash
    run_id = "run-tampered"
    input_snapshot = {"prompt": "test", "context": "data"}
    output_snapshot = {"result": "output"}

    tampered_input_hash = "tampered-hash-value"

    db.add(
        AgentRunModel(
            id=run_id,
            run_id=run_id,
            trace_id="trace-123",
            agent_name="test-agent",
            input_hash=tampered_input_hash,
            output_hash=snapshot_hash(output_snapshot),
            status="completed",
            retry_attempt=0,
            started_at="2026-05-20T00:00:00Z",
        )
    )
    db.commit()

    # Attempt to load with verification
    with pytest.raises(IntegrityError, match="input hash mismatch"):
        service.load_agent_run_verified(run_id=run_id, input_snapshot=input_snapshot)


def test_agent_run_read_passes_on_valid_hashes() -> None:
    """Agent run read must succeed when stored hashes match snapshot content."""
    db = _build_session()
    service = AgentAuditService(db)

    # Seed agent run with correct hashes
    run_id = "run-valid"
    input_snapshot = {"prompt": "test", "context": "data"}
    output_snapshot = {"result": "output"}

    input_hash = snapshot_hash(input_snapshot)
    output_hash = snapshot_hash(output_snapshot)

    db.add(
        AgentRunModel(
            id=run_id,
            run_id=run_id,
            trace_id="trace-456",
            agent_name="test-agent",
            input_hash=input_hash,
            output_hash=output_hash,
            status="completed",
            retry_attempt=0,
            started_at="2026-05-20T00:00:00Z",
        )
    )
    db.commit()

    # Load with verification should succeed
    loaded = service.load_agent_run_verified(run_id=run_id, input_snapshot=input_snapshot)
    assert loaded.id == run_id
    assert loaded.input_hash == input_hash


def test_agent_run_persist_stores_hashes() -> None:
    """Agent run persistence must compute and store input/output hashes."""
    db = _build_session()
    service = AgentAuditService(db)

    input_snapshot = {"prompt": "persist test"}
    output_snapshot = {"result": "persist output"}

    run_id = service.persist_agent_run(
        run_id="run-persist",
        trace_id="trace-persist",
        agent_name="persist-agent",
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
        status="completed",
    )

    persisted = db.query(AgentRunModel).filter_by(id=run_id).one()
    assert persisted.input_hash == snapshot_hash(input_snapshot)
    assert persisted.output_hash == snapshot_hash(output_snapshot)


def test_pipeline_orchestrator_persists_agent_audit_records_per_stage() -> None:
    db = _build_session()
    spec_id = "spec-audit"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-audit",
            spec_payload='{"report_id":"report-audit","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
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
    db.commit()

    PipelineOrchestrator(db).run_pipeline(spec_id)

    runs = db.query(AgentRunModel).filter(AgentRunModel.run_id == spec_id).all()
    assert len(runs) >= 2
    assert {r.agent_name for r in runs} >= {"rule_generation", "static_validation"}


def test_pipeline_orchestrator_records_refinement_iteration_on_validation_failure() -> None:
    db = _build_session()
    spec_id = "spec-refine"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-refine",
            spec_payload='{"report_id":"report-refine","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"Image contains \'powershell\'"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRuleModel(
            id="rule-bad-refine",
            detection_spec_id=spec_id,
            rule_content="not-yaml",
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
    db.commit()

    with pytest.raises(PipelineTransitionError):
        PipelineOrchestrator(db).run_pipeline(spec_id)

    iterations = db.query(RefinementIterationModel).filter_by(rule_id="rule-bad-refine").all()
    assert len(iterations) == 1

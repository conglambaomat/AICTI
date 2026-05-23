"""Integration tests for orchestrator state transitions."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
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


def test_pipeline_positive_flow_reaches_awaiting_review() -> None:
    db = _build_session()
    orchestrator = PipelineOrchestrator(db)

    spec_id = "spec-ok"
    db.add(
        DetectionSpecModel(
            id=spec_id,
            report_id="report-ok",
            spec_payload='{"report_id":"report-ok","behavior_rules":[{"evidence":["e"],"attack_ids":["T1059.001"],"required_telemetry":["process_creation"],"detection_logic":"detect powershell"}],"false_positive_hypotheses":["fp"],"test_plan":"tp"}',
            is_validated=True,
        )
    )
    db.add(
        GeneratedRuleModel(
            id="rule-ok",
            detection_spec_id=spec_id,
            rule_content="""title: detect powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'powershell'
  condition: selection
""",
        )
    )
    db.commit()

    final_state = orchestrator.run_pipeline(spec_id)
    assert final_state == PipelineState.AWAITING_REVIEW


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

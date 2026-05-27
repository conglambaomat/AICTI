from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.models.base import Base
from de_forge.models.domain import (
    DetectionSpec,
    Evidence,
    Report,
    Review,
    Rule,
    Run,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def test_report_model_creation(db_session: Session) -> None:
    report = Report(
        report_id="rep_test123",
        source_type="txt",
        content="Sample threat report content",
        trace_id="trc_abc",
    )
    db_session.add(report)
    db_session.commit()

    retrieved = db_session.query(Report).filter_by(report_id="rep_test123").first()
    assert retrieved is not None
    assert retrieved.source_type == "txt"
    assert retrieved.content == "Sample threat report content"


def test_run_model_with_lineage(db_session: Session) -> None:
    report = Report(report_id="rep_test", source_type="txt", content="test", trace_id="trc_1")
    db_session.add(report)
    db_session.commit()

    run = Run(
        run_id="run_test123",
        report_id="rep_test",
        profile="balanced",
        status="completed",
        trace_id="trc_xyz",
    )
    db_session.add(run)
    db_session.commit()

    retrieved = db_session.query(Run).filter_by(run_id="run_test123").first()
    assert retrieved is not None
    assert retrieved.report_id == "rep_test"
    assert retrieved.profile == "balanced"
    assert retrieved.status == "completed"


def test_evidence_model_with_chunk_lineage(db_session: Session) -> None:
    report = Report(report_id="rep_test", source_type="txt", content="test", trace_id="trc_1")
    run = Run(
        run_id="run_test",
        report_id="rep_test",
        profile="balanced",
        status="running",
        trace_id="trc_2",
    )
    db_session.add_all([report, run])
    db_session.commit()

    evidence = Evidence(
        evidence_id="ev_test123",
        run_id="run_test",
        chunk_id="ch_abc",
        quote="malicious behavior observed",
        start_offset=100,
        end_offset=150,
    )
    db_session.add(evidence)
    db_session.commit()

    retrieved = db_session.query(Evidence).filter_by(evidence_id="ev_test123").first()
    assert retrieved is not None
    assert retrieved.chunk_id == "ch_abc"
    assert retrieved.quote == "malicious behavior observed"


def test_detection_spec_immutable_lineage(db_session: Session) -> None:
    report = Report(report_id="rep_test", source_type="txt", content="test", trace_id="trc_1")
    run = Run(
        run_id="run_test",
        report_id="rep_test",
        profile="balanced",
        status="running",
        trace_id="trc_2",
    )
    db_session.add_all([report, run])
    db_session.commit()

    spec = DetectionSpec(
        detection_spec_id="spec_test123",
        run_id="run_test",
        version=1,
        content={"behavior": "test"},
    )
    db_session.add(spec)
    db_session.commit()

    retrieved = db_session.query(DetectionSpec).filter_by(detection_spec_id="spec_test123").first()
    assert retrieved is not None
    assert retrieved.version == 1
    assert retrieved.content == {"behavior": "test"}


def test_rule_immutable_versioning(db_session: Session) -> None:
    report = Report(report_id="rep_test", source_type="txt", content="test", trace_id="trc_1")
    run = Run(
        run_id="run_test",
        report_id="rep_test",
        profile="balanced",
        status="running",
        trace_id="trc_2",
    )
    spec = DetectionSpec(detection_spec_id="spec_test", run_id="run_test", version=1, content={})
    db_session.add_all([report, run, spec])
    db_session.commit()

    rule_v1 = Rule(
        rule_id="rule_test123",
        detection_spec_id="spec_test",
        version=1,
        format="sigma",
        content="title: Test Rule v1",
    )
    db_session.add(rule_v1)
    db_session.commit()

    rule_v2 = Rule(
        rule_id="rule_test124",
        detection_spec_id="spec_test",
        version=2,
        content="title: Test Rule v2",
        format="sigma",
    )
    db_session.add(rule_v2)
    db_session.commit()

    all_rules = db_session.query(Rule).filter_by(detection_spec_id="spec_test").all()
    assert len(all_rules) == 2
    assert all_rules[0].version == 1
    assert all_rules[1].version == 2


def test_review_approval_lineage(db_session: Session) -> None:
    report = Report(report_id="rep_test", source_type="txt", content="test", trace_id="trc_1")
    run = Run(
        run_id="run_test",
        report_id="rep_test",
        profile="balanced",
        status="completed",
        trace_id="trc_2",
    )
    db_session.add_all([report, run])
    db_session.commit()

    review = Review(
        review_id="rev_test123",
        run_id="run_test",
        reviewer="analyst@example.com",
        decision="approved",
        comments="Looks good",
    )
    db_session.add(review)
    db_session.commit()

    retrieved = db_session.query(Review).filter_by(review_id="rev_test123").first()
    assert retrieved is not None
    assert retrieved.decision == "approved"
    assert retrieved.reviewer == "analyst@example.com"

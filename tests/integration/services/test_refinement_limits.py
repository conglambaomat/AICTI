"""Integration tests for bounded refinement limits."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import RefinementIteration as RefinementIterationModel
from de_forge.services.refinement import (
    MAX_DYNAMIC_REFINEMENT,
    MAX_QUERY_REFINEMENT,
    MAX_RULE_REFINEMENT,
    RefinementLimitExceededError,
    RefinementService,
)


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_query_refinement_stops_at_three_iterations() -> None:
    """Query refinement must stop at canonical limit of 3 iterations."""
    db = _build_session()
    service = RefinementService(db)

    detection_spec_id = "spec-query-limit"

    # First 3 iterations succeed
    for _ in range(MAX_QUERY_REFINEMENT):
        service.record_query_refinement(detection_spec_id=detection_spec_id)

    # Fourth iteration must fail
    with pytest.raises(RefinementLimitExceededError, match="query refinement limit"):
        service.record_query_refinement(detection_spec_id=detection_spec_id)


def test_rule_refinement_stops_at_two_iterations() -> None:
    """Rule refinement must stop at canonical limit of 2 iterations."""
    db = _build_session()
    service = RefinementService(db)

    rule_id = "rule-limit"

    # First 2 iterations succeed
    for _ in range(MAX_RULE_REFINEMENT):
        service.record_rule_refinement(rule_id=rule_id)

    # Third iteration must fail
    with pytest.raises(RefinementLimitExceededError, match="rule refinement limit"):
        service.record_rule_refinement(rule_id=rule_id)


def test_dynamic_refinement_stops_at_two_iterations() -> None:
    """Dynamic refinement must stop at canonical limit of 2 iterations."""
    db = _build_session()
    service = RefinementService(db)

    rule_id = "rule-dynamic-limit"

    # First 2 iterations succeed
    for _ in range(MAX_DYNAMIC_REFINEMENT):
        service.record_dynamic_refinement(rule_id=rule_id)

    # Third iteration must fail
    with pytest.raises(RefinementLimitExceededError, match="dynamic refinement limit"):
        service.record_dynamic_refinement(rule_id=rule_id)


def test_refinement_iterations_persist_with_lineage() -> None:
    """Refinement iterations must persist with detection_spec_id or rule_id lineage."""
    db = _build_session()
    service = RefinementService(db)

    detection_spec_id = "spec-persist"
    rule_id = "rule-persist"

    service.record_query_refinement(detection_spec_id=detection_spec_id)
    service.record_rule_refinement(rule_id=rule_id)

    # Verify persistence
    iterations = db.query(RefinementIterationModel).all()
    assert len(iterations) == 2

    spec_iteration = next(i for i in iterations if i.detection_spec_id == detection_spec_id)
    assert spec_iteration.detection_spec_id == detection_spec_id
    assert spec_iteration.rule_id is None

    rule_iteration = next(i for i in iterations if i.rule_id == rule_id)
    assert rule_iteration.rule_id == rule_id
    assert rule_iteration.detection_spec_id is None

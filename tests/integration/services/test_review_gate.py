"""Integration tests for human review gate and export policy."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import ReviewDecision as ReviewDecisionModel
from de_forge.services.review import ExportBlockedError, ReviewService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def test_export_blocked_without_human_approval() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-no-approval"

    with pytest.raises(ExportBlockedError, match="human approval required"):
        service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")


def test_append_only_review_decisions() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-append-only"
    first = service.record_decision(rule_id=rule_id, decision="rejected", reviewer="alice")
    second = service.record_decision(rule_id=rule_id, decision="approved", reviewer="bob")

    assert first != second

    rows = db.query(ReviewDecisionModel).filter_by(rule_id=rule_id).all()
    assert len(rows) == 2
    assert {row.id for row in rows} == {first, second}


def test_export_allowed_after_latest_approval() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-approved"
    service.record_decision(rule_id=rule_id, decision="approved", reviewer="carol")

    assert service.can_export(rule_status="awaiting_review", review_decision="approved") is True
    service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")

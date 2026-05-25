"""Integration tests for human review gate and export policy."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import ReviewDecision as ReviewDecisionModel
from de_forge.schemas.proof_obligation import (
    ProofObligation,
    ProofObligationStatus,
    ProofObligationType,
)
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

    with pytest.raises(ExportBlockedError, match="review handoff memory required"):
        service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")


def test_append_only_review_decisions() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-append-only"
    first = service.record_decision(
        rule_id=rule_id,
        decision="rejected",
        reviewer="alice",
        run_id=f"run-{rule_id}",
        comments="Rejected before approval.",
    )
    second = service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="bob",
        run_id="run-append-only",
        comments="Approved in append-only test.",
    )

    assert first != second

    rows = db.query(ReviewDecisionModel).filter_by(rule_id=rule_id).all()
    assert len(rows) == 2
    assert {row.id for row in rows} == {first, second}


def test_review_decision_requires_run_id() -> None:
    db = _build_session()
    service = ReviewService(db)

    with pytest.raises(TypeError):
        service.record_decision(
            rule_id="rule-missing-run",
            decision="approved",
            reviewer="analyst@example.com",
        )


def test_review_decision_persists_run_id_and_comments() -> None:
    db = _build_session()
    service = ReviewService(db)

    decision_id = service.record_decision(
        rule_id="rule-audit-fields",
        run_id="run-audit-fields",
        decision="approved",
        reviewer="analyst@example.com",
        comments="Evidence and proof obligations reviewed.",
    )

    row = db.query(ReviewDecisionModel).filter_by(id=decision_id).one()
    assert row.rule_id == "rule-audit-fields"
    assert row.run_id == "run-audit-fields"
    assert row.decision == "approved"
    assert row.reviewer == "analyst@example.com"
    assert row.comments == "Evidence and proof obligations reviewed."


def test_invalid_review_decision_is_rejected_before_persistence() -> None:
    db = _build_session()
    service = ReviewService(db)

    with pytest.raises(ValueError, match="invalid review decision"):
        service.record_decision(
            rule_id="rule-invalid-decision",
            run_id="run-invalid-decision",
            decision="maybe",
            reviewer="analyst@example.com",
            comments="Invalid decision must not persist.",
        )

    rows = db.query(ReviewDecisionModel).filter_by(rule_id="rule-invalid-decision").all()
    assert rows == []


def test_export_allowed_after_latest_approval() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-approved"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )

    assert service.can_export(rule_status="awaiting_review", review_decision="approved") is True
    service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")


def test_export_blocked_when_latest_decision_is_rejected() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-latest-rejected"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )
    service.record_decision(
        rule_id=rule_id,
        decision="rejected",
        reviewer="dave",
        run_id=f"run-{rule_id}",
        comments="Rejected after approval.",
    )

    with pytest.raises(ExportBlockedError, match="human approval required before export"):
        service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")

    latest = service._get_latest_decision(rule_id)
    assert latest is not None
    assert latest.rule_id == rule_id


def test_rejected_then_approved_replaces_latest_review_handoff_memory() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-rejected-then-approved"
    service.record_decision(
        rule_id=rule_id,
        decision="rejected",
        reviewer="alice",
        run_id=f"run-{rule_id}",
        comments="Rejected before approval.",
    )
    approved_decision_id = service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="bob",
        run_id=f"run-{rule_id}",
        comments="Approved after rejection.",
    )

    service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")

    rows = (
        db.execute(
            text(
                """
                SELECT value
                FROM memory_views
                WHERE scope = :scope AND key = 'latest'
                """
            ),
            {"scope": f"{rule_id}:review.handoff"},
        )
        .mappings()
        .all()
    )
    assert len(rows) == 1
    assert '"approved": true' in rows[0]["value"]
    assert f'"decision_id": "{approved_decision_id}"' in rows[0]["value"]


def _required_obligations(rule_id: str) -> list[ProofObligation]:
    return [
        ProofObligation(
            run_id="run-proof",
            rule_candidate_id=rule_id,
            claim_type=ProofObligationType.DETECTS_REPORT_BEHAVIOR,
            claim_text="Rule detects report behavior.",
            required_artifact_types=["evidence_quote"],
            status=ProofObligationStatus.PROVEN,
        ),
        ProofObligation(
            run_id="run-proof",
            rule_candidate_id=rule_id,
            claim_type=ProofObligationType.NOT_OVERBROAD,
            claim_text="Rule is not overbroad.",
            required_artifact_types=["false_positive_analysis"],
            status=ProofObligationStatus.PROVEN,
        ),
    ]


def test_export_blocked_when_proof_obligations_failed() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-proof-failed"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )

    obligations = _required_obligations(rule_id)
    obligations[0] = obligations[0].model_copy(update={"status": ProofObligationStatus.FAILED})

    with pytest.raises(ExportBlockedError, match="proof obligation"):
        service.assert_can_export(
            rule_id=rule_id,
            rule_status="awaiting_review",
            proof_obligations=obligations,
        )


def test_export_blocked_when_proof_obligations_unknown() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-proof-unknown"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )

    obligations = _required_obligations(rule_id)
    obligations[0] = obligations[0].model_copy(update={"status": ProofObligationStatus.UNKNOWN})

    with pytest.raises(ExportBlockedError, match="proof obligation"):
        service.assert_can_export(
            rule_id=rule_id,
            rule_status="awaiting_review",
            proof_obligations=obligations,
        )


def test_export_blocked_when_not_applicable_missing_justification() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-proof-no-justification"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )

    obligations = _required_obligations(rule_id)
    obligations[0] = obligations[0].model_copy(
        update={"status": ProofObligationStatus.NOT_APPLICABLE, "justification": None}
    )

    with pytest.raises(ExportBlockedError, match="proof obligation"):
        service.assert_can_export(
            rule_id=rule_id,
            rule_status="awaiting_review",
            proof_obligations=obligations,
        )


def test_export_allowed_when_not_applicable_has_justification() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-proof-justified"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )

    obligations = _required_obligations(rule_id)
    obligations[0] = obligations[0].model_copy(
        update={
            "status": ProofObligationStatus.NOT_APPLICABLE,
            "justification": "No telemetry in scope",
        }
    )

    service.assert_can_export(
        rule_id=rule_id,
        rule_status="awaiting_review",
        proof_obligations=obligations,
    )


def test_export_allowed_when_all_proof_obligations_proven() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-proof-proven"
    service.record_decision(
        rule_id=rule_id,
        decision="approved",
        reviewer="carol",
        run_id=f"run-{rule_id}",
        comments="Approved for export test.",
    )

    obligations = _required_obligations(rule_id)

    service.assert_can_export(
        rule_id=rule_id,
        rule_status="awaiting_review",
        proof_obligations=obligations,
    )


def test_rejected_decision_writes_non_approved_handoff_and_export_requires_approved_handoff() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-rejected-handoff"
    decision_id = service.record_decision(
        rule_id=rule_id,
        run_id="run-rejected-handoff",
        decision="rejected",
        reviewer="analyst@example.com",
        comments="Rejected handoff should not export.",
    )

    handoff = (
        db.execute(
            text(
                """
                SELECT value
                FROM memory_views
                WHERE scope = :scope AND key = 'latest'
                """
            ),
            {"scope": f"{rule_id}:review.handoff"},
        )
        .mappings()
        .one()
    )
    assert '"approved": true' not in handoff["value"]
    assert '"approved": false' in handoff["value"]
    assert '"decision": "rejected"' in handoff["value"]
    assert f'"decision_id": "{decision_id}"' in handoff["value"]

    with pytest.raises(ExportBlockedError, match="human approval required before export"):
        service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")


def test_substring_scope_spoofing_does_not_satisfy_target_rule_handoff() -> None:
    db = _build_session()
    service = ReviewService(db)

    target_rule_id = "rule-target"
    spoof_rule_id = "prefix-rule-target-suffix"
    service.record_decision(
        rule_id=spoof_rule_id,
        decision="approved",
        reviewer="analyst@example.com",
        run_id="run-spoof-rule",
        comments="Spoof attempt approval.",
    )

    with pytest.raises(ExportBlockedError, match="review handoff memory required"):
        service.assert_can_export(rule_id=target_rule_id, rule_status="awaiting_review")


class _ProofLookupFailingSession:
    def __init__(self, db: Session) -> None:
        self._db = db

    def __getattr__(self, name: str):
        return getattr(self._db, name)

    def execute(self, statement, params=None, *args, **kwargs):
        if "FROM proof_obligations" in str(statement):
            raise SQLAlchemyError("simulated proof obligation lookup failure")
        return self._db.execute(statement, params or {}, *args, **kwargs)


def test_proof_obligation_lookup_error_blocks_export_fail_closed() -> None:
    db = _build_session()
    ReviewService(db).record_decision(
        rule_id="rule-proof-lookup-error",
        decision="approved",
        reviewer="analyst@example.com",
        run_id="run-proof-lookup-error",
        comments="Approved before proof lookup failure.",
    )
    service = ReviewService(_ProofLookupFailingSession(db))

    with pytest.raises(ExportBlockedError, match="proof obligation gate failed"):
        service.assert_can_export(
            rule_id="rule-proof-lookup-error",
            rule_status="awaiting_review",
        )

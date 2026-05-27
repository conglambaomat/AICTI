from de_forge.schemas.review import ReviewAction, ReviewRequest
from de_forge.services.review import ReviewService


def test_review_service_records_approval_decision() -> None:
    request = ReviewRequest(
        run_id="run_1",
        rule_candidate_id="candidate_1",
        action=ReviewAction.APPROVE,
        reviewer_notes="Looks good",
    )

    decision = ReviewService().decide(request)

    assert decision.action == ReviewAction.APPROVE
    assert decision.export_allowed is False


def test_review_service_blocks_export_on_reject() -> None:
    request = ReviewRequest(
        run_id="run_1",
        rule_candidate_id="candidate_1",
        action=ReviewAction.REJECT,
        reviewer_notes="Too broad",
    )

    decision = ReviewService().decide(request)

    assert decision.export_allowed is False

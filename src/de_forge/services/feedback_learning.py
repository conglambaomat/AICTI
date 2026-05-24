from __future__ import annotations

from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.feedback import FeedbackDecision, ReviewFeedback
from de_forge.schemas.regression import RegressionTest


class FeedbackLearningService:
    def to_regression_test(self, feedback: ReviewFeedback) -> RegressionTest:
        regression_type = (
            "must_still_pass" if feedback.decision == FeedbackDecision.ACCEPT else "do_not_repeat"
        )
        payload = feedback.model_dump(mode="json")
        return RegressionTest(
            id=f"regression_{snapshot_hash(payload)[:16]}",
            regression_type=regression_type,
            pattern=feedback.pattern,
            source_rule_candidate_id=feedback.rule_candidate_id,
            reason=feedback.reason,
        )

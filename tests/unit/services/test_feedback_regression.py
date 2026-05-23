import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.feedback import FeedbackDecision, ReviewFeedback
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.feedback_learning import FeedbackLearningService
from de_forge.services.regression import RegressionService


def sample_sigma_rule() -> SigmaRule:
    return SigmaRule(
        title="Suspicious Encoded PowerShell Command",
        id="rule_1",
        status="experimental",
        description="Detects encoded PowerShell command execution.",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}, "condition": "selection_1"},
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )


def test_rejected_feedback_becomes_do_not_repeat_regression() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_1",
        decision=FeedbackDecision.REJECT,
        reason="overbroad PowerShell process-name-only rule",
        pattern="powershell_process_name_only",
    )

    regression = FeedbackLearningService().to_regression_test(feedback)

    assert regression.regression_type == "do_not_repeat"
    assert regression.pattern == "powershell_process_name_only"


def test_regression_service_blocks_rejected_pattern() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_1",
        decision=FeedbackDecision.REJECT,
        reason="overbroad PowerShell process-name-only rule",
        pattern="powershell_process_name_only",
    )
    regression = FeedbackLearningService().to_regression_test(feedback)

    with pytest.raises(ValidationGateError):
        RegressionService([regression]).assert_candidate_safe(
            candidate_patterns=["powershell_process_name_only"],
            rule=sample_sigma_rule(),
        )


def test_regression_service_allows_candidate_without_rejected_pattern() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_1",
        decision=FeedbackDecision.REJECT,
        reason="overbroad PowerShell process-name-only rule",
        pattern="powershell_process_name_only",
    )
    regression = FeedbackLearningService().to_regression_test(feedback)

    assert (
        RegressionService([regression]).assert_candidate_safe(
            candidate_patterns=["encoded_command_behavior"],
            rule=sample_sigma_rule(),
        )
        is True
    )

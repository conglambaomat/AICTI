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


def test_accepted_feedback_does_not_block_same_pattern() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_2",
        decision=FeedbackDecision.ACCEPT,
        reason="pattern is precise and evidence-backed",
        pattern="encoded_command_behavior",
    )
    regression = FeedbackLearningService().to_regression_test(feedback)

    assert (
        RegressionService([regression]).assert_candidate_safe(
            candidate_patterns=["encoded_command_behavior"],
            rule=sample_sigma_rule(),
        )
        is True
    )


def test_multiple_regressions_block_if_any_rejected_pattern_reappears() -> None:
    reject_feedback = ReviewFeedback(
        rule_candidate_id="candidate_3",
        decision=FeedbackDecision.REJECT,
        reason="known noisy pattern",
        pattern="noisy_parent_image",
    )
    accept_feedback = ReviewFeedback(
        rule_candidate_id="candidate_4",
        decision=FeedbackDecision.ACCEPT,
        reason="known good pattern",
        pattern="encoded_command_behavior",
    )

    regressions = [
        FeedbackLearningService().to_regression_test(reject_feedback),
        FeedbackLearningService().to_regression_test(accept_feedback),
    ]

    with pytest.raises(ValidationGateError, match="repeats rejected pattern noisy_parent_image"):
        RegressionService(regressions).assert_candidate_safe(
            candidate_patterns=["encoded_command_behavior", "noisy_parent_image"],
            rule=sample_sigma_rule(),
        )


def test_feedback_learning_generates_stable_regression_id_for_same_feedback() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_5",
        decision=FeedbackDecision.REJECT,
        reason="too broad",
        pattern="broad_rule_pattern",
    )

    first = FeedbackLearningService().to_regression_test(feedback)
    second = FeedbackLearningService().to_regression_test(feedback)

    assert first.id == second.id
    assert first.id.startswith("regression_")

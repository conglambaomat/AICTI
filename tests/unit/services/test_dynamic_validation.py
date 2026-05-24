from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.schemas.test_event import ValidationEvent
from de_forge.services.adversarial_validation import AdversarialValidationService
from de_forge.services.counterfactual_evaluation import CounterfactualEvaluationService
from de_forge.services.dynamic_validation import DynamicValidationService


def encoded_rule() -> SigmaRule:
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


def test_dynamic_validation_matches_positive_event() -> None:
    event = ValidationEvent(
        id="event_attack_1", fields={"CommandLine": "powershell.exe -enc AAA"}, expected_match=True
    )

    result = DynamicValidationService().evaluate(
        encoded_rule(), positive_events=[event], benign_events=[]
    )

    assert result.true_positives == 1
    assert result.false_negatives == 0
    assert result.recall == 1.0


def test_dynamic_validation_counts_benign_false_positive() -> None:
    benign = ValidationEvent(
        id="event_benign_1",
        fields={"CommandLine": "powershell.exe -enc benign_admin"},
        expected_match=False,
    )

    result = DynamicValidationService().evaluate(
        encoded_rule(), positive_events=[], benign_events=[benign]
    )

    assert result.false_positives == 1
    assert result.precision == 0.0


def test_adversarial_validation_scores_variant_matches() -> None:
    variants = [
        ValidationEvent(
            id="variant_1", fields={"CommandLine": "pwsh.exe -enc AAA"}, expected_match=True
        ),
        ValidationEvent(
            id="variant_2",
            fields={"CommandLine": "powershell.exe -EncodedCommand AAA"},
            expected_match=True,
        ),
    ]

    result = AdversarialValidationService().evaluate(encoded_rule(), variants)

    assert result.total_variants == 2
    assert result.matched_variants == 1
    assert result.robustness_score == 0.5


def test_counterfactual_evaluation_reports_condition_importance() -> None:
    result = CounterfactualEvaluationService().evaluate_condition_importance(
        encoded_rule(),
        positive_events=[
            ValidationEvent(
                id="event_attack_1",
                fields={"CommandLine": "powershell.exe -enc AAA"},
                expected_match=True,
            )
        ],
        benign_events=[
            ValidationEvent(
                id="event_benign_1",
                fields={"CommandLine": "powershell.exe normal"},
                expected_match=False,
            )
        ],
    )

    assert result["selection_1"] == "important"


def test_dynamic_validation_respects_and_condition_across_selections() -> None:
    rule = SigmaRule(
        title="rule and",
        id="rule_and",
        status="experimental",
        description="",
        references=[],
        tags=[],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={
            "selection_1": {"CommandLine|contains": ["-enc"]},
            "selection_2": {"Image|contains": ["powershell.exe"]},
            "condition": "selection_1 and selection_2",
        },
        falsepositives=[],
        level="medium",
        provenance={},
    )

    result = DynamicValidationService().evaluate(
        rule,
        positive_events=[
            ValidationEvent(
                id="event_attack_1",
                fields={"CommandLine": "powershell.exe -enc AAA", "Image": "powershell.exe"},
                expected_match=True,
            )
        ],
        benign_events=[
            ValidationEvent(
                id="event_benign_1",
                fields={"CommandLine": "powershell.exe -enc AAA", "Image": "cmd.exe"},
                expected_match=False,
            )
        ],
    )

    assert result.true_positives == 1
    assert result.false_positives == 0


def test_dynamic_validation_respects_or_condition_across_selections() -> None:
    rule = SigmaRule(
        title="rule or",
        id="rule_or",
        status="experimental",
        description="",
        references=[],
        tags=[],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={
            "selection_1": {"CommandLine|contains": ["-enc"]},
            "selection_2": {"Image|contains": ["pwsh.exe"]},
            "condition": "selection_1 or selection_2",
        },
        falsepositives=[],
        level="medium",
        provenance={},
    )

    result = DynamicValidationService().evaluate(
        rule,
        positive_events=[
            ValidationEvent(
                id="event_attack_1",
                fields={"CommandLine": "cmd.exe /c whoami", "Image": "pwsh.exe"},
                expected_match=True,
            )
        ],
        benign_events=[],
    )

    assert result.true_positives == 1


def test_dynamic_validation_raises_for_invalid_condition_reference() -> None:
    rule = SigmaRule(
        title="rule invalid",
        id="rule_invalid",
        status="experimental",
        description="",
        references=[],
        tags=[],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={
            "selection_1": {"CommandLine|contains": ["-enc"]},
            "condition": "selection_1 and selection_missing",
        },
        falsepositives=[],
        level="medium",
        provenance={},
    )

    try:
        DynamicValidationService().evaluate(
            rule,
            positive_events=[
                ValidationEvent(
                    id="event_attack_invalid_ref",
                    fields={"CommandLine": "powershell.exe -enc AAA"},
                    expected_match=True,
                )
            ],
            benign_events=[],
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Unknown selection in condition" in str(exc)


def test_dynamic_validation_raises_for_unsupported_condition_shape() -> None:
    rule = SigmaRule(
        title="rule unsupported",
        id="rule_unsupported",
        status="experimental",
        description="",
        references=[],
        tags=[],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={
            "selection_1": {"CommandLine|contains": ["-enc"]},
            "condition": "selection_1 and (selection_2 or selection_3)",
        },
        falsepositives=[],
        level="medium",
        provenance={},
    )

    try:
        DynamicValidationService().evaluate(
            rule,
            positive_events=[
                ValidationEvent(
                    id="event_attack_unsupported_shape",
                    fields={"CommandLine": "powershell.exe -enc AAA"},
                    expected_match=True,
                )
            ],
            benign_events=[],
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "Unsupported condition" in str(exc)

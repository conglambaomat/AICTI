from de_forge.schemas.oracle import OracleCase
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.oracle_evaluation import OracleEvaluationService


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


def test_oracle_evaluation_scores_expected_technique_and_telemetry() -> None:
    oracle = OracleCase(
        id="oracle_1",
        expected_techniques=["T1059.001"],
        expected_behaviors=["encoded PowerShell execution"],
        expected_telemetry=["process_creation"],
        expected_positive_event_ids=["event_attack_1"],
        must_not_match_benign_event_ids=["event_benign_1"],
        expected_logic_family=["suspicious_commandline_argument"],
    )

    result = OracleEvaluationService().evaluate(
        rule=encoded_rule(),
        oracle=oracle,
        matched_positive_event_ids=["event_attack_1"],
        matched_benign_event_ids=[],
        logic_family="suspicious_commandline_argument",
    )

    assert result.technique_score == 1.0
    assert result.telemetry_score == 1.0
    assert result.event_score == 1.0
    assert result.overall_score == 1.0


def test_oracle_evaluation_penalizes_benign_match() -> None:
    oracle = OracleCase(
        id="oracle_1",
        expected_techniques=["T1059.001"],
        expected_behaviors=["encoded PowerShell execution"],
        expected_telemetry=["process_creation"],
        expected_positive_event_ids=["event_attack_1"],
        must_not_match_benign_event_ids=["event_benign_1"],
        expected_logic_family=["suspicious_commandline_argument"],
    )

    result = OracleEvaluationService().evaluate(
        rule=encoded_rule(),
        oracle=oracle,
        matched_positive_event_ids=["event_attack_1"],
        matched_benign_event_ids=["event_benign_1"],
        logic_family="suspicious_commandline_argument",
    )

    assert result.benign_avoidance_score == 0.0
    assert result.overall_score < 1.0

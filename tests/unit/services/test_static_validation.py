from de_forge.schemas.rule_candidate import CandidateScore, CandidateType, RuleCandidate
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.broad_rule_detector import BroadRuleDetector
from de_forge.services.portfolio_service import PortfolioService
from de_forge.services.static_validation import StaticValidationService


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


def test_rule_candidate_tracks_type_rule_and_score() -> None:
    candidate = RuleCandidate(
        id="candidate_1",
        detection_spec_id="spec_1",
        candidate_type=CandidateType.HIGH_PRECISION,
        sigma_rule=sample_sigma_rule(),
        score=CandidateScore(evidence_support=1.0, citation_faithfulness=1.0, telemetry_fit=1.0),
        passed_static_validation=False,
    )

    assert candidate.candidate_type == CandidateType.HIGH_PRECISION
    assert candidate.score.evidence_support == 1.0


def test_portfolio_service_wraps_sigma_rule_as_candidate() -> None:
    candidate = PortfolioService().create_candidate(
        detection_spec_id="spec_1",
        candidate_type=CandidateType.BALANCED,
        sigma_rule=sample_sigma_rule(),
    )

    assert candidate.id.startswith("candidate_")
    assert candidate.candidate_type == CandidateType.BALANCED
    assert candidate.score.citation_faithfulness == 1.0


def test_broad_rule_detector_flags_single_process_name_powershell_rule() -> None:
    rule = SigmaRule(
        title="Too Broad PowerShell",
        id="rule_broad",
        status="experimental",
        description="too broad",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={
            "selection_1": {"Image|contains": ["powershell.exe"]},
            "condition": "selection_1",
        },
        falsepositives=["many admin scripts"],
        level="low",
        provenance={"selection_1": ["evidence_1"]},
    )

    assert BroadRuleDetector().is_overbroad(rule) is True


def test_static_validation_passes_precise_encoded_command_rule() -> None:
    candidate = PortfolioService().create_candidate(
        "spec_1", CandidateType.HIGH_PRECISION, sample_sigma_rule()
    )

    validated = StaticValidationService().validate(candidate)

    assert validated.passed_static_validation is True
    assert validated.score.static_validity == 1.0


def test_static_validation_fails_overbroad_rule() -> None:
    rule = SigmaRule(
        title="Too Broad PowerShell",
        id="rule_broad",
        status="experimental",
        description="too broad",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={
            "selection_1": {"Image|contains": ["powershell.exe"]},
            "condition": "selection_1",
        },
        falsepositives=["many admin scripts"],
        level="low",
        provenance={"selection_1": ["evidence_1"]},
    )
    candidate = PortfolioService().create_candidate("spec_1", CandidateType.BALANCED, rule)

    validated = StaticValidationService().validate(candidate)

    assert validated.passed_static_validation is False
    assert validated.score.false_positive_risk == 1.0


def test_static_validation_service_db_mode_still_works() -> None:
    assert callable(StaticValidationService.validate_rule)


def test_validate_retrieval_faithfulness_still_exported() -> None:
    from de_forge.services.static_validation import validate_retrieval_faithfulness

    result = validate_retrieval_faithfulness([], {}, [])
    assert result["valid"] is True
    assert result["errors"] == []

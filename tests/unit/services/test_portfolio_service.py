from __future__ import annotations

import pytest

from de_forge.schemas.rule_candidate import CandidateScore, CandidateType
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.portfolio_service import PortfolioService


def _sigma_rule() -> SigmaRule:
    return SigmaRule(
        title="candidate",
        id="rule-1",
        status="experimental",
        description="candidate rule",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection": {"Image|contains": "powershell"}, "condition": "selection"},
        falsepositives=["admin script"],
        level="medium",
        provenance={"evidence_ids": ["ev-1"]},
    )


def test_candidate_score_has_required_sota_dimensions() -> None:
    score = CandidateScore(
        evidence_support=0.9,
        citation_faithfulness=0.95,
        telemetry_fit=0.9,
        static_validity=1.0,
        false_positive_risk=0.2,
    )

    score_dict = score.model_dump()

    assert "adversarial_robustness" in score_dict
    assert "counterfactual_stability" in score_dict
    assert "oracle_alignment" in score_dict
    assert "regression_safety" in score_dict
    assert "explainability" in score_dict


def test_candidate_score_has_penalty_dimensions() -> None:
    score = CandidateScore(
        evidence_support=0.9,
        citation_faithfulness=0.95,
        telemetry_fit=0.9,
        static_validity=1.0,
        false_positive_risk=0.2,
    )

    score_dict = score.model_dump()

    assert "overbreadth_penalty" in score_dict
    assert "complexity_penalty" in score_dict
    assert "drift_risk_penalty" in score_dict


def test_portfolio_service_rejects_candidate_without_required_score_dimensions() -> None:
    service = PortfolioService()
    candidate = service.create_candidate(
        detection_spec_id="spec-1",
        candidate_type=CandidateType.BALANCED,
        sigma_rule=_sigma_rule(),
    )

    with pytest.raises(ValueError, match="missing required score dimensions"):
        service.validate_candidate_ranking_readiness(candidate)


def test_portfolio_service_rejects_candidate_when_penalties_missing() -> None:
    service = PortfolioService()
    candidate = service.create_candidate(
        detection_spec_id="spec-1",
        candidate_type=CandidateType.BALANCED,
        sigma_rule=_sigma_rule(),
    )
    candidate.score = CandidateScore(
        evidence_support=0.9,
        citation_faithfulness=0.95,
        telemetry_fit=0.9,
        adversarial_robustness=0.8,
        counterfactual_stability=0.8,
        oracle_alignment=0.8,
        regression_safety=0.8,
        explainability=0.8,
    )

    with pytest.raises(ValueError, match="missing required penalties"):
        service.validate_candidate_ranking_readiness(candidate)

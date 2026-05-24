from __future__ import annotations

from de_forge.schemas.oracle import OracleCase, OracleEvaluationResult
from de_forge.schemas.sigma import SigmaRule


class OracleEvaluationService:
    def evaluate(
        self,
        rule: SigmaRule,
        oracle: OracleCase,
        matched_positive_event_ids: list[str],
        matched_benign_event_ids: list[str],
        logic_family: str,
    ) -> OracleEvaluationResult:
        rule_techniques = {
            tag.removeprefix("attack.").upper() for tag in rule.tags if tag.startswith("attack.")
        }
        technique_score = 1.0 if set(oracle.expected_techniques).issubset(rule_techniques) else 0.0
        telemetry_score = 1.0 if rule.logsource.category in oracle.expected_telemetry else 0.0

        expected_positive = set(oracle.expected_positive_event_ids)
        event_score = (
            len(expected_positive.intersection(matched_positive_event_ids)) / len(expected_positive)
            if expected_positive
            else 1.0
        )

        forbidden = set(oracle.must_not_match_benign_event_ids)
        benign_avoidance_score = 0.0 if forbidden.intersection(matched_benign_event_ids) else 1.0
        logic_family_score = 1.0 if logic_family in oracle.expected_logic_family else 0.0

        scores = [
            technique_score,
            telemetry_score,
            event_score,
            benign_avoidance_score,
            logic_family_score,
        ]
        return OracleEvaluationResult(
            technique_score=technique_score,
            telemetry_score=telemetry_score,
            event_score=event_score,
            benign_avoidance_score=benign_avoidance_score,
            logic_family_score=logic_family_score,
            overall_score=sum(scores) / len(scores),
        )

from __future__ import annotations

from typing import Any

from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.rule_candidate import CandidateScore, CandidateType, RuleCandidate
from de_forge.schemas.sigma import SigmaRule


class PortfolioService:
    def create_candidate(
        self,
        detection_spec_id: str,
        candidate_type: CandidateType,
        sigma_rule: SigmaRule,
    ) -> RuleCandidate:
        payload: dict[str, Any] = {
            "spec": detection_spec_id,
            "type": candidate_type.value,
            "rule": sigma_rule.model_dump(mode="json"),
        }
        return RuleCandidate(
            id=f"candidate_{snapshot_hash(payload)[:16]}",
            detection_spec_id=detection_spec_id,
            candidate_type=candidate_type,
            sigma_rule=sigma_rule,
            score=CandidateScore(
                evidence_support=1.0, citation_faithfulness=1.0, telemetry_fit=1.0
            ),
            passed_static_validation=False,
        )

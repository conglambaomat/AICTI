from __future__ import annotations


class MetricsService:
    def quality_snapshot(
        self,
        citation_faithfulness: float,
        proof_pass_rate: float,
        static_validity_rate: float,
        regression_pass_rate: float,
    ) -> dict[str, float]:
        values = [
            citation_faithfulness,
            proof_pass_rate,
            static_validity_rate,
            regression_pass_rate,
        ]
        return {
            "citation_faithfulness": citation_faithfulness,
            "proof_pass_rate": proof_pass_rate,
            "static_validity_rate": static_validity_rate,
            "regression_pass_rate": regression_pass_rate,
            "overall_quality": round(sum(values) / len(values), 4),
        }

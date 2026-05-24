from de_forge.services.metrics import MetricsService


def test_metrics_service_summarizes_quality_snapshot() -> None:
    summary = MetricsService().quality_snapshot(
        citation_faithfulness=1.0,
        proof_pass_rate=0.9,
        static_validity_rate=0.95,
        regression_pass_rate=1.0,
    )

    assert summary["citation_faithfulness"] == 1.0
    assert summary["overall_quality"] == 0.9625

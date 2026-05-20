from __future__ import annotations

import pytest

from de_forge.services.kpi_evaluator import KPIEvaluator


def _thresholds() -> dict[str, dict[str, float]]:
    return {
        "evidence_extraction": {"recall": 0.85, "precision": 0.80},
        "attack_mapping": {"accuracy": 0.90},
        "rule_quality": {"precision": 0.75, "recall": 0.70, "f1": 0.72},
        "abstain_quality": {"precision": 0.80, "coverage": 0.15},
        "cost_budget": {"max_cost_usd": 5.0},
        "latency_budget": {"max_latency_seconds": 120.0},
    }


def _metrics() -> dict[str, dict[str, float]]:
    return {
        "evidence_extraction": {"recall": 0.90, "precision": 0.85},
        "attack_mapping": {"accuracy": 0.92},
        "rule_quality": {"precision": 0.78, "recall": 0.73, "f1": 0.75},
        "abstain_quality": {"precision": 0.82, "coverage": 0.12},
        "cost_budget": {"max_cost_usd": 3.5},
        "latency_budget": {"max_latency_seconds": 95.0},
    }


def test_evaluate_kpis_returns_pass_when_all_thresholds_met() -> None:
    evaluator = KPIEvaluator()
    result = evaluator.evaluate_kpis(
        metrics=_metrics(),
        thresholds=_thresholds(),
        profile="balanced",
    )

    assert result["pass"] is True
    assert result["profile"] == "balanced"
    assert result["failures"] == []
    assert result["summary"]


def test_evaluate_kpis_returns_fail_when_threshold_violated() -> None:
    evaluator = KPIEvaluator()
    bad_metrics = _metrics()
    bad_metrics["evidence_extraction"]["recall"] = 0.70

    result = evaluator.evaluate_kpis(
        metrics=bad_metrics,
        thresholds=_thresholds(),
        profile="strict",
    )

    assert result["pass"] is False
    assert result["profile"] == "strict"
    assert len(result["failures"]) > 0
    assert any("evidence_extraction" in f["category"] for f in result["failures"])


def test_evaluate_kpis_rejects_missing_category() -> None:
    evaluator = KPIEvaluator()
    incomplete_metrics = dict(_metrics())
    incomplete_metrics.pop("attack_mapping")

    with pytest.raises(ValueError, match="Missing required KPI category"):
        evaluator.evaluate_kpis(
            metrics=incomplete_metrics,
            thresholds=_thresholds(),
            profile="balanced",
        )


def test_evaluate_kpis_rejects_missing_metric_key() -> None:
    evaluator = KPIEvaluator()
    incomplete_metrics = _metrics()
    incomplete_metrics["rule_quality"].pop("f1")

    with pytest.raises(ValueError, match="Missing required metric"):
        evaluator.evaluate_kpis(
            metrics=incomplete_metrics,
            thresholds=_thresholds(),
            profile="balanced",
        )

from __future__ import annotations

import pytest

from de_forge.services.canary_ops import CanaryOpsService


def _kpi_pass_result() -> dict[str, object]:
    return {
        "pass": True,
        "profile": "balanced",
        "failures": [],
        "summary": "All KPI thresholds satisfied",
    }


def _kpi_fail_result() -> dict[str, object]:
    return {
        "pass": False,
        "profile": "balanced",
        "failures": [
            {
                "category": "rule_quality",
                "metric": "f1",
                "actual": 0.61,
                "required": 0.72,
                "operator": ">=",
            }
        ],
        "summary": "KPI threshold violations detected",
    }


def test_evaluate_canary_allows_promotion_when_gates_pass() -> None:
    service = CanaryOpsService()

    result = service.evaluate_canary(
        kpi_result=_kpi_pass_result(),
        baseline_delta_pass=True,
        profile="balanced",
    )

    assert result["action"] == "promote"
    assert result["rollback_required"] is False
    assert result["reason_code"] == "CANARY_PASS"


def test_evaluate_canary_triggers_rollback_when_kpi_fails() -> None:
    service = CanaryOpsService()

    result = service.evaluate_canary(
        kpi_result=_kpi_fail_result(),
        baseline_delta_pass=True,
        profile="strict",
    )

    assert result["action"] == "rollback"
    assert result["rollback_required"] is True
    assert result["reason_code"] == "KPI_GATE_FAIL"


def test_evaluate_canary_triggers_rollback_when_baseline_delta_fails() -> None:
    service = CanaryOpsService()

    result = service.evaluate_canary(
        kpi_result=_kpi_pass_result(),
        baseline_delta_pass=False,
        profile="balanced",
    )

    assert result["action"] == "rollback"
    assert result["rollback_required"] is True
    assert result["reason_code"] == "BASELINE_DELTA_FAIL"


def test_evaluate_canary_rejects_invalid_kpi_result_shape() -> None:
    service = CanaryOpsService()

    with pytest.raises(ValueError, match="kpi_result missing required key"):
        service.evaluate_canary(
            kpi_result={"profile": "balanced"},
            baseline_delta_pass=True,
            profile="balanced",
        )

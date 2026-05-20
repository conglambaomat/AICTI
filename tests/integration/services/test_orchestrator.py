from __future__ import annotations

import pytest

from de_forge.services.orchestrator import OrchestratorService


def _telemetry_registry() -> dict[str, list[str]]:
    return {"process_creation": ["Image", "CommandLine"]}


def test_run_pipeline_returns_abstain_when_no_evidence_extracted() -> None:
    service = OrchestratorService()

    result = service.run_pipeline(
        report_text="benign text",
        profile="balanced",
        telemetry_registry=_telemetry_registry(),
        baseline_delta_pass=True,
        validation_issues=[],
        iteration=1,
    )

    assert result["abstain"] is True
    assert result["stage"] == "evidence"
    assert "reason" in result


def test_run_pipeline_returns_rollout_decision_with_rule_when_all_gates_pass() -> None:
    service = OrchestratorService()

    result = service.run_pipeline(
        report_text="PowerShell -enc command launches",
        profile="balanced",
        telemetry_registry=_telemetry_registry(),
        baseline_delta_pass=True,
        validation_issues=[],
        iteration=1,
    )

    assert result["abstain"] is False
    assert result["sigma_rule"]
    assert result["canary"]["action"] == "promote"


def test_run_pipeline_rolls_back_when_baseline_delta_fails() -> None:
    service = OrchestratorService()

    result = service.run_pipeline(
        report_text="PowerShell -enc command launches",
        profile="balanced",
        telemetry_registry=_telemetry_registry(),
        baseline_delta_pass=False,
        validation_issues=[],
        iteration=1,
    )

    assert result["abstain"] is False
    assert result["canary"]["action"] == "rollback"
    assert result["canary"]["reason_code"] == "BASELINE_DELTA_FAIL"


def test_run_pipeline_rejects_empty_report_text() -> None:
    service = OrchestratorService()

    with pytest.raises(ValueError, match="report_text must not be empty"):
        service.run_pipeline(
            report_text="",
            profile="balanced",
            telemetry_registry=_telemetry_registry(),
            baseline_delta_pass=True,
            validation_issues=[],
            iteration=1,
        )

from __future__ import annotations

from de_forge.schemas.run import RunMode, RunState
from de_forge.services.orchestrator import Orchestrator


def test_run_golden_path_auto_reaches_awaiting_review() -> None:
    orchestrator = Orchestrator()

    result = orchestrator.run_golden_path(
        report_id="report-auto",
        report_text="PowerShell -enc command launches",
        mode=RunMode.AUTO,
    )

    assert result.report_id == "report-auto"
    assert result.state == RunState.AWAITING_REVIEW


def test_run_golden_path_cautious_stops_at_detection_spec_ready() -> None:
    orchestrator = Orchestrator()

    result = orchestrator.run_golden_path(
        report_id="report-cautious",
        report_text="PowerShell -enc command launches",
        mode=RunMode.CAUTIOUS,
    )

    assert result.report_id == "report-cautious"
    assert result.state == RunState.DETECTION_SPEC_READY

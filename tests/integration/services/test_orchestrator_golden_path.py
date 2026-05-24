from de_forge.schemas.run import RunMode, RunState
from de_forge.services.orchestrator import Orchestrator


def test_orchestrator_auto_mode_reaches_awaiting_review_for_golden_path() -> None:
    orchestrator = Orchestrator()

    result = orchestrator.run_golden_path(
        report_id="report_1",
        report_text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        mode=RunMode.AUTO,
    )

    assert result.state == RunState.AWAITING_REVIEW
    assert result.report_id == "report_1"


def test_orchestrator_cautious_mode_pauses_at_detection_spec() -> None:
    orchestrator = Orchestrator()

    result = orchestrator.run_golden_path(
        report_id="report_1",
        report_text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        mode=RunMode.CAUTIOUS,
    )

    assert result.state == RunState.DETECTION_SPEC_READY

"""Unit tests for orchestration gate predicates."""

from de_forge.services.gates import can_generate_rule, has_required_lineage_fields


def test_rule_generation_gate_requires_validated_detection_spec() -> None:
    """Rule generation must only proceed when DetectionSpec is validated."""
    assert can_generate_rule("validated") is True
    assert can_generate_rule("draft") is False
    assert can_generate_rule("reviewed") is False
    assert can_generate_rule("") is False


def test_stage_gate_fails_without_lineage_fields() -> None:
    """Stage gate must fail when required lineage fields are missing."""
    complete_lineage = {
        "report_id": "report-1",
        "trace_id": "trace-1",
        "run_id": "run-1",
        "agent_run_id": "agent-run-1",
    }
    assert has_required_lineage_fields(complete_lineage) is True

    missing_report = {
        "trace_id": "trace-1",
        "run_id": "run-1",
        "agent_run_id": "agent-run-1",
    }
    assert has_required_lineage_fields(missing_report) is False

    blank_trace = {
        "report_id": "report-1",
        "trace_id": "   ",
        "run_id": "run-1",
        "agent_run_id": "agent-run-1",
    }
    assert has_required_lineage_fields(blank_trace) is False

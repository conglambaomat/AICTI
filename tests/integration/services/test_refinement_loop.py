from __future__ import annotations

from de_forge.services.refinement import RefinementController


def _rule() -> dict[str, object]:
    return {
        "title": "Test Rule",
        "detection": {"selection": {"Image": "test.exe"}, "condition": "selection"},
    }


def _validation_issues() -> list[dict[str, object]]:
    return [{"severity": "error", "message": "Missing field: CommandLine"}]


def test_refine_applies_fixes_and_returns_revised_rule() -> None:
    controller = RefinementController(max_iterations=3)
    result = controller.refine(
        current_rule=_rule(),
        validation_issues=_validation_issues(),
        detection_spec={"logic": {"required_fields": ["Image", "CommandLine"]}},
        iteration=1,
    )

    assert result["should_abort"] is False
    assert result["revised_sigma_rule"]
    assert result["applied_fixes"]


def test_refine_aborts_at_max_iterations() -> None:
    controller = RefinementController(max_iterations=3)
    result = controller.refine(
        current_rule=_rule(),
        validation_issues=_validation_issues(),
        detection_spec={},
        iteration=3,
    )

    assert result["should_abort"] is True
    assert result["abort_reason"]
    assert "max iterations" in result["abort_reason"].lower()


def test_refine_aborts_on_plateau() -> None:
    controller = RefinementController(max_iterations=3)
    controller.record_iteration_result(iteration=1, issues_count=5)
    controller.record_iteration_result(iteration=2, issues_count=5)

    result = controller.refine(
        current_rule=_rule(),
        validation_issues=_validation_issues(),
        detection_spec={},
        iteration=2,
    )

    assert result["should_abort"] is True
    assert "plateau" in result["abort_reason"].lower()

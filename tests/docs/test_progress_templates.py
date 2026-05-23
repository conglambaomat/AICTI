from pathlib import Path


def test_progress_template_contains_required_fields() -> None:
    text = Path("docs/operational/IMPLEMENTATION_PROGRESS.md").read_text(encoding="utf-8")
    for field in ["Status:", "Phase/Plan reference:", "Verification evidence:", "Commit SHA:", "Next step:"]:
        assert field in text


def test_changelog_template_contains_required_fields() -> None:
    text = Path("docs/operational/CHANGELOG_AUTONOMOUS.md").read_text(encoding="utf-8")
    for field in ["Date/Time (UTC)", "Change summary", "Scope", "Commit SHA"]:
        assert field in text

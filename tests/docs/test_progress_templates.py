from pathlib import Path


def test_progress_template_contains_required_fields() -> None:
    text = Path("docs/operational/IMPLEMENTATION_PROGRESS.md").read_text(encoding="utf-8")
    for field in [
        "Status:",
        "Phase/Plan reference:",
        "Verification evidence:",
        "Commit SHA:",
        "Next step:",
    ]:
        assert field in text


def test_changelog_template_contains_required_fields() -> None:
    text = Path("docs/operational/CHANGELOG_AUTONOMOUS.md").read_text(encoding="utf-8")
    for field in ["Date/Time (UTC)", "Change summary", "Scope", "Commit SHA"]:
        assert field in text


def test_production_hardening_progress_entry_has_closure_evidence() -> None:
    text = Path("docs/operational/IMPLEMENTATION_PROGRESS.md").read_text(encoding="utf-8")
    entry = text.split("### 2026-05-27 00:00 UTC", 1)[1].split("\n### ", 1)[0]

    assert "Commit SHA: pending" not in entry
    assert "c0129d8" in entry
    assert "edbaaf8" in entry
    assert "final verification pending" not in entry.lower()
    assert "Next step: run full production-hardening verification" not in entry


def test_production_hardening_changelog_entry_has_commit_sha() -> None:
    text = Path("docs/operational/CHANGELOG_AUTONOMOUS.md").read_text(encoding="utf-8")
    entry = text.split("- 2026-05-27 00:00 UTC", 1)[1].split("\n- 2026-05", 1)[0]

    assert "Commit SHA: pending" not in entry
    assert "c0129d8" in entry
    assert "edbaaf8" in entry

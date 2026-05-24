import subprocess
import sys
from pathlib import Path


def run_docs_preflight() -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, "scripts/docs_preflight.py"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )


def test_docs_preflight_passes_on_valid_repo_state() -> None:
    result = run_docs_preflight()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DOCS_PREFLIGHT: PASS" in result.stdout


def test_docs_preflight_prints_startup_contract_fields() -> None:
    result = run_docs_preflight()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BRANCH:" in result.stdout
    assert "COMMIT_SHA:" in result.stdout
    assert "LAYOUT:" in result.stdout


def test_full_completion_checklist_has_layer_headers() -> None:
    checklist_path = (
        Path(__file__).resolve().parents[2]
        / "docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md"
    )
    content = checklist_path.read_text(encoding="utf-8")

    assert "## Layer A" in content
    assert "## Layer B" in content
    assert "## Layer C" in content

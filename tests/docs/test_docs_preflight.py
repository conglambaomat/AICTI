import subprocess
import sys


def run_docs_preflight() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/docs_preflight.py"], capture_output=True, text=True
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

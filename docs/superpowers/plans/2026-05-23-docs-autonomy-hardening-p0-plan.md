# Docs Autonomy Hardening P0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make documentation governance deterministic and fail-closed so Claude CLI can autonomously execute SOTA work with a single, stable source-of-truth layout.

**Architecture:** Freeze one authoritative documentation layout (`docs/canonical`, `docs/operational`, `docs/governance`, `docs/legacy`) and enforce it with executable checks instead of prose-only policy. Add an executable preflight script plus CI docs-consistency gate, then bind startup docs to mandatory branch/SHA/layout verification output before any implementation activity.

**Tech Stack:** Python 3.11, pytest, GitHub Actions workflow YAML, Markdown documentation.

---

### Task 1: Freeze single layout and map authoritative files

**Files:**
- Modify: `docs/governance/canonical_manifest.yaml`
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Test: `docs/governance/canonical_manifest.yaml` (schema sanity and path existence)

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_manifest_freeze.py
from pathlib import Path
import yaml


def test_manifest_declares_single_layout_and_authoritative_paths():
    manifest = yaml.safe_load(Path("docs/governance/canonical_manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["mode"] == "fail-closed"
    assert "canonical" in manifest["tiers"]
    assert "operational" in manifest["tiers"]
    assert "governance" in manifest["tiers"]
    assert "legacy" in manifest["tiers"]
    for p in manifest["tiers"]["canonical"]["paths"] + manifest["tiers"]["operational"]["paths"]:
        assert Path(p).exists(), f"missing authoritative path: {p}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_manifest_freeze.py -v`
Expected: FAIL if any authoritative path is missing or manifest shape is incomplete.

- [ ] **Step 3: Write minimal implementation**

Update `docs/governance/canonical_manifest.yaml` to include exactly one authoritative layout and complete path list for:
- canonical design
- startup contract
- execution/quality/escalation docs
- governance policy/preflight/warnings/progress docs

Update `CLAUDE.md` and `README.md` so startup sequence references only this frozen layout.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/docs/test_manifest_freeze.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/governance/canonical_manifest.yaml CLAUDE.md README.md tests/docs/test_manifest_freeze.py
git commit -m "docs(governance): freeze authoritative documentation layout"
```

### Task 2: Add executable preflight script and tests

**Files:**
- Create: `scripts/docs_preflight.py`
- Create: `tests/docs/test_docs_preflight.py`
- Modify: `docs/governance/preflight_checklist.md`
- Modify: `docs/operational/START_HERE_FOR_CLAUDE.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_docs_preflight.py
import subprocess
import sys


def test_docs_preflight_passes_on_valid_repo_state():
    result = subprocess.run([sys.executable, "scripts/docs_preflight.py"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DOCS_PREFLIGHT: PASS" in result.stdout


def test_docs_preflight_prints_startup_contract_fields():
    result = subprocess.run([sys.executable, "scripts/docs_preflight.py"], capture_output=True, text=True)
    assert "BRANCH:" in result.stdout
    assert "COMMIT_SHA:" in result.stdout
    assert "LAYOUT:" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_docs_preflight.py -v`
Expected: FAIL because `scripts/docs_preflight.py` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/docs_preflight.py
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import yaml


def git(cmd: list[str]) -> str:
    return subprocess.check_output(["git", *cmd], text=True).strip()


def main() -> int:
    manifest_path = Path("docs/governance/canonical_manifest.yaml")
    if not manifest_path.exists():
        print("DOCS_PREFLIGHT: FAIL missing manifest")
        return 1

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    for tier in ("canonical", "operational", "governance"):
        for p in manifest["tiers"][tier]["paths"]:
            if p.endswith("/"):
                if not Path(p).exists():
                    missing.append(p)
            elif not Path(p).exists():
                missing.append(p)

    branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    sha = git(["rev-parse", "HEAD"])
    print(f"BRANCH: {branch}")
    print(f"COMMIT_SHA: {sha}")
    print("LAYOUT: canonical/operational/governance/legacy")

    if missing:
        print("DOCS_PREFLIGHT: FAIL missing authoritative paths")
        for p in missing:
            print(f"- {p}")
        return 1

    print("DOCS_PREFLIGHT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Update startup docs to require executing:
- `python scripts/docs_preflight.py`
before implementation.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/docs/test_docs_preflight.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/docs_preflight.py tests/docs/test_docs_preflight.py docs/governance/preflight_checklist.md docs/operational/START_HERE_FOR_CLAUDE.md
git commit -m "feat(docs): add executable docs preflight gate"
```

### Task 3: Add CI docs-consistency gate

**Files:**
- Create: `.github/workflows/docs-governance.yml`
- Create: `tests/docs/test_docs_references.py`
- Modify: `docs/governance/docs_governance_policy.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_docs_references.py
from pathlib import Path

ACTIVE_DOCS = [
    Path("CLAUDE.md"),
    Path("README.md"),
    Path("docs/operational/START_HERE_FOR_CLAUDE.md"),
]

BANNED_ACTIVE_PATTERNS = [
    "docs/legacy/",
]


def test_active_docs_do_not_reference_legacy_as_authority():
    for p in ACTIVE_DOCS:
        text = p.read_text(encoding="utf-8")
        for pattern in BANNED_ACTIVE_PATTERNS:
            assert pattern not in text, f"{p} references legacy authority: {pattern}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_docs_references.py -v`
Expected: FAIL if active docs currently contain legacy-authority references.

- [ ] **Step 3: Write minimal implementation**

```yaml
# .github/workflows/docs-governance.yml
name: docs-governance

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  docs-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install pytest pyyaml
      - run: python scripts/docs_preflight.py
      - run: pytest tests/docs/test_manifest_freeze.py tests/docs/test_docs_preflight.py tests/docs/test_docs_references.py -v
```

Update policy doc to declare CI docs-gate mandatory for readiness claims.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/docs/test_docs_references.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/docs-governance.yml tests/docs/test_docs_references.py docs/governance/docs_governance_policy.md
git commit -m "ci(docs): enforce documentation consistency gate"
```

### Task 4: Enforce progress logging contract for autonomous continuation

**Files:**
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`
- Create: `tests/docs/test_progress_templates.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_progress_templates.py
from pathlib import Path


def test_progress_template_contains_required_fields():
    text = Path("docs/operational/IMPLEMENTATION_PROGRESS.md").read_text(encoding="utf-8")
    for field in ["Status:", "Phase/Plan reference:", "Verification evidence:", "Commit SHA:", "Next step:"]:
        assert field in text


def test_changelog_template_contains_required_fields():
    text = Path("docs/operational/CHANGELOG_AUTONOMOUS.md").read_text(encoding="utf-8")
    for field in ["Date/Time (UTC)", "Change summary", "Scope", "Commit SHA"]:
        assert field in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_progress_templates.py -v`
Expected: FAIL if required progress fields are missing.

- [ ] **Step 3: Write minimal implementation**

Add required immutable template sections and explicit rule:
- “Task cannot be marked complete until progress and changelog entries are added with evidence and SHA.”

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/docs/test_progress_templates.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md tests/docs/test_progress_templates.py
git commit -m "docs(ops): enforce autonomous progress logging contract"
```

### Task 5: Final readiness verification for docs-autonomy-ready state

**Files:**
- Modify: `docs/operational/DOCS_PRECHECK.md`
- Modify: `docs/governance/preflight_checklist.md`
- Test: all docs governance tests + preflight script output

- [ ] **Step 1: Write the failing test**

```python
# Failing condition: no explicit final readiness command sequence documented
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rg -n "DOCS_PREFLIGHT: PASS|docs-governance|startup contract" docs/operational/DOCS_PRECHECK.md docs/governance/preflight_checklist.md`
Expected: missing one or more required markers before update.

- [ ] **Step 3: Write minimal implementation**

Document final required command sequence:

```bash
python scripts/docs_preflight.py
pytest tests/docs/test_manifest_freeze.py tests/docs/test_docs_preflight.py tests/docs/test_docs_references.py tests/docs/test_progress_templates.py -v
```

And expected success markers:
- `DOCS_PREFLIGHT: PASS`
- all tests pass

- [ ] **Step 4: Run test to verify it passes**

Run: `python scripts/docs_preflight.py && pytest tests/docs/test_manifest_freeze.py tests/docs/test_docs_preflight.py tests/docs/test_docs_references.py tests/docs/test_progress_templates.py -v`
Expected: preflight PASS + full docs suite PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/operational/DOCS_PRECHECK.md docs/governance/preflight_checklist.md
git commit -m "docs(governance): define final docs-autonomy-ready verification"
```

## Self-Review

- Spec coverage: plan covers all P0 items (single layout freeze, executable preflight, CI docs gate, startup contract output verification, mandatory progress logging).
- Placeholder scan: no TBD/TODO placeholders remain in implementation steps.
- Type consistency: file paths, test names, and command sequence are internally consistent and reusable by subagents.

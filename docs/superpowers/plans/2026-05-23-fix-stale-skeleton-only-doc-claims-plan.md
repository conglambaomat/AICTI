# Fix Stale Skeleton-Only Documentation Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove stale “skeleton-only” statements and synchronize core guidance documents with current repository reality.

**Architecture:** Update authoritative docs first (`README.md`, `CLAUDE.md`, `docs/operational/START_HERE_FOR_CLAUDE.md`, `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`) using claims verifiable from current code and tests. Preserve SOTA Core v2 invariants and execution order while replacing outdated project-state language with evidence-grounded current-state wording.

**Tech Stack:** Markdown documentation, git, pytest/ruff/mypy command references for verification claims.

---

### Task 1: Replace stale project-state claims in README

**Files:**
- Modify: `README.md`
- Test: `README.md` (manual consistency check against codebase)

- [ ] **Step 1: Write the failing test**

```python
# Pseudo-test checklist (documentation TDD)
# FAIL condition: README still contains claim that repo is only skeleton-level.
assert "early skeleton-level" not in open("README.md", encoding="utf-8").read()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -c "from pathlib import Path; s=Path('README.md').read_text(encoding='utf-8'); print('FAIL' if 'skeleton-level' in s else 'PASS')"`
Expected: `FAIL`

- [ ] **Step 3: Write minimal implementation**

Update README project reality section to:
- remove “skeleton-only” wording,
- describe that core API/service/test surfaces are implemented,
- add caution that specific completion metrics must be verified via current test runs.

Example replacement text:
```md
Current implementation is beyond initial skeleton stage: core API routing, ingestion/review/export flows, orchestration services, and broad unit/integration/e2e tests are present in the repository. Treat historical “skeleton-only” statements as superseded.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -c "from pathlib import Path; s=Path('README.md').read_text(encoding='utf-8'); print('PASS' if 'skeleton-level' not in s else 'FAIL')"`
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: replace stale skeleton-only claim in README"
```

### Task 2: Update project CLAUDE guidance reality section

**Files:**
- Modify: `CLAUDE.md`
- Test: `CLAUDE.md` (manual consistency + grep)

- [ ] **Step 1: Write the failing test**

```python
# FAIL if "early skeleton-level" claim still exists in CLAUDE.md
assert "early skeleton-level" not in open("CLAUDE.md", encoding="utf-8").read()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -c "from pathlib import Path; s=Path('CLAUDE.md').read_text(encoding='utf-8'); print('FAIL' if 'early skeleton-level' in s else 'PASS')"`
Expected: `FAIL`

- [ ] **Step 3: Write minimal implementation**

Rewrite “Current Project Reality” block to:
- remove outdated minimal-state claim,
- state that repository contains substantial SOTA Core v2-aligned implementation,
- require runtime verification commands to validate current pass status at session start.

Example addition:
```md
As of 2026-05-23, the repository includes substantial implementation beyond the initial skeleton baseline (multiple API domains, orchestrator/service modules, and broad test suites). Use current test and quality-gate runs as authoritative status evidence for the active session.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -c "from pathlib import Path; s=Path('CLAUDE.md').read_text(encoding='utf-8'); print('PASS' if 'early skeleton-level' not in s else 'FAIL')"`
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: refresh CLAUDE project reality guidance"
```

### Task 3: Align START_HERE and execution kit with current state

**Files:**
- Modify: `docs/operational/START_HERE_FOR_CLAUDE.md`
- Modify: `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`
- Test: both files (consistency check)

- [ ] **Step 1: Write the failing test**

```python
# FAIL if start/execution docs still instruct from stale skeleton baseline
from pathlib import Path
start = Path("docs/operational/START_HERE_FOR_CLAUDE.md").read_text(encoding="utf-8")
kit = Path("docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md").read_text(encoding="utf-8")
assert "skeleton-level" not in start + kit
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -c "from pathlib import Path; s=Path('docs/operational/START_HERE_FOR_CLAUDE.md').read_text(encoding='utf-8')+Path('docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md').read_text(encoding='utf-8'); print('FAIL' if 'skeleton-level' in s else 'PASS')"`
Expected: `FAIL`

- [ ] **Step 3: Write minimal implementation**

Update both docs to:
- keep SOTA Core v2 process order,
- explicitly mark old skeleton framing as stale,
- direct readers to verify status with current commands and traceability/reality-alignment docs.

Add verification note block:
```md
Session reality check (authoritative for current state):
- pytest -q
- mypy src
- ruff check .
Use these outputs as current truth; treat historical milestone statements as non-authoritative.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -c "from pathlib import Path; s=Path('docs/operational/START_HERE_FOR_CLAUDE.md').read_text(encoding='utf-8')+Path('docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md').read_text(encoding='utf-8'); print('PASS' if 'skeleton-level' not in s else 'FAIL')"`
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add docs/operational/START_HERE_FOR_CLAUDE.md docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md
git commit -m "docs: align start and execution kit with current repo reality"
```

### Task 4: Cross-document consistency and stale-phrase sweep

**Files:**
- Modify: any additional docs containing stale “skeleton-only” claims discovered by grep
- Test: global grep validation

- [ ] **Step 1: Write the failing test**

```python
# FAIL if stale phrases remain in docs after targeted fixes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rg -n "skeleton-level|skeleton only|only skeleton" README.md CLAUDE.md docs`
Expected: one or more matches before cleanup

- [ ] **Step 3: Write minimal implementation**

For each remaining match:
- either replace with current-state wording,
- or prepend explicit legacy/superseded warning if file must remain historical.

Template warning:
```md
> Legacy note: This section reflects an earlier skeleton-stage snapshot and is superseded by current SOTA Core v2 reality-sync documents.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `rg -n "skeleton-level|skeleton only|only skeleton" README.md CLAUDE.md docs`
Expected: no matches in active guidance docs; legacy docs allowed only when explicitly marked as historical.

- [ ] **Step 5: Commit**

```bash
git add README.md CLAUDE.md docs
git commit -m "docs: remove stale skeleton-only language across active docs"
```

### Task 5: Final verification and audit note

**Files:**
- Modify: `docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md` (or current governance summary file)
- Test: docs + command output checks

- [ ] **Step 1: Write the failing test**

```python
# FAIL if no explicit note links updated active docs to verification commands
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rg -n "Session reality check|authoritative for current state" docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`
Expected: no match before update

- [ ] **Step 3: Write minimal implementation**

Add a concise “Documentation Sync Note” section listing:
- which active docs were updated,
- date of sync,
- mandatory status verification commands.

- [ ] **Step 4: Run test to verify it passes**

Run: `rg -n "Documentation Sync Note|Session reality check" docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`
Expected: matches found

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md
git commit -m "docs: add governance sync note for reality verification"
```

## Self-Review

- Spec coverage: plan covers all identified stale “skeleton-only” claims in active guidance docs plus global sweep.
- Placeholder scan: no TBD/TODO placeholders remain; each task has concrete files and commands.
- Type consistency: commands and paths are consistent across tasks.

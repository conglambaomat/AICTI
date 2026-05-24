# SOTA Core v2 Full Completion Checklist Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a definitive DONE/NOT DONE verdict for full SOTA Core v2 by executing a fail-closed, evidence-first checklist across Plan Completion (A), Invariants (B), and Global Gates (C).

**Architecture:** The execution flow is deterministic and fail-closed: first establish authoritative scope, then verify all five mandatory plans in order, then verify all ten invariants on active runtime paths, then run full global quality gates with fresh evidence. Every checklist row must carry command evidence and artifact references; any FAIL/MISSING yields NOT DONE.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, pytest, mypy, ruff, uv, git, markdown artifacts under docs/operational.

---

### Task 1: Initialize master checklist artifact and row schema

**Files:**
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`

- [ ] **Step 1: Write failing baseline checklist with all items MISSING**

Create `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md` with this exact table skeleton:

```markdown
# SOTA Core v2 Full Completion Checklist

| Item ID | Layer | Requirement | Verification command | Expected pass marker | Evidence artifact/path | Status | Blocker if fail | Next action |
|---|---|---|---|---|---|---|---|---|
| A1 | Plan | Foundation plan complete | pending | pending | pending | MISSING | pending | pending |
| A2 | Plan | Compiler plan complete | pending | pending | pending | MISSING | pending | pending |
| A3 | Plan | Validation-oracle-regression plan complete | pending | pending | pending | MISSING | pending | pending |
| A4 | Plan | Agents plan complete | pending | pending | pending | MISSING | pending | pending |
| A5 | Plan | Orchestrator-UI-dashboard plan complete | pending | pending | pending | MISSING | pending | pending |
| B1 | Invariant | No raw-report-to-rule shortcut | pending | pending | pending | MISSING | pending | pending |
| B2 | Invariant | DetectionSpec-first mandatory | pending | pending | pending | MISSING | pending | pending |
| B3 | Invariant | Citation integrity hard gate | pending | pending | pending | MISSING | pending | pending |
| B4 | Invariant | ATT&CK modeling chain correctness | pending | pending | pending | MISSING | pending | pending |
| B5 | Invariant | Required proof obligations enforced | pending | pending | pending | MISSING | pending | pending |
| B6 | Invariant | Detection AST/compiler preferred source | pending | pending | pending | MISSING | pending | pending |
| B7 | Invariant | Human review before export mandatory | pending | pending | pending | MISSING | pending | pending |
| B8 | Invariant | Agent/refinement loops bounded | pending | pending | pending | MISSING | pending | pending |
| B9 | Invariant | Feedback -> regression protection | pending | pending | pending | MISSING | pending | pending |
| B10 | Invariant | Full lineage/auditability preserved | pending | pending | pending | MISSING | pending | pending |
| C1 | Gate | docs preflight passes | `python scripts/docs_preflight.py` | `DOCS_PREFLIGHT: PASS` | command output | MISSING | pending | pending |
| C2 | Gate | full tests pass | `python -m uv run pytest tests/ -q` | `X passed` and exit 0 | command output | MISSING | pending | pending |
| C3 | Gate | mypy passes | `python -m uv run mypy src/` | `Success: no issues found` | command output | MISSING | pending | pending |
| C4 | Gate | ruff check passes | `python -m uv run ruff check src/ tests/` | `All checks passed` | command output | MISSING | pending | pending |
| C5 | Gate | format check passes | `python -m uv run ruff format --check src/ tests/` | `... files already formatted` | command output | MISSING | pending | pending |
| C6 | Gate | strict runtime E2E bundle passes | `python -m uv run pytest tests/e2e/test_api_health_and_contracts.py tests/e2e/test_api_schema_validation.py tests/e2e/test_api_abstain_vs_hard_fail.py tests/e2e/test_api_review_and_export.py tests/e2e/test_api_run_status.py tests/e2e/test_pipeline_e2e.py -q` | `17 passed` and exit 0 | command output | MISSING | pending | pending |
```

- [ ] **Step 2: Run baseline validation that checklist exists**

Run: `python -m uv run pytest tests/docs/test_progress_templates.py -q`
Expected: PASS and docs template integrity unaffected.

- [ ] **Step 3: Log kickoff**

Append one entry to:
- `docs/operational/IMPLEMENTATION_PROGRESS.md`
- `docs/operational/CHANGELOG_AUTONOMOUS.md`
with scope “full completion checklist execution kickoff”.

- [ ] **Step 4: Commit checklist baseline**

```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): initialize full SOTA completion checklist baseline"
```

---

### Task 2: Execute Layer A verification (five plans in locked order)

**Files:**
- Read: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`
- Read: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`
- Read: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`
- Read: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`
- Read: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`

- [ ] **Step 1: Verify all five plan files exist**

Run: `python -m uv run pytest tests/docs/test_manifest_freeze.py -q`
Expected: PASS.

- [ ] **Step 2: For A1, map foundation completion evidence and set PASS/FAIL**

Update row A1 with concrete command(s), pass marker, evidence path(s), status.

- [ ] **Step 3: For A2, map compiler completion evidence and set PASS/FAIL**

Update row A2 similarly.

- [ ] **Step 4: For A3, map validation-oracle-regression evidence and set PASS/FAIL**

Update row A3 similarly.

- [ ] **Step 5: For A4, map agents plan evidence and set PASS/FAIL**

Update row A4 similarly.

- [ ] **Step 6: For A5, map orchestrator-ui-dashboard evidence and set PASS/FAIL**

Update row A5 similarly.

- [ ] **Step 7: Fail-closed checkpoint for Layer A**

Run: `python -m uv run python -c "from pathlib import Path; t=Path('docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md').read_text(encoding='utf-8'); print('A_FAIL_OR_MISSING' if any(f'| A{i} |' in t and ('| FAIL |' in t.split(f'| A{i} |',1)[1].split('\n',1)[0] or '| MISSING |' in t.split(f'| A{i} |',1)[1].split('\n',1)[0]) else '' for i in range(1,6)) else 'A_ALL_PASS')"`
Expected: `A_ALL_PASS` or explicit fail marker.

- [ ] **Step 8: Commit Layer A results**

```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): evaluate Layer A plan-completion status"
```

---

### Task 3: Execute Layer B invariant conformance verification (B1-B10)

**Files:**
- Read: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- Read: `src/de_forge/services/orchestrator.py`
- Read: `src/de_forge/api/routes/pipeline.py`
- Read: `tests/e2e/test_api_review_and_export.py`
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`

- [ ] **Step 1: Re-run strict runtime E2E bundle for fresh invariant evidence**

Run:
```bash
python -m uv run pytest tests/e2e/test_api_health_and_contracts.py tests/e2e/test_api_schema_validation.py tests/e2e/test_api_abstain_vs_hard_fail.py tests/e2e/test_api_review_and_export.py tests/e2e/test_api_run_status.py tests/e2e/test_pipeline_e2e.py -q
```
Expected: `17 passed`.

- [ ] **Step 2: Fill B1-B5 with command+path evidence and status**

Update rows B1..B5 with concrete file:line references and exact commands.

- [ ] **Step 3: Fill B6-B10 with command+path evidence and status**

Update rows B6..B10 similarly.

- [ ] **Step 4: Fail-closed checkpoint for Layer B**

Manual rule: if any Bx is FAIL/MISSING, mark global verdict blocked and list P0 blockers.

- [ ] **Step 5: Commit Layer B results**

```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): evaluate Layer B invariant-conformance status"
```

---

### Task 4: Execute Layer C global gates with fresh evidence (C1-C6)

**Files:**
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`

- [ ] **Step 1: Run docs preflight**

Run: `python scripts/docs_preflight.py`
Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 2: Run full tests**

Run: `python -m uv run pytest tests/ -q`
Expected: `... passed` and exit 0.

- [ ] **Step 3: Run mypy**

Run: `python -m uv run mypy src/`
Expected: `Success: no issues found`.

- [ ] **Step 4: Run ruff lint**

Run: `python -m uv run ruff check src/ tests/`
Expected: `All checks passed`.

- [ ] **Step 5: Run ruff format check**

Run: `python -m uv run ruff format --check src/ tests/`
Expected: no files need formatting.

- [ ] **Step 6: Re-run strict runtime bundle (fresh)**

Run command in C6 row.
Expected: `17 passed`.

- [ ] **Step 7: Update C1-C6 rows to PASS/FAIL with exact markers**

Populate checklist row fields with exact output snippets.

- [ ] **Step 8: Commit Layer C results**

```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): evaluate Layer C global quality-gate status"
```

---

### Task 5: Resolve final verdict and blocker triage

**Files:**
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`

- [ ] **Step 1: Compute final verdict from checklist status values**

Rule:
- DONE only if all A1..A5, B1..B10, C1..C6 are PASS.
- Otherwise NOT DONE.

- [ ] **Step 2: Add final verdict section to checklist artifact**

Append:

```markdown
## Final Verdict
- Verdict: DONE | NOT DONE
- PASS count: <n>
- FAIL count: <n>
- MISSING count: <n>

## P0 Blockers (if NOT DONE)
- <item>: <blocker>

## Ordered Next Actions
1. <highest-priority action>
2. <next action>
```

- [ ] **Step 3: Synchronize operational logs with verdict**

Update both operational logs with exact command evidence and verdict line.

- [ ] **Step 4: Commit final verdict package**

```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): publish full SOTA completion verdict and blocker triage"
```

---

### Task 6: Post-verdict consistency guard

**Files:**
- Modify: `tests/docs/test_progress_templates.py`

- [ ] **Step 1: Add failing test for verdict-field presence in checklist artifact**

Add test ensuring `Final Verdict` section exists in full checklist artifact.

```python
from pathlib import Path

def test_full_completion_checklist_has_final_verdict_section() -> None:
    text = Path("docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md").read_text(encoding="utf-8")
    assert "## Final Verdict" in text
    assert "- Verdict:" in text
```

- [ ] **Step 2: Run test to verify pass**

Run: `python -m uv run pytest tests/docs/test_progress_templates.py -q`
Expected: PASS.

- [ ] **Step 3: Commit guard test**

```bash
git add tests/docs/test_progress_templates.py
git commit -m "test(docs): guard final verdict section in full completion checklist"
```

---

## Self-Review Checklist (Plan Quality)

- Spec coverage: Layer A/B/C requirements all mapped to concrete tasks and commands.
- Placeholder scan: no TBD/TODO placeholders remain in executable steps.
- Consistency check: unified status vocabulary (`PASS|FAIL|MISSING`) and deterministic verdict rule used throughout.

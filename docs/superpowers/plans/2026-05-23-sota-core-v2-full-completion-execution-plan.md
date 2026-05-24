# SOTA Core v2 Full Completion Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete all remaining DE-Forge SOTA Core v2 work across Phase 1→5 with strict TDD, dual reviews, full verification gates, and task-scoped commits.

**Architecture:** Use a single-writer execution model (one implementation agent at a time) with parallel read-only subagents for research/audit/review. Enforce per-task RED→GREEN→REFACTOR gates, then spec-compliance review and code-quality review before commit. Enforce phase exit only after full phase verification gates pass.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest/pytest-asyncio/pytest-cov/httpx, mypy, ruff, uv.

---

## File Structure and Control Artifacts

**Modify (runtime tracking + plan orchestration):**
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`
- `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`
- `docs/superpowers/specs/2026-05-23-sota-core-v2-full-completion-execution-design.md`

**Modify (product code/tests, exact files decided task-by-task from phase plans):**
- `src/**`
- `tests/**`

**Modify (reality-sync docs after verified outcomes):**
- `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- `docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`
- `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

---

### Task 1: Reconstruct execution state and runtime todo ledger

**Files:**
- Modify: runtime task list in Claude task tracker
- Read: all phase plans and quality gates

- [ ] **Step 1: Build/refresh runtime phase checklist**

Create/update runtime tasks for:
1) Phase 1 Foundation
2) Phase 2 Compiler
3) Phase 3 Validation/Oracle/Regression
4) Phase 4 Agents
5) Phase 5 Orchestrator/API/UI/Dashboard

- [ ] **Step 2: Reconcile repo state before implementation**

Run: `git status --short`
Expected: show all current modified/untracked files.

Run: `git log --oneline -n 20`
Expected: identify latest completed checkpoints.

- [ ] **Step 3: Define allowed commit scope policy for session**

Allowed to commit only files tied to active task; never commit:
- `.env*` with secrets
- `*.db`, `*.db-shm`, `*.db-wal`
- `.claude/*.lock`
- transient debug artifacts

- [ ] **Step 4: Commit (if only plan/tracking files changed)**

```bash
git add docs/superpowers/plans/2026-05-23-sota-core-v2-full-completion-execution-plan.md
git commit -m "docs(plan): add full SOTA Core v2 completion execution plan"
```

---

### Task 2: Phase-by-phase execution harness (template applied to every plan task)

**Files:**
- Modify: active phase plan checklist status (if tracked inline)
- Modify: runtime task tracker
- Modify: task-specific `src/**`, `tests/**`

- [ ] **Step 1: Write failing test for active task (RED)**

Template test pattern:
```python
def test_<active_requirement_id>_<behavior>() -> None:
    # arrange
    # act
    # assert expected deterministic behavior
    assert False  # replace with real failing expectation first
```

- [ ] **Step 2: Run failing test and capture expected failure**

Run: `python -m uv run pytest <exact_test_path>::<exact_test_name> -v`
Expected: FAIL for expected reason tied to missing/incorrect behavior.

- [ ] **Step 3: Implement minimum code (GREEN)**

Template implementation discipline:
```python
# minimal production code to satisfy the failing test,
# no speculative abstractions, no unrelated refactors
```

- [ ] **Step 4: Re-run targeted test and verify pass**

Run: `python -m uv run pytest <exact_test_path>::<exact_test_name> -v`
Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run: `python -m uv run pytest <affected_test_subset> -v`
Expected: PASS.

- [ ] **Step 6: Spec compliance review pass (subagent, read-only)**

Dispatch reviewer with required output format:
- Requirement IDs checked
- Violations (if any)
- file_path:line_number evidence
- pass/fail verdict

- [ ] **Step 7: Fix and re-review until spec pass**

Run targeted tests after each fix.
Expected: findings resolved and tests still pass.

- [ ] **Step 8: Code quality review pass (subagent, read-only)**

Dispatch reviewer with required output format:
- Correctness/safety findings
- Simplicity/YAGNI findings
- Test quality findings
- pass/fail verdict

- [ ] **Step 9: Fix and re-review until quality pass**

Run targeted tests after each fix.
Expected: findings resolved and tests still pass.

- [ ] **Step 10: Task verification and commit**

Run:
- `python -m uv run pytest <active_scope_tests> -v`
- any task-specific checks required by the phase plan.

Commit:
```bash
git add <task_scoped_files>
git commit -m "feat|fix|refactor: <task outcome linked to requirement>"
```

---

### Task 3: Execute Phase 1 Foundation to completion

**Files:**
- Modify/Test: exact files from `2026-05-21-de-forge-sota-core-v2-foundation-plan.md`

- [ ] **Step 1: Enumerate all remaining Phase 1 tasks from plan**
- [ ] **Step 2: Apply Task 2 template to each Phase 1 task in order**
- [ ] **Step 3: Run Phase 1 full verification gates**

Run:
- `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Expected: all pass.

- [ ] **Step 4: Commit Phase 1 completion sync**

```bash
git add <phase1_scoped_files>
git commit -m "test: finalize phase 1 foundation verification gates"
```

---

### Task 4: Execute Phase 2 Compiler to completion

**Files:**
- Modify/Test: exact files from `2026-05-21-de-forge-sota-core-v2-compiler-plan.md`

- [ ] **Step 1: Enumerate all remaining Phase 2 tasks from plan**
- [ ] **Step 2: Apply Task 2 template to each Phase 2 task in order**
- [ ] **Step 3: Run Phase 2 verification gates**

Run:
- `python -m uv run pytest tests/unit/services/test_detection_ast.py -v`
- `python -m uv run pytest tests/unit/services/test_sigma_compiler.py -v`
- `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Expected: all pass.

- [ ] **Step 4: Commit Phase 2 completion sync**

```bash
git add <phase2_scoped_files>
git commit -m "feat: complete phase 2 detection AST and sigma compiler"
```

---

### Task 5: Execute Phase 3 Validation/Oracle/Regression to completion

**Files:**
- Modify/Test: exact files from `2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`

- [ ] **Step 1: Enumerate all remaining Phase 3 tasks from plan**
- [ ] **Step 2: Apply Task 2 template to each Phase 3 task in order**
- [ ] **Step 3: Run Phase 3 verification gates**

Run:
- `python -m uv run pytest tests/unit/validators/ -v`
- `python -m uv run pytest tests/unit/services/test_validation*.py -v`
- `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Expected: all pass.

- [ ] **Step 4: Commit Phase 3 completion sync**

```bash
git add <phase3_scoped_files>
git commit -m "feat: complete phase 3 validation oracle regression gates"
```

---

### Task 6: Execute Phase 4 Controlled Agents to completion

**Files:**
- Modify/Test: exact files from `2026-05-21-de-forge-sota-core-v2-agents-plan.md`

- [ ] **Step 1: Enumerate all remaining Phase 4 tasks from plan**
- [ ] **Step 2: Apply Task 2 template to each Phase 4 task in order**
- [ ] **Step 3: Run Phase 4 verification gates**

Run:
- `python -m uv run pytest tests/unit/agents/ -v`
- `python -m uv run pytest tests/integration/agents/ -v`
- `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Expected: all pass.

- [ ] **Step 4: Commit Phase 4 completion sync**

```bash
git add <phase4_scoped_files>
git commit -m "feat: complete phase 4 controlled multi-agent workflow"
```

---

### Task 7: Execute Phase 5 Orchestrator/API/UI/Dashboard to completion

**Files:**
- Modify/Test: exact files from `2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`

- [ ] **Step 1: Enumerate all remaining Phase 5 tasks from plan**
- [ ] **Step 2: Apply Task 2 template to each Phase 5 task in order**
- [ ] **Step 3: Run runtime + API + UI smoke checks**

Run (adapt exact commands to project scripts):
- `python -m uv run pytest tests/integration/api/ -v`
- `python -m uv run pytest tests/integration/orchestrator/ -v`
- `python -m uv run pytest tests/e2e/ -v`

Expected: all pass.

- [ ] **Step 4: Run Phase 5 verification gates**

Run:
- `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Expected: all pass.

- [ ] **Step 5: Commit Phase 5 completion sync**

```bash
git add <phase5_scoped_files>
git commit -m "feat: complete phase 5 orchestrator api ui dashboard"
```

---

### Task 8: Reality-sync docs with verified outcomes

**Files:**
- Modify: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Modify: `docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`
- Modify: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

- [ ] **Step 1: Update requirement statuses only from current-session evidence**
- [ ] **Step 2: Verify no placeholder/contradictory claims remain**

Run:
- `python -m uv run pytest tests/ -q` (or latest full verification command already passing)
- `git diff -- docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

Expected: docs reflect actual pass/fail state.

- [ ] **Step 3: Commit doc reality-sync**

```bash
git add docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md
git commit -m "docs(spec): reality-sync SOTA v2 verification and governance status"
```

---

### Task 9: Final full-system verification-before-completion

**Files:**
- Modify: none (verification only unless issues found)

- [ ] **Step 1: Run final universal gates**

Run:
- `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing`
- `python -m uv run mypy src/`
- `python -m uv run ruff check src/ tests/`
- `python -m uv run ruff format --check src/ tests/`

Expected: all pass.

- [ ] **Step 2: Run final provider-dependent smoke path (if present in tests/scripts)**

Run project-specific smoke command(s) that exercise provider-backed flow.
Expected: pass with healthy auth.

- [ ] **Step 3: Run final git hygiene check**

Run: `git status --short`
Expected: clean working tree or only intentional post-verify files.

---

### Task 10: Completion handoff and branch-finishing decision

**Files:**
- Modify: optional status docs if needed

- [ ] **Step 1: Summarize completed phases with evidence references**
- [ ] **Step 2: Present integration options (keep local / PR / cleanup) via finishing-a-development-branch**
- [ ] **Step 3: Do not push/create PR unless explicitly requested by user**

---

## Self-Review Checklist (Completed)

- Spec coverage: Plan covers execution model, TDD gates, dual-review gates, phase verification, provider-dependent checks, doc reality-sync, and final completion verification.
- Placeholder scan: No TBD/TODO placeholders.
- Type/signature consistency: This is an execution plan; implementation signatures are delegated to phase tasks and must be defined concretely per task during execution.

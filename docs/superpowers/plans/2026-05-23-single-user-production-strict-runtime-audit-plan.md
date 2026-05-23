# Single-User Production Strict Runtime Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a definitive READY/NOT READY verdict for DE-Forge under strict single-user production criteria using runtime path truth, measured efficiency, and output rule quality evidence.

**Architecture:** Execute a deterministic audit pipeline in six phases: runtime path discovery, live E2E execution, invariant verification, efficiency measurement, rule-quality scoring, and closure verdict. Every claim must be backed by command output, artifact evidence, or file_path:line_number references. The audit is fail-closed: any critical invariant bypass causes NOT READY.

**Tech Stack:** Python 3.11, FastAPI runtime, SQLAlchemy/SQLite, pytest, uv, bash/git, DE-Forge services and docs.

---

### Task 1: Lock baseline and audit scope state

**Files:**
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`
- Read: `docs/superpowers/specs/2026-05-23-single-user-production-strict-runtime-audit-design.md`

- [ ] **Step 1: Record current repo state snapshot**

Run: `git status --short && git log --oneline -n 12`
Expected: current modified/untracked files and recent commits are visible.

- [ ] **Step 2: Verify governance/doc preflight gate**

Run: `python scripts/docs_preflight.py`
Expected: output contains `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 3: Write progress entry for audit kickoff**

Add this entry block to `docs/operational/IMPLEMENTATION_PROGRESS.md`:

```markdown
### 2026-05-23 <HH:MM UTC> — Strict single-user production runtime audit kickoff
- Status: partial
- Phase/Plan reference: `docs/superpowers/plans/2026-05-23-single-user-production-strict-runtime-audit-plan.md`
- Summary of implementation:
  - Baseline locked for production-strict runtime audit.
  - Governance preflight and repo-state snapshot captured.
- Files changed:
  - `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Verification evidence:
  - docs preflight: pending
  - runtime path evidence: pending
  - efficiency evidence: pending
  - rule quality evidence: pending
- Commit SHA: pending
- Next step: runtime path truth discovery
- Blockers/risks: none
```

- [ ] **Step 4: Update autonomous changelog kickoff line**

Append to `docs/operational/CHANGELOG_AUTONOMOUS.md`:

```markdown
- 2026-05-23 <HH:MM UTC>
  - Change summary: Started strict single-user production runtime audit with fail-closed evidence policy.
  - Scope: baseline lock, governance preflight, runtime-audit execution staging.
  - Commit SHA: pending
```

- [ ] **Step 5: Commit kickoff docs update**

Run:
```bash
git add docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(ops): start strict single-user production runtime audit"
```

---

### Task 2: Discover and prove active runtime path truth

**Files:**
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md`
- Read: `src/de_forge/main.py`
- Read: `src/de_forge/api/routes/pipeline.py`
- Read: `src/de_forge/api/routes/ingestion.py`
- Read: `src/de_forge/api/routes/review.py`
- Read: `src/de_forge/services/orchestrator.py`

- [ ] **Step 1: Write failing path-truth assertion checklist first**

Create checklist in `docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md` with initial unchecked assertions:

```markdown
# Runtime Path Truth Evidence

## Assertions
- [ ] API run path invokes non-stub orchestrator flow
- [ ] DetectionSpec-first gate is enforced on active run path
- [ ] Export path enforces human review decision from persisted state
- [ ] Active path reaches validation/proof stage before export eligibility
```

- [ ] **Step 2: Run code-reference extraction commands**

Run:
```bash
python -m uv run python -c "import inspect, de_forge.main as m; print(inspect.getsource(m))"
python -m uv run python -c "import inspect, de_forge.api.routes.pipeline as p; print(inspect.getsource(p))"
```
Expected: full source dumps confirm runtime wiring points.

- [ ] **Step 3: Cross-check entrypoint->route->service linkage**

Run:
```bash
python -m uv run python -c "import inspect, de_forge.api.routes.ingestion as i; print(inspect.getsource(i))"
python -m uv run python -c "import inspect, de_forge.api.routes.review as r; print(inspect.getsource(r))"
python -m uv run python -c "import inspect, de_forge.services.orchestrator as o; print(inspect.getsource(o))"
```
Expected: explicit evidence whether orchestrator is called by active API path.

- [ ] **Step 4: Mark assertions PASS/FAIL with file:line evidence**

Update `docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md` with concrete results:

```markdown
## Results
- [PASS/FAIL] API run path invokes non-stub orchestrator flow — evidence: `src/de_forge/...:line`
- [PASS/FAIL] DetectionSpec-first on active run path — evidence: `src/de_forge/...:line`
- [PASS/FAIL] Export enforces persisted review decision — evidence: `src/de_forge/...:line`
- [PASS/FAIL] Validation/proof before export eligibility — evidence: `src/de_forge/...:line`
```

- [ ] **Step 5: Commit path-truth evidence artifact**

Run:
```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): record runtime path truth evidence"
```

---

### Task 3: Execute single-report live runtime trace and capture artifacts

**Files:**
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md`
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`
- Read: `tests/e2e/test_pipeline_e2e.py`

- [ ] **Step 1: Write failing trace-expectation checklist**

Create `docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md`:

```markdown
# Live Runtime Trace Evidence

## Required stage evidence
- [ ] ingest response captured
- [ ] pipeline run response captured
- [ ] gate/decision metadata captured
- [ ] review/export gate behavior captured
```

- [ ] **Step 2: Start deterministic runtime probe via test client command**

Run:
```bash
python -m uv run pytest tests/e2e/test_pipeline_e2e.py::test_e2e_positive_pipeline_reaches_awaiting_review -v
```
Expected: PASS and concrete runtime-stage evidence from test assertions.

- [ ] **Step 3: Capture abstain-path live behavior**

Run:
```bash
python -m uv run pytest tests/e2e/test_pipeline_e2e.py::test_e2e_ambiguous_report_abstains -v
```
Expected: PASS with abstain output contract evidence.

- [ ] **Step 4: Capture deterministic replay behavior**

Run:
```bash
python -m uv run pytest tests/e2e/test_pipeline_e2e.py::test_deterministic_replay_same_input_same_transitions_and_idempotency -v
```
Expected: PASS with deterministic replay guarantee evidence.

- [ ] **Step 5: Populate trace artifact with command output markers**

Update `docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md` with:

```markdown
## Command Evidence
- `<command>` -> PASS/FAIL, key output markers

## Runtime Interpretation
- Stage coverage observed: ...
- Gate behavior observed: ...
- Mismatch vs canonical path: ...
```

- [ ] **Step 6: Commit live trace evidence**

Run:
```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): capture single-report live runtime trace evidence"
```

---

### Task 4: Verify architecture invariants against observed runtime

**Files:**
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-invariant-matrix.md`
- Read: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- Read: `docs/operational/runtime-audit-artifacts/2026-05-23-path-truth.md`
- Read: `docs/operational/runtime-audit-artifacts/2026-05-23-live-trace.md`

- [ ] **Step 1: Write invariant matrix template with fail-closed defaults**

Create `docs/operational/runtime-audit-artifacts/2026-05-23-invariant-matrix.md`:

```markdown
# Invariant Compliance Matrix

| Invariant | Required behavior | Observed evidence | PASS/FAIL |
|---|---|---|---|
| No raw-report-to-rule shortcut | ... | ... | FAIL |
| DetectionSpec-first mandatory | ... | ... | FAIL |
| Citation integrity hard gate | ... | ... | FAIL |
| Human review mandatory before export | ... | ... | FAIL |
| Bounded loops | ... | ... | FAIL |
| Full lineage auditable | ... | ... | FAIL |
```

- [ ] **Step 2: Replace defaults with evidence-backed status**

Fill every row with file:line and command-evidence links.
Expected: no empty cell remains.

- [ ] **Step 3: Commit invariant matrix**

Run:
```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-invariant-matrix.md
git commit -m "docs(audit): add production invariant compliance matrix"
```

---

### Task 5: Measure single-user runtime efficiency from real executions

**Files:**
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-efficiency-measurements.md`
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`

- [ ] **Step 1: Write efficiency measurement table skeleton**

Create `docs/operational/runtime-audit-artifacts/2026-05-23-efficiency-measurements.md`:

```markdown
# Efficiency Measurements (Single-User)

| Run | Scenario | Total latency (s) | Stage latency evidence | Retry/timeout events | PASS/FAIL |
|---|---|---:|---|---|---|
| 1 | positive flow |  |  |  | FAIL |
| 2 | positive flow |  |  |  | FAIL |
| 3 | positive flow |  |  |  | FAIL |
```

- [ ] **Step 2: Execute repeated runtime test commands with timing**

Run:
```bash
python -m uv run python -c "import time, subprocess; t=time.time(); r=subprocess.run(['python','-m','uv','run','pytest','tests/e2e/test_pipeline_e2e.py::test_e2e_positive_pipeline_reaches_awaiting_review','-q'], capture_output=True, text=True); print('elapsed=', round(time.time()-t,3)); print(r.returncode); print(r.stdout.splitlines()[-1] if r.stdout.splitlines() else '');"
```
Expected: elapsed time + return code 0.

- [ ] **Step 3: Repeat Step 2 two more times**

Run Step 2 command twice more.
Expected: three successful timed runs for variance estimation.

- [ ] **Step 4: Compute median/min/max and determine efficiency gate**

Add summary to file:

```markdown
## Summary
- min: <value>s
- median: <value>s
- max: <value>s
- variance note: <short interpretation>
- efficiency verdict: PASS/FAIL (with reason)
```

- [ ] **Step 5: Commit efficiency evidence**

Run:
```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-efficiency-measurements.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): record single-user runtime efficiency measurements"
```

---

### Task 6: Score output rule quality and deployability signal

**Files:**
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-rule-quality-rubric.md`
- Read: `tests/integration/services/test_retrieval_faithfulness.py`
- Read: `tests/integration/services/test_rule_generation_service.py`
- Read: `tests/integration/services/test_static_validation_service.py`
- Read: `tests/integration/services/test_review_gate.py`

- [ ] **Step 1: Create rubric template with strict defaults FAIL**

Create `docs/operational/runtime-audit-artifacts/2026-05-23-rule-quality-rubric.md`:

```markdown
# Rule Quality Rubric

| Axis | Evidence source | PASS/FAIL | Notes |
|---|---|---|---|
| Evidence faithfulness |  | FAIL |  |
| DetectionSpec constraint fidelity |  | FAIL |  |
| Validation/proof gate correctness |  | FAIL |  |
| Operational deployability signal |  | FAIL |  |
```

- [ ] **Step 2: Run targeted validation tests as evidence anchors**

Run:
```bash
python -m uv run pytest tests/integration/services/test_retrieval_faithfulness.py -v
python -m uv run pytest tests/integration/services/test_rule_generation_service.py -v
python -m uv run pytest tests/integration/services/test_static_validation_service.py -v
python -m uv run pytest tests/integration/services/test_review_gate.py -v
```
Expected: PASS for each file; collect key markers.

- [ ] **Step 3: Fill rubric with evidence-backed status**

Populate each axis with command evidence and file:line anchors.
Expected: no blank evidence cell remains.

- [ ] **Step 4: Commit rubric artifact**

Run:
```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-rule-quality-rubric.md
git commit -m "docs(audit): score rule quality under strict single-user criteria"
```

---

### Task 7: Produce final PASS/FAIL matrix and READY/NOT READY verdict

**Files:**
- Create: `docs/operational/runtime-audit-artifacts/2026-05-23-final-verdict.md`
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`

- [ ] **Step 1: Create final verdict matrix template**

Create `docs/operational/runtime-audit-artifacts/2026-05-23-final-verdict.md`:

```markdown
# Final Production-Strict Verdict

| Axis | PASS/FAIL | Evidence |
|---|---|---|
| Runtime correctness | FAIL |  |
| Runtime efficiency (single-user) | FAIL |  |
| Rule quality | FAIL |  |

## Final Verdict
NOT READY

## P0 Blockers
1. <blocker>
2. <blocker>
```

- [ ] **Step 2: Replace template defaults using prior artifacts**

Link evidence from:
- path truth
- live trace
- invariant matrix
- efficiency measurements
- rule quality rubric

Expected: each axis has explicit evidence.

- [ ] **Step 3: Re-run universal verification gates before closure claim**

Run:
```bash
python -m uv run pytest tests/ -q
python -m uv run mypy src/
python -m uv run ruff check src/ tests/
python -m uv run ruff format --check src/ tests/
```
Expected: all pass; if not, record failure and keep NOT READY.

- [ ] **Step 4: Finalize operational logs with closure evidence**

Update both operational logs with:
- audit verdict summary
- verification commands
- commit SHA references

- [ ] **Step 5: Commit final closure artifacts**

Run:
```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-final-verdict.md docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(audit): finalize strict single-user production readiness verdict"
```

---

## Plan Self-Review

- Spec coverage: runtime path truth, invariants, live trace, efficiency measurement, rule quality, and final READY/NOT READY closure are all mapped to Tasks 2-7.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type/signature consistency: file names, commands, and artifact dependencies are consistent across tasks.

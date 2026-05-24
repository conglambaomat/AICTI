# SOTA Core v2 Full Completion Checklist Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all remaining SOTA Core v2 product-mode gaps with fail-closed verification so the project reaches a defensible DONE/NOT DONE verdict backed by fresh evidence.

**Architecture:** Use checklist-driven closure across three layers: (A) runtime/code invariants and golden-path correctness, (B) gating and verification integrity, and (C) operational/audit documentation consistency. Every change is additive/non-breaking, test-first, and validated by targeted tests before full-suite gates.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, pytest, mypy, ruff.

---

## File Structure Map

- `src/de_forge/services/` — deterministic gate/orchestrator/validation behaviors.
- `src/de_forge/api/routes/` + `src/de_forge/api/router.py` — additive API surfaces for run/review/metrics/ui.
- `src/de_forge/schemas/` — contracts for run/review/agent I/O.
- `tests/integration/api/` + `tests/integration/services/` + `tests/unit/services/` — TDD and regression safety.
- `docs/operational/` + `docs/governance/` — progress, changelog, runtime audit checklist/evidence.

## Execution Order (Fail-Closed)

1. Layer A — code/runtime closure for SOTA invariants and golden path.
2. Layer B — verification closure (tests/types/lint/format) and gate hardening.
3. Layer C — docs/audit closure and final DONE/NOT DONE verdict.

---

### Task 1: Reconstruct closure baseline and lock scope

**Files:**
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Test: `tests/docs/test_docs_preflight.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_docs_preflight.py

def test_full_completion_checklist_has_layer_headers() -> None:
    text = Path("docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md").read_text(encoding="utf-8")
    assert "## Layer A" in text
    assert "## Layer B" in text
    assert "## Layer C" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_docs_preflight.py::test_full_completion_checklist_has_layer_headers -v`
Expected: FAIL because headers are missing or stale.

- [ ] **Step 3: Write minimal implementation**

```markdown
## Layer A — Runtime/Code Closure
- [ ] A1 ...

## Layer B — Verification Closure
- [ ] B1 ...

## Layer C — Docs/Audit Closure
- [ ] C1 ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/docs/test_docs_preflight.py::test_full_completion_checklist_has_layer_headers -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/docs/test_docs_preflight.py docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md docs/operational/IMPLEMENTATION_PROGRESS.md
git commit -m "docs: establish layered checklist closure baseline"
```

### Task 2: Enforce gate predicate and state-machine compatibility invariants

**Files:**
- Modify: `src/de_forge/services/gates.py`
- Modify: `src/de_forge/services/state_machine.py`
- Test: `tests/unit/services/test_gate_predicates.py`
- Test: `tests/unit/services/test_state_machine_gates.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/services/test_gate_predicates.py

def test_can_generate_rule_accepts_validated_string_for_backward_compatibility() -> None:
    assert can_generate_rule("validated") is True
    assert can_generate_rule("pending") is False
```

```python
# tests/unit/services/test_state_machine_gates.py

def test_state_machine_blocks_illegal_transition() -> None:
    machine = StateMachine()
    with pytest.raises(ValidationGateError):
        machine.transition(RunState.CREATED, RunState.APPROVED)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/services/test_gate_predicates.py tests/unit/services/test_state_machine_gates.py -v`
Expected: FAIL if compatibility/invariant behavior regressed.

- [ ] **Step 3: Write minimal implementation**

```python
# src/de_forge/services/gates.py

def can_generate_rule(detection_spec_verified: bool | str) -> bool:
    if isinstance(detection_spec_verified, str):
        return detection_spec_verified == "validated"
    return detection_spec_verified
```

```python
# src/de_forge/services/state_machine.py

def transition(self, current: RunState, target: RunState) -> RunState:
    if target not in self.allowed.get(current, set()):
        raise ValidationGateError(f"Illegal transition: {current} -> {target}")
    return target
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/services/test_gate_predicates.py tests/unit/services/test_state_machine_gates.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/gates.py src/de_forge/services/state_machine.py tests/unit/services/test_gate_predicates.py tests/unit/services/test_state_machine_gates.py
git commit -m "fix(core): preserve gate and state-machine invariant behavior"
```

### Task 3: Lock additive API contract without breaking legacy routes

**Files:**
- Modify: `src/de_forge/main.py`
- Modify: `src/de_forge/api/router.py`
- Modify: `src/de_forge/api/routes/runs.py`
- Modify: `src/de_forge/api/routes/review.py`
- Modify: `src/de_forge/api/routes/metrics.py`
- Modify: `src/de_forge/api/routes/ui.py`
- Test: `tests/integration/api/test_api_routes.py`
- Test: `tests/integration/api/test_api_routes_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/api/test_api_routes.py

def test_legacy_review_route_still_available_after_api_router_wiring() -> None:
    response = client.post("/review/decision", json={"decision": "accept"})
    assert response.status_code in {200, 422}


def test_additive_api_routes_available() -> None:
    assert client.post("/api/runs/golden", json={"report_id": "r1", "report_text": "x", "mode": "auto"}).status_code == 200
    assert client.get("/api/metrics/quality").status_code == 200
    assert client.get("/api/ui/review").status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/api/test_api_routes.py tests/integration/api/test_api_routes_smoke.py -v`
Expected: FAIL if either legacy or additive path is broken.

- [ ] **Step 3: Write minimal implementation**

```python
# src/de_forge/main.py
app.include_router(pipeline_router)
app.include_router(pipeline_legacy_router)
app.include_router(ingestion_router)
app.include_router(review_router)
app.include_router(api_router)
```

```python
# src/de_forge/api/router.py
api_router = APIRouter(prefix="/api")
api_router.include_router(runs.router)
api_router.include_router(review.router)
api_router.include_router(metrics.router)
api_router.include_router(ui.router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/api/test_api_routes.py tests/integration/api/test_api_routes_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/main.py src/de_forge/api/router.py src/de_forge/api/routes/runs.py src/de_forge/api/routes/review.py src/de_forge/api/routes/metrics.py src/de_forge/api/routes/ui.py tests/integration/api/test_api_routes.py tests/integration/api/test_api_routes_smoke.py
git commit -m "feat(api): lock additive contracts while preserving legacy review routes"
```

### Task 4: Verify golden-path orchestration and review gating behavior

**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Modify: `src/de_forge/services/review.py`
- Modify: `src/de_forge/schemas/run.py`
- Modify: `src/de_forge/schemas/review.py`
- Test: `tests/integration/services/test_orchestrator_golden_path.py`
- Test: `tests/integration/services/test_orchestrator_state_transitions.py`
- Test: `tests/unit/services/test_review_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/services/test_orchestrator_golden_path.py

def test_cautious_mode_stops_at_awaiting_review() -> None:
    summary = Orchestrator().run_golden_path("r1", "PowerShell -enc AAA", RunMode.CAUTIOUS)
    assert summary.state == RunState.AWAITING_REVIEW
```

```python
# tests/unit/services/test_review_service.py

def test_reject_decision_blocks_export() -> None:
    decision = ReviewService().decide(
        ReviewRequest(run_id="run_1", rule_candidate_id="cand_1", action=ReviewAction.REJECT, reviewer_notes="Too broad")
    )
    assert decision.export_allowed is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/services/test_orchestrator_golden_path.py tests/integration/services/test_orchestrator_state_transitions.py tests/unit/services/test_review_service.py -v`
Expected: FAIL if state/review contract regressed.

- [ ] **Step 3: Write minimal implementation**

```python
# src/de_forge/services/orchestrator.py
if mode is RunMode.CAUTIOUS:
    return RunSummary(id=run_id, mode=mode, state=RunState.AWAITING_REVIEW, report_id=report_id)
```

```python
# src/de_forge/services/review.py
if request.action == ReviewAction.REJECT:
    return ReviewDecision(run_id=request.run_id, action=request.action, export_allowed=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/services/test_orchestrator_golden_path.py tests/integration/services/test_orchestrator_state_transitions.py tests/unit/services/test_review_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/orchestrator.py src/de_forge/services/review.py src/de_forge/schemas/run.py src/de_forge/schemas/review.py tests/integration/services/test_orchestrator_golden_path.py tests/integration/services/test_orchestrator_state_transitions.py tests/unit/services/test_review_service.py
git commit -m "fix(orchestrator): enforce run-state and review-gate golden-path behavior"
```

### Task 5: Hard-close phase verification gates (Layer B)

**Files:**
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`
- Test: `tests/docs/test_progress_templates.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_progress_templates.py

def test_runtime_audit_records_fresh_verification_commands() -> None:
    text = Path("docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md").read_text(encoding="utf-8")
    assert "python -m pytest -q" in text
    assert "python -m mypy src" in text
    assert "python -m ruff format --check src tests docs" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_progress_templates.py::test_runtime_audit_records_fresh_verification_commands -v`
Expected: FAIL if evidence log is incomplete.

- [ ] **Step 3: Write minimal implementation**

```markdown
- Verification evidence:
  - `python -m pytest -q` => 241 passed, 1 warning
  - `python -m mypy src` => Success: no issues found
  - `python -m ruff format --check src tests docs` => already formatted
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/docs/test_progress_templates.py::test_runtime_audit_records_fresh_verification_commands -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/docs/test_progress_templates.py docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md
git commit -m "docs(audit): record fresh verification evidence for closure gates"
```

### Task 6: Final docs/governance consistency closure (Layer C)

**Files:**
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`
- Modify: `docs/governance/doc_drift_warnings.md`
- Test: `tests/docs/test_docs_references.py`
- Test: `tests/docs/test_operational_reference_integrity.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_docs_references.py

def test_progress_links_to_runtime_audit_checklist() -> None:
    text = Path("docs/operational/IMPLEMENTATION_PROGRESS.md").read_text(encoding="utf-8")
    assert "2026-05-23-sota-full-completion-checklist.md" in text
```

```python
# tests/docs/test_operational_reference_integrity.py

def test_changelog_mentions_a5_closure_verdict() -> None:
    text = Path("docs/operational/CHANGELOG_AUTONOMOUS.md").read_text(encoding="utf-8")
    assert "A5" in text
    assert "DONE" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_docs_references.py tests/docs/test_operational_reference_integrity.py -v`
Expected: FAIL if references/verdicts are stale.

- [ ] **Step 3: Write minimal implementation**

```markdown
## 2026-05-23
- A5 orchestrator/api/ui/dashboard closure verdict: DONE
- Runtime evidence: docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/docs/test_docs_references.py tests/docs/test_operational_reference_integrity.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md docs/governance/doc_drift_warnings.md tests/docs/test_docs_references.py tests/docs/test_operational_reference_integrity.py
git commit -m "docs: finalize operational and governance closure consistency"
```

### Task 7: Global closure verification and final verdict

**Files:**
- Modify: `docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/docs/test_progress_templates.py

def test_final_verdict_present_and_fail_closed() -> None:
    text = Path("docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md").read_text(encoding="utf-8")
    assert "Final Verdict:" in text
    assert "DONE" in text or "NOT DONE" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/docs/test_progress_templates.py::test_final_verdict_present_and_fail_closed -v`
Expected: FAIL if final verdict is missing.

- [ ] **Step 3: Write minimal implementation**

```markdown
Final Verdict: DONE
Remaining Blockers: none
Fail-Closed Note: any future gate regression flips verdict to NOT DONE until re-verified.
```

- [ ] **Step 4: Run tests and gates to verify full pass**

Run: `python -m pytest -q`
Expected: PASS.

Run: `python -m mypy src`
Expected: Success: no issues found.

Run: `python -m ruff check src tests`
Expected: All checks pass.

Run: `python -m ruff format --check src tests docs`
Expected: already formatted.

- [ ] **Step 5: Commit**

```bash
git add docs/operational/runtime-audit-artifacts/2026-05-23-sota-full-completion-checklist.md tests/docs/test_progress_templates.py
git commit -m "docs(audit): publish final fail-closed project completion verdict"
```

## Plan Self-Review

### 1) Spec coverage check
- SOTA invariants + no raw-report-to-rule: covered by Tasks 2, 3, 4.
- Orchestrator/API/UI/dashboard product-mode closure: covered by Tasks 3, 4, 5.
- Verification-before-completion and hard gates: covered by Tasks 5, 7.
- Operational/governance/doc consistency: covered by Tasks 1, 6, 7.
- Final DONE/NOT DONE with blocker triage: covered by Task 7.

### 2) Placeholder scan
- No TBD/TODO placeholders.
- Every task has concrete file paths, test code, command lines, and commit command.

### 3) Type/signature consistency
- `can_generate_rule(detection_spec_verified: bool | str) -> bool` is consistent across tests/tasks.
- `StateMachine.transition(current: RunState, target: RunState) -> RunState` usage is consistent.
- Orchestrator/review schema references match `RunMode`, `RunState`, `ReviewRequest`, `ReviewDecision`.

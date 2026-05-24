# DE-Forge SOTA Core v2 Subagent Execution Strategy

Date: 2026-05-21
Purpose: Make Claude CLI use subagents as much as practical while preserving correctness, TDD discipline, and conflict-free implementation.

## 1. Operating principle

Use a **subagent-heavy, review-heavy, sequential-implementation** workflow.

The user prefers maximum accuracy and effective subagent usage over token savings. Claude should spend tokens on independent research, implementation isolation, review, verification, debugging, and phase audits.

Do not spend tokens by allowing multiple agents to write overlapping code at the same time. Parallel implementation is only allowed when file ownership is disjoint and the active plan explicitly makes the tasks independent.

Default rule:

```text
parallel research/review/audit/debugging
+
sequential implementation task-by-task
+
TDD and verification gates after every task
```

## 2. Mandatory subagent roles

For each implementation task, Claude should use these roles unless the task is purely administrative and no code or behavior changes occur.

### Task Scoper

Use before implementation when task boundaries are non-trivial.

Responsibilities:

- Read the active task in the active plan.
- Identify exact files allowed to change.
- Identify required tests and expected failure mode.
- Identify relevant SOTA Core v2 invariants.
- Report any ambiguity before implementation starts.

### Implementer

Use exactly one implementation subagent at a time by default.

Responsibilities:

- Implement only the assigned task.
- Follow RED-GREEN-REFACTOR.
- Write the failing test first.
- Run the failing test and observe expected failure.
- Add minimal implementation.
- Run targeted tests and affected-area tests.
- Avoid unrelated cleanup or speculative abstraction.
- Stop on blockers instead of guessing.

### Spec Compliance Reviewer

Use after each implementation task.

Responsibilities:

- Check compliance with the active plan.
- Check compliance with `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`.
- Check all architecture invariants.
- Check that no stale MVP/Agentic Deep-Analysis assumptions were used.
- Return `PASS` or `FAIL` with exact issues.

### Code Quality Reviewer

Use after spec compliance review.

Responsibilities:

- Check type correctness, Pydantic v2 usage, SQLAlchemy boundaries, service/schema/model separation, test quality, security, and maintainability.
- Check that implementation is minimal and not over-engineered.
- Return `PASS` or `FAIL` with exact issues.

### Test Failure Debugger

Use when tests fail unexpectedly or tooling behaves inconsistently.

Responsibilities:

- Diagnose root cause.
- Propose the smallest safe fix.
- Never bypass tests, validators, hooks, proof gates, or type checks.
- Report when missing tooling or environment setup blocks verification.

### Phase Auditor

Use before marking any phase complete.

Responsibilities:

- Verify all phase exit criteria.
- Verify quality gates.
- Check plan order was preserved.
- Check no architecture invariant was weakened.
- Check full test/type/lint verification status.
- Report unresolved risks and changed files.

## 3. Runtime todo/checklist requirement

Before dispatching implementation subagents, Main Claude must create a runtime todo/checklist for the session.

The todo list must include:

- Current phase and all remaining SOTA Core v2 phases.
- Active plan tasks for the current phase.
- Current task gates: scoping, failing test, expected failure, implementation, targeted pass, affected tests, spec review, quality review, fixes, final verification, commit.
- Phase gates: full phase tests, mypy, ruff check, ruff format check, phase auditor, phase status summary.

Main Claude must update the todo list:

- before dispatching a subagent,
- after each subagent returns,
- after each test/check command,
- after each review pass/fail,
- after each fix cycle,
- after each commit,
- before moving to the next task or phase.

Subagents should report enough progress for Main Claude to update the todo accurately. Main Claude must not mark a task complete until all task gates pass.

If the session resumes after context compaction, Main Claude must reconstruct state from the runtime todo list, git log, git status, and the active plan before dispatching more implementation work.

## 4. Required task execution loop

Use this loop for every implementation task:

```text
Main Claude
  -> optionally dispatch Task Scoper
  -> dispatch exactly one Implementer
  -> inspect actual changes and test output
  -> dispatch Spec Compliance Reviewer
  -> fix all spec issues
  -> dispatch Code Quality Reviewer
  -> fix all quality issues
  -> run final verification for the task
  -> mark task complete only when all gates pass
```

If a review fails, do not continue to the next task. Fix and re-review.

## 5. Parallelization policy

### Strongly encouraged parallel work

Claude should use parallel subagents for read-only or independent verification work, including:

- Reading different plan/spec sections.
- Auditing different modules.
- Independent spec review and code quality review.
- Security review after sensitive changes.
- Debug hypothesis generation when tests fail.
- Phase-level documentation/code consistency checks.

### Forbidden by default

Do not run multiple implementation subagents in parallel when they may touch overlapping files, shared schemas, common services, database models, API routing, test fixtures, or package configuration.

Forbidden examples:

- Two agents editing `src/de_forge/services/*` at the same time.
- Two agents editing schema files that depend on each other.
- One agent refactoring a module while another writes tests for the same module.
- One agent updating the active plan while another implements from it.

### Allowed only with explicit safe boundaries

Parallel implementation is allowed only when all are true:

1. The active plan identifies independent tasks.
2. File ownership is disjoint.
3. Tests are disjoint or read-only shared fixtures are stable.
4. Main Claude can merge/review changes safely.
5. No database migration, package config, public schema, or central registry file is shared.

If any condition is uncertain, use sequential implementation.

## 6. Worktree and conflict policy

Use worktree isolation only when the current Claude CLI environment is inside the correct git repository and worktree creation is reliable.

Preferred strategy for DE-Forge implementation:

- Main working tree for sequential task implementation.
- Optional isolated worktrees for read-only research, experimental prototypes, or review when supported.
- Do not keep stale worktrees after a task finishes.
- Before destructive worktree cleanup, ask the user unless the user has already explicitly authorized that exact cleanup scope.

If worktree isolation fails, continue with non-isolated read-only subagents for research/review and keep implementation sequential in the main working tree.

## 7. Implementer prompt template

Use this template when dispatching an implementation subagent:

```text
You are implementing exactly Task <N> from:
<active-plan-path>

Read and obey:
- docs/operational/START_HERE_FOR_CLAUDE.md
- docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md
- docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md
- docs/operational/QUALITY_GATES_SOTA_CORE_V2.md
- docs/operational/BLOCKERS_AND_ESCALATION.md
- docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md
- the assigned task section in the active plan

Constraints:
- Implement only the assigned task.
- Follow TDD strictly: failing test first, observe expected failure, minimal implementation, observe pass.
- Do not modify files outside the task unless required to make the task coherent; report any extra file before changing it when possible.
- Preserve all SOTA Core v2 architecture invariants.
- Do not add dependencies unless the active plan explicitly requires them or overnight autonomy policy clearly allows them.
- Do not commit from inside the subagent unless Main Claude explicitly delegates that step.
- Report progress in enough detail for Main Claude to update the runtime todo/checklist.
- Stop and report if blocked.

Return:
- files changed
- tests added or changed
- commands run
- expected failure evidence
- passing evidence
- runtime todo/checklist updates needed
- blockers or risks
```

## 8. Spec compliance reviewer prompt template

```text
Review the current changes for SOTA Core v2 spec compliance only.

Check:
- The assigned active-plan task is fully satisfied.
- No unrelated scope was added.
- No architecture invariant was weakened.
- No raw-report-to-production-rule path exists.
- DetectionSpec/evidence/proof/human-review gates are preserved where relevant.
- ATT&CK modeling uses Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field where relevant.
- No stale MVP/Agentic Deep-Analysis assumptions were used.

Return PASS or FAIL.
If FAIL, list exact required fixes and affected files.
```

## 9. Code quality reviewer prompt template

```text
Review the current changes for code quality, maintainability, testing quality, and security.

Check:
- Minimal implementation, no speculative abstractions.
- Clear schema/model/service boundaries.
- Type hints and mypy-friendly code.
- Pydantic v2 patterns.
- SQLAlchemy boundaries where relevant.
- Tests are meaningful and fail for the right reason.
- No security issues, secret leakage, command injection, unsafe file handling, or silent validator bypass.
- No unrelated formatting or churn.

Return PASS or FAIL.
If FAIL, list exact required fixes and affected files.
```

## 10. Phase audit prompt template

```text
Audit completion of phase <phase-name> for DE-Forge SOTA Core v2.

Read:
- docs/operational/START_HERE_FOR_CLAUDE.md
- docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md
- docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md
- docs/operational/QUALITY_GATES_SOTA_CORE_V2.md
- docs/operational/BLOCKERS_AND_ESCALATION.md
- docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md
- completed phase plan

Check:
- All phase tasks are complete.
- All exit criteria are satisfied.
- Required tests/type/lint checks passed or missing tooling is clearly reported.
- No later phase was started prematurely.
- No architecture invariant was weakened.
- No stale docs guided implementation.
- Changed files match the phase scope.

Return PASS or FAIL with exact gaps.
```

## 11. Completion rule

A task is not complete until:

1. Implementer reports completion.
2. Main Claude inspects the result.
3. Spec Compliance Reviewer passes.
4. Code Quality Reviewer passes.
5. Required tests pass or a documented environment blocker is escalated.
6. No unrelated changes remain.

A phase is not complete until a Phase Auditor passes.

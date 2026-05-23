# SOTA Core v2 Full Completion Execution Design

Date: 2026-05-23
Status: Proposed for implementation planning
Related baseline: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`

## 1. Goal

Execute and complete all remaining DE-Forge SOTA Core v2 work in a single controlled session with maximum correctness, preserving all architecture invariants, and producing verification-backed completion evidence for all five mandatory phases.

This execution design constrains *how* implementation proceeds, not *what* product architecture changes. Product architecture remains governed by the approved SOTA Core v2 design spec and phase plans.

## 2. Scope and boundaries

In scope:

- Complete remaining tasks across Phase 1 -> Phase 5 in required order.
- Use strict per-task TDD gates (red -> green -> refactor).
- Use two-stage review per task (spec compliance, then code quality).
- Run phase-level verification gates before phase exit.
- Produce task-scoped local commits for verified work.

Out of scope:

- Replacing approved SOTA Core v2 architecture.
- Bypassing or weakening mandatory invariants/gates.
- Pushing/publishing external state without explicit user request.

## 3. Execution architecture: single-writer, parallel-readers

### 3.1 Control plane

Main session agent is the execution controller and sole final decision point for:

- task start/finish decisions,
- review finding prioritization,
- fix acceptance,
- commit boundaries,
- phase exit decisions.

Runtime todo is the live control ledger and must be updated before/after every meaningful step.

### 3.2 Write isolation policy

Only one implementation writer is active at a time:

- one implementation subagent, or
- main session agent directly.

No parallel code-writing paths are allowed.

### 3.3 Parallel acceleration policy

Parallel subagents are allowed only for independent read-only work:

- spec-to-code trace audits,
- quality audits,
- invariant checks,
- test impact mapping,
- phase preflight analysis,
- docs consistency checks.

All synthesis/merge decisions remain with the main session agent.

## 4. Per-task lifecycle contract

Each plan task must pass this lifecycle in order:

1. Scope task against active phase plan and SOTA v2 invariants.
2. Write failing test first.
3. Execute failing test and confirm expected failure reason.
4. Implement minimum code to satisfy test.
5. Re-run targeted test and confirm pass.
6. Run affected-area tests.
7. Run Spec Compliance Review (subagent).
8. Fix findings and re-review until clean.
9. Run Code Quality Review (subagent).
10. Fix findings and re-review until clean.
11. Run task verification commands.
12. Create task-scoped commit.
13. Mark task complete in runtime todo.

A task may not advance if any prior gate is unresolved.

## 5. Review topology

For each task, use two independent review passes:

- Review A: Spec Compliance
  - validates plan/spec alignment,
  - checks invariant preservation,
  - checks acceptance criteria completeness.
- Review B: Code Quality
  - validates correctness and safety,
  - checks simplicity/YAGNI/DRY compliance,
  - checks maintainability and test quality.

If either review returns blocking findings, implementation must re-enter fix loop before continuing.

## 6. Verification and evidence strategy

### 6.1 Evidence-before-assertion rule

No completion/fix/pass claim is allowed without command output evidence from the current session.

Historical claims from previous sessions are context, not proof.

### 6.2 Task-level verification cadence

At minimum per task:

- RED evidence (failing test),
- GREEN evidence (targeted test pass),
- affected-tests pass evidence,
- post-fix re-verification evidence after each review-fix cycle.

### 6.3 Phase-level verification cadence

Before phase exit, run required quality gates from `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`, including:

- pytest phase/full suite as required,
- `mypy src/`,
- `ruff check src/ tests/`,
- `ruff format --check src/ tests/`.

Phase exit is blocked until all required gates pass.

## 7. Provider-dependent resilience policy

Primary execution assumes provider auth is healthy.

If provider-dependent checks fail due to transient auth/runtime issues:

1. record failure evidence,
2. apply bounded retry,
3. continue independent local verification work where safe,
4. return to provider-dependent gates and complete them before closure.

No provider-dependent gate may be silently skipped.

## 8. Artifact and change hygiene

- Temporary debug/helper scripts may be created only when needed and must be removed after use.
- Commits must include only task-relevant files.
- Never commit secrets, `.env`, local db/wal/shm, lock/session/cache artifacts.
- Never use destructive git shortcuts to bypass review/verification problems.

## 9. Commit and completion policy

### 9.1 Task completion definition

Task is complete only when:

- TDD cycle is fully evidenced,
- both review gates pass,
- task verification passes,
- commit is created with scoped changes,
- runtime todo updated.

### 9.2 Phase completion definition

Phase is complete only when:

- all phase tasks are complete,
- required phase quality gates pass,
- phase-level review/audit outcomes are clean,
- relevant traceability/governance docs are reality-aligned when required by plan scope.

### 9.3 Program completion definition (Phase 1 -> 5)

SOTA Core v2 execution is complete only when:

- all five phases meet their exit criteria,
- end-to-end pipeline path remains invariant-safe,
- required runtime/API/UI smoke evidence is present,
- no open blocker remains unresolved.

## 10. Risk controls and stop conditions

Immediate stop/escalation is required if any action would:

- introduce raw-report-to-rule bypass,
- bypass DetectionSpec-first requirement,
- downgrade citation mismatch to warning,
- allow failed/unknown required proof obligations into final selection,
- bypass mandatory human review before export,
- create unbounded agent loops,
- proceed with unrelated work while tests are failing.

## 11. Expected outcomes

By applying this execution design:

- throughput is increased via parallel read-only analysis,
- correctness is protected by single-writer discipline,
- quality is protected by mandatory TDD + dual reviews,
- completion claims are audit-ready through evidence-backed verification.

# DE-Forge SOTA Core v2 Execution Kit

Date: 2026-05-21
Purpose: Source-of-truth index for autonomous Claude CLI implementation of DE-Forge SOTA Core v2.

## 1. Mission

Implement DE-Forge as a single-user, production-grade, proof-carrying, evidence-graph controlled multi-agent detection engineering system.

Primary priorities:

1. Highest practical detection accuracy.
2. Strong evidence/citation faithfulness.
3. High automation with human final review.
4. Full audit trail.
5. Minimal user questions during implementation.

The target architecture is documented in:

- `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`

The mandatory subagent strategy is documented in:

- `docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md`

The first executable plan is:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`

## 2. Current project reality

As of 2026-05-23, the repository includes substantial SOTA Core v2 implementation across services, API/UI/runtime surfaces, and broad tests.

Session reality check (authoritative for current state):

- `pytest -q`
- `mypy src`
- `ruff check .`

Treat historical milestone metrics as non-authoritative unless re-verified in the current source tree.

## 3. Mandatory execution order

Claude must execute implementation in this order unless a later approved plan explicitly changes it:

1. Foundation plan: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`.
2. Detection AST + Sigma compiler plan: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`.
3. Validation, oracle, and regression plan: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`.
4. Controlled LLM agents plan: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`.
5. Orchestrator, API, UI, and dashboard plan: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`.
6. Future benchmark adapter plan after product-mode quality is stable.

Do not start agents, UI, or benchmark work before the deterministic foundation passes.

## 4. Required Superpowers workflow

For development work, Claude must follow the repository Superpowers workflow:

1. Use the approved design spec.
2. Use writing-plans for implementation plans.
3. Use `subagent-driven-development` as the default execution mode.
4. Follow `docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md`.
5. Use one implementation subagent at a time by default.
6. Use parallel subagents aggressively for read-only research, independent review, debugging, and phase audits.
7. Use TDD for each task: red, green, refactor.
8. Use two-stage review after each implementation task:
   - spec compliance review,
   - code quality review.
9. Use verification-before-completion before claiming completion.

## 5. Runtime todo/checklist policy

Claude must create and maintain a runtime todo/checklist for every implementation session.

Required top-level todo items:

1. Phase 1: deterministic foundation.
2. Phase 2: Detection AST and Sigma compiler.
3. Phase 3: validation, oracle, and regression.
4. Phase 4: controlled LLM agents.
5. Phase 5: orchestrator, API, UI, and dashboard.

For the active phase, expand todo items to the active plan's tasks. For the active task, expand todo items to these gates:

1. Scope the task against the active plan and spec.
2. Dispatch or perform Task Scoper when needed.
3. Write failing test.
4. Run failing test and confirm expected failure.
5. Implement minimal code.
6. Run targeted test and confirm pass.
7. Run affected tests.
8. Dispatch Spec Compliance Reviewer.
9. Fix spec review issues and re-review.
10. Dispatch Code Quality Reviewer.
11. Fix quality review issues and re-review.
12. Run final task verification.
13. Commit task-scoped changes.
14. Mark task complete.

For phase completion, expand todo items to phase tests, mypy, ruff check, ruff format check, phase audit, and phase status summary.

Runtime todo rules:

- Update the todo list after every meaningful implementation step.
- Update before and after subagent dispatch.
- Update after every test/check command.
- Update after every commit.
- Never mark a task complete while tests, reviews, verification, or commit policy are incomplete.
- On resume or context compaction, reconstruct state from todo list, git log, git status, and the active plan before continuing.

## 6. Autonomous implementation policy

Claude may proceed autonomously when:

- The action is local and reversible.
- The action follows an approved spec/plan.
- The change is within the current plan's scope.
- The task has clear tests and acceptance gates.
- No secrets, external systems, destructive operations, or user data deletion are involved.

Claude must ask the user before:

- Changing approved architecture scope.
- Adding a new provider/model strategy.
- Introducing external services not in the plan.
- Deleting files, branches, worktrees, or user data.
- Pushing, force-pushing, publishing, or creating PRs.
- Changing security-sensitive behavior.
- Bypassing tests, hooks, validators, or proof gates.
- Proceeding when the plan/spec contradicts observed code and no safe interpretation exists.

## 7. Non-negotiable architecture invariants

1. No raw-report-to-production-rule path.
2. DetectionSpec is mandatory before rule generation.
3. Evidence citations must be exact and verified.
4. ATT&CK modeling uses Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field.
5. Required proof obligations must be proven before final candidate selection.
6. Detection AST and compiler are preferred over free-form Sigma YAML generation.
7. Human review is mandatory before export.
8. Agent/refinement loops are bounded.
9. Feedback must produce regression protection.
10. Full lineage and auditability are mandatory.

## 8. First golden path

The first end-to-end target case is:

```text
English TXT report
  -> PowerShell encoded command behavior
  -> T1059.001
  -> Process Creation data component
  -> Sysmon EID 1 / Windows Security 4688
  -> verified DetectionSpec
  -> high-precision Sigma candidate
  -> static validation
  -> proof obligations
  -> human review
```

All later features should preserve this path.

## 9. Quality gates

Before any task is marked complete:

- Relevant failing test was written first.
- Failure was observed.
- Minimal implementation was added.
- Relevant tests pass.
- Existing tests pass for affected area.
- Spec compliance review passes.
- Code quality review passes.
- No unrelated changes are included.

Before any phase is marked complete:

- `pytest tests/ -v --cov=src --cov-report=term-missing` passes, or the phase-specific equivalent passes if full suite is not yet available.
- `mypy src/` passes.
- `ruff check src/ tests/` passes.
- `ruff format --check src/ tests/` passes.

## 10. How to handle stale documentation

If documentation conflicts with current code:

1. Trust current source tree for implementation reality.
2. Trust `2026-05-21-de-forge-sota-core-v2-design.md` for target architecture.
3. Trust the active plan for exact implementation steps.
4. Update stale docs only when the active plan includes documentation alignment.
5. Do not silently implement against stale claims such as unverified test counts.

## 11. Handoff prompt for a fresh Claude CLI session

Use this prompt when starting a new autonomous implementation session:

```text
Read `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md` first. Then read `docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md` and the approved design spec `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`. Create a runtime todo/checklist that mirrors phases, active-plan tasks, TDD gates, review gates, verification gates, and commit checkpoints. Then execute the active plan `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md` task by task using Superpowers subagent-driven-development. Update the runtime todo after every meaningful step. Use one implementation subagent at a time by default, use parallel subagents aggressively for research/review/debug/audit, follow TDD strictly, run the specified tests, perform spec compliance and code quality reviews after each task, and only ask the user when the autonomous decision policy requires it.
```

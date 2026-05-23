# Project Guidelines for Claude Code

## Project Identity

Project name: DE-Forge

Full name: Evidence-Grounded AI-assisted Detection Rule Generation from Threat Reports

DE-Forge is a single-user, production-grade, proof-carrying, evidence-graph controlled multi-agent detection engineering system. It reads English TXT/PDF cyber threat reports and produces evidence-grounded Sigma detection artifacts through deterministic validators, controlled agents, proof obligations, and mandatory human review.

## Current Source of Truth

The active architecture and implementation track is **DE-Forge SOTA Core v2**.

Claude CLI sessions must start here:

- `docs/operational/START_HERE_FOR_CLAUDE.md`

Then follow, in order:

1. `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`
2. `docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md`
3. `docs/operational/AUTONOMOUS_DECISION_POLICY.md`
4. `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`
5. `docs/operational/BLOCKERS_AND_ESCALATION.md`
6. `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
7. The active SOTA Core v2 implementation plan.

Before execution, load `docs/governance/canonical_manifest.yaml` and perform manifest preflight.

## Current Project Reality

The repository now contains substantial implementation beyond the initial skeleton phase. Treat status assertions as verification-bound: establish current truth from up-to-date verification commands and the current code and test tree, not from older progress claims.

## Mandatory Execution Order

Execute the SOTA Core v2 plans in this order:

1. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`
2. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`
3. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`
4. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`
5. `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`

Do not start agents, UI, dashboard, benchmark, or deployment work before the deterministic foundation and prerequisite plans pass.

## Non-Negotiable Architecture Invariants

1. No raw-report-to-production-rule path exists.
2. DetectionSpec is mandatory before rule generation.
3. Evidence citations are exact and verified.
4. ATT&CK modeling uses:

```text
Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field
```

5. Required proof obligations must be proven before final candidate selection.
6. Detection AST and compiler are the preferred source for Sigma YAML.
7. Human review is mandatory before export.
8. Agent/refinement loops are bounded.
9. Feedback creates regression protection.
10. Full artifact lineage and auditability are preserved.

Any change that weakens these invariants is a hard failure.

## Core Pipeline

The mandatory production path is:

```text
raw report -> evidence graph -> verified DetectionSpec -> detection AST -> compiled Sigma -> validation/proof -> human review
```

The system must never generate production detection rules directly from raw report text.

## Model and Provider Configuration

Use one provider/model for all agent roles unless the user explicitly approves a different strategy.

- Provider type: OpenAI-compatible
- Base URL: `https://shopapikey.com/v1`
- API key env var: `OPENAI_API_KEY`
- Model: `cx/gpt-5.5`

Do not add fallback provider/model logic unless explicitly requested by the user.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- Pydantic v2
- Pydantic Settings
- SQLite local default runtime
- PostgreSQL-compatible schema design for future migration
- pytest + pytest-asyncio + pytest-cov + httpx
- ruff + mypy
- uv package manager when available

## Superpowers Workflow

For development work, follow the repository Superpowers workflow:

1. Use the approved SOTA Core v2 design spec.
2. Use the active SOTA Core v2 implementation plan.
3. Use `subagent-driven-development` as the default execution mode.
4. Follow `docs/operational/SUBAGENT_EXECUTION_STRATEGY_SOTA_CORE_V2.md`.
5. Use one implementation subagent at a time by default.
6. Use parallel subagents aggressively for read-only research, independent review, debugging, and phase audits.
7. Use `test-driven-development` for every implementation task.
8. Use two-stage review after each task:
   - spec compliance review,
   - code quality review.
9. Use `verification-before-completion` before claiming any task or phase complete.

## Runtime Todo and Checklist Policy

Claude CLI must create and maintain a runtime todo/checklist for every implementation session.

The todo list must mirror:

- all SOTA Core v2 phases,
- active phase plan tasks,
- per-task TDD gates,
- spec compliance review,
- code quality review,
- final verification,
- task-scoped commit,
- phase-level tests, type checks, lint checks, format checks, and phase audit.

Update the todo list after every meaningful step, before and after subagent dispatches, after each test/check command, after each review result, after each fix cycle, and after each commit. Do not mark a task complete until tests, reviews, verification, and commit policy all pass.

On resume or context compaction, reconstruct progress from the todo list, git log, git status, and active plan before continuing.

## Testing and Quality Gates

Follow `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`.

Universal task gates:

1. Write a failing test first.
2. Run it and observe failure for the expected reason.
3. Add minimal implementation.
4. Run the targeted test and observe pass.
5. Run affected area tests.
6. Complete spec compliance review.
7. Complete code quality review.
8. Avoid unrelated changes.
9. Preserve all architecture invariants.

Phase-level verification commands are defined in the quality gates document and in each active plan.

## Overnight End-to-End Autonomy Policy

When the user asks Claude CLI to run unattended or overnight, complete DE-Forge SOTA Core v2 end-to-end with maximum safe autonomy inside the approved plan/spec.

Claude may autonomously:

- Research the codebase, active docs, tests, and declared dependency documentation before choosing an implementation.
- Choose the best in-scope approach when multiple approaches satisfy the approved SOTA Core v2 design, active plan, tests, and invariants.
- Split large plan tasks into smaller internal subtasks without changing the approved outcome.
- Set up or repair the development environment needed for verification, preferring project-local setup and installing/downloading missing tools or packages as needed.
- Add missing dependencies to project metadata when clearly required by the approved plan and no existing dependency satisfies the need.
- Use fake placeholder API keys for config, schema, unit, and non-network tests when real keys are unavailable.
- Fix local test, type, lint, formatting, import, and package-structure failures caused by current-session implementation.
- Update tests when they are clearly wrong relative to the approved spec/plan.
- Create, modify, or delete files required by the active plan, plus disposable temporary/task artifacts Claude created in the current session.
- Continue across tasks and phases when all gates pass.

Claude must not stop solely because package managers, local tools, declared dependencies, clearly required missing dependencies, or API keys are missing. It should self-install or configure what is needed for local verification, use placeholder API keys for non-live tests, and stop only when continuing could endanger the repository, delete user work/data, publish or push external state, bypass gates, or change approved architecture/security behavior.

## Commit and Local Conflict Policy

For SOTA Core v2 end-to-end implementation, the user authorizes Claude CLI to create local git commits during the implementation session.

- Commit after each completed, reviewed, and verified task.
- Commit only files related to the current task.
- Never stage or commit unrelated modified/untracked files.
- Never commit secrets, `.env` files, local databases, cache files, or Claude/session lock files.
- Never use `--no-verify` unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Do not push, force-push, publish, or create PRs unless explicitly requested.
- Resolve conflicts caused by Claude's own current-session changes when the active SOTA Core v2 plan/spec/tests clearly determine the correct result.
- Ask before resolving conflicts involving pre-existing user changes, unclear safe commit boundaries, architecture/scope/security changes, or destructive git operations.

## Blockers and Escalation

Follow `docs/operational/BLOCKERS_AND_ESCALATION.md`.

Ask the user only when required by that policy. Otherwise proceed autonomously inside the approved SOTA Core v2 spec and active plan.

Must not continue when:

- a raw-report-to-rule path is introduced or required,
- DetectionSpec-first is bypassed,
- citation mismatch is treated as warning instead of hard failure,
- a candidate with failed/unknown required proof obligations would be selected,
- human review would be skipped before export,
- an agent loop becomes unbounded,
- tests are failing and the next action is unrelated to fixing them,
- the user explicitly says stop, pause, or wait.

## Legacy Documentation Warning

Older DE-Forge documents from 2026-05-20 and the previous Agentic Deep-Analysis/MVP track are superseded for implementation. Do not use them as execution instructions for SOTA Core v2.

If an older document conflicts with the SOTA Core v2 spec, active SOTA Core v2 plan, quality gates, or blocker policy, trust SOTA Core v2.

## Coding Standards

- Type hints are required for application code.
- API routes should stay thin; business logic belongs in services.
- Schemas define contracts; models define persistence; agents produce structured outputs; deterministic services validate and gate outputs.
- Avoid speculative abstractions and unrelated refactors.
- Do not introduce new dependencies unless approved by the active plan or the user.
- Do not log secrets or raw sensitive model/report content outside approved audit storage.

## Build Priority

1. Product-mode correctness, traceability, and deterministic gates.
2. Evidence/citation faithfulness.
3. Rule quality and validation depth.
4. Human review and auditability.
5. Benchmark adapters after the product-mode core is stable.

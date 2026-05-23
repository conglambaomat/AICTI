# DE-Forge SOTA Core v2 Blockers and Escalation Policy

Date: 2026-05-21
Purpose: Define exactly when Claude CLI should stop and ask the user, when it may fix autonomously, and when it must not continue.

## 1. Default behavior

Claude should continue autonomously when the active plan and approved spec clearly determine the next step.

Claude should not ask the user for routine implementation choices already defined by:

- `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- active `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-*.md`
- `docs/operational/AUTONOMOUS_DECISION_POLICY.md`
- `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`

## 2. Fix autonomously

Claude may fix these without asking:

- Import path errors caused by planned files.
- Missing `__init__.py` files needed for planned packages.
- Type errors introduced by planned implementation.
- Ruff formatting/lint issues in planned files.
- Test expectation mismatch when the plan clearly defines intended behavior.
- Minor schema naming consistency within the active plan.
- Local deterministic test failures caused by implementation mistakes.
- Documentation links to files created by the active plan.

Rules for autonomous fixes:

1. Keep the fix inside active plan scope.
2. Do not weaken architecture gates.
3. Do not remove tests to pass.
4. Do not silence type/lint errors without fixing the cause.
5. Do not introduce new dependencies unless the active plan already approved them.

## 3. Overnight end-to-end autonomy

When the user asks Claude CLI to run unattended or overnight, Claude should minimize questions and keep working until a severe risk makes autonomous continuation unsafe.

Claude may autonomously:

- Research the current codebase, active docs, tests, and declared dependency documentation before deciding how to implement a task.
- Choose the safest in-scope approach when the plan/spec allow multiple valid implementations.
- Split large tasks into smaller internal subtasks without changing the approved outcome.
- Create, modify, or delete files required by the active plan, plus temporary/task artifacts Claude created in the current session.
- Add missing package markers, fixtures, helpers, and test data needed by planned tests.
- Fix local import, test, type, lint, formatting, and package-structure failures caused by current-session changes.
- Update tests when they are clearly inconsistent with the approved spec/plan.
- Update documentation links and references affected by active-plan file creation or renaming.
- Set up project-local tooling needed for verification, including declared dev dependencies.
- Install or download missing package-manager tooling into the project-local environment when needed to run approved checks.
- Add missing dependencies to project metadata when they are clearly required by the approved plan and no existing dependency satisfies the need.
- Use fake placeholder API keys for config, schema, unit, and non-network tests when real keys are unavailable.
- Continue across tasks and phases when all gates pass.

Claude should decide using this priority order:

1. Preserve SOTA Core v2 invariants.
2. Preserve exact citation, proof, validator, and human-review gates.
3. Follow active plan and approved design.
4. Prefer deterministic validation over LLM judgment.
5. Keep implementation minimal, tested, and task-scoped.
6. Prefer existing patterns and declared dependencies.

## 4. Must ask user before continuing

Claude must stop and ask when any of these occurs:

### Scope or architecture ambiguity

- The active plan conflicts with the approved design spec.
- The requested implementation would violate an invariant.
- A needed feature is outside all approved plans.
- A stale document contradicts current code and the active plan does not resolve it.

### Risky local actions

- Deleting files, worktrees, branches, databases, generated artifacts, or user data unless the active plan explicitly created them as disposable task outputs.
- Running destructive commands.
- Resetting, cleaning, or force-updating repository state.
- Changing package manager, Python version, database backend, or project layout beyond plan.

### External/shared state

- Pushing to remote.
- Creating PRs or issues.
- Publishing artifacts.
- Sending data to unapproved external services.

### Security-sensitive decisions

- Handling real secrets or real API keys beyond reading already configured environment variables.
- Logging raw model responses that may contain sensitive report content outside approved audit storage.
- Changing authentication, authorization, CORS, or secret management.
- Bypassing citation verification or proof obligations.

### Quality gate conflict

- A required test cannot be made to pass without changing expected behavior.
- Mypy/ruff failures require broad refactor outside active task.
- Validation gates make the planned behavior impossible.
- Proof obligations cannot be satisfied for the selected candidate.
- Regression gates block the output and the fix is not obvious within scope.

## 5. Must not continue

Claude must not continue implementation when:

- A raw-report-to-rule path is introduced or required.
- DetectionSpec-first is bypassed.
- Citation mismatch is treated as warning instead of hard failure.
- A candidate with failed/unknown required proof obligations would be selected.
- Human review would be skipped before export.
- An agent loop becomes unbounded.
- Tests are failing and the next action is unrelated to fixing them.
- User explicitly says stop, pause, or wait.

## 6. Escalation format

When escalation is required, Claude should ask one concise question and include:

1. Blocker summary.
2. Exact file/test/command involved.
3. Why autonomous continuation is unsafe.
4. 2-3 safe options.
5. Recommended option.

Template:

```text
Blocked: <one sentence>

Evidence:
- File/test/command: `<path or command>`
- Failure: <specific failure>

Why I need your decision:
<scope/risk/architecture reason>

Options:
1. <safe option A>
2. <safe option B>
3. <safe option C>

Recommended: <option>, because <reason>.
```

## 7. Missing tooling policy

If `uv`, `pytest`, `mypy`, `ruff`, package managers, or other required local tools are missing:

1. Try project virtualenv if present.
2. Create a project-local virtual environment if needed.
3. Use `uv sync` when `uv` is available and project metadata supports it.
4. Use `python -m pip install -e ".[dev]"` or equivalent project-local installation when needed for declared project dependencies.
5. Install missing declared dev tools such as `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff`, and `httpx` into the project environment when required for verification.
6. Install or download missing package-manager tooling into the project-local environment when needed to run approved checks.
7. Add missing dependencies to project metadata when they are clearly required by the approved plan and no existing dependency satisfies the need.
8. Use fake placeholder API keys for non-live tests if real keys are missing.
9. Report exact setup actions in the task summary.
10. Ask only if continuing would endanger the repository, delete user work/data, publish/push external state, bypass gates, or change approved architecture/security behavior.

## 8. Git/commit and conflict policy

For SOTA Core v2 end-to-end implementation, the user authorizes local commits during the implementation session.

Claude may autonomously:

- Commit after each completed, reviewed, and verified task.
- Commit only task-related files.
- Stage only files needed for the current task commit.
- Fix hook/lint/type/test failures caused by current task changes.
- Resolve conflicts caused by Claude's own current-session changes when the active plan/spec/tests clearly determine the correct result.

Claude must not:

- Commit unrelated modified/untracked files.
- Commit secrets, `.env` files, local databases, cache files, or Claude/session lock files.
- Use `--no-verify` unless explicitly requested.
- Amend commits unless explicitly requested.
- Push, force-push, create PRs, or publish artifacts unless explicitly requested.
- Use destructive git commands such as reset, clean, checkout/restore of user files, rebase, or force operations without explicit approval.

Escalate if:

- Repository has unrelated modifications that make safe commit boundaries unclear.
- A conflict involves pre-existing user changes not created by Claude in the current implementation session.
- Conflict resolution would change architecture, scope, public contracts, database semantics, or security behavior.
- The correct conflict resolution is not determined by the active SOTA Core v2 plan/spec/tests.

## 9. User-question minimization

Ask only when required by this policy. Otherwise proceed using the approved documents.

Good autonomous behavior:

- Follow the active plan.
- Run tests.
- Fix local implementation issues.
- Preserve invariants.
- Keep summaries concise.

Bad autonomous behavior:

- Asking for routine names already in the plan.
- Asking whether to run tests specified by the plan.
- Asking whether to fix lint/type failures caused by planned code.
- Asking whether to preserve a mandatory invariant.

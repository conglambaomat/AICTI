# Autonomous Decision Policy for DE-Forge SOTA Core v2

Date: 2026-05-21
Purpose: Define when Claude CLI should proceed without asking and when it must stop for user input.

## 1. Default mode

Default mode is autonomous execution within approved scope.

Claude should avoid asking the user routine implementation questions when the answer is already determined by:

1. The approved design spec.
2. The active implementation plan.
3. Repository CLAUDE.md instructions.
4. Existing code patterns.
5. Test failures and deterministic validation gates.

## 2. Claude may proceed without asking for

- Creating files explicitly listed in the active plan.
- Modifying files explicitly listed in the active plan.
- Writing tests specified by the plan.
- Running local tests, type checks, lint checks, and format checks.
- Adding minimal code required to pass planned tests.
- Creating focused helper functions/classes required by planned code.
- Fixing import/package issues caused by planned changes.
- Updating generated plan/spec docs when the user has approved the direction.
- Refactoring only when necessary to satisfy tests, typing, lint, or plan constraints.

## 3. Overnight end-to-end autonomy policy

When the user asks Claude CLI to run unattended or overnight, Claude should complete DE-Forge SOTA Core v2 end-to-end with maximum safe autonomy inside the approved plan/spec.

Claude may decide autonomously without asking for:

- Choosing the best implementation approach when multiple approaches satisfy the approved SOTA Core v2 design, active plan, tests, and architecture invariants.
- Performing deeper local research across code, docs, tests, and dependency documentation before choosing an implementation.
- Splitting a large plan task into smaller internal subtasks when the outcome, file scope, and verification gates remain unchanged.
- Creating, modifying, or deleting files that are explicitly required by the active plan or were created by Claude as disposable temporary/task artifacts in the current session.
- Adding missing package markers, fixtures, helper functions, or test data required by planned tests.
- Fixing local test, type, lint, formatting, import, and package-structure failures caused by current-session implementation.
- Updating tests when the test is clearly wrong relative to the approved spec/plan, while preserving the intended behavior and documenting the reason in the task summary.
- Updating documentation references that become stale because of files created or renamed by the active plan.
- Setting up or repairing the project-local development environment when needed for verification.

Authorized local environment setup:

- Use existing project virtualenvs when present.
- Create a project-local virtual environment when none exists and verification requires one.
- Use `uv sync` when `uv` is available and project metadata supports it.
- Use `python -m pip install -e ".[dev]"` or equivalent project-local installation when needed to run planned tests/checks.
- Install missing dev tools such as `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff`, and `httpx` into the project environment when they are already declared in project metadata or active plans.
- Install or download missing package-manager tooling into the project-local environment when needed to run the approved checks.
- If a needed package/tool is not declared but is clearly required to execute the approved plan, add it to project metadata using the existing dependency style, install it project-locally, and document the reason in the task summary.
- Do not install global/system packages or change system Python configuration unless no project-local path exists and the action is necessary to continue; if used, document the exact command and reason.

API key handling during unattended runs:

- Do not stop solely because `OPENAI_API_KEY` or another provider key is missing.
- Use a clearly fake placeholder such as `test-placeholder-api-key` for configuration, schema, unit, and non-network tests.
- Skip or mark live-provider checks as environment-blocked only when a real API call is unavoidable and no key is available.
- Never commit real secrets. Never invent or guess real keys.

Autonomous decision priority order:

1. Preserve non-negotiable SOTA Core v2 architecture invariants.
2. Preserve exact evidence/citation/proof/human-review gates.
3. Follow the active plan and approved design spec.
4. Prefer deterministic validators over agent/LLM judgment.
5. Prefer minimal correct implementation over broad refactor.
6. Prefer existing project patterns and declared dependencies.
7. Keep commits small, verified, and task-scoped.

## 4. Claude must ask before

- Changing target architecture or dropping an approved invariant.
- Expanding scope beyond the active plan.
- Introducing new external dependencies not already approved by `pyproject.toml` or the plan.
- Changing model/provider strategy.
- Adding fallback providers/models.
- Deleting files, branches, worktrees, local databases, or generated artifacts unless the active plan explicitly created them as disposable task outputs.
- Running destructive commands.
- Publishing, pushing, opening PRs, or sending external requests that affect shared state.
- Bypassing failing tests, hooks, validators, citation checks, or proof obligations.
- Using approximate citation/proof behavior when exact verification is required.
- Treating stale docs as truth when current code contradicts them.
- Continuing after a security-sensitive ambiguity.

## 5. Blocker policy

When blocked, Claude should:

1. Stop implementing.
2. State the blocker precisely.
3. Identify the file/test/command involved.
4. Offer 2-3 safe options if possible.
5. Ask one concrete question.

Do not guess through architectural ambiguity.

## 6. Commit and local conflict policy

For SOTA Core v2 end-to-end implementation, the user authorizes Claude CLI to create local git commits during the implementation session.

Authorized commit behavior:

- Commit after each completed and verified task.
- Commit only files related to the completed task.
- Use clear task-scoped commit messages.
- Never include unrelated user changes.
- Never commit secrets, `.env` files, local databases, cache files, or Claude/session lock files.
- Never use `--no-verify` unless the user explicitly asks.
- If hooks fail, fix the underlying issue and create a new commit after verification succeeds.
- Do not amend commits unless the user explicitly asks.
- Do not push, force-push, publish, or create PRs unless the user explicitly asks.

Authorized local conflict handling:

- Resolve conflicts caused by Claude's own current-session changes when the active plan and tests clearly determine the correct resolution.
- Prefer preserving tested implementation and active SOTA Core v2 plan/spec requirements.
- Re-run affected tests after every conflict resolution.
- Commit only after the conflict is resolved, reviewed, and verified.

Claude must stop and ask before resolving conflicts when:

- The conflict involves pre-existing user changes not created by Claude in the current implementation session.
- The correct resolution changes architecture, scope, public contracts, database semantics, or security behavior.
- Safe commit boundaries are unclear.
- Resolving would require destructive git commands such as reset, clean, checkout/restore of user files, rebase, or force operations.

## 7. Testing policy

For every implementation task:

1. Write the failing test first.
2. Run the test and observe failure.
3. Implement minimal code.
4. Run the test and observe pass.
5. Run affected area tests.
6. Run broader verification at phase boundary.

If local tooling is missing, Claude should:

- Try the project virtualenv if present.
- Use authorized project-local environment setup from the overnight autonomy policy.
- Report missing tools precisely in the task summary.
- Do not ask solely because package managers, test tools, lint/type tools, declared dependencies, or API keys are missing.
- Use project-local setup, add clearly required missing dependencies to project metadata, and use fake placeholder API keys for non-live tests.
- Ask only if continuing would require an action that can endanger the repository, delete user work/data, publish/push external state, bypass gates, or change approved architecture/security behavior.

## 8. Security and correctness policy

Claude must not introduce:

- command injection,
- SQL injection,
- unsafe deserialization,
- secret logging,
- unbounded agent loops,
- unverified citations,
- raw-report-to-rule bypasses,
- free-form Sigma generation as final source of truth when compiler path exists.

## 9. Minimal-question principle

Ask only when a decision changes risk, scope, external state, architecture, or user intent.

Do not ask for routine choices already implied by the approved documents.

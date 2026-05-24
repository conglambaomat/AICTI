# SOTA Core v2 Reality Alignment Addendum

Date: 2026-05-23
Scope: Canonical interpretation overlay for SOTA Core v2 documentation.
Authority: This addendum supersedes conflicting wording in older SOTA Core v2 execution docs for execution decisions until those docs are realigned.

## 1) Confirmed architecture-conformant areas

The traceability matrix confirms that the current repository is substantially beyond the stale early-baseline snapshot. Execution sessions should use the matrix as the operational source of truth for current capability status.

Confirmed areas:

- Foundation primitives: R-P1-01, R-P1-02, R-P1-03.
- Artifact lineage, persistence, and graph foundation: R-P1-04, R-P1-05, R-P1-06, R-P1-07, R-P1-08.
- ATT&CK, telemetry, DetectionSpec, and proof gates: R-P1-09, R-P1-10, R-P1-11, R-P1-12, R-P1-13.
- DetectionSpec → AST → Sigma path: R-P2-01, R-P2-02, R-P2-03, R-P2-04, R-P2-05, R-P2-06, R-P2-07, R-P2-08.
- Validation, oracle, and regression services: R-P3-01 through R-P3-11.
- Controlled agent contracts and audit: R-P4-01 through R-P4-10.
- Orchestrator, API, UI, runtime, review, export, and dashboard surfaces: R-P5-01 through R-P5-10.
- Hard architecture invariants with implemented evidence: R-INV-01 through R-INV-07, R-INV-09, R-INV-10.
- Architecture invariant R-INV-08 now has explicit bounded static/dynamic refinement default assertions; future loop-policy changes must preserve bounded behavior.

## 2) Stale or contradictory statements found in current docs

| Doc | Section | Claim | Reality | Resolution |
| --- | --- | --- | --- | --- |
| `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md` | §2 Current project reality | Source tree is “early baseline-only” and reliable implementation only includes FastAPI skeleton, health endpoints, settings/config, profile constants, and small threshold tests. | Current source contains implemented services, schemas, models, API routes, UI support, runtime ops, agents, compiler path, validation/oracle/regression services, and 127 collected tests. | Treat that baseline-only statement as stale. Use the traceability matrix for current status. |
| `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md` | §3 Mandatory execution order | Do not start agents, UI, or benchmark work before deterministic foundation passes. | Agent, UI, runtime, validation, compiler, and orchestrator code already exists in the current branch. | Preserve the dependency rule for future work, but audit existing code by capability and tests rather than assuming phase order. |
| `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md` | File structure map | Several plan paths are treated as “Create” paths. | Many of the referenced capabilities already exist, and in several cases the planned paths now exist exactly. | Treat “Create” directives as historical implementation instructions. Reality-synced plans should use current evidence anchors. |
| `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md` | Prerequisites and file structure | Compiler implementation depends on prior foundation and creates AST/Sigma/compiler files. | AST, Sigma, compiler, validator, and tests are already present. | Treat compiler plan as satisfied at capability level pending full quality gates. |
| `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md` | File structure map | Validation/oracle/regression files are future created files. | Candidate, validation, oracle, feedback, and regression schemas/services/tests are present. | Treat as capability-present; future work should harden semantics rather than recreate files. |
| `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md` | File structure map | Agent files are future created files. | Controlled agent contracts, prompt registry, LLM client, agent audit, and agent tests are present. | Treat as capability-present; next work should focus on invariant and integration evidence. |
| `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md` | File structure map | Orchestrator/API/UI/dashboard files are future created files. | Orchestrator, API routes, runtime UI routes, metrics, review/export gates, readiness, ops, and tests are present. | Treat as capability-present; do not expand UI/runtime until deterministic core verification is explicit. |

## 3) Canonical interpretation rules

1. The traceability matrix is the execution-facing source of truth for current capability status.
2. Older plan files remain useful for intended architecture and acceptance gates, but their “Create” wording must not be interpreted as proof that the capability is absent.
3. If a historical plan references a path and that exact path exists, use the current file as evidence.
4. If a historical plan references a path that does not exist but equivalent capability exists elsewhere, classify the requirement as `drifted`, not automatically `missing`.
5. If a capability has code but lacks direct tests or full quality-gate execution, classify it as `partial` until verified.
6. Architecture invariants R-INV-01 through R-INV-10 remain non-negotiable.
7. Documentation realignment must not weaken any gate from hard failure to warning.
8. Code changes are out of scope for this alignment package; any implementation changes require a later code-modifying plan.
9. Full phase completion requires actual quality-gate runs, not only pytest collection.

## 4) Open questions deferred to next planning round

- Should R-INV-08 bounded agent loops be strengthened with explicit constants and direct tests, or is current orchestrator/agent behavior sufficient after line-level review?
- Should simple metric defaults in runtime/API/UI paths be hardened before any user-facing dashboard expansion?
- Should the older 2026-05-21 implementation plans be edited in place, superseded by 2026-05-22 reality-sync plans, or retained as historical baselines?
- Should future code-modifying work start with full verification of all current tests, mypy, ruff, and format checks before choosing Phase 2 or Phase 3 hardening?

## 5) Cross-references

- Traceability matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Requirement inventory: `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`
- Evidence index: `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`
- Alignment design: `docs/superpowers/specs/2026-05-22-sota-v2-plan-code-alignment-design.md`
- Alignment implementation plan: `docs/superpowers/plans/2026-05-22-sota-v2-plan-code-alignment-plan.md`

# SOTA Core v2 Governance Execution Summary

Date: 2026-05-23
Scope: One-page operational guidance for execution coordinators and future Claude CLI sessions.

## 1) Hard blockers

Do not claim any phase complete, start broader UI/runtime expansion, or export production candidates if any of these are unverified or weakened:

- R-INV-01 — No raw-report-to-rule path.
- R-INV-02 — DetectionSpec mandatory before rule generation.
- R-INV-03 — Citation exactness gate.
- R-INV-05 — Proof obligation gate.
- R-INV-06 — Detection AST + compiler path before Sigma output.
- R-INV-07 — Human review gate before export.
- R-INV-08 — Bounded agent loops.
- R-INV-09 — Feedback creates regression protection.
- R-INV-10 — Full lineage and auditability.

## 2) Must-fix documentation drifts

- The old skeleton-only project reality claim is stale. Use `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md` instead.
- Historical plan files that say “Create” for files that now exist must be treated as implementation history, not current absence.
- Phase order remains a governance rule for future work, but existing code already spans all five phases. Audit current code by capability and tests.
- R-INV-08 now has explicit bounded static/dynamic refinement default assertions; preserve these bounds when changing agent/refinement behavior.
- Full repository gates passed after the alignment package: 127 pytest tests, 93% coverage, mypy, ruff check, and ruff format check. Manual runtime/UI smoke remains required before UI/runtime release completion.

## 3) Safe deferrals

These can be deferred without weakening architecture if hard blockers remain enforced:

- Deeper adversarial/counterfactual scoring beyond current heuristic coverage.
- Rich dashboard metrics beyond current quality snapshot support.
- Full frontend graph visualization beyond current trust-oriented UI.
- Benchmark adapter or CTI-REALM integration.
- Additional ATT&CK/telemetry registry breadth beyond current curated entries.

## 4) Recommended execution order checkpoints

1. Preserve the passing repository gates: pytest, mypy, ruff check, and ruff format check.
2. Run product E2E smoke from TXT report through awaiting review and gated export.
3. Run runtime/API/UI smoke for review, dashboard, evidence graph, and readiness pages.
4. Reconfirm Phase 2 compiler-first behavior before any rule-quality expansion.
5. Reconfirm Phase 3 regression protection before adding new review/feedback workflows.
6. Keep Phase 5 API/UI/runtime work constrained until deterministic gates and manual smoke evidence are both current.

## 5) Canonical docs for future Claude CLI sessions

Read in this order before selecting the next code-modifying phase:

1. `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
2. `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`
3. `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md`
4. `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md`
5. `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md`
6. `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md`
7. `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md`

## 6) Documentation Sync Note

Date: 2026-05-23

Active guidance docs synchronized for stale baseline phrasing:

- `README.md`
- `CLAUDE.md`
- `docs/operational/START_HERE_FOR_CLAUDE.md`
- `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`

Session reality check commands (authoritative for current state):

- `pytest -q`
- `mypy src`
- `ruff check .`

## 7) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`
- Requirement inventory: `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`
- Evidence index: `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`

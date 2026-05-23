# DE-Forge SOTA Core v2 Orchestrator/API/UI/Dashboard Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Provide a reality-synced plan for orchestrator, API surface, runtime path, minimal UI, and dashboard support.

**Architecture:** Maps Phase 5 matrix rows to current orchestrator, state machine, gates, export gate, API routes, UI routes, runtime services, and e2e tests. UI/runtime work must not expand beyond deterministic-core trust boundaries.

## 1) Current reality summary

Matrix rows R-P5-01 through R-P5-10 are implemented with code and test anchors. R-P5-11 is partial because full test/type/lint/format/UI smoke gates were not run during this documentation-only pass.

Key implemented anchors:

- Run modes/states and transition guards: R-P5-01, R-P5-02.
- Hard rule/review/export gates: R-P5-03, R-P5-07.
- Auto and cautious orchestration paths: R-P5-04, R-P5-05.
- Review service and API surface: R-P5-06, R-P5-08.
- Metrics/dashboard and trust UI: R-P5-09, R-P5-10.

## 2) Strict scope boundary

- This plan does not modify orchestrator/API/UI/runtime code.
- It does not approve expanding UI/dashboard before full deterministic-core verification.
- Runtime convenience endpoints must not weaken proof/citation/review gates.

## 3) Dependency edges

- Export remains downstream of human review R-INV-07 and proof obligations R-INV-05.
- Orchestrator remains downstream of DetectionSpec-first R-INV-02 and compiler-first R-INV-06.
- UI/dashboard may show evidence but must not create production rule bypass paths.

## 4) Ordered tasks for next Orchestrator/API/UI-oriented session

1. Run full orchestrator/API/UI/dashboard gates.
   - Inputs: R-P5-11.
   - Required outcome: actual pytest/mypy/ruff/format and UI smoke evidence.
   - Verification: targeted orchestrator/API/UI tests plus quality gates.
2. Keep review/export gate evidence central.
   - Inputs: R-P5-06, R-P5-07, R-INV-07.
   - Required outcome: export always requires approved review and gate pass.
   - Verification: export route tests remain passing.
3. Prevent runtime/UI feature creep.
   - Inputs: R-P5-08, R-P5-09, R-P5-10.
   - Required outcome: UI remains trust-oriented and read/review focused until deterministic core is fully verified.
   - Verification: no new raw-report-to-rule or direct export path is introduced.

## 5) Do not assume

- Do not infer deterministic-core completion from operational/API readiness.
- Do not expand dashboard metrics without documenting whether values are computed, persisted, or placeholders.
- Do not allow export without human review.

## 6) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

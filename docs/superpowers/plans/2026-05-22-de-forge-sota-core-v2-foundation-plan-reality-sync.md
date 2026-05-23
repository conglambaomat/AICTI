# DE-Forge SOTA Core v2 Foundation Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. This plan is documentation-aligned; it does not modify code.

**Goal:** Provide a reality-synced, evidence-cited plan for the Foundation phase that reflects current repository state and remaining verification gaps.

**Architecture:** Reads from the traceability matrix and addendum. Produces an execution-ready breakdown of what is implemented, what remains partial, and what must be verified before future code-modifying work.

## 1) Current reality summary

Matrix rows R-P1-01 through R-P1-13 are implemented with code and test anchors. R-P1-14 is partial because this documentation pass only ran pytest collection, not full pytest/mypy/ruff/format gates.

Key implemented anchors:

- Hashing/idempotency: R-P1-01, R-P1-02.
- Domain errors and artifact lineage: R-P1-03, R-P1-04, R-P1-05.
- Evidence graph and citation exactness: R-P1-06, R-P1-07, R-P1-08.
- ATT&CK, telemetry, DetectionSpec, proof obligations: R-P1-09 through R-P1-13.

## 2) Strict scope boundary

- This reality-sync plan does not change source code or tests.
- It defines what future implementation sessions should verify or harden.
- Do not recreate existing modules just because the older plan says “Create”.

## 3) Dependency edges

- Foundation invariants R-INV-01 through R-INV-10 must remain satisfied before new compiler, validation, agent, or UI expansion work.
- Citation exactness R-INV-03 and proof obligations R-INV-05 are high-risk gates and must remain hard failures.

## 4) Ordered tasks for next Foundation-oriented session

1. Run full foundation quality gates.
   - Inputs: R-P1-14.
   - Required outcome: pytest/mypy/ruff/format evidence, not collect-only.
   - Verification: run the phase-specific commands from `QUALITY_GATES_SOTA_CORE_V2.md`.
2. Add line-level evidence if future auditors require exact anchors.
   - Inputs: R-P1-01 through R-P1-13.
   - Required outcome: optional refined matrix with file_path:line anchors.
   - Verification: every high-risk row still cites code and tests.
3. Preserve hard citation and proof semantics.
   - Inputs: R-P1-08, R-P1-13, R-INV-03, R-INV-05.
   - Required outcome: no doc or code path treats citation/proof failure as warning.
   - Verification: relevant tests remain passing.

## 5) Do not assume

- Do not assume the source tree is skeleton-level.
- Do not assume historical “Create” steps imply missing files.
- Do not mark Foundation complete until full quality gates run successfully.

## 6) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

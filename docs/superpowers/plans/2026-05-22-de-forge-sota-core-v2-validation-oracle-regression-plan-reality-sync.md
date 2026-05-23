# DE-Forge SOTA Core v2 Validation, Oracle, Regression Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Provide a reality-synced plan for static validation, dynamic validation, oracle scoring, and feedback-derived regression protection.

**Architecture:** Maps Phase 3 matrix rows to current validation, oracle, feedback, and regression services. Treats initial heuristic implementations as present but still requiring full quality-gate verification before phase completion.

## 1) Current reality summary

Matrix rows R-P3-01 through R-P3-11 are implemented with code and test anchors. R-P3-12 is partial because full phase gates were not run during this documentation-only pass.

Key implemented anchors:

- Candidate and portfolio schemas/services: R-P3-01, R-P3-02.
- Static validation and broad-rule rejection: R-P3-03, R-P3-04.
- Dynamic positive/benign evaluation and metrics: R-P3-05, R-P3-06.
- Adversarial and counterfactual evaluation: R-P3-07, R-P3-08.
- Oracle scoring: R-P3-09.
- Feedback-to-regression and regression blocking: R-P3-10, R-P3-11.

## 2) Strict scope boundary

- This plan does not modify validation, oracle, or regression code.
- It documents that these capabilities are present and identifies verification as the remaining phase-level requirement.

## 3) Dependency edges

- Compiler rows R-P2-01 through R-P2-08 must remain valid before validation hardening.
- Feedback regression protection R-INV-09 depends on R-P3-10 and R-P3-11.
- Proof obligation gating R-INV-05 depends on validation outcomes remaining hard gates.

## 4) Ordered tasks for next Validation-oriented session

1. Run full validation/oracle/regression quality gates.
   - Inputs: R-P3-12.
   - Required outcome: actual pytest/mypy/ruff/format evidence.
   - Verification: targeted validation tests and full service tests.
2. Distinguish heuristic depth from capability presence.
   - Inputs: R-P3-07, R-P3-08, R-P3-09.
   - Required outcome: future work items deepen scoring only if required by benchmark or product quality goals.
   - Verification: no current capability is mislabeled as missing.
3. Preserve feedback regression invariant.
   - Inputs: R-P3-10, R-P3-11, R-INV-09.
   - Required outcome: rejected feedback creates future blocking protection.
   - Verification: regression tests remain passing.

## 5) Do not assume

- Do not assume oracle/regression are absent; current code and tests exist.
- Do not claim Phase 3 complete without full quality gates.
- Do not weaken broad-rule or regression failures into warnings.

## 6) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

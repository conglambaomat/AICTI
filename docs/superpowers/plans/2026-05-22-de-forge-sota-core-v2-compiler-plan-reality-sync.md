# DE-Forge SOTA Core v2 Compiler Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Provide a reality-synced plan for the Detection AST and Sigma compiler phase.

**Architecture:** Reads Phase 2 matrix rows. Aligns documented expectations for AST schema, Sigma schema, compiler service, validator, provenance, and YAML output with current code paths.

## 1) Current reality summary

Matrix rows R-P2-01 through R-P2-08 are implemented with code and test anchors. R-P2-09 is partial because actual compiler quality gates were not run during this documentation-only pass.

Key implemented anchors:

- Typed Detection AST: R-P2-01.
- Verified DetectionSpec to AST conversion: R-P2-02.
- Evidence provenance through AST: R-P2-03.
- Typed Sigma schema and compiler: R-P2-04, R-P2-05.
- Telemetry/logsource validation and unsupported field rejection: R-P2-06.
- YAML serialization and Sigma structure validation: R-P2-07, R-P2-08.

## 2) Strict scope boundary

- This plan does not modify compiler code.
- Future code-modifying compiler work should harden semantics only after running existing tests and quality gates.

## 3) Dependency edges

- Foundation rows R-P1-08, R-P1-10, R-P1-11, R-P1-12, and R-P1-13 must remain valid before compiler expansion.
- R-INV-06 depends on R-P2-01 through R-P2-08 staying true.

## 4) Ordered tasks for next Compiler-oriented session

1. Run compiler quality gates.
   - Inputs: R-P2-09.
   - Required outcome: actual pytest/mypy/ruff/format evidence.
   - Verification: `pytest tests/unit/services/test_detection_ast.py tests/unit/services/test_sigma_compiler.py -v`, then project quality gates.
2. Preserve AST-first behavior.
   - Inputs: R-P2-02, R-P2-05, R-INV-06.
   - Required outcome: no raw Sigma generation path bypasses Detection AST.
   - Verification: targeted tests plus orchestrator vertical slice.
3. Preserve provenance.
   - Inputs: R-P2-03, R-P2-04.
   - Required outcome: Sigma conditions remain traceable to evidence IDs.
   - Verification: compiler tests assert provenance.

## 5) Do not assume

- Do not assume Phase 2 is missing; the matrix shows the compiler contract is present.
- Do not recreate `schemas/detection_ast.py`, `schemas/sigma.py`, `services/sigma_compiler.py`, or `services/sigma_validator.py`.
- Do not treat YAML as source of truth.

## 6) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

# DE-Forge SOTA Core v2 Controlled Agents Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Provide a reality-synced plan for controlled multi-agent components.

**Architecture:** Maps Phase 4 matrix rows to existing agent modules, LLM contracts, prompt registry, and agent audit infrastructure. Agents remain untrusted producers whose outputs must pass deterministic validators and gates.

## 1) Current reality summary

Matrix rows R-P4-01 through R-P4-10 are implemented with code and test anchors. R-P4-11 is partial because full agent quality gates were not run during this documentation-only pass.

Key implemented anchors:

- Strict agent envelopes and citation spans: R-P4-01, R-P4-02.
- Prompt registry and OpenAI-compatible LLM contracts: R-P4-03, R-P4-04.
- Agent audit persistence: R-P4-05.
- Base controlled runner: R-P4-06.
- Evidence, ATT&CK mapping, DetectionSpec, and critic contracts: R-P4-07 through R-P4-10.

## 2) Strict scope boundary

- This plan does not modify agent code.
- It does not add new provider/model fallback behavior.
- It preserves the single-provider/model policy unless the user explicitly approves a change.

## 3) Dependency edges

- Foundation citation verification R-P1-08 and R-INV-03 must remain hard gates after evidence agent output.
- DetectionSpec verification R-P1-12 must remain after DetectionSpec agent output.
- Validation and proof gates must remain deterministic and not agent-trusted.

## 4) Ordered tasks for next Agents-oriented session

1. Run full controlled-agent quality gates.
   - Inputs: R-P4-11.
   - Required outcome: actual pytest/mypy/ruff/format evidence.
   - Verification: agent unit/integration tests plus full quality gates.
2. Strengthen bounded-loop evidence if needed.
   - Inputs: R-INV-08.
   - Required outcome: explicit constants/tests for loop bounds if current line-level evidence is insufficient.
   - Verification: new code-modifying plan only after this doc-only phase.
3. Preserve citation and DetectionSpec deterministic validation.
   - Inputs: R-P4-07, R-P4-09, R-INV-03, R-INV-02.
   - Required outcome: agent output never directly becomes production rule output.
   - Verification: orchestrator/product path tests remain passing.

## 5) Do not assume

- Do not assume agent capability means invariant compliance; deterministic gates still decide.
- Do not add model/provider fallback logic.
- Do not expand agent loops without explicit bounded-loop gates.

## 6) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

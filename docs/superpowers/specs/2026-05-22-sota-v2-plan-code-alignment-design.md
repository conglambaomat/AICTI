# SOTA Core v2 Plan↔Code Reality Alignment Design (All 5 Phases)

Date: 2026-05-22
Owner: Claude (analysis-only mode)
Scope: Audit + Spec/Plan documentation alignment only (no source code changes)

## 1) Objective

Produce a precise, evidence-grounded alignment package that synchronizes SOTA Core v2 plans/spec expectations with current repository reality across all 5 phases.

This design explicitly avoids implementation/code edits. The output is an operational documentation baseline for execution teams.

## 2) Non-Negotiable Constraints

1. No code modification in `src/`, `tests/`, or runtime behavior.
2. Architecture invariants from SOTA Core v2 remain authoritative.
3. Every claim must be traceable to concrete evidence:
   - code file paths,
   - test file paths,
   - authoritative doc sections.
4. If docs conflict with code reality, mark as drift/stale and propose doc correction only.
5. Do not invent completion claims where evidence is absent.

## 3) In-Scope / Out-of-Scope

### In-Scope
- End-to-end audit across all 5 SOTA phases:
  1. Foundation
  2. Compiler
  3. Validation/Oracle/Regression
  4. Controlled Agents
  5. Orchestrator/API/UI/Dashboard
- Requirement-to-evidence traceability mapping.
- Documentation drift detection and normalization proposals.
- Updated/replacement spec-plan documentation set for team execution.

### Out-of-Scope
- Feature implementation.
- Refactor or bugfix.
- Test rewrites.
- Runtime infra changes.

## 4) Deliverables

### Deliverable A — Master Traceability Matrix
Path:
- `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`

Structure per row:
- Phase
- Requirement / Plan Task ID
- Expected Capability
- Code Evidence (file_path:line or module-level when line not required)
- Test Evidence
- Status: `implemented` | `partial` | `missing` | `drifted`
- Risk Level: `high` | `medium` | `low`
- Recommended Doc Action

### Deliverable B — Reality-Aligned Spec Addendum
Path:
- `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

Contents:
- Confirmed architecture-conformant areas.
- Stale/contradictory statements currently in docs.
- Canonical interpretation guidance for execution sessions.

### Deliverable C — 5 Reality-Synced Phase Plan Docs
Paths:
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md`

Each plan must include:
- Current reality summary.
- Strict scope boundary.
- Ordered tasks tied to evidence and acceptance gates.
- Explicit dependency edges to prior phases.
- “Do not assume” section for previously stale claims.

### Deliverable D — Governance Execution Summary (1 page)
Path:
- `docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`

Contents:
- Hard blockers for trustworthy progress reporting.
- Must-fix documentation drifts.
- Safe deferrals.
- Recommended execution order checkpoints.

## 5) Methodology

## Step 1: Build Canonical Requirement Inventory
Extract and normalize requirements from:
- START_HERE
- EXECUTION_KIT
- QUALITY_GATES
- Active design spec
- All 5 phase plan documents

Output: normalized requirement catalog with IDs.

## Step 2: Evidence Harvest (Read-only)
For each requirement, collect evidence from:
- `src/de_forge/**`
- `tests/**`
- API boundaries and service interfaces
- existing gate logic and run-state transitions

Evidence must be specific and reproducible.

## Step 3: Status Classification
Apply deterministic rubric:
- `implemented`: complete behavior present + test evidence.
- `partial`: core behavior present but missing required edges/tests/integration depth.
- `missing`: no credible implementation evidence.
- `drifted`: capability exists but materially diverges from documented contract/path.

## Step 4: Drift and Contradiction Analysis
Detect:
- stale claims,
- phase-order inconsistencies,
- naming/path mismatches that break traceability,
- ambiguous gate criteria.

## Step 5: Documentation Synthesis
Generate A/B/C/D deliverables with cross-links and consistent terminology.

## Step 6: Internal Consistency Pass
Before user handoff, verify:
- no unresolved placeholders,
- no contradictory status labels,
- no task without evidence anchor,
- no recommendation violating architecture invariants.

## 6) Quality Criteria for This Documentation Project

Success is achieved only if:
1. Teams can execute phase work without guessing what is real vs stale.
2. Every major requirement has explicit status + evidence.
3. Documented next steps are ordered and dependency-safe.
4. No architecture invariants are weakened by reinterpretation.

## 7) Risks and Mitigations

### Risk A: False confidence from broad “implemented” labels
Mitigation: require both code and test anchors; otherwise classify `partial`.

### Risk B: Overfitting to file names instead of behavior
Mitigation: prioritize capability evidence over exact historical path names, but record path drift explicitly.

### Risk C: Contradictions across old and new docs
Mitigation: add a canonical “reality-aligned interpretation” section and mark stale sections explicitly.

### Risk D: Scope creep into implementation
Mitigation: enforce doc-only boundary and defer code changes to subsequent execution plans.

## 8) Review Protocol

- First review: structural completeness (all 5 phases represented).
- Second review: evidence rigor (spot-check requirement→evidence mapping).
- Third review: operational usability (can a subagent execute from docs without hidden assumptions).

## 9) Approval Gate

After this design is approved, the next and only skill transition is:
- `writing-plans`

The plan will define concrete documentation tasks, checkpoints, and verification commands for producing the alignment package.
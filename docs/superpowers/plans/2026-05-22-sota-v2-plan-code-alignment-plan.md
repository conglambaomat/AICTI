# SOTA Core v2 Plan↔Code Reality Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a complete, evidence-grounded documentation alignment package across all 5 SOTA Core v2 phases without modifying any source code or tests.

**Architecture:** This plan creates documentation artifacts only. It builds a canonical requirement inventory, harvests code/test evidence read-only, classifies status using a deterministic rubric, then synthesizes a traceability matrix, a reality-alignment addendum, five reality-synced phase plans, and a one-page governance summary. Each task ends with a verification command and a scoped commit.

**Tech Stack:** Markdown documentation only. Tooling used for verification: `git`, `pytest --collect-only`, `Grep`, `Glob`. No Python production code is added or modified.

> **Commit policy:** Authorized by user-level CLAUDE.md for SOTA Core v2 alignment work. Commit after each completed and verified task using a task-scoped message. Do not stage unrelated working-tree changes.

---

## Scope boundary

This plan produces documentation only. It does NOT:

- modify `src/`, `tests/`, configuration, or runtime behavior,
- create new code modules,
- rewrite existing tests,
- weaken or reinterpret architecture invariants.

It DOES produce:

- `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`
- `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`
- `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`
- `docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md`
- `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md`

## File structure map

| File | Purpose |
| --- | --- |
| `2026-05-22-sota-v2-requirement-inventory.md` | Normalized list of every SOTA v2 requirement with stable IDs (`R-P{phase}-{nn}`). |
| `2026-05-22-sota-v2-evidence-index.md` | Read-only index of code + test evidence anchors (file paths, symbols). |
| `2026-05-22-sota-v2-traceability-matrix.md` | Master matrix: requirement → code/test evidence → status → risk → doc action. |
| `2026-05-22-sota-core-v2-reality-alignment-addendum.md` | Reality-aligned interpretation, drift list, canonical guidance. |
| `2026-05-22-sota-v2-governance-execution-summary.md` | One-page execution governance summary for coordinators. |
| `2026-05-22-de-forge-sota-core-v2-{phase}-plan-reality-sync.md` (×5) | Phase-by-phase reality-synced plans referencing matrix rows. |

## Phase model used in deliverables

1. Foundation
2. Compiler (Detection AST and Sigma compiler)
3. Validation, Oracle, Regression
4. Controlled Agents
5. Orchestrator, API, UI, Dashboard

---

## Task 1: Build canonical requirement inventory

**Files:**
- Create: `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`

- [ ] **Step 1: Read source documents**

Read in this order:

- `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`
- `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`
- `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`
- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`

- [ ] **Step 2: Write the requirement inventory file**

Use the exact structure below. Replace placeholders `<...>` with content extracted from the source documents.

```markdown
# SOTA Core v2 Requirement Inventory

Date: 2026-05-23
Scope: Documentation-only normalization of SOTA Core v2 requirements.

## Conventions

Requirement ID format: `R-P{phase}-{nn}` where `phase` is `1..5` and `nn` is a zero-padded sequence per phase.
Each row records a single atomic requirement traceable to a source document section.

## Phase 1 — Foundation

| ID | Requirement | Source |
| --- | --- | --- |
| R-P1-01 | <atomic requirement text> | <doc path + section heading> |
| R-P1-02 | <...> | <...> |

## Phase 2 — Compiler

| ID | Requirement | Source |
| --- | --- | --- |
| R-P2-01 | <...> | <...> |

## Phase 3 — Validation, Oracle, Regression

| ID | Requirement | Source |
| --- | --- | --- |
| R-P3-01 | <...> | <...> |

## Phase 4 — Controlled Agents

| ID | Requirement | Source |
| --- | --- | --- |
| R-P4-01 | <...> | <...> |

## Phase 5 — Orchestrator, API, UI, Dashboard

| ID | Requirement | Source |
| --- | --- | --- |
| R-P5-01 | <...> | <...> |

## Cross-cutting Architecture Invariants

| ID | Invariant | Source |
| --- | --- | --- |
| R-INV-01 | No raw-report-to-rule path. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-02 | DetectionSpec mandatory before rule generation. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-03 | Citations exact and verified. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-04 | ATT&CK chain Technique → Strategy → Analytic → Data Component → Telemetry → Field. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-05 | Required proof obligations proven before final candidate selection. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-06 | AST + compiler preferred over free-form Sigma generation. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-07 | Human review mandatory before export. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-08 | Bounded agent loops. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-09 | Feedback creates regression protection. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |
| R-INV-10 | Full lineage and auditability. | docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md §7 |

## Completion criteria for this inventory

- Every phase has at least one requirement row.
- No requirement row has empty Source.
- IDs are unique and follow the format above.
```

- [ ] **Step 3: Verify file exists and structure is non-empty**

Run:

```bash
test -s docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md && echo OK
```

Expected: prints `OK`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md
git commit -m "docs(spec): add SOTA v2 requirement inventory"
```

---

## Task 2: Build evidence index from current code and tests

**Files:**
- Create: `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`

- [ ] **Step 1: Enumerate source modules**

Run:

```bash
git ls-files src/de_forge | sort
```

Capture full list. Do not modify files.

- [ ] **Step 2: Enumerate tests**

Run:

```bash
git ls-files tests | sort
```

Capture full list.

- [ ] **Step 3: Verify tests are collectible (read-only)**

Run:

```bash
python -m pytest --collect-only -q
```

If the command fails because of environment issues, record the failure verbatim in the evidence index under a “Collection Status” section, but do not modify code/tests to make it pass.

- [ ] **Step 4: Write the evidence index file**

```markdown
# SOTA Core v2 Evidence Index (Read-Only)

Date: 2026-05-23
Scope: Read-only catalog of code and test evidence anchors used by the traceability matrix.

## Source modules (src/de_forge)

<paste output from `git ls-files src/de_forge`>

## Test files

<paste output from `git ls-files tests`>

## Symbol anchors (high-signal, read-only)

For each module below, list public classes/functions found via Grep (no edits):

- `src/de_forge/services/orchestrator.py` — <classes/functions>
- `src/de_forge/services/graph_builder.py` — <classes/functions>
- `src/de_forge/services/detection_spec_verifier.py` — <classes/functions>
- `src/de_forge/services/detection_ast_service.py` — <classes/functions>
- `src/de_forge/services/sigma_compiler.py` — <classes/functions>
- `src/de_forge/services/sigma_validator.py` — <classes/functions>
- `src/de_forge/services/static_validation.py` — <classes/functions>
- `src/de_forge/services/dynamic_validation.py` — <classes/functions>
- `src/de_forge/services/regression.py` — <classes/functions>
- `src/de_forge/services/proof_obligation_service.py` — <classes/functions>
- `src/de_forge/services/state_machine.py` — <classes/functions>
- `src/de_forge/services/gates.py` — <classes/functions>
- `src/de_forge/services/export_gate.py` — <classes/functions>
- `src/de_forge/services/run_repository.py` — <classes/functions>
- `src/de_forge/api/router.py` — <route inclusions>
- `src/de_forge/api/routes/*.py` — <route handlers per file>

## Test anchors per area

- Foundation: <list test files under tests/unit/core, tests/unit/schemas, tests/integration/db>
- Compiler: <list test files referencing AST/compiler/validator>
- Validation/Oracle/Regression: <list test files under tests/integration/services and tests/e2e relevant>
- Agents: <list test files under tests/integration/agents and tests/unit/agents>
- Orchestrator/API: <list test files under tests/integration/api and tests/e2e>

## Collection Status

<paste short summary of pytest --collect-only result, including any errors verbatim>
```

- [ ] **Step 5: Verify the evidence index file is non-empty**

Run:

```bash
test -s docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md && echo OK
```

Expected: prints `OK`.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md
git commit -m "docs(spec): add SOTA v2 read-only evidence index"
```

---

## Task 3: Build the master traceability matrix

**Files:**
- Create: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`

- [ ] **Step 1: Define the deterministic status rubric inside the file**

Use exactly this rubric in the matrix file:

```markdown
## Status rubric

- `implemented`: Requirement covered by clear code AND test evidence.
- `partial`: Code present but missing tests, integration, or required edge behavior.
- `missing`: No credible code evidence found.
- `drifted`: Capability exists but materially diverges from documented contract or path.
```

- [ ] **Step 2: Write the matrix file**

Use exactly this structure:

```markdown
# SOTA Core v2 Plan↔Code Traceability Matrix

Date: 2026-05-23
Scope: Documentation-only mapping of every requirement in `2026-05-22-sota-v2-requirement-inventory.md` to current code/test evidence.

## How to use

- Source of requirements: `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`
- Source of evidence anchors: `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`
- Status values use the rubric below.

## Status rubric

- `implemented`
- `partial`
- `missing`
- `drifted`

## Risk levels

- `high`: violates an architecture invariant or blocks downstream phase.
- `medium`: weakens a phase deliverable but not blocking.
- `low`: cosmetic or naming drift only.

## Phase 1 — Foundation

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-P1-01 | <capability> | <file_path[:line]> | <test_path::test_name> | implemented | low | <action> |

## Phase 2 — Compiler

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |

## Phase 3 — Validation, Oracle, Regression

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |

## Phase 4 — Controlled Agents

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |

## Phase 5 — Orchestrator, API, UI, Dashboard

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |

## Architecture Invariants

| ID | Invariant | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |

## Completion criteria for the matrix

- Every requirement ID from the inventory appears exactly once.
- Status is set per the rubric.
- `implemented` rows MUST cite both code and test evidence.
- `partial`/`drifted` rows MUST include a `Doc Action`.
- No row is empty.
```

- [ ] **Step 3: Populate matrix rows from inventory + evidence index**

For each requirement ID in the inventory, fill the row using ONLY anchors that exist in the evidence index. If no evidence exists, set Status = `missing` with Risk per rubric and add a Doc Action describing what plan task should resolve it.

- [ ] **Step 4: Self-check**

Run:

```bash
grep -E "^\| R-(P[1-5]|INV)-[0-9]+ \|" docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md | wc -l
```

Verify the count equals the number of requirement rows in the inventory file (excluding headers).

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md
git commit -m "docs(spec): add SOTA v2 traceability matrix"
```

---

## Task 4: Write the reality-aligned spec addendum

**Files:**
- Create: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`

- [ ] **Step 1: Write the addendum**

```markdown
# SOTA Core v2 Reality Alignment Addendum

Date: 2026-05-23
Scope: Canonical interpretation overlay for SOTA Core v2 documentation.
Authority: This addendum supersedes any conflicting wording in older docs for execution decisions, until older docs are realigned.

## 1) Confirmed architecture-conformant areas

For each area below, cite traceability matrix IDs that are `implemented`:

- Foundation primitives: <list IDs>
- Persistence and lineage: <list IDs>
- DetectionSpec/AST/Sigma path: <list IDs>
- Validation/proof gates: <list IDs>
- Review/export gates: <list IDs>
- Agent infrastructure: <list IDs>
- API and runtime path: <list IDs>

## 2) Stale or contradictory statements found in current docs

| Doc | Section | Claim | Reality | Resolution |
| --- | --- | --- | --- | --- |
| docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md | §2 | Source tree is "skeleton-level" only | Substantial services + tests exist | Mark as superseded; refer to traceability matrix |

Add additional rows for every stale claim discovered.

## 3) Canonical interpretation rules

- When older docs reference a file path that does not exist but the capability exists under another path, treat it as `drifted`. Use the traceability matrix as the source of truth.
- Architecture invariants R-INV-01 .. R-INV-10 are non-negotiable and not subject to reinterpretation.
- Documentation may be reorganized; code changes are out of scope for this alignment package.

## 4) Open questions deferred to next planning round

Use bullets. No code changes are proposed here.

## 5) Cross-references

- Traceability matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Requirement inventory: `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`
- Evidence index: `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`
```

- [ ] **Step 2: Verify file exists and is non-empty**

Run:

```bash
test -s docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md
git commit -m "docs(spec): add SOTA v2 reality alignment addendum"
```

---

## Task 5: Write reality-synced Foundation phase plan

**Files:**
- Create: `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md`

- [ ] **Step 1: Write the file using the exact section template below**

```markdown
# DE-Forge SOTA Core v2 Foundation Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. This plan is documentation-aligned; it does not modify code.

**Goal:** Provide a reality-synced, evidence-cited plan for the Foundation phase that reflects current repository state and remaining gaps.

**Architecture:** Reads from the traceability matrix and addendum. Produces an execution-ready breakdown of what is `implemented`, what is `partial`, what is `missing`, and what is `drifted`, with prioritized doc/code follow-up actions to be sequenced in later code-modifying plans.

## 1) Current reality summary

Cite specific matrix IDs and status counts for Phase 1.

## 2) Strict scope boundary

- This plan does not change code.
- It defines doc-only follow-ups and prerequisites for any future code-modifying foundation work.

## 3) Dependency edges

- Phase 1 must reach a verified `implemented` status for invariants R-INV-01..R-INV-10 before any new Compiler-phase code work begins.

## 4) Ordered tasks

For each task, list:
- Inputs (matrix IDs)
- Required outcome (doc-level only)
- Verification (file existence or matrix update)

## 5) Do not assume

- Do not assume historical "skeleton-only" claims; rely on the traceability matrix.
- Do not assume any file path that is not present in the evidence index.

## 6) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`
```

- [ ] **Step 2: Verify file exists and is non-empty**

Run:

```bash
test -s docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md
git commit -m "docs(plan): add reality-synced foundation plan"
```

---

## Task 6: Write reality-synced Compiler phase plan

**Files:**
- Create: `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md`

- [ ] **Step 1: Write the file**

Use the same section template as Task 5, but specialized to Phase 2:

```markdown
# DE-Forge SOTA Core v2 Compiler Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Reality-synced plan for the Detection AST and Sigma compiler phase.

**Architecture:** Reads matrix Phase 2 rows. Aligns documented expectations (AST schema, Sigma schema, compiler service, validator) with current code paths and reports drift as `drifted` rather than `missing` whenever capability exists under another module name.

## 1) Current reality summary

Cite Phase 2 matrix IDs.

## 2) Strict scope boundary

Doc-only.

## 3) Dependency edges

Foundation phase invariants must be confirmed before code-changing work begins on the compiler.

## 4) Ordered tasks

- Confirm AST representation in current code and document it under R-P2-* matrix rows.
- Confirm Sigma compilation path and document evidence anchors.
- Identify validator coverage gaps as `partial` or `missing` with explicit doc actions.

## 5) Do not assume

- Do not assume specific file names from older plans (`schemas/detection_ast.py`, etc.) without evidence index confirmation.

## 6) Cross-references

- Matrix and addendum paths as in Task 5.
```

- [ ] **Step 2: Verify**

Run:

```bash
test -s docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md
git commit -m "docs(plan): add reality-synced compiler plan"
```

---

## Task 7: Write reality-synced Validation/Oracle/Regression phase plan

**Files:**
- Create: `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md`

- [ ] **Step 1: Write the file**

```markdown
# DE-Forge SOTA Core v2 Validation, Oracle, Regression Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Reality-synced plan for static validation, dynamic validation, oracle evaluation, and regression protection.

**Architecture:** Maps Phase 3 matrix rows to current `static_validation`, `dynamic_validation`, `regression`, and proof-obligation evidence. Documents which oracle/regression behaviors are `partial` or `missing`, in line with R-INV-09.

## 1) Current reality summary

Cite Phase 3 matrix IDs.

## 2) Strict scope boundary

Doc-only.

## 3) Dependency edges

Compiler phase reality must be confirmed before locking validator gate semantics in code changes.

## 4) Ordered tasks

- Document oracle evaluation anchor or mark missing.
- Document regression gate anchor or mark missing.
- Document feedback loop anchor or mark missing.
- Map proof-obligation gate evidence to R-INV-05.

## 5) Do not assume

- Do not assume regression protection is implemented merely because `regression.py` exists; require test evidence.

## 6) Cross-references

- Matrix and addendum paths as in Task 5.
```

- [ ] **Step 2: Verify**

Run:

```bash
test -s docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md
git commit -m "docs(plan): add reality-synced validation/oracle/regression plan"
```

---

## Task 8: Write reality-synced Controlled Agents phase plan

**Files:**
- Create: `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md`

- [ ] **Step 1: Write the file**

```markdown
# DE-Forge SOTA Core v2 Controlled Agents Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Reality-synced plan for controlled multi-agent components.

**Architecture:** Maps Phase 4 matrix rows to existing agent modules and audit infrastructure. Validates that bounded loops (R-INV-08) and citation faithfulness (R-INV-03) are reflected in evidence; otherwise marks `partial`.

## 1) Current reality summary

Cite Phase 4 matrix IDs.

## 2) Strict scope boundary

Doc-only.

## 3) Dependency edges

Validation/oracle phase doc-sync required before any code-modifying agent reliability work.

## 4) Ordered tasks

- Confirm agent envelope and audit anchors.
- Confirm bounded-loop evidence; otherwise mark partial.
- Confirm citation propagation to DetectionSpec via evidence chain.

## 5) Do not assume

- Agent feature presence does not imply invariant compliance until tests demonstrate it.

## 6) Cross-references

- Matrix and addendum paths as in Task 5.
```

- [ ] **Step 2: Verify**

Run:

```bash
test -s docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md
git commit -m "docs(plan): add reality-synced controlled agents plan"
```

---

## Task 9: Write reality-synced Orchestrator/API/UI/Dashboard phase plan

**Files:**
- Create: `docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md`

- [ ] **Step 1: Write the file**

```markdown
# DE-Forge SOTA Core v2 Orchestrator/API/UI/Dashboard Plan (Reality-Synced)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Documentation-only.

**Goal:** Reality-synced plan for orchestrator, API surface, runtime path, and minimal UI.

**Architecture:** Maps Phase 5 matrix rows to `orchestrator.py`, `state_machine.py`, `gates.py`, `export_gate.py`, `api/router.py`, route modules, and e2e test anchors. Confirms human review and export gates (R-INV-07) are reflected in evidence.

## 1) Current reality summary

Cite Phase 5 matrix IDs.

## 2) Strict scope boundary

Doc-only.

## 3) Dependency edges

Earlier phase reality-sync plans must be in place; UI/dashboard expansions are deferred until the deterministic core is confirmed.

## 4) Ordered tasks

- Document run state transitions and gate anchors.
- Document review and export gate enforcement evidence.
- Document API surface inventory and e2e coverage.

## 5) Do not assume

- Operational maturity in API does not imply earlier phases are fully aligned with invariants.

## 6) Cross-references

- Matrix and addendum paths as in Task 5.
```

- [ ] **Step 2: Verify**

Run:

```bash
test -s docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md
git commit -m "docs(plan): add reality-synced orchestrator/api/ui plan"
```

---

## Task 10: Write the governance execution summary

**Files:**
- Create: `docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md`

- [ ] **Step 1: Write the file**

```markdown
# SOTA Core v2 Governance Execution Summary

Date: 2026-05-23
Scope: One-page operational guidance for execution coordinators.

## 1) Hard blockers (must clear before claiming any phase complete)

- Citation exactness gate (R-INV-03)
- Proof obligation gate (R-INV-05)
- Human review gate before export (R-INV-07)
- Bounded agent loops (R-INV-08)
- Lineage and auditability (R-INV-10)

## 2) Must-fix documentation drifts

Cite each `drifted` matrix row by ID and the recommended doc action.

## 3) Safe deferrals

List capabilities classified as `partial` whose deferral does not violate invariants. Provide rationale.

## 4) Recommended execution order checkpoints

1. Confirm Phase 1 invariants are aligned in docs.
2. Confirm Phase 2 compiler evidence and resolve drift.
3. Confirm Phase 3 oracle and regression evidence; if missing, schedule code-modifying plans.
4. Confirm Phase 4 agent invariant evidence.
5. Confirm Phase 5 review/export gate evidence.

## 5) Cross-references

- Matrix: `docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md`
- Addendum: `docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md`
```

- [ ] **Step 2: Verify**

Run:

```bash
test -s docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md && echo OK
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md
git commit -m "docs(spec): add SOTA v2 governance execution summary"
```

---

## Task 11: Final consistency pass and link verification

**Files:**
- Modify only if a cross-link is wrong: any of the previously created docs.

- [ ] **Step 1: Confirm all expected files exist**

Run:

```bash
for f in \
  docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md \
  docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md \
  docs/superpowers/specs/2026-05-22-sota-v2-traceability-matrix.md \
  docs/superpowers/specs/2026-05-22-sota-core-v2-reality-alignment-addendum.md \
  docs/superpowers/specs/2026-05-22-sota-v2-governance-execution-summary.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-foundation-plan-reality-sync.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-compiler-plan-reality-sync.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-validation-oracle-regression-plan-reality-sync.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-agents-plan-reality-sync.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan-reality-sync.md; do
  test -s "$f" && echo "OK $f" || echo "MISSING $f";
done
```

Expected: every line begins with `OK`.

- [ ] **Step 2: Detect placeholder leakage**

Run:

```bash
grep -nE "(TBD|TODO|FIXME|<\.\.\.>|placeholder)" \
  docs/superpowers/specs/2026-05-22-sota-v2-*.md \
  docs/superpowers/specs/2026-05-22-sota-core-v2-*.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-*-reality-sync.md || true
```

Expected: empty output. If anything is found, fix the file content (not the search) and rerun.

- [ ] **Step 3: Verify cross-references resolve**

Run:

```bash
grep -nE "docs/superpowers/(specs|plans)/2026-05-22-" \
  docs/superpowers/specs/2026-05-22-sota-v2-*.md \
  docs/superpowers/specs/2026-05-22-sota-core-v2-*.md \
  docs/superpowers/plans/2026-05-22-de-forge-sota-core-v2-*-reality-sync.md \
  | awk '{print $0}' | sort -u
```

Manually confirm each referenced path exists in the file list from Step 1.

- [ ] **Step 4: Confirm no source code changes were made**

Run:

```bash
git diff --name-only main...HEAD -- src tests | sort -u
```

Expected: empty output.

- [ ] **Step 5: Commit any final fixes**

If Step 2 or Step 3 required fixes:

```bash
git add docs/superpowers/specs docs/superpowers/plans
git commit -m "docs(spec): final consistency pass for SOTA v2 alignment package"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage in this plan:

- Deliverable A — Master Traceability Matrix: Tasks 1, 2, 3.
- Deliverable B — Reality-Aligned Spec Addendum: Task 4.
- Deliverable C — 5 Reality-Synced Phase Plans: Tasks 5, 6, 7, 8, 9.
- Deliverable D — Governance Execution Summary: Task 10.
- Methodology Steps 1–6 from the spec are exercised in Tasks 1–11.
- Architecture invariants R-INV-01..R-INV-10 are explicitly preserved across the matrix, addendum, and governance summary.
- No code or tests are modified.
- Every task ends with a verification command and a scoped commit.

# SOTA Core v2 Requirement Inventory

Date: 2026-05-23
Scope: Documentation-only normalization of SOTA Core v2 requirements.

## Conventions

Requirement ID format: `R-P{phase}-{nn}` where `phase` is `1..5` and `nn` is a zero-padded sequence per phase.
Each row records one atomic requirement traceable to a source document section or plan task.
This inventory records target requirements only; it does not claim current implementation status.

## Phase 1 — Foundation

| ID | Requirement | Source |
| --- | --- | --- |
| R-P1-01 | Provide stable canonical JSON serialization and deterministic snapshot hashes for artifact payloads. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 1 |
| R-P1-02 | Provide stage-scoped deterministic idempotency keys for repeatable pipeline operations. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 1 |
| R-P1-03 | Define domain exceptions for validation gates, citation verification failures, and proof obligation failures. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 2 |
| R-P1-04 | Define persisted artifact lineage schemas with artifact kind, stage, payload, input hash, output hash, parent artifact IDs, and creator. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 2 |
| R-P1-05 | Provide SQLAlchemy base/session primitives and artifact persistence with lineage queryability. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 3 |
| R-P1-06 | Provide evidence graph node and edge schemas/models with support-path query capability. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 4 |
| R-P1-07 | Provide deterministic text chunking with stable chunk IDs and character offsets. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 5 |
| R-P1-08 | Verify citation quotes exactly against source chunk text and supplied offsets, failing hard on mismatch. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 5 |
| R-P1-09 | Maintain a curated ATT&CK detection registry mapping techniques to detection strategies, analytics, and data components. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 6 |
| R-P1-10 | Maintain a multi-platform telemetry registry validating known telemetry sources and fields. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 6 |
| R-P1-11 | Define a formal DetectionSpec contract covering evidence, behavior, ATT&CK, strategy, analytic, data component, telemetry, allowed fields, logic, false positives, and test plan. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 7 |
| R-P1-12 | Verify DetectionSpecs before rule generation, including evidence presence, ATT&CK presence, telemetry existence, field validity, and logic evidence references. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 7 |
| R-P1-13 | Generate required proof obligations for rule candidates and block selectable candidates unless required obligations are proven or justified as not applicable. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 8 |
| R-P1-14 | Run foundation verification across relevant tests, type checks, lint checks, and formatting checks before phase completion. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md §Task 9; docs/operational/QUALITY_GATES_SOTA_CORE_V2.md §Universal Quality Gate Rules |

## Phase 2 — Compiler

| ID | Requirement | Source |
| --- | --- | --- |
| R-P2-01 | Define a typed Detection AST schema as the source representation for detection rule logic. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Task 1 |
| R-P2-02 | Convert only verified DetectionSpecs into Detection ASTs and reject unverified specs. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Task 2 |
| R-P2-03 | Preserve provenance from AST conditions back to evidence IDs. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Goal; §Task 1 |
| R-P2-04 | Define a typed Sigma rule schema including logsource, detection, tags, false positives, severity, and provenance. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Task 3 |
| R-P2-05 | Compile Detection ASTs into typed Sigma rule objects without relying on free-form YAML generation as source of truth. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Goal; §Task 4 |
| R-P2-06 | Validate telemetry/logsource compatibility and reject unsupported fields during compilation. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Architecture; §Task 4 |
| R-P2-07 | Serialize compiled Sigma rule objects to YAML after typed compilation. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Task 5 |
| R-P2-08 | Validate Sigma structure, required condition references, and selection consistency before candidate use. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Task 5 |
| R-P2-09 | Run compiler verification across compiler tests, affected service tests, type checks, lint checks, and format checks. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md §Task 6; docs/operational/QUALITY_GATES_SOTA_CORE_V2.md §Universal Quality Gate Rules |

## Phase 3 — Validation, Oracle, Regression

| ID | Requirement | Source |
| --- | --- | --- |
| R-P3-01 | Define rule candidate and candidate score schemas for portfolio evaluation. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 1 |
| R-P3-02 | Wrap compiled Sigma rules into typed candidate portfolio entries. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 1 |
| R-P3-03 | Run static validation gates for Sigma structure and candidate static validity. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 2 |
| R-P3-04 | Detect and reject overbroad detection patterns before final candidate selection. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 2 |
| R-P3-05 | Evaluate rules dynamically against positive and benign normalized test events. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 3 |
| R-P3-06 | Compute dynamic precision and recall from true positive, false positive, true negative, and false negative counts. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 3 |
| R-P3-07 | Evaluate adversarial variants to score robustness against expected bypass variants. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 4 |
| R-P3-08 | Evaluate counterfactual condition importance by removing or mutating conditions and comparing detection behavior. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 4 |
| R-P3-09 | Define oracle cases and score candidates against expected techniques, telemetry, events, benign avoidance, and logic family. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 5 |
| R-P3-10 | Convert human review feedback into regression tests or do-not-repeat patterns. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 6 |
| R-P3-11 | Enforce feedback-derived regression gates before future candidate acceptance. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 6 |
| R-P3-12 | Run validation/oracle/regression verification across target tests, service tests, type checks, lint checks, and formatting checks. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md §Task 7; docs/operational/QUALITY_GATES_SOTA_CORE_V2.md §Universal Quality Gate Rules |

## Phase 4 — Controlled Agents

| ID | Requirement | Source |
| --- | --- | --- |
| R-P4-01 | Define strict controlled agent input/output envelopes including metadata, confidence, citations, abstain state, and output payload. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 1 |
| R-P4-02 | Define citation schemas carrying exact chunk ID, quote, start offset, and end offset. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 1 |
| R-P4-03 | Maintain a versioned prompt registry for controlled agents. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 2 |
| R-P4-04 | Provide OpenAI-compatible LLM request/response contracts and client interface. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 2 |
| R-P4-05 | Persist agent run audit records with input/output payloads, hashes, model, prompt version, token counts, latency, cost, and terminal status. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 3 |
| R-P4-06 | Run agents through a base controlled runner that wraps LLM responses in strict output envelopes. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 4 |
| R-P4-07 | Implement an evidence agent contract that extracts evidence quotes and returns exact citations. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 5 |
| R-P4-08 | Implement an ATT&CK mapping agent that maps behaviors to techniques using only supplied evidence. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 6 |
| R-P4-09 | Implement a DetectionSpec agent that constructs DetectionSpecs with evidence, ATT&CK, telemetry, logic, false positives, and test plan fields. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 6 |
| R-P4-10 | Implement a critic/refinement agent contract that identifies false positive, false negative, bypass, telemetry, and unsupported-claim risks. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 6 |
| R-P4-11 | Verify controlled agents with unit and integration tests plus type, lint, and formatting checks. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md §Task 7; docs/operational/QUALITY_GATES_SOTA_CORE_V2.md §Universal Quality Gate Rules |

## Phase 5 — Orchestrator, API, UI, Dashboard

| ID | Requirement | Source |
| --- | --- | --- |
| R-P5-01 | Define run modes and run states for orchestrated pipeline execution. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 1 |
| R-P5-02 | Enforce legal state transitions and reject raw-report-to-rule-candidate transitions. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 1 |
| R-P5-03 | Implement hard gate predicates for rule generation and final review entry. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 2 |
| R-P5-04 | Implement auto-mode golden-path orchestration to reach awaiting human review when gates pass. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 3 |
| R-P5-05 | Implement cautious mode that pauses at DetectionSpec review before rule generation. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 3 |
| R-P5-06 | Define human review schemas and service behavior for approve, reject, edit, and abstain decisions. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 4 |
| R-P5-07 | Block export unless human review explicitly permits export. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 4 |
| R-P5-08 | Provide API routes for run start/inspection and human review submission. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 5 |
| R-P5-09 | Provide quality metric snapshots for dashboard views. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 6 |
| R-P5-10 | Provide a minimal trust-oriented review UI exposing evidence quote, detection logic, Sigma condition, proof status, and validation score. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 7 |
| R-P5-11 | Verify orchestrator, API, UI, and dashboard behavior with targeted tests, full tests, type checks, lint checks, formatting checks, and UI smoke test. | docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md §Task 8; docs/operational/QUALITY_GATES_SOTA_CORE_V2.md §Universal Quality Gate Rules |

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
- This file contains requirements only, not implementation status claims.

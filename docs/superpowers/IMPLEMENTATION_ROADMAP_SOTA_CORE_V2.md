# DE-Forge SOTA Core v2 Implementation Roadmap

Date: 2026-05-21
Purpose: End-to-end roadmap from current skeleton to SOTA Core v2.

This roadmap is descriptive. For execution, use the exact plan order in:

- `docs/operational/START_HERE_FOR_CLAUDE.md`
- `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`

## Phase 0: Documentation and reality alignment

Artifacts:

- Approved design spec: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- Execution kit: `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`
- Autonomous decision policy: `docs/operational/AUTONOMOUS_DECISION_POLICY.md`
- Quality gates: `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`
- Blockers and escalation policy: `docs/operational/BLOCKERS_AND_ESCALATION.md`
- Start-here handoff: `docs/operational/START_HERE_FOR_CLAUDE.md`

Goal:

- Make future Claude sessions know the source of truth.
- Avoid stale MVP/Agentic Deep-Analysis claims.
- Ensure SOTA Core v2 documents override older historical docs.

Exit criteria:

- Current `CLAUDE.md` points to SOTA Core v2.
- Superseded docs are clearly marked and cannot be mistaken for active plans.
- Implementation order is unambiguous.

## Phase 1: Deterministic foundation

Executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-foundation-plan.md`

Build:

- Stable hashing.
- Deterministic idempotency.
- Domain errors.
- Artifact lineage schemas.
- SQLAlchemy base/session.
- Artifact persistence.
- Evidence graph schemas/models/services.
- Deterministic chunking.
- Exact citation verification.
- ATT&CK Detection Strategy / Analytic / Data Component registry.
- Multi-platform telemetry registry.
- Formal DetectionSpec verifier.
- Proof obligation service.

Exit criteria:

- Foundation tests pass.
- Citation mismatch is hard failure.
- Unknown telemetry fields are rejected.
- DetectionSpec cannot verify without evidence/telemetry/logic support.
- Candidate cannot be selected with unknown/failed proof obligations.

## Phase 2: Detection AST and Sigma compiler

Executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`

Build:

- Detection AST schema.
- Sigma rule schema.
- Verified DetectionSpec-to-AST conversion.
- AST-to-Sigma compiler.
- Sigma field/logsource/condition validation.
- YAML serialization that preserves Sigma content while excluding internal provenance.

Exit criteria:

- Sigma YAML is compiled from AST, not free-form raw LLM text.
- Compiler rejects unknown fields.
- Compiler rejects invalid logsource/field combinations.
- Golden PowerShell encoded command AST compiles to valid Sigma candidate.

## Phase 3: Validation, oracle, and regression

Executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`

Build:

- Rule candidate and portfolio schemas.
- Candidate score breakdown.
- Static validation gates.
- Broad-rule detector.
- Dynamic positive/benign event matching.
- Adversarial evaluation.
- Counterfactual condition mutation and importance scoring.
- Oracle case/evaluation schemas and scoring.
- Feedback-to-regression conversion.
- Accepted/rejected regression gate execution.

Exit criteria:

- Overbroad rules are rejected.
- Dynamic validation reports TP, FP, TN, FN, precision, and recall.
- Oracle evaluation checks expected technique, telemetry, positive events, benign must-not-match events, and logic family.
- Feedback rejection creates enforceable do-not-repeat gates.
- Accepted/rejected regression gates are enforceable.

## Phase 4: Controlled LLM agents

Executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`

Build:

- Agent IO envelope.
- Prompt registry.
- OpenAI-compatible LLM client contract.
- Agent run audit persistence.
- Base agent runner.
- Evidence agent citation contract.
- ATT&CK mapping agent contract.
- DetectionSpec agent contract.
- Critic agent contract.

Exit criteria:

- Every agent output is schema-validated.
- Agent run audit is persisted with input/output hashes.
- Invalid agent output cannot enter graph/spec/rule layers.
- Citation-bearing output is ready for exact citation verification.
- Agent outputs cannot bypass deterministic validators.

## Phase 5: Orchestrator, API, UI, and dashboard

Executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`

Build:

- Run states and modes.
- State transition predicates.
- Hard gate predicates.
- Golden-path orchestrator skeleton.
- Human review service.
- Run/review/metrics API routes.
- Minimal trust-oriented review UI.
- Quality dashboard snapshot endpoint.

Exit criteria:

- State machine rejects illegal raw-report-to-rule transition.
- Gate predicates block rule generation without verified DetectionSpec.
- Auto mode reaches human review for golden case.
- Cautious mode pauses at DetectionSpec or uncertainty points.
- Human review approval is required for export.
- Minimal review UI displays evidence, logic, Sigma condition, proof status, and validation score.

## Future phase: Benchmark adapter after product-mode stability

No active implementation plan exists for this phase yet. Do not start it during SOTA Core v2 product-mode implementation.

Future build:

- CTI-REALM adapter.
- Benchmark run reports.
- Benchmark-compatible packaging.

Entry criteria:

- Product-mode SOTA Core v2 end-to-end gates pass.
- Human review workflow works.
- Audit trail and regression gates are stable.

## Roadmap invariant

Do not start a later phase if a prior phase's hard gates are missing. Later phases may be planned early, but implementation must preserve foundation-first order.

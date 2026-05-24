# Remaining SOTA Completion Design

## Goal

Complete the remaining DE-Forge SOTA Core v2 work after Phase 3 without weakening any architecture invariant. The remaining work is split into sequential, independently verifiable slices: Retrieval Audit Lineage, Validation/Proof Persistence Enrichment, True Pipeline Orchestration Repair, Runtime API Hardening, Health/Metrics Truthfulness, and Full SOTA End-to-End Verification.

## Non-Negotiable Invariants

The implementation must preserve the canonical production path:

```text
raw report -> evidence graph -> verified DetectionSpec -> detection AST -> compiled Sigma -> validation/proof -> human review
```

The system must continue to fail closed when evidence citations mismatch, proof obligations are missing or failed, review is absent or rejected, schema state is invalid, or a runtime API cannot derive truthful state from persisted data.

## Architecture Overview

The remaining work should be implemented as one end-to-end architecture with separate phase plans. Each phase must produce a working, testable checkpoint and must not depend on placeholder state from a later phase.

The recommended sequence is:

1. Retrieval Audit Lineage
2. Validation/Proof Persistence Enrichment
3. True Pipeline Orchestration Repair
4. Runtime API Hardening
5. Health/Metrics Truthfulness
6. Full SOTA End-to-End Verification

This order creates the persisted lineage foundation first, enriches validation/proof state second, then repairs orchestration and public runtime surfaces on top of durable facts.

## Phase 4: Retrieval Audit Lineage

Retrieval must become auditable and connected to persisted report chunks. The current retrieval behavior may remain lightweight, but each production retrieval operation must leave enough persisted evidence to reconstruct why a chunk was used.

Required behavior:

- Persist retrieval runs with `run_id`, `report_id`, query text or query hash, retrieval mode, created timestamp, and selected candidate metadata.
- Persist candidate chunk links to existing `ReportChunk` records, including rank, score fields available from the current retrieval implementation, and whether the chunk was selected for downstream evidence extraction.
- Preserve citation semantics: persisted evidence still validates against `ReportChunk.chunk_text` through `EvidenceService`.
- Replace placeholder lineage responses with DB-derived lineage from `Report`, `ReportChunk`, `EvidenceSpan`, ATT&CK mapping records, `DetectionSpec`, `GeneratedRule`, validation/proof records, review decisions, and export eligibility.
- Add tests proving `report_id -> chunk_id -> evidence_id` lineage is queryable and that missing retrieval lineage cannot be represented as a successful production lineage.

Out of scope for this phase:

- Replacing the current ranking algorithm with real BM25/vector embeddings.
- Adding an external vector database.
- Changing evidence citation contracts.

## Phase 5: Validation/Proof Persistence Enrichment

Validation and proof decisions must be derived from persisted artifacts rather than in-memory assumptions. Static validation, synthetic validation, oracle evaluation, regression safety, and proof obligations should share a clear persistence boundary.

Required behavior:

- Persist static validation outcomes with rule/spec/run linkage, status, and structured detail JSON.
- Persist dynamic synthetic validation results when executed.
- Persist oracle evaluation results and regression run results through the existing models or minimal schema extensions if the current schema is insufficient.
- Persist proof obligation records with deterministic status derived from available validation/evaluation/regression artifacts.
- Fail closed when required proof obligations are absent, unknown, failed, or cannot be evaluated.
- Add tests showing required proof status cannot be satisfied by memory-only objects or missing database rows.

Out of scope for this phase:

- Building a full production sandbox for dynamic execution.
- Adding benchmark adapters beyond the current SOTA product-mode gates.

## Phase 6: True Pipeline Orchestration Repair

The orchestrator must execute the real SOTA path instead of assuming pre-existing validated specs and proof records. Pipeline behavior should be deterministic at the service boundary and explicitly persist state transitions.

Required behavior:

- Start from a persisted `Report` and fail with a truthful error if the report does not exist.
- Use persisted chunks and evidence lineage before DetectionSpec generation or validation.
- Require a verified `DetectionSpec` before any rule generation.
- Generate rules through Detection AST/compiler path, not raw report text.
- Run static validation and wire persistence from Phase 5.
- Execute or explicitly record unavailable dynamic/oracle/regression stages according to fail-closed proof policy.
- Derive proof obligation state from persisted artifacts before allowing final candidate selection.
- Persist `PipelineRunRecord` stage/status transitions truthfully.
- Add tests for successful orchestration and fail-closed paths: missing report, missing evidence, invalid spec, failed validation, failed proof.

Out of scope for this phase:

- UI/dashboard redesign.
- Changing the provider/model strategy.
- Adding fallback model providers.

## Phase 7: Runtime API Hardening

Runtime API surfaces must not expose stubbed or misleading production state. Endpoints that describe runs, lineage, evidence, specs, validation, review, export, dashboard, or metrics must either return DB-derived truth or be explicitly non-production/mock-only.

Required behavior:

- Replace hardcoded run/evidence/spec/validation responses with service-backed persisted state.
- Ensure legacy or convenience endpoints cannot bypass canonical pipeline gates.
- Ensure review/export APIs enforce latest persisted review decision and proof-obligation gates.
- Return clear errors for missing persisted state instead of successful placeholder payloads.
- Keep API routes thin; business logic belongs in services.
- Add integration tests that call runtime endpoints and verify persisted data drives responses.

Out of scope for this phase:

- Full frontend redesign.
- Adding authentication/authorization unless required by existing active plan.

## Phase 8: Health/Metrics Truthfulness

Health and metrics must be measured from actual runtime state. They must not report success, quality, queue depth, latency, or proof/review readiness from constants unless the response clearly labels those values as static configuration.

Required behavior:

- Health checks should report database reachability, schema contract state, and service readiness truthfully.
- Metrics should derive run counts, status distribution, validation/proof/review/export counts, and quality snapshots from persisted records.
- Empty datasets should return explicit empty/no-data values, not optimistic defaults.
- Fail closed or degrade clearly when database/schema checks fail.
- Add tests for empty DB metrics, populated DB metrics, and unhealthy schema/DB behavior.

Out of scope for this phase:

- Production observability integrations such as Prometheus exporters unless already present and needed.
- Synthetic latency values.

## Phase 9: Full SOTA End-to-End Verification

The final phase proves the canonical system behavior through HTTP/API and service-level end-to-end tests.

Required behavior:

- Test successful TXT ingestion through persisted report/chunk creation.
- Test pipeline execution through evidence lineage, DetectionSpec, AST/compiler rule generation, validation/proof persistence, human review, and export eligibility.
- Test fail-closed adversarial cases:
  - missing report;
  - citation mismatch;
  - missing retrieval/evidence lineage;
  - invalid or unvalidated DetectionSpec;
  - failed/unknown proof obligation;
  - latest review rejected after prior approval;
  - legacy/stub endpoints cannot create export eligibility.
- Run schema/migration, docs preflight, evidence/citation, review/export, orchestration, API, health, and metrics regression selections.

Out of scope for this phase:

- Pushing to remote or creating a PR unless explicitly requested.
- Deployment automation.

## Data Flow

```text
Report
  -> ReportChunk
  -> Retrieval audit run/candidates
  -> EvidenceSpan
  -> Evidence graph + ATT&CK mapping
  -> DetectionSpec
  -> Detection AST
  -> GeneratedRule
  -> ValidationResult / TestRun / OracleEvaluationResult / RegressionRun
  -> ProofObligationRecord
  -> ReviewDecision
  -> Export eligibility
```

Each service should accept persisted identifiers, read the required upstream records, and write its downstream artifact only after deterministic validation succeeds.

## Error Handling

All production gates must fail closed. A missing record, stale schema, invalid citation, unavailable proof artifact, failed validation, rejected review, or ambiguous runtime state must block downstream generation/export rather than produce a warning-only success.

Errors should be explicit enough for tests and operators to distinguish:

- missing input;
- invalid persisted state;
- failed deterministic validation;
- missing proof artifact;
- rejected or absent review;
- schema/runtime unavailable.

## Testing Strategy

Each implementation phase gets its own plan with TDD steps and commits. Required test layers:

- Unit tests for deterministic services and derivation logic.
- Integration tests for database persistence and lineage joins.
- API tests for runtime endpoint truthfulness.
- End-to-end tests for canonical SOTA flow and fail-closed adversarial paths.
- Regression checks for schema/migration parity and docs preflight.

## Implementation Strategy

Use one implementation plan per phase or a single plan with phase sections if the implementation scope stays manageable. Each phase must follow the repository workflow:

1. Write failing tests first.
2. Run and observe expected failure.
3. Implement minimal code.
4. Run targeted and affected tests.
5. Complete spec compliance review.
6. Complete code quality review.
7. Commit only related files.

Subagents should be used for implementation and review, but only one implementation subagent should modify the repository at a time.

## Self-Review

Spec coverage: This design covers all requested remaining phases and preserves the SOTA Core v2 production path and fail-closed gates.

Placeholder scan: No TODO, TBD, or unspecified placeholder behavior remains. Items that are deliberately out of scope are explicitly listed.

Scope check: The whole remaining program is large, so the design requires sequential phase plans rather than one large implementation batch.

Ambiguity check: The design explicitly chooses DB-derived truth over placeholders, persistence-derived proof over in-memory proof, and fail-closed behavior over warning-only continuation.

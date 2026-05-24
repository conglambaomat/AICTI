# DE-Forge SOTA Core v2 — Agent-Shared Working Memory Design

**Date:** 2026-05-23  
**Status:** Approved-for-implementation  
**Scope:** Multi-agent context and memory architecture for production runtime path

## 1. Goal

Implement a production-grade, policy-controlled **agent-shared working memory** so agent roles can collaborate efficiently without duplicating context, while preserving fail-closed behavior, deterministic replay, and full auditability.

This design is authoritative for memory/context behavior in the SOTA Core v2 runtime path.

## 2. Decision and Rationale

Chosen architecture: **Memory Bus + Policy Engine + Append-only Event Store + Materialized View**.

Why this is the best fit for DE-Forge:

1. **Correctness-first**: policy is enforced centrally before every memory read/write.
2. **Fail-closed by default**: missing contract, invalid schema, unauthorized role, hash mismatch, or version conflict blocks progression.
3. **Audit/replay strength**: append-only event chain with integrity hash allows deterministic reconstruction.
4. **Operational efficiency**: fast read path via materialized views, while preserving immutable event history.

Alternatives rejected:

- Shared table direct access with DB triggers: policy scatter and weak maintainability.
- Cache-first hybrid (Redis + DB): higher consistency complexity and drift risk for current project constraints.

## 3. Architecture

### 3.1 Components

1. **MemoryService** (single entrypoint)
   - Mandatory gateway for all agent memory operations.
   - Agents and orchestrator do not access memory storage directly.

2. **PolicyEngine**
   - Authorizes operation using `(run_id, agent_role, stage, run_state, namespace, op)`.
   - Default deny; explicit whitelist only.

3. **MemoryEventStore** (append-only)
   - Immutable event log for every successful write/patch/append operation.
   - Carries lineage refs and integrity chain.

4. **MemoryViews** (materialized current state)
   - Per `(run_id, namespace)` current payload + version for low-latency reads.
   - Updated only through MemoryService transaction flow.

5. **Orchestrator Memory Gate Adapter**
   - Enforces stage contract before transition and before stage execution.

6. **ReplayVerifier**
   - Reconstructs state from event chain and validates hash continuity.

### 3.2 Data flow

1. Agent calls MemoryService read/write.
2. PolicyEngine evaluates ACL + stage contract.
3. On write: validate schema and expected version.
4. Append event with `prev_hash -> event_hash` continuity.
5. Update materialized view in same transaction.
6. Return `{version, hash}` to caller.

Any failure in steps 2–5 returns deterministic error and blocks stage progression.

## 4. Data Model

### 4.1 Namespaces (per run_id)

- `evidence.working_set`
- `attack_mapping.hypotheses`
- `detection_spec.draft`
- `rule_generation.draft`
- `validation.findings`
- `refinement.plan`
- `review.handoff`

Each namespace has:
- `schema_version`
- `required_fields`
- `sensitivity`
- `ttl_policy`
- monotonic `version`

### 4.2 memory_events (append-only)

Fields:
- `id` (uuid)
- `run_id`
- `namespace`
- `op` (`append|replace|patch`)
- `actor_role`
- `stage`
- `input_ref` (artifact lineage refs)
- `payload` (JSON, schema-validated)
- `version`
- `prev_hash`
- `event_hash`
- `created_at_utc`

Hash contract:

`event_hash = H(run_id, namespace, version, payload, prev_hash, actor_role, stage, created_at_utc)`

### 4.3 memory_views (materialized)

Fields:
- `run_id`
- `namespace`
- `current_version`
- `current_payload`
- `last_event_hash`
- `updated_at_utc`

## 5. Access Control and Contracts

## 5.1 ACL principles

- Default deny for all `(role, namespace, operation)` tuples.
- Explicit allow-list only.
- Write access is narrower than read access.
- Orchestrator can enforce but not bypass ACL.

### 5.2 Role-to-namespace baseline

- `evidence_agent`: write `evidence.working_set`
- `attack_mapping_agent`: read `evidence.working_set`, write `attack_mapping.hypotheses`
- `detection_spec_agent`: read evidence+mapping, write `detection_spec.draft`
- `rule_generation_agent`: read spec draft, write `rule_generation.draft`
- `static_validation`: read rule draft, write `validation.findings`
- `critic/refiner`: read rule+validation, write `refinement.plan`
- `review_service`: read required handoff, write `review.handoff`

### 5.3 Stage memory contracts

Each pipeline stage defines required memory preconditions:
- required namespaces
- required fields in payload
- minimum versions (when relevant)

Examples:
- Before rule generation: `detection_spec.draft` with required telemetry and behavior rules.
- Before export: valid `review.handoff` and approved latest decision gate.

Violation blocks transition with `PipelineTransitionError`.

## 6. Runtime Integration

In `PipelineOrchestrator.run_pipeline(...)`:

1. `require_contract(...)` before each stage.
2. Stage output persisted via `MemoryService.write(...)`.
3. Next stage reads from MemoryService only.
4. Any memory integrity/policy failure blocks the run (`fail-closed`).

No fallback to in-memory ad-hoc state for authoritative stage memory.

## 7. Fail-Closed Rules

The following must hard-fail the stage:

1. Unauthorized read/write operation.
2. Missing required namespace or required payload field.
3. Namespace schema mismatch.
4. Expected version mismatch (write conflict).
5. Hash chain discontinuity or tamper detection.
6. Replay reconstruction mismatch with materialized view hash.

Failure status should be persisted in run timeline with memory error code.

## 8. Replay and Auditability

Replay contract:
- Rebuild namespace state from `memory_events` in order.
- Verify `prev_hash` chain at each step.
- Resulting reconstructed payload hash must match `memory_views.last_event_hash`.

This provides forensic confidence and deterministic post-incident analysis.

## 9. Performance and Retention

- Read path: `memory_views` keyed by `(run_id, namespace)`.
- Write path: append event + update view in one transaction.
- Compaction: periodic snapshots may be added, but full event history is retained for audit.
- TTL applies only where policy allows, never to required compliance-critical records.

## 10. Verification Matrix

Required tests before DONE:

1. Happy path shared-memory flow across full pipeline.
2. ACL violation blocks unauthorized role.
3. Missing contract blocks stage transition.
4. Version conflict rejects concurrent stale write.
5. Hash tamper detection blocks replay/integrity.
6. Replay determinism equals materialized state.
7. Export blocked without valid `review.handoff` + approval.

All tests are mandatory and fail-closed.

## 11. Non-Negotiable Invariants Preserved

1. No raw-report-to-rule bypass.
2. DetectionSpec-first remains mandatory.
3. Human review remains mandatory before export.
4. Agent/refinement loops remain bounded.
5. Full artifact lineage and memory event auditability preserved.

## 12. Implementation Boundaries

This design introduces shared working memory for agent collaboration only.

Out of scope for this slice:
- external distributed cache infrastructure,
- cross-project memory federation,
- non-deterministic heuristic memory ranking.

These are intentionally deferred to preserve deterministic product-mode behavior.

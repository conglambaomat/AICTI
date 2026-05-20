# DE-Forge Production Completion Design

Date: 2026-05-20  
Status: READY_FOR_IMPLEMENTATION  
Scope: Complete missing production-critical layers without breaking existing agentic service invariants

---

## A) Scope & Non-scope

### In-scope (this design cycle)
This design defines production-completion work for the following 5 gaps:
1. API layer (pipeline endpoints + human review/export gate endpoints)
2. Persistence layer (SQLAlchemy models + Alembic migrations + lineage traceability)
3. E2E validation layer (full profile pipeline behavior from API ingress to review-ready output)
4. Benchmark evaluation runner (baseline delta + KPI gate computation over dataset manifest)
5. Real LLM integration testing (provider-backed, schema-validated, deterministic-enough harness)

### Out-of-scope (this design cycle)
- SIEM auto-deployment and tenant routing
- Full OpenCTI/MISP integration
- OCR pipeline
- Multi-region/high-availability infra deployment
- Replacing existing service behavior semantics already validated by current integration tests

### Gap mapping to current repo
- API gap: no `src/de_forge/api/routes/pipeline.py`; only root/health exists in `src/de_forge/main.py:22-35`
- Persistence gap: no `src/de_forge/models/` package, no migration scripts for domain entities
- E2E gap: no `tests/e2e/` suite while required by project guidance
- Benchmark runner gap: no `tests/benchmark/test_baseline_delta.py` implementation
- Real LLM test gap: `tests/integration/services/test_llm_client.py` currently uses transport-level contract tests, not real provider integration

---

## B) Current-state audit (concise and concrete)

### Reusable modules already present
- Orchestration skeleton: `src/de_forge/services/orchestrator.py:12-142`
- LLM contract and retry logic: `src/de_forge/services/llm_client.py:14-315`
- Retrieval deterministic skeleton: `src/de_forge/services/retrieval.py:39-148`
- Evidence/ATT&CK/DetectionSpec/Rule/Refinement services:
  - `src/de_forge/services/evidence.py:7-54`
  - `src/de_forge/services/attack_mapping.py:8-62`
  - `src/de_forge/services/detection_spec.py:5-60`
  - `src/de_forge/services/rule_generation.py:5-43`
  - `src/de_forge/services/refinement.py:5-66`
- KPI and canary gates:
  - `src/de_forge/services/kpi_evaluator.py:5-60`
  - `src/de_forge/services/canary_ops.py:5-53`
- Config/profile constants:
  - `src/de_forge/core/config.py:10-80`
  - `src/de_forge/core/constants.py`

### Stub/mock/heuristic points to replace with real integrations
- Orchestrator evidence is heuristic stub (`_extract_evidence_stub`): `src/de_forge/services/orchestrator.py:132-141`
- Orchestrator KPI inputs are mock literals (`mock_metrics`, `mock_thresholds`): `src/de_forge/services/orchestrator.py:94-109`
- Retrieval dense/sparse/rerank are deterministic placeholders (no real embeddings or cross-encoder)
- No persisted run/report/stage state; all service outputs are in-memory transient
- No API abstraction separating abstain outcome vs hard-fail transport errors

### Architecture constraints already encoded and must be preserved
- DetectionSpec-first and abstain propagation in orchestration: `src/de_forge/services/orchestrator.py:52-74`
- Bounded refinement loops: `src/de_forge/services/refinement.py:27-42`
- Profile-aware ATT&CK confidence thresholds: `src/de_forge/services/attack_mapping.py:22-49`

---

## C) Target architecture (textual diagram)

```
[API Ingress]
  POST /v1/reports:ingest
    -> Persist Report + create run_id/trace_id
    -> Orchestrator start

[Orchestrator Service Layer]
  report input
    -> RetrievalService.index_chunks/retrieve
    -> EvidenceAgentService.extract (retrieval-grounded)
    -> AttackMappingService.map_attack
    -> DetectionSpecService.build_detection_spec
    -> RuleGenerationService.generate_rule
    -> StaticValidator + RefinementController (bounded loops)
    -> KPIEvaluator.evaluate_kpis (real metrics)
    -> CanaryOpsService.evaluate_canary
    -> HumanReviewGate (required approval)

[Persistence Boundary]
  Persist each stage artifact + lineage:
  report_id, run_id, trace_id, detection_spec_id, rule_id, evidence_id/chunk_id, agent_run_id

[Validation Boundary]
  Contract validators (schema/citation/faithfulness/state-machine/loop bounds)
  Hard-fail blocks progression

[Review & Export Boundary]
  Review decision endpoint required before export endpoint
  Export only if review_approved=true and all hard gates pass
```

### Required traceability fields carried end-to-end
- `report_id`
- `run_id`
- `trace_id`
- `agent_run_id` per stage
- `evidence_id` and `chunk_id`
- `detection_spec_id`
- `rule_id` and `rule_version`

---

## D) Detailed design per 5 workstreams

### Workstream 1: API layer

**Responsibilities**
- Expose deterministic, contract-first endpoints for ingest, execute pipeline, review, and export
- Normalize abstain vs hard-fail into standardized response model
- Prevent raw-report-to-rule bypass by endpoint policy

**Interfaces/contracts**
- FastAPI routers under `src/de_forge/api/routes/`
- Pydantic request/response schemas under `src/de_forge/schemas/`
- Service invocation only through orchestrator facade (no direct stage skip endpoints)

**Input/output schemas**
- Request schema includes profile, report content/meta, optional idempotency key
- Response schema includes stage outcomes, abstain code/reason, gate status, traceability IDs

**Failure modes + mapping**
- Contract invalid input -> HTTP 422 (`HARD_FAIL_INPUT_SCHEMA`)
- Stage abstain -> HTTP 200 with `status="abstain"` and code
- Hard gate failure (citation mismatch, loop breach, schema-invalid stage) -> HTTP 409/422 depending on locus
- Dependency outage -> HTTP 503

**Deterministic validation hooks**
- Request schema validation
- State transition guard (must follow stage order)
- Disallow endpoint combinations that imply bypass

**Security/safety constraints**
- No endpoint to submit direct rule text for production path
- No unsupported claims accepted without citation lineage
- Redact secrets from logs; never log raw API keys

---

### Workstream 2: Persistence layer

**Responsibilities**
- Persist immutable stage artifacts and run lineage
- Support replay, audit, and benchmark extraction queries

**Interfaces/contracts**
- SQLAlchemy ORM models in `src/de_forge/models/`
- Repository interfaces in `src/de_forge/services/repositories/`
- Alembic migrations in `alembic/versions/`

**Input/output schemas**
- ORM maps exactly to canonical artifact contracts (evidence, attack mapping, DetectionSpec, rule output)
- JSON columns for contract payload snapshots + hash fields for integrity

**Failure modes + mapping**
- Persistence write failure -> hard fail (pipeline halts)
- Duplicate idempotency key -> return existing run state
- Version conflict on immutable artifact -> hard fail

**Deterministic validation hooks**
- Unique constraints: `(report_id, run_id)`, immutable `(rule_id, version)`
- Payload schema hash check before persistence

**Security/safety constraints**
- Store raw reports with retention policy + optional encryption at rest configuration
- No mutation of persisted generated rule versions

---

### Workstream 3: E2E validation layer

**Responsibilities**
- Verify full API→services→persistence→review flow per profile
- Assert hard gate and abstain policy behavior from external interface

**Interfaces/contracts**
- HTTPX-based tests in `tests/e2e/test_agentic_pipeline_profiles.py`
- Fixtures from `tests/fixtures/ground_truth/`

**Input/output schemas**
- E2E inputs are report payloads + profile parameters
- E2E outputs include stage outcomes + persisted IDs + review/export eligibility

**Failure modes + mapping**
- Any state-machine violation => test hard fail
- Any missing lineage field => test hard fail
- Abstain misuse (coverage explosion with precision drop) => gate fail

**Deterministic validation hooks**
- Replay same input twice, compare critical deterministic fields
- Stage timestamp tolerance allowed; payload hash and decision path must match

**Security/safety constraints**
- Negative test asserts no API path can create/export rule without DetectionSpec and review approval

---

### Workstream 4: Benchmark evaluation runner

**Responsibilities**
- Execute baseline-delta protocol from dataset manifest
- Compute KPI and promotion decision matrix per profile

**Interfaces/contracts**
- Benchmark tests under `tests/benchmark/test_baseline_delta.py`
- Runner utility module `src/de_forge/services/benchmark_runner.py`

**Input/output schemas**
- Inputs: ground truth bundles + baseline results JSON + profile config
- Outputs: structured benchmark report (`run_summary`, `quality`, `abstain`, `faithfulness`, `cost_latency`, `delta`, `promotion`)

**Failure modes + mapping**
- Missing fixture/baseline file -> hard fail
- Metrics computation incomplete -> hard fail
- Any hard gate breach -> promotion=false

**Deterministic validation hooks**
- Fixed fixture ordering
- Stable metric aggregation order and decimal rounding policy

**Security/safety constraints**
- Benchmark runner must not silently skip failed samples

---

### Workstream 5: Real LLM integration testing

**Responsibilities**
- Validate real provider compatibility for LLMClient contracts and schema parsing
- Measure real latency/token/cost telemetry paths

**Interfaces/contracts**
- `tests/integration/services/test_llm_client_real_provider.py`
- Marked test category requiring `OPENAI_API_KEY` and explicit opt-in env var (e.g., `RUN_REAL_LLM_TESTS=1`)

**Input/output schemas**
- Inputs: deterministic prompts + strict JSON schema constraints
- Outputs: validated `LLMResponse`, parsed object, usage/cost metadata

**Failure modes + mapping**
- Missing credentials -> skip (not fail) in CI default
- Provider auth/model error -> fail real-integration suite
- Schema/parse violation -> fail suite

**Deterministic validation hooks**
- Temperature=0, strict JSON response format
- Assertions on shape and contract, not exact natural-language token strings

**Security/safety constraints**
- No secret in logs/assert messages
- Rate-limit-safe retry bounds obey client contract

---

## E) Detailed API contract

### Endpoint list

1. `POST /v1/reports:ingest`
- Purpose: ingest report and create canonical report record
- Request:
```json
{
  "source_type": "txt",
  "content": "<report text>",
  "external_ref": "optional-ref",
  "metadata": {"title": "sample"}
}
```
- Response `201`:
```json
{
  "report_id": "rep_...",
  "status": "ingested",
  "trace_id": "trc_..."
}
```

2. `POST /v1/pipeline:run`
- Purpose: execute DetectionSpec-first pipeline for an ingested report
- Request:
```json
{
  "report_id": "rep_...",
  "profile": "balanced",
  "idempotency_key": "optional-key"
}
```
- Response `200` (success/abstain both in-body):
```json
{
  "run_id": "run_...",
  "status": "ok",
  "abstain": false,
  "stage": "canary",
  "detection_spec_id": "ds_...",
  "rule_id": "rule_...",
  "canary": {"action": "promote", "reason_code": "CANARY_PASS"}
}
```
- Abstain response:
```json
{
  "run_id": "run_...",
  "status": "abstain",
  "abstain": true,
  "stage": "attack_mapping",
  "abstain_code": "ATTACK_CONFIDENCE_BELOW_PROFILE_THRESHOLD",
  "reason": "..."
}
```

3. `GET /v1/runs/{run_id}`
- Purpose: inspect run state + stage artifacts summary
- Response `200` with stage timeline and lineage IDs

4. `POST /v1/reviews`
- Purpose: human review decision gate
- Request:
```json
{
  "run_id": "run_...",
  "decision": "approve",
  "reviewer": "analyst@team",
  "notes": "looks correct"
}
```
- Response `200`: review record and export eligibility

5. `POST /v1/exports/sigma`
- Purpose: export approved rule version
- Preconditions: run hard gates pass + review approved
- Request:
```json
{"run_id": "run_..."}
```
- Response `200` contains immutable `rule_id`, `rule_version`, `sigma_rule`
- If precondition missing: `409`

### Idempotency and async behavior
- `POST /v1/pipeline:run` supports idempotency key; duplicate returns existing run state
- Initial version can be sync for MVP-sized reports; async transition-ready by persisting run status machine (`queued/running/completed/failed/abstained`)

### Standardized error model
- `status="abstain"`: expected safe non-generation outcome
- `status="failed"`: hard-fail due to invariant/gate/runtime/persistence errors
- Error body shape:
```json
{
  "status": "failed",
  "error_code": "CITATION_MISMATCH_HARD_FAIL",
  "message": "...",
  "trace_id": "trc_...",
  "run_id": "run_..."
}
```

---

## F) Detailed persistence contract

### Core tables/models
1. `reports`
- `id (report_id PK)`
- `source_type`, `content`, `content_hash`, `metadata_json`, `created_at`

2. `pipeline_runs`
- `id (run_id PK)`, `report_id FK`, `trace_id`, `profile`, `status`, `abstain_code`, `error_code`, `started_at`, `ended_at`, `idempotency_key (nullable unique)`

3. `retrieval_chunks`
- `id (chunk_id PK)`, `report_id FK`, `chunk_index`, `text`, `start_offset`, `end_offset`, `token_count`, `embedding_ref (nullable)`

4. `evidence_spans`
- `id (evidence_id PK)`, `run_id FK`, `chunk_id FK`, `quote`, `start_offset`, `end_offset`, `behavior_label`, `supported`

5. `attack_mappings`
- `id PK`, `run_id FK`, `technique_id`, `technique_name`, `confidence`, `rationale`, `evidence_ids_json`

6. `detection_specs`
- `id (detection_spec_id PK)`, `run_id FK unique`, `payload_json`, `schema_version`, `payload_hash`

7. `generated_rules`
- `id (rule_id PK)`, `run_id FK`, `version`, `format`, `payload_json`, `immutable=true`, `created_at`
- Unique `(rule_id, version)`

8. `validation_events`
- `id PK`, `run_id FK`, `stage`, `validator`, `status`, `details_json`, `created_at`

9. `review_decisions`
- `id PK`, `run_id FK unique`, `reviewer`, `decision`, `notes`, `created_at`

10. `export_events`
- `id PK`, `run_id FK`, `rule_id FK`, `version`, `format`, `exported_at`, `export_ref`

11. `llm_call_logs`
- `id PK`, `run_id FK`, `trace_id`, `agent_name`, `stage`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`, `latency_ms`, `status`, `error_type`

### Relationships
- reports 1:N pipeline_runs
- pipeline_runs 1:N evidence_spans, attack_mappings, validation_events, llm_call_logs
- pipeline_runs 1:1 detection_specs, review_decisions
- pipeline_runs 1:N generated_rules, export_events
- retrieval_chunks linked by report_id; evidence_spans linked by chunk_id

### Versioning and immutability strategy
- DetectionSpec and Rule artifacts are append-only snapshots
- Rule edits produce new `version`; previous versions immutable

### Migration strategy (Alembic)
- Initial migration creates all tables + constraints + essential indexes
- Follow-up migration can add performance indexes (report_id+created_at, run status)
- Backward compatibility: API reads tolerate additional JSON fields; no destructive rename without data migration

### Data retention and audit trail
- Minimum retention for pipeline_runs/artifacts/logs configurable (default 180 days)
- Audit trail preserved in validation_events/review_decisions/export_events

---

## G) Detailed test strategy (test pyramid)

### Unit tests
- Pure logic: validators, state machine transitions, DTO/schema validators
- Fast deterministic checks for mapping/threshold/abstain policies

### Integration tests
- Service-level contracts (already present) remain required
- Add DB integration tests for repositories and transactional consistency

### E2E tests
- API-level full profile paths:
  - success with review+export
  - abstain paths
  - hard-fail gate paths
  - no bypass policy assertions

### Benchmark tests
- Dataset manifest-driven delta gate checks
- Per-profile promotion decisions and hard-fail audit checks

### Contract tests
- JSON schema conformance for each persisted/returned artifact

### RED-GREEN-REFACTOR rollout clusters
1. API schema + endpoint red tests
2. Persistence schema/repository red tests
3. E2E profile path red tests
4. Benchmark runner red tests
5. Real LLM integration red tests (opt-in)

### Gate commands that must pass
- `pytest tests/ -v --cov=src --cov-report=term-missing`
- `mypy src/`
- `ruff check src/`
- `ruff format --check src/`
- `pytest tests/benchmark/test_baseline_delta.py -v`
- `pytest tests/e2e/test_agentic_pipeline_profiles.py -v`

### Deterministic replay criteria
- Same input report/profile/config must produce identical:
  - stage decision path
  - abstain/hard-fail code
  - detection_spec payload hash
  - rule payload hash (if generated)
- Allowed non-deterministic fields: timestamps, DB surrogate IDs if not externally meaningful

---

## H) KPI & rollout gates

### Real metric capture (non-mock)
- Quality/abstain/faithfulness metrics derived from benchmark fixtures + persisted run artifacts
- Cost/latency from `llm_call_logs` and stage timing fields
- Citation faithfulness from static validation events against chunk offsets

### Canary + rollback trigger matrix
- Rollback immediately if:
  - hard-fail invariant event (schema violation, citation mismatch, loop breach, state transition violation)
  - KPIEvaluator returns fail on required profile thresholds
  - baseline delta gate fails
- Promote only if:
  - all required KPI thresholds pass
  - no hard-fail events
  - review approved

### Promotion criteria vs baseline delta
- Must enforce documented deltas from `docs/benchmark/eval-dataset-manifest.md` and `docs/implementation/kpi-threshold-matrix.md`
- Balanced default promotion requires quality gains with no abstain regression and cost/latency within policy limits

---

## I) Implementation plan (handoff-ready)

### Phase 1 — API and schema foundation

Task 1 (2–6m)
- Files: `tests/e2e/test_api_health_and_contracts.py`
- RED: add failing tests for `/v1/reports:ingest`, `/v1/pipeline:run` non-existence
- Expected fail: 404
- Minimal implementation: create router skeleton with strict request/response schemas
- Expected pass: status codes and body shape pass
- Verify: `pytest tests/e2e/test_api_health_and_contracts.py -v`

Task 2 (3–8m)
- Files: `src/de_forge/schemas/api_pipeline.py`, `src/de_forge/api/routes/pipeline.py`, `src/de_forge/main.py`
- RED: schema validation tests for invalid profile and missing report_id
- Expected fail: 422 contract mismatch
- Minimal implementation: wire Pydantic models + router inclusion
- Expected pass: 422/200 behavior
- Verify: same test command

Task 3 (2–8m)
- Files: `tests/e2e/test_api_abstain_vs_hard_fail.py`, `src/de_forge/api/routes/pipeline.py`
- RED: assert abstain returns `status=abstain` (200), hard fail returns standardized error
- Expected fail: wrong/unstructured error mapping
- Minimal implementation: error mapper + abstain mapper
- Expected pass: body codes match contract
- Verify: `pytest tests/e2e/test_api_abstain_vs_hard_fail.py -v`

### Phase 2 — Persistence and migrations

Task 4 (3–10m)
- Files: `tests/integration/persistence/test_models_schema.py`
- RED: expected tables/columns/constraints absent
- Expected fail: metadata/table lookup failure
- Minimal implementation: add SQLAlchemy models in `src/de_forge/models/*.py`
- Expected pass: model metadata assertions pass
- Verify: `pytest tests/integration/persistence/test_models_schema.py -v`

Task 5 (4–10m)
- Files: `alembic/versions/*_create_pipeline_tables.py`, `tests/integration/persistence/test_migration_up_down.py`
- RED: migration test fails due missing revision
- Expected fail: alembic upgrade failure
- Minimal implementation: create initial migration with required FKs/uniques/indexes
- Expected pass: upgrade/downgrade pass
- Verify: `pytest tests/integration/persistence/test_migration_up_down.py -v`

Task 6 (3–8m)
- Files: `src/de_forge/services/repositories/*.py`, `tests/integration/persistence/test_repositories.py`
- RED: repository roundtrip fails
- Expected fail: unimplemented repository methods
- Minimal implementation: CRUD for report/run/artifact/review/export flows
- Expected pass: roundtrip and immutability checks pass
- Verify: `pytest tests/integration/persistence/test_repositories.py -v`

### Phase 3 — Orchestrator persistence integration

Task 7 (3–9m)
- Files: `tests/integration/services/test_orchestrator_persistence_lineage.py`, `src/de_forge/services/orchestrator.py`
- RED: lineage fields not persisted
- Expected fail: missing IDs in persisted records
- Minimal implementation: orchestrator writes stage artifacts via repositories
- Expected pass: lineage assertions pass
- Verify: `pytest tests/integration/services/test_orchestrator_persistence_lineage.py -v`

Task 8 (3–8m)
- Files: `tests/integration/services/test_orchestrator_no_bypass_policy.py`, `src/de_forge/api/routes/pipeline.py`
- RED: bypass path exists or review gate unenforced
- Expected fail: export allowed without review
- Minimal implementation: enforce review prerequisite
- Expected pass: 409 before approval, 200 after approval
- Verify: `pytest tests/integration/services/test_orchestrator_no_bypass_policy.py -v`

### Phase 4 — E2E profile validation

Task 9 (3–10m)
- Files: `tests/e2e/test_agentic_pipeline_profiles.py`
- RED: full profile flow tests fail
- Expected fail: missing persistence/API coupling
- Minimal implementation: finalize API-service-repo wiring
- Expected pass: strict/balanced/exploratory scenarios pass
- Verify: `pytest tests/e2e/test_agentic_pipeline_profiles.py -v`

Task 10 (2–8m)
- Files: `tests/e2e/test_review_export_gate.py`
- RED: review/export lifecycle failing
- Expected fail: missing endpoint or wrong status
- Minimal implementation: review and export endpoints + state checks
- Expected pass: lifecycle assertions pass
- Verify: `pytest tests/e2e/test_review_export_gate.py -v`

### Phase 5 — Benchmark runner

Task 11 (3–10m)
- Files: `tests/benchmark/test_baseline_delta.py`, `src/de_forge/services/benchmark_runner.py`
- RED: benchmark module absent
- Expected fail: import/logic failures
- Minimal implementation: metric aggregator + baseline delta evaluator + promotion decision
- Expected pass: manifest-defined gates enforced
- Verify: `pytest tests/benchmark/test_baseline_delta.py -v`

Task 12 (2–8m)
- Files: `tests/benchmark/test_kpi_matrix_enforcement.py`
- RED: profile matrix gates not applied correctly
- Expected fail: false-pass/false-fail
- Minimal implementation: map KPI matrix thresholds by profile
- Expected pass: threshold tests pass
- Verify: `pytest tests/benchmark/test_kpi_matrix_enforcement.py -v`

### Phase 6 — Real LLM integration tests

Task 13 (3–8m)
- Files: `tests/integration/services/test_llm_client_real_provider.py`
- RED: real-provider contract test absent
- Expected fail: import skip or failing auth path
- Minimal implementation: opt-in test harness + env checks + strict JSON schema call
- Expected pass: when opt-in creds present, contract assertions pass
- Verify: `RUN_REAL_LLM_TESTS=1 pytest tests/integration/services/test_llm_client_real_provider.py -v`

Task 14 (2–8m)
- Files: `tests/integration/services/test_llm_observability_accounting.py`
- RED: missing persisted usage/cost telemetry assertions
- Expected fail: no storage/event link
- Minimal implementation: persist llm_call_logs and assert fields
- Expected pass: tokens/cost/latency linked to run_id/trace_id
- Verify: `pytest tests/integration/services/test_llm_observability_accounting.py -v`

### Dependency graph (high-level)
- Phase1 -> Phase2 -> Phase3 -> Phase4 -> Phase5
- Phase6 depends on Phase1 + LLM client contract stability
- Task 8 depends on Task 10 endpoint contracts being present

### Risk register + mitigation by phase
- P1 Risk: API contract churn  
  Mitigation: freeze schemas early + contract tests first
- P2 Risk: migration mismatch across SQLite/Postgres  
  Mitigation: DB-agnostic types and migration integration tests
- P3 Risk: orchestration side effects break existing service tests  
  Mitigation: preserve service APIs and add adapter layer
- P4 Risk: flaky E2E timing/state  
  Mitigation: deterministic fixtures + explicit run state machine checks
- P5 Risk: baseline data drift  
  Mitigation: fixture hash check + fail on missing baseline
- P6 Risk: provider instability/rate limits  
  Mitigation: opt-in suite + bounded retries + non-blocking default CI path

---

## J) Definition of Done (production-complete)

### Functional
- [ ] API endpoints for ingest/run/review/export implemented and contract-tested
- [ ] Pipeline enforces DetectionSpec-first and no raw-report-to-rule bypass
- [ ] Human review gate enforced before export

### Quality and safety
- [ ] Hard-gate validators block invalid progression (schema/citation/state/loop)
- [ ] Abstain and hard-fail outcomes mapped consistently to contract
- [ ] Existing integration service suite continues to pass

### Persistence and traceability
- [ ] All required lineage IDs persisted for every run/stage
- [ ] Artifacts immutable/versioned where required
- [ ] Alembic migrations reproducible up/down

### Testing and gates
- [ ] Unit + integration + e2e + benchmark suites pass
- [ ] `pytest && mypy src/ && ruff check src/` pass
- [ ] Benchmark baseline delta gates pass for deployment profile
- [ ] Deterministic replay criteria satisfied

### Observability and reproducibility
- [ ] LLM usage/cost/latency metrics persisted by run/agent/stage
- [ ] Run reports reproducible with run_id/trace_id/prompt_version/model_id
- [ ] Review decision and export events auditable end-to-end

---

## Spec self-review loop

### Round 1: Spec compliance review (CLAUDE.md + architecture docs)
- Verified DetectionSpec-first invariant is preserved in API/orchestration rules
- Verified hard gates, abstain policy, bounded loops, human review gate are explicitly represented
- Verified no raw-report-to-rule bypass allowed
- Verified KPI/baseline delta policies mapped from implementation docs
- Fix applied: explicit review prerequisite added to export endpoint section and Task 8/10 plan details

### Round 2: Codebase feasibility review
- Ensured design extends existing modules rather than replacing service contracts
- Avoided over-design (no premature multi-tenant/SIEM deployment work)
- Kept orchestration adapter strategy to preserve current integration tests
- Fix applied: added concrete file paths for missing layers and test-first sequence by 2–10 minute tasks

Final status: READY_FOR_IMPLEMENTATION

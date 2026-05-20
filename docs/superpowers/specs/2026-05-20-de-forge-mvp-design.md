# DE-Forge MVP Design Spec (Contract-First Vertical Slices)

Date: 2026-05-20
Status: Approved (brainstorming complete)
Approach: Contract-first vertical slices

## 1. Goal and Priority
Build a production-minded MVP pipeline for DE-Forge that prioritizes correctness, robustness, and traceability over speed/cost.

Pipeline target:
Threat report -> evidence extraction -> ATT&CK mapping -> telemetry grounding -> DetectionSpec -> Sigma generation -> static/dynamic validation -> human review gate.

## 2. Authoritative Sources and Conflict Resolution
Precedence order applied:
1. `E:/Khoaluanfinal/ai-threat-detection/CLAUDE.md`
2. `E:/Khoaluanfinal/CLAUDE.md`
3. `docs/` architecture/spec/implementation contracts
4. Ultra-autonomous directive

Conflict resolution note:
- No material contradictions found between directive and higher-priority CLAUDE docs.
- Where loop/retry semantics are concerned, `docs/architecture/08-canonical-retry-state.md` is treated as canonical source of truth.

## 3. Non-Negotiable Invariants
1. DetectionSpec-first invariant is mandatory.
2. No direct raw-report-to-rule path may exist.
3. DetectionSpec-first is enforced both at runtime and in tests (no bypass path).
4. Retry/state/idempotency must conform to canonical retry-state contract before stage advancement.
5. Every stage must persist evidence-backed lineage fields before transition.
6. Failed gate checks deterministically ABSTAIN or fail-fast; no soft-pass.

## 4. Architecture (Contract-First Vertical Slices)
Use stage-by-stage implementation where each stage has hard advancement gates:
- Contract validity gate (schema + semantic constraints)
- Persistence gate (lineage + idempotent write success)
- State gate (canonical transition predicate satisfied)

Hard-gate rule:
- A stage cannot emit downstream input unless all three gates pass.
- Rule generation is blocked unless a validated DetectionSpec exists.

## 5. Stage Design and Gate Contracts

### Stage 1: Report ingestion + deterministic chunking
Inputs: TXT/PDF report
Outputs: `reports`, `report_chunks`
Gates:
- deterministic chunk IDs and offsets
- content hash uniqueness
- transaction success and lineage persistence

### Stage 2: Evidence extraction
Inputs: persisted chunks
Outputs: `evidence_spans`, `extracted_iocs`
Gates:
- strict evidence payload contract
- quote offsets and claim support validity
- fail-fast for empty/invalid extraction

### Stage 3: ATT&CK mapping + abstain eligibility
Inputs: evidence
Outputs: `attack_mappings` or structured abstain
Gates:
- ATT&CK ID format validity
- confidence bounds
- deterministic abstain when evidence is insufficient

### Stage 4: Telemetry grounding
Inputs: ATT&CK mapping + schema registry
Outputs: `telemetry_selections`
Gates:
- allowed telemetry fields only
- required telemetry presence for behavior rules
- deterministic abstain when telemetry unsupported

### Stage 5: DetectionSpec build + strict validation
Inputs: evidence + mapping + telemetry
Outputs: `detection_specs`
Gates:
- full DetectionSpec schema validity
- behavior_rule vs abstain branch constraints
- mandatory evidence/attack/telemetry linkage for behavior rules

### Stage 6: Sigma generation (MVP primary)
Inputs: validated DetectionSpec
Outputs: `query_candidates` (if used), `generated_rules`
Gates:
- no generation without validated DetectionSpec
- output constrained to DetectionSpec logic/telemetry
- immutable rule versioning

### Stage 7: Static validation gates
Inputs: generated Sigma
Outputs: `validation_results` (static)
Gates:
- schema and syntax validity
- evidence integrity checks
- ATT&CK ID validity
- telemetry field validity
- broad-rule detection checks

### Stage 8: Minimal dynamic validation
Inputs: statically valid rule
Outputs: `test_runs`, `validation_results` (dynamic)
Gates:
- synthetic log path executes deterministically
- TP/FP summary generated
- bounded dynamic refinement eligibility determined

### Stage 9: Bounded refinement loop
Inputs: validation failures
Outputs: refined spec/rule or terminal failure/abstain
Gates:
- canonical retry ceilings respected
- loop termination proven by integration tests
- no unbounded retries

### Stage 10: Human review gate + export policy
Inputs: validated artifact
Outputs: `review_decisions`, terminal status
Gates:
- no export without explicit human approval
- append-only review decisions

## 6. Persistence and Traceability Contract
Implement and enforce `docs/architecture/06-data-persistence-contract.md`.

Key enforcement:
- all artifacts persisted with lineage: `report_id`, `chunk_id/evidence_id`, `detection_spec_id`, `rule_id`, `run_id`, `trace_id`, `agent_run_id`
- generated rules immutable; edits create new versions
- all state transitions idempotent

### Idempotency key policy (deterministic)
- `idempotency_key = hash(stage_identifier + canonicalized_input_payload)`
- canonicalization strategy is deterministic and documented in code/tests
- no random entropy in idempotency keys

### Transaction boundaries
Atomic transactions align with persistence contract and canonical retry/state semantics:
- report + chunks
- evidence + IOCs
- spec + telemetry linkage
- rule + query artifacts
- validation + test runs

Rollback policy:
- any atomic failure rolls back the full transaction and marks corresponding run state as failed/abstained per canonical transition rules.

## 7. Agent Run Auditability
`agent_runs` must capture full audit trail beyond status:
- normalized input payload snapshot
- normalized output payload snapshot
- input/output hashes
- model/prompt metadata
- retry attempts and terminal status

Integrity requirement:
- payload hashes are verified on read; mismatch yields deterministic corruption error state.

## 8. Retry/State/Abstain Policy
Canonical source: `docs/architecture/08-canonical-retry-state.md`.

Enforcement:
- retry ceilings strictly enforced
- refinement loops bounded and terminating
- no automatic retry for validation failures outside defined loops

### Structured abstain model
Abstain reasons are not free text. Use structured format:
- `abstain_code` (enum)
- `abstain_context` (object with stage-specific fields)
- `human_message` (short deterministic explanation)

Initial enum set (MVP):
- `NO_EVIDENCE_BACKED_BEHAVIOR`
- `NO_TELEMETRY_SUPPORT`
- `ONLY_CVE_WITHOUT_OBSERVABLES`
- `ONLY_TOOL_OR_MALWARE_NAME_NO_BEHAVIOR`
- `OVERBROAD_AFTER_BOUNDED_REFINEMENT`
- `CONTRACT_VALIDATION_EXHAUSTED`

## 9. Testing Strategy (Strict TDD)
TDD per stage: RED -> GREEN -> REFACTOR, no implementation before failing tests.

### Unit tests
- gate predicates isolated and deterministic
- no dependency on full pipeline state
- DetectionSpec hard-gate predicate tests

### Integration tests
- transaction boundary correctness
- retry ceiling enforcement and loop termination proofs
- deterministic fail-fast vs abstain transitions
- migration-level DB constraints/indexes/foreign keys validation

### End-to-end tests
- positive path: report -> DetectionSpec -> validated Sigma -> awaiting human review
- negative/adversarial path: ambiguous threat report must deterministically ABSTAIN
- no bypass path around DetectionSpec

### Deterministic replay tests
Same input across replayed runs must produce:
- same stage outputs (modulo immutable identifiers where allowed by contract)
- same state transitions
- same idempotency behavior

## 10. MVP Scope Boundaries
In scope:
- TXT/PDF ingestion
- evidence extraction
- ATT&CK mapping
- telemetry grounding
- DetectionSpec generation
- Sigma generation
- static validation
- basic synthetic dynamic testing
- human review gate

## 10.1 Model/Provider Lock (Mandatory)
All agent roles must use one provider/model configuration:
- provider type: OpenAI-compatible
- base URL: `https://shopapikey.com/v1`
- API key env var: `OPENAI_API_KEY`
- model: `cx/gpt-5.5`

No fallback provider/model logic is allowed unless explicitly requested.

Out of scope:
- auto-deploy to production SIEM
- replacing human detection engineers
- full OpenCTI/MISP integration
- enterprise multi-tenant auth
- fallback model/provider logic

Out of scope:
- auto-deploy to production SIEM
- replacing human detection engineers
- full OpenCTI/MISP integration
- enterprise multi-tenant auth
- fallback model/provider logic

## 11. Definition of Done
Done only when all are true:
1. End-to-end run completes: report -> DetectionSpec -> validated Sigma artifact -> human review gate.
2. DetectionSpec-first invariant is enforced at runtime and proven by tests.
3. Retry/state/idempotency comply with canonical contract.
4. Persistence/lineage/idempotency constraints enforced and tested.
5. Structured abstain model implemented and validated.
6. Unit + integration + E2E + deterministic replay + migration tests pass.
7. Verification commands pass in a clean run:
   - `pytest tests/ -v --cov=src --cov-report=term-missing`
   - `mypy src/`
   - `ruff check src/`
   - `ruff format --check src/`

## 12. Execution Hand-off
Next mandatory step is `writing-plans` to produce an implementation plan with bite-sized tasks, exact file-level edits, TDD checkpoints, and per-task verification gates before subagent-driven execution.
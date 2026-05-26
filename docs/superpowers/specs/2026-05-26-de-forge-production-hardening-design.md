# DE-Forge Production Hardening Design

Date: 2026-05-26
Status: Approved design for implementation planning
Architecture track: DE-Forge SOTA Core v2 production hardening

## 1. Goal

Harden the current DE-Forge SOTA Core v2 implementation from a verified MVP into a production-grade, fail-closed, evidence-graph controlled detection engineering system.

This design fixes the audited gaps without weakening the canonical SOTA path:

```text
raw report -> evidence graph -> verified DetectionSpec -> detection AST -> compiled Sigma -> validation/proof -> human review
```

The work follows a layered strategy:

1. Close dangerous bypasses and invariant gaps.
2. Harden schema, lineage, evidence graph, proof coverage, and retrieval/review integrity.
3. Wire production PDF, LLM, and controlled-agent capabilities after deterministic gates are solid.
4. Harden operations, performance, readiness, and operational documentation.

## 2. Non-goals

This design does not introduce:

- Multi-user, multi-tenant, SaaS, billing, or RBAC features.
- OCR for scanned or image-only PDFs.
- Direct raw-report-to-rule generation.
- Multiple provider/model fallback logic.
- Auto-deployment to SIEM without human approval.
- A full rewrite of the existing backend.

## 3. Design principles

### 3.1 Fail closed before expansion

The first layer closes routes and gates that could allow unproven artifacts into review or export. PDF, LLM, and agent improvements come only after export eligibility, proof coverage, and lineage gates are reliable.

### 3.2 Lineage is a gate, not decoration

Production export must not trust artifact existence alone. Export requires verified lineage across report, evidence, DetectionSpec, AST, compiler output, validation, proof obligations, and latest human review.

### 3.3 Required proof coverage is explicit

The system must verify that every required proof obligation exists in the correct run/rule scope and is resolved by policy. Absence of a failed proof is not enough.

### 3.4 Production API surface is clean

Dev/test seed helpers and non-authoritative legacy endpoints must not be mounted in production by default.

### 3.5 Schema supports invariants

Important SOTA invariants must be backed by persistence contracts, indexes, constraints, and schema guard checks where practical.

## 4. Phase 1: bypass and invariant gate hardening

Phase 1 closes the highest-risk paths first.

### 4.1 Seed route hardening

Current issue: public seed endpoints can create production-like report, evidence, DetectionSpec, rule, validation, and proof rows.

Design:

- Move seed endpoints out of the default production router.
- Add an explicit setting such as `enable_dev_seed_routes`, defaulting to `false`.
- Mount seed routes only when the environment is development/test and the flag is explicitly enabled.
- Production and staging must not expose seed endpoints.
- Tests may use fixtures or explicitly enabled dev routes, not production-mounted seed routes.

Acceptance tests:

- Production app returns 404 for `/v1/pipeline:seed` and `/v1/pipeline:seed-abstain`.
- Test/dev app can opt in when explicitly configured.
- Seeded or manual artifacts cannot satisfy production export gates unless they also satisfy compiler provenance, lineage, validation, proof, and review gates.

### 4.2 Export eligibility service

Create `ExportEligibilityService` as the single policy service used by Sigma export routes.

Input:

```text
run_id
rule_id
```

Checks, in fail-closed order:

1. Pipeline run exists.
2. Pipeline run maps to the requested rule.
3. Generated rule exists and has content.
4. DetectionSpec exists and is validated.
5. Rule has compiler provenance.
6. Evidence graph path is complete.
7. Artifact lineage is complete.
8. Required validation outcomes pass.
9. Required proof coverage is satisfied.
10. Latest human review decision for the run/rule is approved.
11. No newer rejection exists.

The service returns success or raises a structured blocking reason such as:

```text
PIPELINE_RUN_MISSING
RULE_MAPPING_MISMATCH
GENERATED_RULE_MISSING
DETECTION_SPEC_MISSING
COMPILER_PROVENANCE_MISSING
EVIDENCE_GRAPH_INCOMPLETE
ARTIFACT_LINEAGE_INCOMPLETE
VALIDATION_COVERAGE_MISSING
PROOF_COVERAGE_MISSING
HUMAN_APPROVAL_REQUIRED
LATEST_REVIEW_REJECTED
```

Export routes must remain thin and call this service before returning Sigma content.

### 4.3 Proof coverage policy

Create a proof coverage policy that verifies the required proof set for the selected rule.

Required proof obligations:

| Claim type | Required | Allowed `not_applicable` | Rule |
|---|---:|---:|---|
| `detects_report_behavior` | yes | no | Must be `proven`. |
| `not_overbroad` | yes | no | Must be `proven`. |
| `telemetry_fields_exist` | yes | no | Must be `proven`. |
| `positive_tests_pass` | yes | conditional | `not_applicable` only when dynamic tests are unavailable and explicitly justified. |
| `benign_baseline_not_matched` | yes | conditional | `not_applicable` only when benign baseline is unavailable and explicitly justified. |
| `citation_faithful` | yes | no | Must be `proven`. |
| `oracle_expectations_satisfied` | yes | yes | `not_applicable` only when no oracle case exists and explicitly justified. |
| `regression_safe` | yes | conditional | `not_applicable` only when no prior regression applies and explicitly justified. |

A proof row counts only when it matches the active `run_id`, `rule_candidate_id`, and required `claim_type`.

The gate blocks:

- Missing required claim type.
- Failed or unknown status.
- Unjustified `not_applicable`.
- `not_applicable` for claim types that do not allow it.
- Proof rows from another run or rule.
- Duplicate conflicting current rows.

### 4.4 Compiler provenance gate

Production Sigma export requires deterministic compiler provenance.

Design:

- Add generated rule provenance fields or equivalent persisted links:
  - `generation_source`
  - `detection_ast_id`
  - `compiled_sigma_id` or `compiler_run_id`
- Production export allows only `generation_source = 'compiler'`.
- A generated rule with only `rule_content` is insufficient.
- Existing generated rules without compiler provenance are treated as draft/manual/imported and cannot be production-exported.
- Orchestrator may reuse an existing rule only if compiler provenance is valid.

Preferred model:

- Add direct fields on `generated_rules` for efficient gates.
- Also persist artifact links and graph edges for full auditability.

Acceptance tests:

- Existing rule without compiler provenance is blocked before review/export.
- Compiler-generated rule with valid AST and compiled Sigma provenance passes this gate.
- Manual or seed source cannot be exported as production Sigma.

### 4.5 State machine hardening

The state machine must not encode a shortcut from DetectionSpec directly to review.

Target lifecycle:

```text
DETECTION_SPEC_READY
-> AST_READY
-> RULE_COMPILED
-> VALIDATION_READY
-> PROOF_READY
-> AWAITING_REVIEW
```

If adding all states at once is too disruptive, remove the direct shortcut and enforce equivalent intermediate gate predicates in services.

Acceptance tests:

- Direct `DETECTION_SPEC_READY -> AWAITING_REVIEW` fails.
- The full validated path can reach `AWAITING_REVIEW`.

## 5. Phase 2: schema, evidence graph, lineage, retrieval, and review hardening

Phase 2 converts auditability from soft JSON and scattered references into queryable, constrained persistence.

### 5.1 Evidence graph tables

Add `graph_nodes`:

```text
id: string primary key
run_id: string not null
node_type: string not null
ref_table: string nullable
ref_id: string nullable
payload_json: text not null default '{}'
created_at: string not null
```

Initial allowed node types:

```text
report
chunk
evidence_quote
behavior
attack_technique
detection_strategy
analytic
data_component
telemetry_source
telemetry_field
detection_spec
detection_ast
compiled_sigma
generated_rule
validation_result
proof_obligation
review_decision
feedback_pattern
regression_test
```

Add `graph_edges`:

```text
id: string primary key
run_id: string not null
source_node_id: string foreign key graph_nodes.id
target_node_id: string foreign key graph_nodes.id
edge_type: string not null
payload_json: text not null default '{}'
created_at: string not null
```

Allowed edge types:

```text
supports
mentions
maps_to
requires
implements
validated_by
derived_from
satisfies
failed_by
contradicts
```

Required constraints and indexes:

- Unique node by `(run_id, node_type, ref_table, ref_id)` when reference fields are present.
- Unique edge by `(run_id, source_node_id, target_node_id, edge_type)`.
- Indexes on `run_id`, `node_type`, `edge_type`, and reference fields.
- No self-edge.
- Edge source and target must belong to the same run, enforced by service-level validation if the database cannot express it portably.

Production graph path requirement:

```text
report -> chunk -> evidence_quote -> detection_spec -> detection_ast -> compiled_sigma -> generated_rule -> proof_obligation -> review_decision
```

### 5.2 Artifact links

Add `artifact_links`:

```text
id: string primary key
parent_artifact_id: string foreign key artifacts.id
child_artifact_id: string foreign key artifacts.id
link_type: string not null
created_at: string not null
```

Allowed link types:

```text
derived_from
compiled_from
validated_by
proven_by
reviewed_by
exported_from
```

Constraints:

- Parent and child cannot be identical.
- Unique `(parent_artifact_id, child_artifact_id, link_type)`.
- Service-level cycle prevention.

`artifacts.parent_artifact_ids` may remain temporarily for compatibility, but production gates must use `artifact_links`.

### 5.3 Detection AST and compiled Sigma persistence

Persist the compiler path explicitly.

Add or standardize `detection_ast_versions`:

```text
id
run_id
detection_spec_id
ast_json
ast_hash
created_at
```

Add or standardize `compiled_sigma_rules`:

```text
id
run_id
detection_ast_id
rule_id
compiler_version
sigma_yaml
sigma_hash
created_at
```

Extend `generated_rules`:

```text
generation_source
detection_ast_id
compiled_sigma_id
```

Production rule condition:

```text
generation_source == 'compiler'
AND detection_ast_id exists
AND compiled_sigma_id exists
AND compiled_sigma_rules.rule_id == generated_rules.id
```

### 5.4 Retrieval-to-evidence links

Add `evidence_retrieval_links`:

```text
id
run_id
evidence_id foreign key evidence_spans.id
retrieval_candidate_id foreign key retrieval_candidates.id
created_at
```

This prevents ambiguous mapping by `chunk_id` when multiple retrieval candidates reference the same chunk.

Gate behavior:

- Retrieval-derived evidence must link to the exact retrieval candidate.
- Deterministic/manual evidence must carry explicit source metadata and justification.
- Duplicate candidates for the same chunk must not be silently collapsed.

### 5.5 Review decision constraints

Harden `review_decisions`:

- `decision in ('approved', 'rejected')`.
- Non-empty reviewer.
- FK from `rule_id` to `generated_rules.id` remains required.
- Use FK or equivalent service validation for `run_id` against `pipeline_runs.run_id`.
- Keep append-only semantics.
- Remove dynamic SQL insert after the stable schema is available.

### 5.6 Proof obligation constraints

Harden `proof_obligations`:

- `claim_type` must be in known proof types.
- `status in ('proven', 'failed', 'unknown', 'not_applicable')`.
- Add index on `(run_id, rule_candidate_id, claim_type)`.
- Prefer one current row per `(run_id, rule_candidate_id, claim_type)`.

If multiple attempts are needed later, add versioning fields such as `attempt` and `is_current` instead of allowing ambiguous duplicate current rows.

### 5.7 Schema guard expansion

`SchemaGuard` must check SOTA-critical tables, columns, and indexes, not only `agent_runs`.

Critical tables include:

```text
reports
report_chunks
evidence_spans
graph_nodes
graph_edges
detection_specs
detection_ast_versions
generated_rules
compiled_sigma_rules
artifacts
artifact_links
proof_obligations
validation_results
review_decisions
pipeline_runs
agent_runs
retrieval_audit_runs
retrieval_candidates
evidence_retrieval_links
```

Readiness fails closed on missing critical tables or required columns/indexes.

## 6. Phase 3: PDF, LLM, and controlled-agent production wiring

Phase 3 adds production capability after deterministic gates are hardened.

### 6.1 Text-based PDF ingestion

Support text-based PDF threat reports only. OCR remains out of scope.

Add `PdfTextExtractionService` with responsibilities:

1. Validate uploaded file type.
2. Enforce file size and page count limits.
3. Reject encrypted, malformed, scanned, or image-only PDFs.
4. Extract text page by page.
5. Preserve page number and global character offset mapping.
6. Return normalized text plus extraction metadata.

Persist:

- `reports.source_type = 'pdf'`.
- Extracted text in `reports.raw_text`.
- Extraction metadata in `reports.metadata_json`.
- Chunk offsets that map back to extracted text.

Citation verification remains exact against extracted normalized text.

### 6.2 Single provider/model enforcement

Production uses one provider/model unless the user explicitly approves otherwise:

```text
provider: OpenAI-compatible
base URL: https://shopapikey.com/v1
API key env var: OPENAI_API_KEY
model: cx/gpt-5.5
```

Design:

- `settings.openai_model` is the single model source of truth.
- Per-request model overrides are rejected in production unless equal to the configured model.
- No fallback provider or model is added.
- Agent audit records the model actually used.

### 6.3 Concrete OpenAI-compatible transport

Add a concrete transport that uses configured base URL, API key, model, timeout, and JSON response format.

Tests must use a mocked transport and must not require live network access.

The transport must:

- Send the configured model.
- Use the configured base URL.
- Include authorization from `OPENAI_API_KEY`.
- Classify retryable and non-retryable errors.
- Respect bounded retry limits.

### 6.4 Citation-bearing agent outputs

Agent roles declare whether citations are required.

Citation-required agents include:

- Evidence Agent.
- Behavior Hypothesis Agent.
- ATT&CK Mapping Agent.
- Detection Strategy/Analytic Mapping Agent.
- Telemetry Grounding Agent.
- DetectionSpec Agent.
- Detection Logic Agent when producing claim-bearing logic.
- Ranking or review assistant when producing rationale claims.

Policy:

```text
if requires_citations and output is not abstain:
  citations must be non-empty
  citations must pass exact citation verification
```

Abstain output is allowed only with an explicit abstain reason.

Agent outputs remain subject to deterministic validators and cannot bypass gates.

## 7. Phase 4: operations, performance, readiness, and docs

### 7.1 Aggregate metrics

Replace unbounded object loading with aggregate SQL queries.

Quality metrics:

```text
proof_total
proof_proven
citation_total
citation_proven
validation_total
validation_passed
regression_total
regression_passed
```

Ops metrics:

```text
runs_total
runs_ok
runs_failed
runs_abstain
runs_in_progress
queue_depth
```

Existing metrics response semantics should remain stable unless tests specify a necessary change.

### 7.2 Health/readiness split

Keep `/health` lightweight for process and basic DB health.

Add `/ready` or equivalent readiness check for production safety:

```text
database ok
schema guard ok
critical policy services available
seed routes disabled in production
provider config valid in production
model policy valid
canonical SOTA policy flags present
```

Production readiness must be false if seed routes are enabled, schema is drifted, or required provider configuration is missing.

### 7.3 Legacy route cleanup

Remove, deprecate, or clearly mark non-authoritative legacy review behavior.

Rules:

- Non-persistent review decisions must never affect export.
- If retained, response must explicitly show `persisted: false`.
- Production docs must guide clients to authoritative review/export endpoints.

### 7.4 Operational documentation update

Update operational docs, not canonical architecture, with:

- Current hardening phase status.
- Verification commands and results.
- Remaining known gaps.
- Production-readiness checklist.

Canonical SOTA docs remain the target and are not weakened to match implementation state.

## 8. Migration strategy

Use non-destructive migrations first.

Order:

1. Add new tables and nullable columns.
2. Update services to write new lineage/provenance data.
3. Backfill existing test fixtures where appropriate.
4. Add gates that require the new data.
5. Tighten constraints after the new write path is stable.

Existing data classification:

- Compiler-produced artifacts may be backfilled with compiler provenance when evidence is available.
- Seed/manual/imported artifacts must be marked non-production by `generation_source` and blocked by export gates.

Do not delete compatibility fields such as `parent_artifact_ids` until all gates and services use relational lineage.

## 9. Testing strategy

Every implementation task follows RED-GREEN-REFACTOR.

### 9.1 Phase 1 tests

- Seed routes are disabled in production.
- Export blocks missing required proof.
- Export blocks wrong-scope proof.
- Export blocks rule without compiler provenance.
- State machine rejects DetectionSpec-to-review shortcut.
- Latest rejection still blocks export.

### 9.2 Phase 2 tests

- Graph nodes and edges persist for the pipeline.
- Export blocks missing evidence graph path.
- Artifact links enforce rule ancestry.
- Retrieval lineage rejects chunk-candidate ambiguity.
- Review decision constraints reject invalid decision values.
- Schema guard checks critical SOTA tables.

### 9.3 Phase 3 tests

- Text-based PDF ingests with offsets.
- Scanned, malformed, or encrypted PDF fails closed.
- Model override is rejected in production.
- OpenAI-compatible transport builds the expected request payload.
- Citation-required agent output rejects empty citations.
- Abstain agent output requires an abstain reason.

### 9.4 Phase 4 tests

- Metrics summaries remain truthful using aggregate queries.
- Readiness fails when seed routes are enabled in production.
- Readiness fails without provider configuration in production.
- Legacy non-authoritative review cannot affect export.
- Operational docs pass preflight.

## 10. Final production acceptance gate

The project is production-ready only when a final E2E proves:

```text
TXT or text-based PDF report
-> ingestion and offset-preserving chunking
-> retrieval-backed evidence
-> evidence graph
-> verified DetectionSpec
-> Detection AST
-> compiled Sigma
-> validation
-> full proof coverage
-> graph and artifact lineage complete
-> latest human approval
-> Sigma export
```

Adversarial E2E must prove export is blocked for:

- Seed/manual rule.
- Missing required proof.
- Wrong-scope proof.
- Missing compiler provenance.
- Missing graph edge.
- Missing artifact lineage.
- Latest rejection.
- PDF citation mismatch.
- Production model override.

## 11. Implementation phase order

Implement in this order:

1. Phase 1A: disable production seed routes and clean bypass surfaces.
2. Phase 1B: add proof coverage policy and export integration.
3. Phase 1C: add compiler provenance gates.
4. Phase 1D: harden state machine transitions.
5. Phase 2A: add evidence graph core.
6. Phase 2B: add artifact links and lineage integrity service.
7. Phase 2C: add retrieval links, review constraints, and schema guard expansion.
8. Phase 3A: add text-based PDF extraction.
9. Phase 3B: add concrete LLM transport and model policy enforcement.
10. Phase 3C: enforce citation-bearing agent outputs.
11. Phase 4A: aggregate metrics and readiness checks.
12. Phase 4B: legacy cleanup, docs update, and final verification.

This order keeps every step reviewable and ensures the most dangerous invariant gaps are closed before adding new production capabilities.

# DE-Forge Runtime Product Path Design

Date: 2026-05-22
Status: Approved for implementation planning
Architecture name: Audit-First Runtime Upload Product Path

## Goal

Turn the completed production-hardening vertical slice from an internal/test-driven pipeline into a real single-user runtime product path exposed through upload API, full persistence/audit, mandatory human review, strict export gates, and operational hardening.

The target runtime path is:

```text
multipart TXT/PDF upload
  -> upload boundary validation
  -> real TXT/text-PDF ingestion
  -> persisted run + report artifact
  -> deterministic chunking + chunk artifacts
  -> live OpenAI-compatible LLM agents with bounded transient retry
  -> agent run audit records
  -> verified evidence graph
  -> verified DetectionSpec
  -> Detection AST
  -> compiled Sigma candidate
  -> static validation + proof obligations
  -> quality snapshot
  -> awaiting human review
  -> approved review decision
  -> export gate
  -> export artifact
```

This is not a replacement architecture. It upgrades the existing SOTA Core v2 services into a production runtime path while preserving the DE-Forge invariants.

## Non-negotiable constraints

- Product runtime input is `POST /api/reports` with multipart TXT/PDF upload.
- Runtime must not expose or use a raw-report-to-rule production path.
- Runtime must not use fake LLM clients.
- Runtime must not fallback to state-only orchestration.
- Runtime must not fallback to another model or provider.
- Runtime uses one configured OpenAI-compatible model/provider:
  - base URL: `https://shopapikey.com/v1`,
  - API key env var: `OPENAI_API_KEY`,
  - model: `cx/gpt-5.5`.
- Bounded retry is allowed only for transient transport failures, with a maximum of two retries. Retry never changes model/provider and never masks deterministic gate failures.
- Invalid JSON, schema mismatch, citation mismatch, DetectionSpec verification failure, static validation failure, missing proof, and export gate failure are hard failures.
- Human review remains mandatory before export.
- Export is a separate boundary from orchestration.
- Deferred items remain out of scope: OCR scanned PDF, multi-user/auth/RBAC, multi-model/provider fallback, automatic SIEM deployment, CTI-REALM benchmark adapter, separate frontend framework, and advanced interactive graph visualization.

## Current state summary

The codebase already has the main primitives needed for this upgrade:

- `IngestionService` for TXT and text-PDF extraction.
- `chunk_text` for deterministic chunking.
- `ArtifactStore` and `Artifact` model for structured lineage artifacts.
- `AgentAuditService` and `AgentRun` model for LLM call audit.
- `EvidenceGraphService`, `GraphBuilder`, graph nodes, and graph edges.
- `LlmClient` for OpenAI-compatible JSON responses.
- `DetectionSpecVerifier`, `DetectionAstService`, `SigmaCompiler`, `StaticValidationService`, and `ProofObligationService`.
- `RunRepository` for runs, quality snapshots, and review decisions.
- Basic API/UI routes and dashboard history backed by persistence when present.

The remaining gap is that runtime API still does not execute the full product path. `/api/runs/golden` accepts raw report text and can call compatibility state-only orchestration. The completed vertical slice proves the pipeline internally, but product runtime must move to upload-first orchestration with mandatory live LLM and complete audit/export gates.

## Architecture

### 1. Upload API boundary

Add `POST /api/reports` as the product entrypoint.

Request:

- `multipart/form-data`
- file field: `file`
- optional field: `mode`, default `auto`, values from `RunMode`

Allowed uploads:

- `.txt` with `text/plain`
- `.pdf` with `application/pdf`

Boundary behavior:

- Reject missing filename.
- Reject unsupported extension/content type combinations.
- Reject empty uploads.
- Enforce a local maximum upload size from settings.
- Do not log raw report content or secrets.
- Pass file bytes to `IngestionService.ingest_bytes()`.

Response on accepted run:

- `run_id`
- `report_id`
- `state`
- `mode`
- high-level artifact ids for report, chunks, candidate, quality snapshot when available
- failure reason when the run ends in `failed`

The first implementation may run synchronously because this project is single-user local runtime. Queue/worker infrastructure is out of scope for this step.

### 2. Product orchestrator method

Add a product-only orchestrator method that requires live dependencies:

```python
run_product_path(
    ingested_report: IngestedReport,
    mode: RunMode,
) -> RunSummary
```

The method must require:

- a real SQLAlchemy `Session`,
- a real `LlmClient`,
- no fake client unless explicitly injected by tests,
- no state-only fallback.

If either session or LLM client is missing, this method raises a domain error. Compatibility methods may remain for old tests, but product API must not call them.

### 3. Transaction and state handling

The product path should be audit-first and stage-aware:

1. Create run in `created`.
2. Persist report artifact.
3. Transition to `ingested`.
4. Chunk text and persist chunk artifacts.
5. Run Evidence Agent.
6. Persist Evidence Agent audit record.
7. Verify citations and build evidence graph.
8. Persist evidence graph artifact or graph build summary artifact.
9. Transition to `evidence_ready`.
10. Run ATT&CK Mapping Agent.
11. Persist ATT&CK Mapping Agent audit record.
12. Run DetectionSpec Agent.
13. Persist DetectionSpec Agent audit record.
14. Persist unverified DetectionSpec artifact.
15. Verify DetectionSpec.
16. Persist verified DetectionSpec artifact.
17. Transition to `detection_spec_verified`.
18. In cautious mode, stop here with committed audit state.
19. Build Detection AST and persist AST artifact.
20. Compile Sigma and persist rule candidate artifact.
21. Transition to `rule_candidates_ready`.
22. Run static validation and persist validation artifact.
23. Generate proof obligations and persist each proof obligation artifact.
24. Verify candidate selectability.
25. Transition to `validated`.
26. Persist quality snapshot.
27. Transition to `awaiting_review`.
28. Commit transaction and return summary.

On hard failure:

- catch domain errors at the product service/API boundary,
- update run state to `failed` when a run exists,
- store a concise `failure_reason` including stage name,
- commit failure state and audit records created before failure,
- return a structured API error or failed run summary depending on where failure occurred.

The system must not transition to `awaiting_review` if any required deterministic gate fails.

### 4. Artifact persistence model

Use existing `ArtifactStore` for all stage outputs rather than creating parallel audit tables.

Required artifact kinds using existing `ArtifactKind` where possible:

- `REPORT`: ingested report metadata and normalized text hash.
- `CHUNK`: each deterministic text chunk with offsets.
- `EVIDENCE_GRAPH`: graph build summary, node ids, edge ids, verified evidence ids.
- `DETECTION_SPEC`: unverified and verified DetectionSpec snapshots distinguished by `stage`.
- `RULE_CANDIDATE`: compiled Sigma candidate and candidate score.
- `VALIDATION_RESULT`: static validation result and export gate result.
- `PROOF_OBLIGATION`: each generated proof obligation with status and justification.

If AST and export artifacts need distinct kinds, extend `ArtifactKind` with:

- `DETECTION_AST`
- `EXPORT`

Every artifact must include:

- `run_id`,
- `kind`,
- `stage`,
- `payload`,
- `input_hash`,
- `output_hash`,
- `parent_artifact_ids`,
- `created_by`.

Parent links must preserve lineage from report -> chunks -> evidence graph -> DetectionSpec -> AST -> Sigma candidate -> validation/proof -> export.

### 5. Agent audit

Every runtime agent call must be persisted with `AgentAuditService`:

- evidence extraction,
- ATT&CK mapping,
- DetectionSpec construction.

The audit record must include:

- agent name,
- model,
- prompt version,
- input hash,
- output hash,
- token counts,
- latency,
- terminal status.

Agent output artifacts should reference the agent run indirectly through payload fields or parent artifacts. Raw secrets and API keys must never be persisted.

### 6. LLM bounded retry

Update `LlmClient` to support bounded retry for transient transport failures:

- maximum two retries after the first attempt,
- short deterministic backoff suitable for local runtime,
- only applies to transient transport exceptions from the OpenAI-compatible client,
- does not apply to invalid JSON,
- does not apply to schema/domain validation errors,
- does not change model/provider/base URL,
- records final latency across attempts.

If all attempts fail, raise `ValidationGateError("LLM transport failed")` or a stage-specific wrapped error. The orchestrator must mark the run failed.

### 7. Review API persistence and state transition

Upgrade `POST /api/review` from in-memory service behavior to product runtime behavior.

Request stays based on `ReviewRequest`:

- `run_id`
- `rule_candidate_id`
- `action`
- `reviewer_notes`

Runtime behavior:

- Open DB session.
- Load run.
- Require state `awaiting_review`.
- Persist review decision through `RunRepository`.
- If action is `approve`, transition run to `approved`.
- If action is `reject`, transition run to `rejected`.
- If action is `edit` or `abstain`, do not export; use existing state behavior or explicit failure/abstain policy in the implementation plan.
- Return persisted review decision.

Review approval does not export anything. It only enables export gate eligibility.

### 8. Export gate API

Add `POST /api/exports/{run_id}` as the only product export boundary.

Export gate checks:

1. Run exists.
2. Run state is `approved`.
3. Latest review decision for run has `action == "approve"` and `export_allowed == True`.
4. Latest rule candidate artifact exists.
5. Latest static validation artifact proves the candidate passed.
6. Required proof obligation artifacts exist and are all `proven` or `not_applicable` with justification.
7. Verified DetectionSpec artifact exists.
8. Candidate lineage links back to verified DetectionSpec and evidence graph artifacts.
9. Sigma YAML comes from compiled candidate artifact, not raw LLM output.

If any check fails, return a hard error and do not create an export artifact.

On success:

- create `EXPORT` artifact containing Sigma YAML and metadata,
- include parent candidate/proof/review artifact ids,
- return export id, run id, candidate id, and Sigma YAML.

This endpoint does not deploy to SIEM and does not write external files unless a later explicitly approved plan adds local file export.

### 9. Operational hardening

Add production-grade local safeguards without adding auth/RBAC:

- Upload size limit setting.
- Clear API errors for unsupported file type, empty report, missing API key, LLM transport failure, and gate failures.
- Stage-specific failure reasons on run records.
- No raw report text in logs.
- No API key or secret logging.
- Deterministic database initialization policy for local runtime.
- Health endpoint remains lightweight and must not call LLM.
- Tests must not call live network.

### 10. UI/dashboard follow-up

Server-rendered UI remains acceptable for this phase.

Enhance existing pages only enough to reflect product runtime state:

- dashboard lists persisted runs and latest states,
- review page can display persisted candidate/spec/evidence/proof data for a run,
- evidence graph page can render persisted node/edge summaries,
- export status appears only after export gate succeeds.

Do not introduce a frontend framework or advanced interactive graph visualization in this plan.

## Error handling policy

Use domain errors for deterministic failures and map them to API responses consistently.

Pre-run failures:

- unsupported upload,
- empty upload,
- ingestion failure before run creation.

These can return HTTP 4xx without a run record when no run exists yet.

Run-stage failures:

- missing API key,
- LLM transport failure after retries,
- invalid LLM JSON,
- citation mismatch,
- DetectionSpec failure,
- static validation failure,
- proof obligation failure.

These must update the run to `failed` with a stage-specific `failure_reason` when the run already exists.

Export failures:

- not approved,
- missing approval decision,
- missing candidate,
- missing proofs,
- failed validation,
- incomplete lineage.

These must not alter validated artifacts or create export artifacts.

## Testing strategy

Use TDD for every implementation task.

Required tests:

1. Upload API rejects unsupported file type.
2. Upload API rejects empty TXT/PDF extraction.
3. Upload API accepts TXT multipart and runs product path with fake dependency override in tests.
4. Upload API creates persisted run, report artifact, chunk artifacts, quality snapshot, and state `awaiting_review`.
5. Product API does not call state-only orchestrator fallback.
6. Product orchestrator requires session and LLM client.
7. Product orchestrator persists agent audit records.
8. Product orchestrator persists report/chunk/spec/candidate/validation/proof artifacts with parent lineage.
9. LLM client retries transient transport failures no more than two times and does not change model/provider.
10. LLM client does not retry malformed JSON as if it were transient transport.
11. Runtime review API persists decision and transitions run to `approved` or `rejected`.
12. Export API rejects run before approval.
13. Export API rejects approved run when proof obligations are missing or not proven.
14. Export API creates export artifact only when approval, validation, proof, and lineage checks pass.
15. Full API/UI tests continue to pass.
16. Full `pytest`, `mypy`, `ruff check`, and `ruff format --check` pass.

Automated tests may use dependency overrides or deterministic fake LLM only inside tests. Product runtime defaults must instantiate live `LlmClient` and fail if configuration is missing.

## Implementation sequencing

Recommended implementation order:

1. Add runtime upload schemas/settings and upload API red tests.
2. Add product run service that creates run and persists ingestion/chunk artifacts.
3. Add product orchestrator method that requires DB session and LLM client.
4. Add agent audit persistence into product orchestrator.
5. Add artifact lineage persistence for spec, AST, candidate, validation, proof, and quality.
6. Add bounded LLM retry.
7. Upgrade review route to use DB-backed service and state transitions.
8. Add export gate service and API route.
9. Add UI/dashboard runtime data visibility.
10. Run final verification and code review gates.

## Acceptance criteria

The work is complete only when:

- `POST /api/reports` is the product entrypoint for TXT/PDF reports.
- Product API uses real ingestion and live LLM configuration by default.
- Runtime has no model/provider/fake/state-only fallback.
- Every trusted stage output is persisted as artifact, graph record, agent audit record, run state, quality snapshot, review decision, or export artifact.
- Runs that fail gates are marked `failed` with clear failure reasons.
- Successful auto runs end at `awaiting_review`, not exported.
- Review approval is persisted and transitions run state.
- Export endpoint refuses unapproved or insufficiently proven candidates.
- Export endpoint creates an export artifact only after all gates pass.
- Tests do not call live network.
- Full verification gates pass.

## Self-review

Placeholder scan: no TBD/TODO placeholders remain.

Internal consistency: upload API is the only product entrypoint; orchestration reaches review, export is separate; review approval enables export but does not export.

Scope check: this remains one coherent runtime product-path upgrade. Deferred advanced systems remain out of scope.

Ambiguity check: bounded retry is explicitly limited to transient transport failures and maximum two retries; no model/provider fallback is allowed.

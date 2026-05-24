# DE-Forge Production-Hardening Vertical Slice Design

Date: 2026-05-22
Status: Approved for implementation planning
Architecture name: Production-Hardening Golden Path Vertical Slice

## Goal

Turn the current SOTA Core v2 skeleton and deterministic contracts into a real golden-path pipeline that can process an English TXT or text-based PDF report through ingestion, evidence grounding, controlled LLM analysis, DetectionSpec verification, deterministic Sigma compilation, validation, proof gating, persistence-backed review, and dashboard visibility.

The target vertical slice is:

```text
TXT/text-PDF report
  -> report ingestion
  -> deterministic chunking
  -> exact citation verification
  -> evidence graph persistence
  -> controlled LLM agents through OpenAI-compatible transport
  -> verified DetectionSpec
  -> Detection AST
  -> compiled Sigma
  -> rule candidate portfolio
  -> static/proof validation
  -> persisted review and quality dashboard state
  -> mandatory human review
```

This work is production-hardening, not a new architecture. It connects and strengthens the existing SOTA Core v2 services while preserving all non-negotiable invariants.

## Scope

Implement the first real product-mode golden path for the encoded PowerShell report scenario and the same class of English TXT/text-PDF reports.

In scope:

- TXT report ingestion.
- Text-based PDF ingestion with `pypdf`.
- Explicit abstain/failure for scanned or text-empty PDFs; OCR remains deferred.
- Deterministic report metadata and content hash generation.
- Chunking through the existing `chunk_text` service.
- Exact citation verification before evidence graph nodes become trusted.
- Evidence graph nodes and edges backed by persisted run data.
- Real OpenAI-compatible LLM transport using the existing settings:
  - base URL: `https://shopapikey.com/v1`,
  - API key env var: `OPENAI_API_KEY`,
  - model: `cx/gpt-5.5`.
- No alternate model/provider fallback.
- Deterministic fake LLM client for tests; tests must not call live network endpoints.
- End-to-end orchestrator integration for the golden path.
- DetectionSpec parsing and verification before AST or Sigma generation.
- Detection AST and Sigma compiler as the only production rule path.
- Static validation and proof obligation gating before review.
- Persistence-backed quality snapshots and review decisions.
- Basic server-rendered UI pages that read real persisted run/dashboard data when available.

Out of scope for this vertical slice:

- OCR for scanned or image-only PDFs.
- Multi-user, authentication, authorization, RBAC, organizations, or tenancy.
- A separate frontend framework.
- Full advanced interactive graph visualization with drag/zoom/filter graph libraries.
- Multi-model ensembles, provider fallback, or fallback model routing.
- Automatic SIEM deployment or export without human approval.
- CTI-REALM or other benchmark adapters.

A basic evidence graph view remains in scope when it uses real persisted nodes/edges. A full advanced interactive graph UI is intentionally deferred until the pipeline produces stable graph data.

## Existing system boundaries

The current implementation already provides core building blocks:

- `chunk_text` for deterministic text chunking.
- `CitationVerifier` for exact quote/span checks.
- `EvidenceGraphService` and graph SQLAlchemy models for nodes and edges.
- `BaseAgent` and specialized agent classes using `LlmClient` contracts.
- `DetectionSpecVerifier` enforcing evidence, telemetry, and logic gates.
- `DetectionAstService` requiring verified DetectionSpecs.
- `SigmaCompiler` and `SigmaValidator` for deterministic Sigma generation and validation.
- `PortfolioService`, `StaticValidationService`, and `ProofObligationService`.
- FastAPI run/review/metrics/UI routes.

The hardening work should extend these boundaries rather than replace them. API routes remain thin; orchestration and business logic stay in services.

## Architecture

### Report ingestion

Add a focused ingestion service that accepts either raw text or file bytes plus filename/content type and returns an ingested report contract. The service extracts text, computes deterministic content hashes, identifies source type, and rejects unsupported or empty inputs with domain errors.

TXT ingestion decodes UTF-8 text. Text PDF ingestion extracts text with `pypdf`. If PDF extraction yields no meaningful text, the pipeline must stop with an explicit unsupported/OCR-deferred result rather than fabricating evidence.

### LLM transport

Replace the intentional `LlmClient.complete_json()` stub with a real OpenAI-compatible JSON transport. It uses the existing settings object and sends one model only: `cx/gpt-5.5`.

The transport must:

- require `OPENAI_API_KEY` for live use,
- call the configured OpenAI-compatible base URL,
- request JSON output,
- parse response content into `dict[str, Any]`,
- report token counts, latency, and optional cost,
- raise a domain error for malformed JSON, missing API key, or transport failure.

Tests use a deterministic fake client or mocked transport. Unit and integration gates do not depend on live network availability or real secrets.

### Agent outputs and deterministic gates

Agents may suggest evidence, mappings, DetectionSpec fields, and critique results, but deterministic services decide whether outputs are trusted.

The Evidence Agent output must pass exact citation verification against the chunks before evidence graph trusted nodes are created. DetectionSpec Agent output must parse into `DetectionSpec` and pass `DetectionSpecVerifier` before AST generation. Sigma YAML must come from `DetectionAstService` and `SigmaCompiler`, not directly from raw report text or free-form LLM output.

### Orchestrator integration

Upgrade the orchestrator from state-only transitions to a real coordinator. The orchestrator owns the golden path flow:

1. ingest report,
2. persist or record report/chunk artifacts,
3. chunk text,
4. run evidence extraction,
5. verify citations,
6. create evidence graph nodes/edges,
7. run ATT&CK mapping and DetectionSpec construction,
8. verify DetectionSpec,
9. create Detection AST,
10. compile Sigma,
11. create rule candidate,
12. run static validation,
13. generate and satisfy deterministic proof obligations where evidence is available,
14. persist quality snapshot,
15. transition to `awaiting_review` only after required gates pass.

Cautious mode pauses after DetectionSpec verification or at the first uncertainty gate that requires human review. Auto mode runs to the final human review gate but never bypasses proof, validation, or review requirements.

### Persistence-backed dashboard and review

Quality history should move from deterministic sample data to persisted snapshots. Review decisions should be stored so the dashboard and review UI can show real run state.

The existing sample UI can remain as an empty-state fallback, but real persisted run data takes precedence. The basic evidence graph page should render persisted graph nodes/edges for a run when available. Advanced interactive graph visualization remains deferred.

## Data flow

```text
ReportInput
  -> IngestionService
  -> IngestedReport
  -> chunk_text
  -> TextChunk[]
  -> EvidenceAgent via LlmClient
  -> CitationVerifier
  -> EvidenceGraphService
  -> AttackMappingAgent / DetectionSpecAgent via LlmClient
  -> DetectionSpecVerifier
  -> DetectionAstService
  -> SigmaCompiler
  -> PortfolioService
  -> StaticValidationService
  -> ProofObligationService
  -> QualitySnapshot persistence
  -> ReviewService persistence
  -> API/UI
```

Every stage emits structured contracts. Each boundary either returns verified data or fails/abstains explicitly.

## Error handling and abstention

Hard failures:

- unsupported file type,
- empty TXT/PDF text,
- text-empty PDF where OCR would be required,
- citation mismatch,
- malformed LLM JSON,
- DetectionSpec verification failure,
- AST/Sigma compilation failure,
- static validation failure for final candidate,
- failed or unknown required proof obligation before selection.

The orchestrator must not convert hard failures into successful review states. It may return `failed` or `abstained` with a clear reason, depending on whether the failure is technical or evidence/telemetry insufficiency.

## Testing strategy

Use TDD for every implementation task.

Required test categories:

- TXT ingestion tests.
- Text PDF ingestion tests using a small generated or fixture PDF.
- Empty/scanned-like PDF rejection tests.
- LLM transport request/response parsing tests with mocked client behavior.
- Missing API key and malformed JSON tests.
- Citation verification integration tests from chunks to graph nodes.
- Orchestrator golden-path test using deterministic fake LLM outputs.
- Cautious-mode pause tests.
- DetectionSpec-to-Sigma end-to-end assertions proving no raw-report-to-rule path.
- Persistence-backed quality history and review decision tests.
- UI/API tests showing real persisted run data appears in review/dashboard pages.

Verification commands:

```bash
python -m pytest tests/ -q
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
```

Manual smoke testing should load the server-rendered review, evidence graph, and dashboard pages after a fake-LLM golden run has created persisted data.

## Security and safety

- Do not log API keys or raw secrets.
- Do not commit `.env` files or real credentials.
- Do not add provider/model fallback logic.
- Do not publish, push, deploy, or call external live services during automated tests.
- Keep live LLM use opt-in through runtime configuration and environment variables.
- Preserve human review as mandatory before export.

## Invariants preserved

1. No raw-report-to-production-rule path exists.
2. DetectionSpec is mandatory before rule generation.
3. Evidence citations are exact and verified.
4. ATT&CK modeling remains Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field.
5. Required proof obligations must be proven before final candidate selection.
6. Detection AST and compiler remain the source for Sigma YAML.
7. Human review remains mandatory before export.
8. Agent/refinement loops remain bounded.
9. Feedback creates regression protection.
10. Full artifact lineage and auditability are preserved.

## Success criteria

The vertical slice is successful when:

- A TXT report can run through the full golden path to `awaiting_review` using deterministic fake LLM outputs in tests.
- A text-based PDF report can be ingested and chunked with verified text extraction.
- Empty/scanned-like PDFs fail or abstain explicitly without fabricated evidence.
- Live LLM transport is implemented behind the existing OpenAI-compatible settings and can be tested without real network calls.
- The orchestrator proves DetectionSpec-first and compiler-first rule generation through tests.
- Quality history and review decisions are persisted and visible through API/UI routes.
- Full pytest, mypy, Ruff lint, and Ruff format gates pass.

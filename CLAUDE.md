# Project Guidelines for Claude Code

## Project Identity
Project name: DE-Forge

Full name: Evidence-Grounded AI-assisted Detection Rule Generation from Threat Reports

DE-Forge is a security engineering system that reads unstructured cyber threat intelligence reports and generates evidence-grounded detection artifacts through a controlled multi-agent pipeline.

Core pipeline:
Threat report → evidence extraction → ATT&CK mapping → telemetry discovery → DetectionSpec → Sigma/KQL generation → validation → testing → human review

## Core Principle
The system must never generate production detection rules directly from raw report text.

DetectionSpec is the mandatory intermediate representation and must contain:
- evidence quotes
- ATT&CK mapping
- required telemetry and allowed fields
- detection logic
- false-positive hypotheses
- test plan
- abstain reason when generation is unsafe

## MVP Scope
MVP must support:
- report ingestion (TXT/PDF)
- evidence extraction
- ATT&CK mapping
- DetectionSpec generation
- Sigma rule generation
- static validation
- basic synthetic log testing
- human review

Initial detection target:
- Sigma as primary format
- Windows Sysmon Event ID 1 (process_creation)
- ATT&CK: T1059.001, T1059.003, T1105

## Non-goals for MVP
- No auto-deploy to production SIEM.
- No claim to replace detection engineers.
- No full OpenCTI/MISP integration.
- No full enterprise multi-tenant auth.

## Agentic Deep-Analysis Phase
Agentic upgrade scope must enforce:
- LLM-backed agents replace service stubs for evidence, ATT&CK mapping, DetectionSpec synthesis, and rule authoring/refinement.
- Retrieval grounding is mandatory for evidence extraction and downstream claims.
- Profile-driven KPI gates must be enforced for `strict`, `balanced`, and `exploratory` modes.
- Baseline delta requirement must pass against MVP benchmark before rollout.

## Mandatory Architecture Rules
1. DetectionSpec is mandatory before rule generation.
2. Controlled multi-agent orchestration only (no free-form debate).
3. Deterministic validators are mandatory.
4. Bounded refinement loops only.
5. Abstain policy is mandatory.
6. Human review gate is mandatory before export.
7. Citation faithfulness = 100% is a hard gate.
8. Retrieval-grounded evidence extraction is mandatory.
9. No hallucinated claims are allowed in any agent output.
10. No raw-report-to-rule bypass path is allowed.
11. No schema-invalid output may advance stage state.
12. MVP contract guarantees are immutable during upgrade.

## Quality Gates
All profile runs must meet thresholds defined in `docs/implementation/kpi-threshold-matrix.md`:
- Evidence extraction quality thresholds (recall/precision)
- ATT&CK mapping accuracy thresholds
- Rule quality thresholds (precision/recall/F1)
- Abstain quality thresholds (precision/coverage)
- Cost and latency budget thresholds

Failure to meet any hard threshold blocks progression or rollout.

## Baseline Delta Requirement
Before enabling agentic upgrade in rollout path, benchmark results must satisfy the baseline delta policy in:
- `docs/implementation/evaluation-protocol-agentic-deep-analysis.md`
- `docs/benchmark/eval-dataset-manifest.md`

If baseline delta gates fail, rollout is blocked.

## Loop Limits
- max_static_refinement_iterations = 3
- max_dynamic_refinement_iterations = 2

## Model and Provider Configuration
Use one provider/model for all agent roles.

- Provider type: OpenAI-compatible
- Base URL: `https://shopapikey.com/v1`
- API key env var: `OPENAI_API_KEY`
- Model (all roles): `cx/gpt-5.5`

Do not add fallback model logic unless explicitly requested by user.

## Retrieval and Grounding Guarantees
- Every major claim must cite retrieved chunk IDs.
- Evidence quotes must map to valid source offsets.
- Citation mismatch is a hard validation failure.
- Retrieval faithfulness is required before DetectionSpec and rule stages.

## Tech Stack
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- SQLite for local default runtime
- PostgreSQL-compatible schema design for future migration
- pytest + httpx
- ruff + mypy
- uv package manager

## Persistence and Traceability
All important outputs must be persisted with lineage:
- report_id
- chunk_id / evidence_id
- detection_spec_id
- rule_id
- run_id / trace_id / agent_run_id

Generated rules are immutable; edits create new versions.

## Validation Requirements
Validation must include deterministic checks for:
- schema validity
- evidence integrity
- ATT&CK ID validity
- telemetry field validity
- broad-rule detection
- Sigma syntax/structure validity
- retrieval faithfulness
- citation/offset integrity

## Superpowers Workflow (Mandatory)
1. Brainstorming → approved design in `docs/superpowers/specs/`
2. Writing plans → detailed tasks in `docs/superpowers/plans/`
3. Subagent-driven-development with reviews
4. Finishing branch workflow

Never skip brainstorming, even for small tasks.

## Coding Standards
### Structure
```
src/
├── api/
├── models/
├── schemas/
├── services/
└── utils/
```

### Style
- PEP 8
- Type hints required for all functions
- Public function docstrings (Google style)
- Max function length: 50 lines
- Max file length: 500 lines

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Testing Requirements
- Coverage minimum: 80%
- Unit + Integration + E2E tests
- Mirror `src/` structure in `tests/`

## Verification Commands
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
mypy src/
ruff check src/
ruff format --check src/
pytest tests/benchmark/test_baseline_delta.py -v
pytest tests/e2e/test_agentic_pipeline_profiles.py -v
pytest && mypy src/ && ruff check src/
```

## Anti-Patterns (Never Do)
- Business logic inside API endpoints
- Direct DB access inside endpoints
- Mutable default arguments
- Bare `except:` clauses
- Magic numbers without constants
- God classes/functions

## Build Priority
1. Product-mode robustness and correctness
2. Benchmark-mode compatibility
3. Benchmark score optimization

## Blocking and Abstain Conditions
Fail-fast when:
- empty/invalid extraction
- impossible schema contract violations
- persistent storage failures
- retry limits exhausted
- retrieval faithfulness gate fails
- citation integrity checks fail

Abstain when:
- no evidence-backed behavior
- no telemetry support
- only CVE mention without observables
- only tool/malware name without behavior
- rule remains overbroad after bounded refinement

## Documentation Map
- Architecture contracts: `docs/architecture/`
- Schemas/contracts: `docs/schemas/`
- Implementation policy: `docs/implementation/`
- Prompt pack: `docs/prompts/`
- Benchmark adapter: `docs/benchmark/`
- KPI thresholds: `docs/implementation/kpi-threshold-matrix.md`
- Evaluation protocol: `docs/implementation/evaluation-protocol-agentic-deep-analysis.md`
- Traceability matrix: `docs/implementation/module-traceability-matrix.md`
- Upgrade precedence: `docs/architecture/agentic-upgrade-precedence.md`

## Operating Rule
When uncertain, stop and ask for clarification instead of guessing.
When implementing agentic upgrade, follow upgrade precedence rules strictly. MVP contract guarantees are immutable.

Detection quality priority: correctness and traceability first.
Quality, grounding, and gate compliance take priority over speed.
## Loop Limits
- max_static_refinement_iterations = 3
- max_dynamic_refinement_iterations = 2

## Model and Provider Configuration
Use one provider/model for all agent roles.

- Provider type: OpenAI-compatible
- Base URL: `https://shopapikey.com/v1`
- API key env var: `OPENAI_API_KEY`
- Model (all roles): `cx/gpt-5.5`

Do not add fallback model logic unless explicitly requested by user.

## Tech Stack
- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- SQLite for local default runtime
- PostgreSQL-compatible schema design for future migration
- pytest + httpx
- ruff + mypy
- uv package manager

## Persistence and Traceability
All important outputs must be persisted with lineage:
- report_id
- chunk_id / evidence_id
- detection_spec_id
- rule_id
- run_id / trace_id / agent_run_id

Generated rules are immutable; edits create new versions.

## Validation Requirements
Validation must include deterministic checks for:
- schema validity
- evidence integrity
- ATT&CK ID validity
- telemetry field validity
- broad-rule detection
- Sigma syntax/structure validity

## Superpowers Workflow (Mandatory)
1. Brainstorming → approved design in `docs/superpowers/specs/`
2. Writing plans → detailed tasks in `docs/superpowers/plans/`
3. Subagent-driven-development with reviews
4. Finishing branch workflow

Never skip brainstorming, even for small tasks.

## Coding Standards
### Structure
```
src/
├── api/
├── models/
├── schemas/
├── services/
└── utils/
```

### Style
- PEP 8
- Type hints required for all functions
- Public function docstrings (Google style)
- Max function length: 50 lines
- Max file length: 500 lines

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Testing Requirements
- Coverage minimum: 80%
- Unit + Integration + E2E tests
- Mirror `src/` structure in `tests/`

## Verification Commands
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
mypy src/
ruff check src/
ruff format --check src/
pytest && mypy src/ && ruff check src/
```

## Anti-Patterns (Never Do)
- Business logic inside API endpoints
- Direct DB access inside endpoints
- Mutable default arguments
- Bare `except:` clauses
- Magic numbers without constants
- God classes/functions

## Build Priority
1. Product-mode robustness and correctness
2. Benchmark-mode compatibility
3. Benchmark score optimization

## Blocking and Abstain Conditions
Fail-fast when:
- empty/invalid extraction
- impossible schema contract violations
- persistent storage failures
- retry limits exhausted

Abstain when:
- no evidence-backed behavior
- no telemetry support
- only CVE mention without observables
- only tool/malware name without behavior
- rule remains overbroad after bounded refinement

## Documentation Map
- Architecture contracts: `docs/architecture/`
- Schemas/contracts: `docs/schemas/`
- Implementation policy: `docs/implementation/`
- Prompt pack: `docs/prompts/`
- Benchmark adapter: `docs/benchmark/`

## Operating Rule
When uncertain, stop and ask for clarification instead of guessing.

Detection quality priority: correctness and traceability first.

## Production-Completion Upgrade Requirements (Post-Agentic)

This section governs the next upgrade phase after the completed 14-task agentic deep-analysis service implementation.

### 1) API Layer (Mandatory)
- Implement pipeline API under `src/de_forge/api/routes/` with contract-first schemas in `src/de_forge/schemas/`.
- Canonical endpoint set:
  - `POST /v1/reports:ingest`
  - `POST /v1/pipeline:run`
  - `GET /v1/runs/{run_id}`
  - `POST /v1/reviews`
  - `POST /v1/exports/sigma`
- Enforce no raw-report-to-rule bypass path at API level.
- Standardize response model:
  - `status=abstain` for safe non-generation outcomes.
  - `status=failed` for hard-fail outcomes.
- Export endpoint must hard-block unless human review approval exists.

### 2) Persistence Layer (Mandatory)
- Add SQLAlchemy domain models in `src/de_forge/models/` and Alembic migrations in `alembic/versions/`.
- Persist required lineage fields for every run and artifact:
  - `report_id`, `run_id`, `trace_id`, `agent_run_id`, `detection_spec_id`, `rule_id`, `evidence_id`, `chunk_id`.
- Generated artifacts are immutable; rule edits create new versions.
- Persistence failures are fail-fast blockers (do not continue stage progression).
- Keep schema design PostgreSQL-compatible while supporting SQLite local runtime.

### 3) E2E Validation Layer (Mandatory)
- Add profile-based full-path E2E suite under `tests/e2e/`.
- Validate end-to-end flow: ingest -> pipeline -> review -> export.
- Validate abstain and hard-fail behavior through external API contracts.
- Deterministic replay requirement:
  - same input/profile/config yields same decision path and artifact hashes (excluding timestamps/opaque DB ids).

### 4) Benchmark Evaluation Runner (Mandatory)
- Implement benchmark runner and tests under `tests/benchmark/`.
- Must enforce baseline delta and KPI matrix gates from:
  - `docs/benchmark/eval-dataset-manifest.md`
  - `docs/implementation/kpi-threshold-matrix.md`
  - `docs/implementation/evaluation-protocol-agentic-deep-analysis.md`
- Promotion decision must fail if any hard gate or baseline delta requirement fails.

### 5) Real LLM Integration Testing (Mandatory)
- Add opt-in provider integration tests for real LLM calls.
- Gate with env var (example): `RUN_REAL_LLM_TESTS=1`.
- Use configured provider/model contract:
  - base URL `https://shopapikey.com/v1`
  - model `cx/gpt-5.5`
- Never log API keys or sensitive prompt content.
- Keep bounded retries/timeouts per LLM client contract.

### 6) Safety and Invariant Preservation
- Preserve existing invariants from current service layer:
  - DetectionSpec-first
  - hard gates
  - abstain policy
  - bounded refinement loops
  - human review gate
- No unsupported claims may pass without evidence/citation integrity.
- No schema-invalid output may advance stage state.

### 7) Required Verification Gates for This Upgrade
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
mypy src/
ruff check src/
ruff format --check src/
pytest tests/e2e/test_agentic_pipeline_profiles.py -v
pytest tests/benchmark/test_baseline_delta.py -v
```

### 8) Implementation Order (Risk-Minimized)
1. API schemas/routes (contract-first)
2. DB models + migrations
3. repository/persistence wiring in orchestrator flow
4. E2E profile validation
5. benchmark delta gates
6. real LLM integration tests

Reference spec for exact handoff tasks:
- `docs/superpowers/specs/2026-05-20-de-forge-production-completion-design.md`.
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

## Mandatory Architecture Rules
1. DetectionSpec is mandatory before rule generation.
2. Controlled multi-agent orchestration only (no free-form debate).
3. Deterministic validators are mandatory.
4. Bounded refinement loops only.
5. Abstain policy is mandatory.
6. Human review gate is mandatory before export.

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
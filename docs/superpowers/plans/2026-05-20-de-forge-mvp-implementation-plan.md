# DE-Forge MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, evidence-grounded DE-Forge MVP pipeline that enforces DetectionSpec-first, strict contracts, canonical retry/state semantics, and human review gate before export.

**Architecture:** Implement contract-first vertical slices with hard gates at each stage: contract validity, persistence+lineage, and state transition eligibility. Every stage persists lineage with deterministic idempotency keys and emits structured abstain/fail-fast outcomes when gates fail. Orchestration and validators enforce bounded loops and canonical terminal states.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest/pytest-asyncio/httpx, mypy, ruff, uv.

---

## File Structure Map

- `src/de_forge/core/constants.py` — global enums/constants (states, abstain codes, retry limits).
- `src/de_forge/core/types.py` — shared typed aliases + canonical envelope helpers.
- `src/de_forge/core/idempotency.py` — deterministic payload canonicalization + idempotency key hashing.
- `src/de_forge/core/hashing.py` — stable content hash + snapshot hash verification helpers.
- `src/de_forge/db/base.py` — SQLAlchemy base metadata.
- `src/de_forge/db/session.py` — engine/session lifecycle and transactional context manager.
- `src/de_forge/models/*.py` — persistence entities from contract (reports/chunks/evidence/mappings/specs/rules/validation/tests/agent_runs/reviews/refinement).
- `src/de_forge/schemas/*.py` — strict pydantic schemas (DetectionSpec, abstain, agent envelopes, validators).
- `src/de_forge/services/ingestion.py` — TXT/PDF ingest + deterministic chunking.
- `src/de_forge/services/evidence.py` — evidence extraction contract validation/persistence.
- `src/de_forge/services/attack_mapping.py` — ATT&CK mapping + structured abstain.
- `src/de_forge/services/telemetry.py` — telemetry grounding against registry.
- `src/de_forge/services/detection_spec.py` — DetectionSpec builder + hard gate.
- `src/de_forge/services/rule_generation.py` — Sigma generation constrained to DetectionSpec.
- `src/de_forge/services/static_validation.py` — deterministic static validators.
- `src/de_forge/services/dynamic_validation.py` — synthetic dynamic validation.
- `src/de_forge/services/refinement.py` — bounded refinement controller.
- `src/de_forge/services/review.py` — human review gate + export policy checks.
- `src/de_forge/services/orchestrator.py` — state machine transitions and end-to-end pipeline control.
- `src/de_forge/api/routes/*.py` — thin API routes (no business logic).
- `tests/unit/...` — isolated gate predicate and utility tests.
- `tests/integration/...` — transaction/retry/migration/state tests.
- `tests/e2e/test_pipeline_e2e.py` — positive and adversarial ABSTAIN paths.
- `alembic/versions/*.py` — schema migrations for persistence contract.

---

### Task 1: Core constants, abstain model, and deterministic hashing/idempotency primitives

**Files:**
- Create: `src/de_forge/core/constants.py`
- Create: `src/de_forge/core/hashing.py`
- Create: `src/de_forge/core/idempotency.py`
- Test: `tests/unit/core/test_idempotency.py`

- [ ] **Step 1: Write the failing tests**

```python
from de_forge.core.idempotency import make_idempotency_key
from de_forge.core.hashing import verify_snapshot_hash


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    payload = {"b": 2, "a": 1}
    key1 = make_idempotency_key("stage.ingest", payload)
    key2 = make_idempotency_key("stage.ingest", {"a": 1, "b": 2})
    assert key1 == key2


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload = {"x": "safe"}
    assert verify_snapshot_hash(payload, "bad-hash") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/core/test_idempotency.py -v`
Expected: FAIL with import errors/functions missing.

- [ ] **Step 3: Write minimal implementation**

```python
# src/de_forge/core/idempotency.py
import hashlib
import json
from typing import Any


def _canonicalize(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_idempotency_key(stage_identifier: str, payload: Any) -> str:
    canonical = _canonicalize(payload)
    digest = hashlib.sha256(f"{stage_identifier}|{canonical}".encode("utf-8")).hexdigest()
    return f"idem_{digest}"
```

```python
# src/de_forge/core/hashing.py
import hashlib
import json
from typing import Any


def snapshot_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_snapshot_hash(payload: Any, expected_hash: str) -> bool:
    return snapshot_hash(payload) == expected_hash
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/core/test_idempotency.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/core/test_idempotency.py src/de_forge/core/idempotency.py src/de_forge/core/hashing.py
git commit -m "feat(core): add deterministic idempotency and hash verification primitives"
```

### Task 2: Persistence foundation (SQLAlchemy base/session + core models + Alembic init)

**Files:**
- Create: `src/de_forge/db/base.py`
- Create: `src/de_forge/db/session.py`
- Create: `src/de_forge/models/report.py`
- Create: `src/de_forge/models/report_chunk.py`
- Create: `src/de_forge/models/evidence_span.py`
- Create: `src/de_forge/models/agent_run.py`
- Modify: `src/de_forge/core/config.py`
- Test: `tests/integration/db/test_schema_contract.py`

- [ ] **Step 1: Write failing migration/schema tests**

```python
def test_reports_table_has_content_hash_unique_constraint() -> None:
    ...

def test_agent_runs_has_input_output_hash_columns() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/db/test_schema_contract.py -v`
Expected: FAIL (tables/constraints missing).

- [ ] **Step 3: Implement models and metadata minimally to satisfy tests**

```python
class Report(Base):
    __tablename__ = "reports"
    id = mapped_column(String, primary_key=True)
    content_hash = mapped_column(String, nullable=False, unique=True)
```

```python
class AgentRun(Base):
    __tablename__ = "agent_runs"
    id = mapped_column(String, primary_key=True)
    input_snapshot = mapped_column(Text, nullable=False)
    output_snapshot = mapped_column(Text, nullable=True)
    input_hash = mapped_column(String, nullable=False)
    output_hash = mapped_column(String, nullable=True)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/db/test_schema_contract.py -v`
Expected: PASS for created subset.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/db src/de_forge/models src/de_forge/core/config.py tests/integration/db/test_schema_contract.py
git commit -m "feat(db): add base session and core persistence contract models"
```

### Task 3: Complete persistence contract and migration validation

**Files:**
- Create/Modify: `src/de_forge/models/*.py` (all tables in docs/architecture/06)
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/20260520_01_initial_contract.py`
- Test: `tests/integration/db/test_migrations_contract.py`

- [ ] **Step 1: Write failing migration tests**

```python
def test_all_contract_tables_exist() -> None:
    expected = {"reports", "report_chunks", "evidence_spans", "attack_mappings", "telemetry_selections", "detection_specs", "generated_rules", "validation_results", "test_runs", "agent_runs", "review_decisions", "refinement_iterations"}
    ...


def test_foreign_keys_and_indexes_match_contract() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/db/test_migrations_contract.py -v`
Expected: FAIL with missing migration/schema artifacts.

- [ ] **Step 3: Implement full migration and model alignment**

```python
# migration must create check constraints, unique constraints, and indexes exactly as contract
op.create_table("attack_mappings", ...)
op.create_index("ix_attack_mappings_technique_id", "attack_mappings", ["technique_id"])
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/db/test_migrations_contract.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add alembic.ini alembic src/de_forge/models tests/integration/db/test_migrations_contract.py
git commit -m "feat(db): implement full persistence contract migration with constraints and indexes"
```

### Task 4: Strict schemas (DetectionSpec, AgentIO envelope, structured abstain)

**Files:**
- Create: `src/de_forge/schemas/abstain.py`
- Create: `src/de_forge/schemas/detection_spec.py`
- Create: `src/de_forge/schemas/agent_io.py`
- Test: `tests/unit/schemas/test_detection_spec_schema.py`

- [ ] **Step 1: Write failing schema tests**

```python
def test_behavior_rule_requires_evidence_attack_telemetry() -> None:
    ...

def test_abstain_requires_structured_abstain_code_and_context() -> None:
    ...

def test_detection_spec_first_gate_rejects_missing_validated_spec() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/unit/schemas/test_detection_spec_schema.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement strict pydantic schemas and validators**

```python
class AbstainCode(str, Enum):
    NO_EVIDENCE_BACKED_BEHAVIOR = "NO_EVIDENCE_BACKED_BEHAVIOR"

class AbstainReason(BaseModel):
    abstain_code: AbstainCode
    abstain_context: dict[str, Any]
    human_message: str
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/unit/schemas/test_detection_spec_schema.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas tests/unit/schemas/test_detection_spec_schema.py
git commit -m "feat(schema): add strict DetectionSpec, AgentIO, and structured abstain contracts"
```

### Task 5: Orchestration states and unit-testable gate predicates

**Files:**
- Create: `src/de_forge/services/state_machine.py`
- Create: `src/de_forge/services/gates.py`
- Test: `tests/unit/services/test_gate_predicates.py`

- [ ] **Step 1: Write failing gate predicate tests**

```python
def test_rule_generation_gate_requires_validated_detection_spec() -> None:
    ...

def test_stage_gate_fails_without_lineage_fields() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/unit/services/test_gate_predicates.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement pure predicate functions and transition map**

```python
def can_generate_rule(spec_status: str) -> bool:
    return spec_status == "validated"
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/unit/services/test_gate_predicates.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/state_machine.py src/de_forge/services/gates.py tests/unit/services/test_gate_predicates.py
git commit -m "feat(orchestration): add canonical state transitions and pure gate predicates"
```

### Task 6: Ingestion service (TXT/PDF + deterministic chunking + persistence transaction)

**Files:**
- Create: `src/de_forge/services/ingestion.py`
- Create: `src/de_forge/api/routes/ingestion.py`
- Modify: `src/de_forge/main.py`
- Test: `tests/integration/services/test_ingestion_service.py`

- [ ] **Step 1: Write failing ingestion tests**

```python
def test_ingest_txt_persists_report_and_chunks_in_one_transaction() -> None:
    ...

def test_chunking_is_deterministic_for_same_input() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_ingestion_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement minimal ingestion and chunk persistence**

```python
def ingest_report(raw_text: str, source_type: str) -> str:
    # create report row + chunk rows in single transaction
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_ingestion_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/ingestion.py src/de_forge/api/routes/ingestion.py src/de_forge/main.py tests/integration/services/test_ingestion_service.py
git commit -m "feat(ingestion): add deterministic txt/pdf ingestion and chunk transaction"
```

### Task 7: Evidence extraction contract + persistence + fail-fast semantics

**Files:**
- Create: `src/de_forge/services/evidence.py`
- Test: `tests/integration/services/test_evidence_service.py`

- [ ] **Step 1: Write failing evidence tests**

```python
def test_empty_evidence_payload_transitions_to_failed_generation() -> None:
    ...

def test_valid_evidence_persists_with_lineage_fields() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_evidence_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement evidence contract validation and transactional writes**

```python
def persist_evidence(...):
    # validate quote offsets, non-empty support claims, confidence bounds
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_evidence_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/evidence.py tests/integration/services/test_evidence_service.py
git commit -m "feat(evidence): enforce strict extraction contract with fail-fast persistence"
```

### Task 8: ATT&CK mapping service with structured abstain

**Files:**
- Create: `src/de_forge/services/attack_mapping.py`
- Test: `tests/integration/services/test_attack_mapping_service.py`

- [ ] **Step 1: Write failing ATT&CK mapping tests**

```python
def test_invalid_technique_id_fails_contract_gate() -> None:
    ...

def test_insufficient_evidence_returns_structured_abstain() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_attack_mapping_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement ATT&CK validation and abstain generation**

```python
ATTACK_ID_PATTERN = re.compile(r"^T\d{4}(\.\d{3})?$")
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_attack_mapping_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/attack_mapping.py tests/integration/services/test_attack_mapping_service.py
git commit -m "feat(attack): add ATT&CK mapping gate and structured abstain handling"
```

### Task 9: Telemetry grounding against registry with allowed-field enforcement

**Files:**
- Create: `src/de_forge/services/telemetry.py`
- Create: `src/de_forge/services/telemetry_registry.py`
- Test: `tests/integration/services/test_telemetry_service.py`

- [ ] **Step 1: Write failing telemetry tests**

```python
def test_unattested_field_is_rejected() -> None:
    ...

def test_no_supported_telemetry_abstains_deterministically() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_telemetry_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement registry-backed field attestation checks**

```python
def validate_fields(selected: list[str], allowed: set[str]) -> None:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_telemetry_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/telemetry.py src/de_forge/services/telemetry_registry.py tests/integration/services/test_telemetry_service.py
git commit -m "feat(telemetry): enforce schema-grounded telemetry field attestation"
```

### Task 10: DetectionSpec builder service with hard runtime gate

**Files:**
- Create: `src/de_forge/services/detection_spec.py`
- Test: `tests/integration/services/test_detection_spec_service.py`

- [ ] **Step 1: Write failing DetectionSpec tests**

```python
def test_behavior_spec_missing_telemetry_fails_gate() -> None:
    ...

def test_abstain_spec_persists_structured_reason() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_detection_spec_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement DetectionSpec build + validation + persistence**

```python
def build_detection_spec(...) -> DetectionSpec:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_detection_spec_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/detection_spec.py tests/integration/services/test_detection_spec_service.py
git commit -m "feat(spec): enforce DetectionSpec-first build and strict validation gate"
```

### Task 11: Sigma generation constrained to validated DetectionSpec only

**Files:**
- Create: `src/de_forge/services/rule_generation.py`
- Test: `tests/integration/services/test_rule_generation_service.py`

- [ ] **Step 1: Write failing rule generation tests**

```python
def test_generation_without_validated_spec_is_blocked() -> None:
    ...

def test_generated_sigma_contains_attack_tags_and_allowed_fields_only() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_rule_generation_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement constrained Sigma generation**

```python
def generate_sigma_from_spec(spec: DetectionSpec) -> str:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_rule_generation_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/rule_generation.py tests/integration/services/test_rule_generation_service.py
git commit -m "feat(rule): add Sigma generation hard-gated by validated DetectionSpec"
```

### Task 12: Static validation service and deterministic issue reporting

**Files:**
- Create: `src/de_forge/services/static_validation.py`
- Test: `tests/integration/services/test_static_validation_service.py`

- [ ] **Step 1: Write failing static validation tests**

```python
def test_static_validator_detects_overbroad_rule() -> None:
    ...

def test_static_validator_blocks_unknown_telemetry_fields() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_static_validation_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement deterministic static validators**

```python
def validate_sigma(rule: str, spec: DetectionSpec) -> ValidationReport:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_static_validation_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/static_validation.py tests/integration/services/test_static_validation_service.py
git commit -m "feat(validation): add deterministic static validation gates"
```

### Task 13: Dynamic validation service and synthetic test harness

**Files:**
- Create: `src/de_forge/services/dynamic_validation.py`
- Create: `tests/fixtures/synthetic/sysmon_event_1_attack.json`
- Create: `tests/fixtures/synthetic/sysmon_event_1_benign.json`
- Test: `tests/integration/services/test_dynamic_validation_service.py`

- [ ] **Step 1: Write failing dynamic validation tests**

```python
def test_dynamic_validation_returns_tp_fp_metrics() -> None:
    ...

def test_dynamic_validation_result_is_deterministic_for_same_inputs() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_dynamic_validation_service.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement minimal deterministic synthetic harness**

```python
def run_synthetic_validation(rule: str, attack_events: list[dict], benign_events: list[dict]) -> dict:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_dynamic_validation_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/dynamic_validation.py tests/fixtures/synthetic tests/integration/services/test_dynamic_validation_service.py
git commit -m "feat(validation): add deterministic synthetic dynamic validation"
```

### Task 14: Bounded refinement controller and retry ceiling enforcement

**Files:**
- Create: `src/de_forge/services/refinement.py`
- Test: `tests/integration/services/test_refinement_limits.py`

- [ ] **Step 1: Write failing retry/loop tests**

```python
def test_query_refinement_stops_at_three_iterations() -> None:
    ...

def test_rule_refinement_stops_at_two_iterations() -> None:
    ...

def test_dynamic_refinement_stops_at_two_iterations() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_refinement_limits.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement bounded refinement with canonical limits**

```python
MAX_QUERY_REFINEMENT = 3
MAX_RULE_REFINEMENT = 2
MAX_DYNAMIC_REFINEMENT = 2
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_refinement_limits.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/refinement.py tests/integration/services/test_refinement_limits.py
git commit -m "feat(refinement): enforce canonical bounded refinement loops"
```

### Task 15: Agent run audit snapshots and hash verification on read

**Files:**
- Create: `src/de_forge/services/agent_audit.py`
- Test: `tests/integration/services/test_agent_audit_integrity.py`

- [ ] **Step 1: Write failing audit integrity tests**

```python
def test_agent_run_read_fails_on_hash_mismatch() -> None:
    ...

def test_agent_run_read_passes_on_valid_hashes() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_agent_audit_integrity.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement audit snapshot persistence and integrity read checks**

```python
def load_agent_run_verified(...):
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_agent_audit_integrity.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/agent_audit.py tests/integration/services/test_agent_audit_integrity.py
git commit -m "feat(audit): verify stored agent input-output snapshot hashes on read"
```

### Task 16: Orchestrator end-to-end service with canonical state transitions

**Files:**
- Create: `src/de_forge/services/orchestrator.py`
- Create: `src/de_forge/api/routes/pipeline.py`
- Modify: `src/de_forge/main.py`
- Test: `tests/integration/services/test_orchestrator_state_transitions.py`

- [ ] **Step 1: Write failing orchestrator tests**

```python
def test_pipeline_positive_flow_reaches_awaiting_review() -> None:
    ...

def test_state_transition_blocked_when_gate_fails() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_orchestrator_state_transitions.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement orchestrator wiring stages with hard gates**

```python
def run_pipeline(report_id: str) -> str:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_orchestrator_state_transitions.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/orchestrator.py src/de_forge/api/routes/pipeline.py src/de_forge/main.py tests/integration/services/test_orchestrator_state_transitions.py
git commit -m "feat(orchestrator): add hard-gated end-to-end state machine execution"
```

### Task 17: Human review gate and export policy enforcement

**Files:**
- Create: `src/de_forge/services/review.py`
- Create: `src/de_forge/api/routes/review.py`
- Test: `tests/integration/services/test_review_gate.py`

- [ ] **Step 1: Write failing review gate tests**

```python
def test_export_blocked_without_human_approval() -> None:
    ...

def test_append_only_review_decisions() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/integration/services/test_review_gate.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement review decision persistence and export guard**

```python
def can_export(rule_status: str, review_decision: str | None) -> bool:
    ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/integration/services/test_review_gate.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/review.py src/de_forge/api/routes/review.py tests/integration/services/test_review_gate.py
git commit -m "feat(review): enforce human approval gate before export"
```

### Task 18: E2E tests (positive + adversarial ABSTAIN + deterministic replay)

**Files:**
- Create: `tests/e2e/test_pipeline_e2e.py`
- Create: `tests/fixtures/reports/positive_report.txt`
- Create: `tests/fixtures/reports/ambiguous_report.txt`

- [ ] **Step 1: Write failing E2E and replay tests**

```python
def test_e2e_positive_pipeline_reaches_awaiting_review() -> None:
    ...

def test_e2e_ambiguous_report_abstains() -> None:
    ...

def test_deterministic_replay_same_input_same_transitions_and_idempotency() -> None:
    ...
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/e2e/test_pipeline_e2e.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement minimal glue needed for deterministic replay assertions**

```python
# ensure run comparison helper ignores allowed volatile IDs only
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/e2e/test_pipeline_e2e.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_pipeline_e2e.py tests/fixtures/reports
git commit -m "test(e2e): add positive, adversarial abstain, and deterministic replay coverage"
```

### Task 19: Full verification gates and coverage check

**Files:**
- Modify: `README.md` (verification section only if needed)
- Test: full suite

- [ ] **Step 1: Run full test and quality gates**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: PASS and coverage >= 80%.

- [ ] **Step 2: Run type checks**

Run: `mypy src/`
Expected: PASS with no errors.

- [ ] **Step 3: Run lint checks**

Run: `ruff check src/`
Expected: PASS with no violations.

- [ ] **Step 4: Run format verification**

Run: `ruff format --check src/`
Expected: PASS.

- [ ] **Step 5: Commit any final non-functional fixes only**

```bash
git add README.md src tests
git commit -m "chore: pass full verification gates for contract-first MVP"
```

---

## Spec Coverage Self-Review

- DetectionSpec-first runtime + tests: covered in Tasks 4, 5, 10, 11, 16, 18.
- Strict production contracts each stage: covered in Tasks 2-18.
- Canonical retry/state/idempotency: covered in Tasks 1, 5, 14, 16, 18.
- Structured abstain enums/context: covered in Tasks 4, 8, 9, 10, 18.
- Agent run snapshots + hash verification: covered in Task 15.
- Migration constraints/index/FK tests: covered in Task 3.
- Adversarial ABSTAIN E2E: covered in Task 18.
- Deterministic replay: covered in Task 18.
- Final clean verification commands: covered in Task 19.

No TODO/TBD placeholders remain.

---

## Execution Notes

- Implement tasks sequentially with strict TDD per task.
- After each task implementation, run two-stage review (spec compliance then code quality) before moving on.
- Do not start parallel implementation subagents for code-changing tasks.
- If any gate fails and cannot be resolved within canonical bounds, terminate with deterministic ABSTAIN/FAILED state and persist context.

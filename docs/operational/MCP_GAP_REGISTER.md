# MCP Gap Register (SOTA Core v2)

Last updated: 2026-05-23
Status: MCP-REG-001, MCP-REG-002, and MCP-REG-003 closed; no open MCP gaps.

## MCP-REG-001 — DetectionSpec formal content under-specified at runtime
- **Type:** MCP
- **Status:** Closed (2026-05-23)
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:242-265`
- **Closure evidence (file_path:line):**
  - `src/de_forge/schemas/detection_spec.py:64-74` adds explicit formal fields: `evidence_ids`, `behavior_ids`, `detection_strategy`, `analytic`, `data_component`, `allowed_telemetry_fields`, `rationale_traceability`.
  - `src/de_forge/schemas/detection_spec.py:87-107` adds fail-closed validators for formal list/string fields (non-empty, whitespace-trimmed).
  - `tests/unit/schemas/test_detection_spec_schema.py:251-327` validates contract acceptance/rejection with formal fields.
  - `tests/unit/services/test_detection_spec_verifier.py:9-55` aligns verifier fixtures with expanded DetectionSpec contract.
  - `tests/integration/services/test_detection_spec_service.py:27-173` updates persistence-path DetectionSpec fixtures to enforce runtime contract compatibility.
- **Verification evidence:**
  - `python -m pytest -q tests/unit/schemas/test_detection_spec_schema.py tests/unit/services/test_detection_spec_verifier.py tests/integration/services/test_detection_spec_service.py` → 16 passed.
  - `python -m mypy src/de_forge/schemas/detection_spec.py src/de_forge/services/detection_spec.py src/de_forge/services/detection_spec_verifier.py` → success.
  - `python -m ruff check src/de_forge/schemas/detection_spec.py src/de_forge/services/detection_spec.py tests/unit/schemas/test_detection_spec_schema.py tests/unit/services/test_detection_spec_verifier.py tests/integration/services/test_detection_spec_service.py` → all checks passed.
- **Residual risk:** None specific to formal DetectionSpec field coverage; remaining runtime durability risk tracked in MCP-REG-003.
- **DoD result:** Passed.

## MCP-REG-002 — Runtime orchestration missing evaluation-depth gates in authoritative path
- **Type:** MCP
- **Status:** Closed (2026-05-23)
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:67-71`
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:267-290`
- **Closure evidence (file_path:line):**
  - `src/de_forge/models/contract.py:249-265` adds persisted `proof_obligations` runtime table contract.
  - `src/de_forge/services/orchestrator.py:117-137` enforces fail-closed proof-obligation gate before `AWAITING_REVIEW`.
  - `tests/integration/services/test_orchestrator_state_transitions.py:325-404` proves missing/unknown obligations block transition, and proven obligations allow transition.
  - `tests/e2e/test_pipeline_e2e.py:76-99` seeds persisted proven obligations for deterministic positive path.
- **Verification evidence:**
  - `python -m pytest -q tests/integration/services/test_orchestrator_state_transitions.py tests/e2e/test_pipeline_e2e.py tests/integration/services/test_review_gate.py tests/integration/api/test_api_routes.py` → 29 passed.
  - `python -m mypy src/de_forge/services/orchestrator.py src/de_forge/models/contract.py src/de_forge/models/__init__.py tests/e2e/test_pipeline_e2e.py tests/integration/services/test_orchestrator_state_transitions.py` → success.
  - `python -m ruff check src/de_forge/models/__init__.py src/de_forge/models/contract.py src/de_forge/services/orchestrator.py tests/e2e/test_pipeline_e2e.py tests/integration/services/test_orchestrator_state_transitions.py` → all checks passed.
- **Residual risk:** Dynamic/adversarial/counterfactual/oracle evaluator invocation remains separate and tracked by remaining gaps.
- **DoD result:** Passed.

## MCP-REG-003 — API run-state persistence is process-memory only
- **Type:** MCP
- **Status:** Closed (2026-05-23)
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:15`
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:222-237`
- **Closure evidence (file_path:line):**
  - `src/de_forge/models/contract.py:249-266` adds persisted `pipeline_runs` table contract for run status semantics.
  - `src/de_forge/api/routes/pipeline.py:291-362` replaces in-memory run maps with DB-backed `PipelineRunRecord` read/write path.
  - `src/de_forge/api/routes/pipeline.py:276-279`, `:390-407` export/review mappings now resolve via persisted run record.
  - `tests/integration/db/test_schema_contract.py:157-175` asserts persisted `pipeline_runs` status columns exist.
  - `tests/e2e/test_api_run_status.py:10-99` validates run-status semantics on persisted source.
- **Verification evidence:**
  - `python -m pytest -q tests/e2e/test_api_run_status.py tests/integration/db/test_schema_contract.py tests/integration/api/test_api_routes.py` → 21 passed.
  - `python -m mypy src/de_forge/api/routes/pipeline.py src/de_forge/models/contract.py src/de_forge/models/__init__.py` → success.
  - `python -m ruff check src/de_forge/api/routes/pipeline.py src/de_forge/models/contract.py src/de_forge/models/__init__.py tests/e2e/test_api_run_status.py tests/integration/db/test_schema_contract.py` → all checks passed.
- **Residual risk:** None for API run-state durability in this path.
- **DoD result:** Passed.

---

## Priority order for closure
1. NONE

## Single-step continuation pointer
NEXT EXACT STEP: Run full verification suite (`pytest -q`, `mypy src`, `ruff check src tests`, `ruff format --check src tests docs`) and if green mark PRODUCTION-COMPLETE.

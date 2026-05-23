# MCP Gap Register (SOTA Core v2)

Last updated: 2026-05-23
Status: MCP-REG-001 and MCP-REG-002 closed; remaining open gaps tracked for one-gap-per-cycle closure.

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
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:15`
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:222-237`
- **Code vs SOTA evidence (file_path:line):**
  - `src/de_forge/api/routes/pipeline.py:281-286` and `src/de_forge/api/routes/pipeline.py:287-293` use in-memory dicts (`_RUN_TO_RULE`, `_RUN_TO_STATUS`, `_RUN_TO_REPORT`, `_RUN_TO_SPEC`, `_RUN_CREATED_AT`, `_RUN_TO_STAGE`) as runtime source of run status.
  - Not persisted lineage for API run status semantics.
- **Impact:** Run-status observability and auditability can reset across process restart, contradicting production-grade traceability goals.
- **DoD:**
  1. Replace in-memory run-state source with persisted run timeline/artifact source of truth.
  2. Keep API status endpoints behaviorally compatible where required.
  3. Add integration/e2e tests proving restart-safe status semantics.
  4. Pass changed-scope gates.
- **Residual risk if unchanged:** Non-durable operational state undermines auditability guarantees.

---

## Priority order for closure
1. MCP-REG-003 (highest remaining product correctness risk)

## Single-step continuation pointer
NEXT EXACT STEP: Implement MCP-REG-003 by replacing in-memory run maps in `src/de_forge/api/routes/pipeline.py` with persisted run timeline/artifact lookups and add restart-safe integration/e2e API status tests first.

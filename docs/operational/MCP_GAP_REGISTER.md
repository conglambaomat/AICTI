# MCP Gap Register (SOTA Core v2)

Last updated: 2026-05-23
Status: MCP-REG-002 closed; remaining open gaps tracked for one-gap-per-cycle closure.

## MCP-REG-001 — DetectionSpec formal content under-specified at runtime
- **Type:** MCP
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:242-265`
- **Code vs SOTA evidence (file_path:line):**
  - `src/de_forge/schemas/detection_spec.py:63-66` only enforces `report_id`, `behavior_rules`, `false_positive_hypotheses`, `test_plan`.
  - Missing explicit fields for formal spec content named by SOTA (evidence ids / behavior ids / detection strategy / analytic / data component / allowed telemetry fields / rationale traceability).
- **Impact:** Partial compliance with mandatory DetectionSpec contract; weaker deterministic guarantees before rule generation.
- **DoD:**
  1. Extend DetectionSpec contract and validators to explicitly represent and validate required formal fields from SOTA.
  2. Update affected services/tests to use expanded contract.
  3. Pass targeted schema/service tests + full relevant gates.
  4. Commit with evidence links.
- **Residual risk if unchanged:** Contract drift between canonical architecture and runtime payload semantics.

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
1. MCP-REG-002 (highest product correctness risk)
2. MCP-REG-001
3. MCP-REG-003

## Single-step continuation pointer
NEXT EXACT STEP: Implement MCP-REG-002 by wiring dynamic/adversarial/counterfactual/oracle + proof-obligation fail-closed checks into `src/de_forge/services/orchestrator.py` and add failing integration tests first.

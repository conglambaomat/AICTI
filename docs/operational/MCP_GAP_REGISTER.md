# MCP Gap Register (SOTA Core v2)

Last updated: 2026-05-24
Status: MCP-REG-001..003 closed; MCP-REG-004..008 opened from SOTA architecture audit backlog.

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

## MCP-REG-004 — Evaluation-depth runtime wiring not fully authoritative before review/export
- **Type:** MCP
- **Status:** Closed (2026-05-24)
- **Priority:** P0
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:67-74`
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:352-430`
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:580-592`
- **Closure evidence (file_path:line):**
  - `src/de_forge/services/orchestrator.py:118-140` enforces fail-closed evaluation-depth gate via persisted `validation_results` requiring at least four outcomes and all `passed` before review transition.
  - `tests/integration/services/test_orchestrator_state_transitions.py:368-437` adds red→green coverage for missing/failed evaluation-depth outcomes blocking transition and pass-path allowing `AWAITING_REVIEW`.
  - `src/de_forge/api/routes/pipeline.py:208-259` seeds required persisted evaluation outcomes in `/v1/pipeline:seed` runtime fixture to keep authoritative API path aligned with new gate.
  - `tests/e2e/test_pipeline_e2e.py:24-102`, `tests/integration/services/test_agent_audit_integrity.py:113-197` seed evaluation outcomes for positive authoritative flows and audit persistence coverage.
- **Verification evidence:**
  - `python -m pytest -q tests/integration/services/test_orchestrator_state_transitions.py` → 15 passed.
  - `python -m pytest -q tests/e2e/test_pipeline_e2e.py tests/e2e/test_api_run_status.py tests/e2e/test_api_review_and_export.py tests/e2e/test_api_health_and_contracts.py tests/integration/services/test_agent_audit_integrity.py` → 24 passed.
  - `python -m pytest -q` → 317 passed, 1 warning.
  - `python -m mypy src` → success.
  - `python -m ruff check src tests` → all checks passed.
  - `python -m ruff format --check src tests docs` → all files already formatted.
- **Residual risk:** Ranking-depth objective semantics remain open and tracked by MCP-REG-006.
- **DoD result:** Passed.
- **NEXT EXACT STEP:** Close MCP-REG-005 by adding schema-contract red tests for highest-impact missing canonical persistence tables.

## MCP-REG-005 — Persistence breadth incomplete vs SOTA §20 canonical model
- **Type:** MCP
- **Status:** Closed (2026-05-24)
- **Priority:** P0
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:484-501`
- **Closure evidence (file_path:line):**
  - `tests/integration/db/test_schema_contract.py:207-693` adds red→green contract coverage for `candidate_scores`, `oracle_evaluation_results`, `regression_runs`, and `quality_snapshots` including PK/FK/index/check constraints.
  - `src/de_forge/models/contract.py:301-391` adds additive persistence models for `candidate_scores`, `oracle_evaluation_results`, `regression_runs`, and `quality_snapshots` with required constraints and indexes.
- **Verification evidence:**
  - `python -m pytest -q tests/integration/db/test_schema_contract.py` → 48 passed.
  - `python -m pytest -q` → 355 passed, 1 warning.
  - `python -m mypy src` → success.
  - `python -m ruff check src tests` → all checks passed.
  - `python -m ruff format --check src tests docs` → all files already formatted.
- **Residual risk:** Additional canonical persistence domains (`retrieval_queries/results`, `proof_evidence_links`, `proof_verification_results`, `rule_candidate_versions`) remain and are tracked by MCP-REG-006+.
- **DoD result:** Passed.
- **NEXT EXACT STEP:** Close MCP-REG-006 by expanding score model dimensions and ranking contract coverage.

## MCP-REG-006 — Portfolio/ranking score model under-specified vs SOTA §13/§17
- **Type:** MCP
- **Status:** Closed (2026-05-24)
- **Priority:** P0
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:309-335`
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:407-430`
- **Closure evidence (file_path:line):**
  - `src/de_forge/schemas/rule_candidate.py:16-29` expands `CandidateScore` with required SOTA dimensions and penalties (`adversarial_robustness`, `counterfactual_stability`, `oracle_alignment`, `regression_safety`, `explainability`, `overbreadth_penalty`, `complexity_penalty`, `drift_risk_penalty`).
  - `src/de_forge/services/portfolio_service.py:11-22` defines fail-closed required score/penalty sets for ranking readiness.
  - `src/de_forge/services/portfolio_service.py:48-56` enforces ranking readiness gate via `model_fields_set` and explicit missing-dimensions/missing-penalties failures.
  - `tests/unit/services/test_portfolio_service.py:26-91` adds/red→green unit coverage for SOTA score/penalty contract presence and fail-closed readiness rejection behavior.
- **Verification evidence:**
  - `python -m pytest -q tests/unit/services/test_portfolio_service.py` → 4 passed.
  - `python -m pytest -q` → 359 passed, 1 warning.
  - `python -m mypy src` → success.
  - `python -m ruff check src tests` → all checks passed.
  - `python -m ruff format --check src tests docs` → all files already formatted.
- **Residual risk:** Canonical persistence breadth for detailed candidate versioning/agent audit payload depth remains tracked by MCP-REG-007+.
- **DoD result:** Passed.
- **NEXT EXACT STEP:** Close MCP-REG-007 by adding schema-contract red tests for missing `agent_runs` audit columns required by SOTA §9.

## MCP-REG-007 — Multi-agent role coverage/audit payload depth incomplete vs SOTA §9
- **Type:** MCP
- **Status:** Closed (2026-05-24)
- **Priority:** P1
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:196-237`
- **Closure evidence (file_path:line):**
  - `src/de_forge/models/contract.py:220-254` expands `agent_runs` with canonical audit payload columns (`prompt_version`, `model_id`, `tokens_in`, `tokens_out`, `latency_ms`, `cost_usd`, `input_payload_json`, `output_payload_json`, `artifact_ids_json`) plus non-negative checks and identity indexes.
  - `alembic/versions/20260520_01_initial_contract.py:145-153` aligns initial migration contract for `agent_runs` with the expanded schema + indexes/check constraints.
  - `src/de_forge/api/routes/pipeline.py:349-397` adds fail-closed runtime schema auto-upgrade for pre-existing `agent_runs` tables so authoritative `/v1` runtime no longer breaks on stale schema.
  - `tests/integration/db/test_schema_contract.py:20-742` provides red→green schema-contract coverage for required `agent_runs` SOTA audit fields/indexes/checks.
- **Verification evidence:**
  - `python -m pytest -q tests/integration/db/test_schema_contract.py -k agent_runs` → 60 passed.
  - `python -m pytest -q tests/e2e/test_api_health_and_contracts.py tests/e2e/test_api_review_and_export.py tests/e2e/test_api_run_status.py` → 16 passed.
  - `python -m pytest -q` → 418 passed, 1 warning.
  - `python -m mypy src` → success.
  - `python -m ruff check src tests` → all checks passed.
  - `python -m ruff format --check src tests docs` → all files already formatted.
- **Residual risk:** Canonical typed evidence-graph lineage semantics remain open and tracked by MCP-REG-008.
- **DoD result:** Passed.
- **NEXT EXACT STEP:** Close MCP-REG-008 by adding integration tests asserting required typed lineage paths from evidence quote to reviewed rule candidate.

## MCP-REG-008 — Evidence-graph typed lineage semantics partial vs SOTA §6
- **Type:** MCP
- **Status:** Closed (2026-05-24)
- **Priority:** P1
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:100-146`
- **Closure evidence (file_path:line):**
  - `src/de_forge/services/evidence_graph.py:11-32` introduces fail-closed typed taxonomy for nodes/edges used in canonical lineage (`evidence_quote`, `detection_strategy`, `analytic`, `data_component`, `telemetry_source`, `reviewed_rule_candidate`; edges `supports`, `derives`, `maps_to`, `implements`).
  - `src/de_forge/services/evidence_graph.py:37-63` enforces taxonomy on write-path by rejecting unsupported node/edge types.
  - `src/de_forge/services/evidence_graph.py:64-105` implements required typed lineage reachability check from `evidence_quote` to `reviewed_rule_candidate` through canonical intermediate node classes.
  - `tests/integration/services/test_evidence_service.py:161-312` adds red→green integration coverage for fail-closed taxonomy rejection and required lineage path positive/negative behavior.
  - `tests/integration/db/test_artifact_graph_persistence.py:59-72` aligns persistence integration to typed node taxonomy contract.
- **Verification evidence:**
  - `python -m pytest -q tests/integration/services/test_evidence_service.py` → 7 passed.
  - `python -m pytest -q tests/integration/db/test_artifact_graph_persistence.py tests/integration/services/test_evidence_service.py` → 10 passed.
  - `python -m pytest -q` → 422 passed, 1 warning.
  - `python -m mypy src` → success.
  - `python -m ruff check src tests` → all checks passed.
  - `python -m ruff format --check src tests docs` → all files already formatted.
- **Residual risk:** Typed lineage is now enforced for canonical path classes currently modeled; future artifact classes need explicit taxonomy extension before use.
- **DoD result:** Passed.
- **NEXT EXACT STEP:** Maintain closed-gap monitoring and run full verification suite before any new backlog reopen.

---

## Priority order for closure
1. MCP-REG-004 (P0)
2. MCP-REG-005 (P0)
3. MCP-REG-006 (P0)
4. MCP-REG-007 (P1)
5. MCP-REG-008 (P1)

## Single-step continuation pointer
NEXT EXACT STEP: Run full verification suite (`pytest -q`, `mypy src`, `ruff check src tests`, `ruff format --check src tests docs`) and keep MCP register closed unless new architecture-audit gaps are proven.

## One-gap-per-cycle policy
- Each execution cycle closes exactly one highest-priority open MCP gap.
- Do not switch gaps mid-cycle.
- A gap may be marked closed only after code + tests + targeted gates + full gates + register evidence update all pass.
- If cycle does not finish, persist exactly one line `NEXT EXACT STEP` and resume from it next cycle.

---

## Historical closed MCP entries

## MCP-REG-001 — DetectionSpec formal content under-specified at runtime
- **Type:** MCP
- **Status:** Closed (2026-05-23)
- **SOTA requirement reference:**
  - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md:242-265`
- **Closure evidence (file_path:line):
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
- **Closure evidence (file_path:line):
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
- **Closure evidence (file_path:line):
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

## Priority order for legacy closure snapshots
1. NONE

## Legacy continuation pointer
NEXT EXACT STEP: Run full verification suite (`pytest -q`, `mypy src`, `ruff check src tests`, `ruff format --check src tests docs`) and if green mark PRODUCTION-COMPLETE.

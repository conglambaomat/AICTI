# SOTA Core v2 Plan↔Code Traceability Matrix

Date: 2026-05-23
Scope: Documentation-only mapping of every requirement in `2026-05-22-sota-v2-requirement-inventory.md` to current code/test evidence.

## How to use

- Source of requirements: `docs/superpowers/specs/2026-05-22-sota-v2-requirement-inventory.md`
- Source of evidence anchors: `docs/superpowers/specs/2026-05-22-sota-v2-evidence-index.md`
- Status values use the rubric below.

## Status rubric

- `implemented`: Requirement covered by clear code AND test evidence.
- `partial`: Code present but missing tests, integration, or required edge behavior.
- `missing`: No credible code evidence found.
- `drifted`: Capability exists but materially diverges from documented contract or path.

## Risk levels

- `high`: violates an architecture invariant or blocks downstream phase.
- `medium`: weakens a phase deliverable but not blocking.
- `low`: cosmetic or naming drift only.

## Phase 1 — Foundation

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-P1-01 | Stable canonical JSON and snapshot hashes | `src/de_forge/core/hashing.py` | `tests/unit/core/test_hashing_idempotency.py` | implemented | low | Keep as complete foundation anchor. |
| R-P1-02 | Stage-scoped deterministic idempotency keys | `src/de_forge/core/idempotency.py` | `tests/unit/core/test_hashing_idempotency.py` | implemented | low | Keep as complete foundation anchor. |
| R-P1-03 | Domain exceptions for validation/citation/proof failures | `src/de_forge/core/errors.py` | `tests/unit/services/test_chunking_citation.py`; `tests/unit/services/test_proof_obligations.py`; `tests/unit/services/test_state_machine_gates.py` | implemented | low | Keep centralized error contract. |
| R-P1-04 | Artifact lineage schemas | `src/de_forge/schemas/artifact.py`; `src/de_forge/models/artifact.py` | `tests/unit/core/test_artifact_schema.py`; `tests/integration/db/test_artifact_graph_persistence.py` | implemented | low | Keep schema/model mapping documented. |
| R-P1-05 | SQLAlchemy base/session and artifact persistence | `src/de_forge/db/base.py`; `src/de_forge/db/session.py`; `src/de_forge/services/artifact_store.py` | `tests/integration/db/test_artifact_graph_persistence.py`; `tests/unit/services/test_product_artifacts.py` | implemented | low | Keep runtime DB notes separate from lineage store. |
| R-P1-06 | Evidence graph schemas/models/query service | `src/de_forge/schemas/evidence_graph.py`; `src/de_forge/models/evidence_graph.py`; `src/de_forge/services/evidence_graph.py`; `src/de_forge/services/graph_builder.py` | `tests/integration/db/test_artifact_graph_persistence.py`; `tests/integration/services/test_graph_builder.py` | implemented | low | Treat `graph_builder.py` as product graph construction evidence. |
| R-P1-07 | Deterministic text chunking with stable IDs and offsets | `src/de_forge/services/chunking.py`; `src/de_forge/services/ingestion.py` | `tests/unit/services/test_chunking_citation.py`; `tests/unit/services/test_ingestion.py` | implemented | low | Keep chunking/ingestion boundary explicit. |
| R-P1-08 | Exact citation quote/offset verification | `src/de_forge/services/citation_verifier.py`; `src/de_forge/services/graph_builder.py` | `tests/unit/services/test_chunking_citation.py`; `tests/integration/services/test_graph_builder.py` | implemented | high | Preserve as hard invariant gate; no warning-only behavior. |
| R-P1-09 | ATT&CK detection registry | `src/de_forge/services/attack_detection_registry.py`; `src/de_forge/schemas/attack_detection.py` | `tests/unit/services/test_attack_telemetry_registry.py` | implemented | medium | Keep registry scope curated; expand only via planned tasks. |
| R-P1-10 | Multi-platform telemetry registry | `src/de_forge/services/telemetry_registry.py`; `src/de_forge/schemas/telemetry.py` | `tests/unit/services/test_attack_telemetry_registry.py` | implemented | high | Preserve unknown-field rejection. |
| R-P1-11 | Formal DetectionSpec contract | `src/de_forge/schemas/detection_spec.py` | `tests/unit/schemas/test_detection_spec_schema.py`; `tests/unit/services/test_detection_spec_verifier.py` | implemented | high | Keep DetectionSpec as mandatory pre-rule artifact. |
| R-P1-12 | DetectionSpec verification before rule generation | `src/de_forge/services/detection_spec_verifier.py`; `src/de_forge/services/detection_ast_service.py`; `src/de_forge/services/gates.py` | `tests/unit/services/test_detection_spec_verifier.py`; `tests/unit/services/test_detection_ast.py`; `tests/unit/services/test_state_machine_gates.py` | implemented | high | Keep verifier and gate references in execution docs. |
| R-P1-13 | Proof obligation generation and selectable-candidate blocking | `src/de_forge/services/proof_obligation_service.py`; `src/de_forge/schemas/proof_obligation.py`; `src/de_forge/services/export_gate.py`; `src/de_forge/services/gates.py` | `tests/unit/services/test_proof_obligations.py`; `tests/integration/api/test_export_routes.py` | implemented | high | Make export/final selection dependency explicit in synced plans. |
| R-P1-14 | Foundation verification gates | `pyproject.toml`; `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md` | `python -m uv run pytest tests/ -v --cov=src --cov-report=term-missing` passed with 127 tests and 93% coverage; `python -m uv run mypy src/` passed; `python -m uv run ruff check src/ tests/` passed; `python -m uv run ruff format --check src/ tests/` passed | implemented | low | Verification evidence recorded; rerun gates after future source or test changes. |

## Phase 2 — Compiler

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-P2-01 | Typed Detection AST schema | `src/de_forge/schemas/detection_ast.py` | `tests/unit/services/test_detection_ast.py` | implemented | high | Mark Phase 2 compiler contract present; older claims of absence are stale. |
| R-P2-02 | Convert verified DetectionSpecs to AST and reject unverified specs | `src/de_forge/services/detection_ast_service.py` | `tests/unit/services/test_detection_ast.py`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Keep verified-spec precondition highlighted. |
| R-P2-03 | Preserve AST condition provenance to evidence IDs | `src/de_forge/schemas/detection_ast.py`; `src/de_forge/services/detection_ast_service.py` | `tests/unit/services/test_detection_ast.py` | implemented | high | Ensure downstream Sigma provenance remains linked. |
| R-P2-04 | Typed Sigma rule schema | `src/de_forge/schemas/sigma.py` | `tests/unit/services/test_sigma_compiler.py` | implemented | high | Keep Sigma schema as typed intermediate. |
| R-P2-05 | Compile Detection ASTs into typed Sigma rule objects | `src/de_forge/services/sigma_compiler.py` | `tests/unit/services/test_sigma_compiler.py`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Treat compiler-first invariant as currently satisfied by code evidence. |
| R-P2-06 | Validate telemetry/logsource compatibility and reject unsupported fields | `src/de_forge/services/sigma_compiler.py`; `src/de_forge/services/telemetry_registry.py` | `tests/unit/services/test_sigma_compiler.py`; `tests/unit/services/test_attack_telemetry_registry.py` | implemented | high | Keep field validation coupled to telemetry registry. |
| R-P2-07 | Serialize compiled Sigma objects to YAML | `src/de_forge/services/sigma_compiler.py` | `tests/unit/services/test_sigma_compiler.py` | implemented | medium | Keep YAML as output, not source of truth. |
| R-P2-08 | Validate Sigma structure and condition references | `src/de_forge/services/sigma_validator.py`; `src/de_forge/services/static_validation.py` | `tests/unit/services/test_sigma_compiler.py`; `tests/unit/services/test_static_validation.py` | implemented | high | Keep validator evidence in compiler and validation docs. |
| R-P2-09 | Compiler verification gates | `tests/unit/services/test_detection_ast.py`; `tests/unit/services/test_sigma_compiler.py` | Targeted compiler invariant tests passed; full pytest/mypy/ruff/format gates passed | implemented | low | Rerun compiler and full quality gates after compiler changes. |

## Phase 3 — Validation, Oracle, Regression

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-P3-01 | Rule candidate and score schemas | `src/de_forge/schemas/rule_candidate.py` | `tests/unit/services/test_static_validation.py` | implemented | medium | Keep candidate scoring schema documented. |
| R-P3-02 | Portfolio wrapping for compiled Sigma rules | `src/de_forge/services/portfolio_service.py` | `tests/unit/services/test_static_validation.py` | implemented | medium | Keep portfolio service as candidate factory anchor. |
| R-P3-03 | Static validation gates | `src/de_forge/services/static_validation.py`; `src/de_forge/services/sigma_validator.py` | `tests/unit/services/test_static_validation.py` | implemented | high | Keep static validation as required candidate gate. |
| R-P3-04 | Overbroad pattern rejection | `src/de_forge/services/broad_rule_detector.py`; `src/de_forge/services/static_validation.py` | `tests/unit/services/test_static_validation.py` | implemented | high | Expand broadness rules only through planned validation work. |
| R-P3-05 | Dynamic validation against positive/benign events | `src/de_forge/services/dynamic_validation.py`; `src/de_forge/schemas/test_event.py` | `tests/unit/services/test_dynamic_validation.py` | implemented | high | Keep dynamic validation separate from static validation. |
| R-P3-06 | Dynamic precision/recall calculation | `src/de_forge/schemas/test_event.py`; `src/de_forge/services/dynamic_validation.py` | `tests/unit/services/test_dynamic_validation.py` | implemented | medium | Keep metric semantics documented. |
| R-P3-07 | Adversarial variant robustness scoring | `src/de_forge/services/adversarial_validation.py` | `tests/unit/services/test_dynamic_validation.py` | implemented | medium | Treat as initial heuristic implementation. |
| R-P3-08 | Counterfactual condition importance evaluation | `src/de_forge/services/counterfactual_evaluation.py` | `tests/unit/services/test_dynamic_validation.py` | implemented | medium | Treat as initial heuristic implementation. |
| R-P3-09 | Oracle cases and scoring | `src/de_forge/schemas/oracle.py`; `src/de_forge/services/oracle_evaluation.py` | `tests/unit/services/test_oracle_evaluation.py` | implemented | high | Mark oracle layer present; future work may deepen benchmark integration. |
| R-P3-10 | Convert review feedback into regression tests | `src/de_forge/schemas/feedback.py`; `src/de_forge/schemas/regression.py`; `src/de_forge/services/feedback_learning.py` | `tests/unit/services/test_feedback_regression.py` | implemented | high | Keep feedback-to-regression as invariant evidence. |
| R-P3-11 | Enforce feedback-derived regression gates | `src/de_forge/services/regression.py` | `tests/unit/services/test_feedback_regression.py` | implemented | high | Keep regression gate before future candidate acceptance. |
| R-P3-12 | Validation/oracle/regression verification gates | `tests/unit/services/test_static_validation.py`; `tests/unit/services/test_dynamic_validation.py`; `tests/unit/services/test_oracle_evaluation.py`; `tests/unit/services/test_feedback_regression.py` | Targeted regression invariant tests passed; full pytest/mypy/ruff/format gates passed | implemented | low | Rerun validation/oracle/regression and full quality gates after scoring or feedback changes. |

## Phase 4 — Controlled Agents

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-P4-01 | Strict agent IO envelopes | `src/de_forge/schemas/agent_io.py` | `tests/unit/agents/test_agent_contracts.py` | implemented | high | Keep schema validation as first agent boundary. |
| R-P4-02 | Citation schema with exact span | `src/de_forge/schemas/agent_io.py`; `src/de_forge/services/citation_verifier.py` | `tests/unit/agents/test_agent_contracts.py`; `tests/unit/services/test_chunking_citation.py` | implemented | high | Keep agent citation output linked to deterministic verifier. |
| R-P4-03 | Versioned prompt registry | `src/de_forge/services/prompt_registry.py` | `tests/unit/agents/test_agent_contracts.py` | implemented | medium | Keep prompt versions stable and auditable. |
| R-P4-04 | OpenAI-compatible LLM request/response contracts | `src/de_forge/services/llm_client.py`; `src/de_forge/core/config.py` | `tests/unit/agents/test_agent_contracts.py`; `tests/unit/services/test_llm_client.py`; `tests/unit/services/test_runtime_config.py` | implemented | high | Preserve single-provider/model policy unless user approves change. |
| R-P4-05 | Persist agent run audits | `src/de_forge/models/agent_run.py`; `src/de_forge/services/agent_audit.py` | `tests/integration/agents/test_agent_audit.py`; `tests/integration/services/test_orchestrator_product_path.py` | implemented | high | Keep agent audit persistence as lineage input. |
| R-P4-06 | Base controlled runner and strict envelopes | `src/de_forge/agents/base.py` | `tests/unit/agents/test_agent_contracts.py` | implemented | high | Keep agents untrusted; deterministic services gate outputs. |
| R-P4-07 | Evidence agent with citation extraction | `src/de_forge/agents/evidence_agent.py` | `tests/unit/agents/test_agent_contracts.py`; `tests/integration/services/test_orchestrator_product_path.py` | implemented | high | Ensure product path still verifies citations before graph insertion. |
| R-P4-08 | ATT&CK mapping agent using supplied evidence only | `src/de_forge/agents/attack_mapping_agent.py` | `tests/unit/agents/test_agent_contracts.py`; `tests/integration/services/test_orchestrator_product_path.py` | implemented | high | Keep evidence-only prompt constraint explicit. |
| R-P4-09 | DetectionSpec agent contract | `src/de_forge/agents/detection_spec_agent.py` | `tests/unit/agents/test_agent_contracts.py`; `tests/integration/services/test_orchestrator_product_path.py` | implemented | high | Keep deterministic DetectionSpec verifier after agent output. |
| R-P4-10 | Critic/refinement risk contract | `src/de_forge/agents/critic_agent.py` | `tests/unit/agents/test_agent_contracts.py` | implemented | medium | Add deeper integration evidence if critic becomes required gate. |
| R-P4-11 | Agents verification gates | `tests/unit/agents/test_agent_contracts.py`; `tests/integration/agents/test_agent_audit.py`; `tests/integration/services/test_orchestrator_product_path.py` | Full pytest/mypy/ruff/format gates passed; bounded-loop settings now have direct default assertions | implemented | low | Rerun agent, product-path, and full quality gates after agent loop changes. |

## Phase 5 — Orchestrator, API, UI, Dashboard

| ID | Capability | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-P5-01 | Run modes and states | `src/de_forge/schemas/run.py` | `tests/unit/services/test_state_machine_gates.py`; `tests/integration/services/test_orchestrator_golden_path.py` | implemented | high | Keep run states aligned with product path. |
| R-P5-02 | Legal state transitions and raw-report-to-rule rejection | `src/de_forge/services/state_machine.py` | `tests/unit/services/test_state_machine_gates.py` | implemented | high | Preserve illegal transition test as invariant guard. |
| R-P5-03 | Hard gate predicates for rule generation/final review | `src/de_forge/services/gates.py`; `src/de_forge/services/export_gate.py` | `tests/unit/services/test_state_machine_gates.py`; `tests/integration/api/test_export_routes.py` | implemented | high | Keep gate predicates and export gate both documented. |
| R-P5-04 | Auto-mode golden-path orchestration | `src/de_forge/services/orchestrator.py` | `tests/integration/services/test_orchestrator_golden_path.py`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Distinguish golden-path skeleton from product-path orchestration in docs. |
| R-P5-05 | Cautious mode pauses at DetectionSpec review | `src/de_forge/services/orchestrator.py` | `tests/integration/services/test_orchestrator_golden_path.py`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Keep cautious-mode pause before rule generation explicit. |
| R-P5-06 | Human review schemas/service | `src/de_forge/schemas/review.py`; `src/de_forge/services/review.py` | `tests/unit/services/test_review_service.py`; `tests/integration/api/test_review_product_route.py` | implemented | high | Keep repository-backed review behavior documented. |
| R-P5-07 | Export blocked unless human review permits | `src/de_forge/services/export_gate.py`; `src/de_forge/api/routes/exports.py`; `src/de_forge/services/review.py` | `tests/integration/api/test_export_routes.py`; `tests/integration/api/test_review_product_route.py` | implemented | high | Preserve export gate as final hard gate. |
| R-P5-08 | API routes for run/review/report/export/ops | `src/de_forge/api/router.py`; `src/de_forge/api/routes/*.py` | `tests/integration/api/test_api_routes.py`; `tests/integration/api/test_ops_routes.py`; `tests/integration/api/test_report_upload_routes.py`; `tests/integration/api/test_review_product_route.py`; `tests/integration/api/test_export_routes.py` | implemented | medium | Update older plans to reflect broader actual API surface. |
| R-P5-09 | Quality metric snapshots/dashboard data | `src/de_forge/services/metrics.py`; `src/de_forge/api/routes/metrics.py`; `src/de_forge/ui_support/review_view.py` | `tests/unit/services/test_metrics.py`; `tests/integration/api/test_api_routes.py`; `tests/unit/ui_support/test_review_view.py` | implemented | medium | Note that some default snapshots are simple and may need production hardening. |
| R-P5-10 | Minimal trust-oriented review UI | `src/de_forge/api/routes/ui.py`; `src/de_forge/ui_support/review_view.py` | `tests/integration/api/test_api_routes.py`; `tests/integration/api/test_runtime_ui_routes.py`; `tests/unit/ui_support/test_review_view.py` | implemented | medium | Keep UI minimal; defer richer frontend until deterministic core remains aligned. |
| R-P5-11 | Orchestrator/API/UI/dashboard verification gates | `tests/integration/services/test_orchestrator_golden_path.py`; `tests/integration/api/test_api_routes.py`; `tests/unit/services/test_metrics.py`; `tests/unit/ui_support/test_review_view.py` | Full pytest/mypy/ruff/format gates passed; manual runtime/UI smoke remains a release-readiness checkpoint | partial | medium | Run browser/runtime smoke before claiming UI/runtime release completion. |

## Architecture Invariants

| ID | Invariant | Code Evidence | Test Evidence | Status | Risk | Doc Action |
| --- | --- | --- | --- | --- | --- | --- |
| R-INV-01 | No raw-report-to-rule path | `src/de_forge/services/state_machine.py`; `src/de_forge/services/orchestrator.py` | `tests/unit/services/test_state_machine_gates.py::test_state_machine_rejects_raw_report_to_rule_candidate_transition`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Keep transition guard and orchestrator path as hard invariant evidence. |
| R-INV-02 | DetectionSpec mandatory before rule generation | `src/de_forge/services/detection_ast_service.py`; `src/de_forge/services/gates.py`; `src/de_forge/services/orchestrator.py` | `tests/unit/services/test_detection_ast.py`; `tests/unit/services/test_state_machine_gates.py`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Keep DetectionSpec verifier and AST gate before Sigma. |
| R-INV-03 | Citations exact and verified | `src/de_forge/services/citation_verifier.py`; `src/de_forge/services/graph_builder.py`; `src/de_forge/schemas/agent_io.py` | `tests/unit/services/test_chunking_citation.py`; `tests/integration/services/test_graph_builder.py` | implemented | high | Never downgrade citation mismatch to warning. |
| R-INV-04 | ATT&CK chain Technique → Strategy → Analytic → Data Component → Telemetry → Field | `src/de_forge/services/attack_detection_registry.py`; `src/de_forge/services/telemetry_registry.py`; `src/de_forge/schemas/detection_spec.py` | `tests/unit/services/test_attack_telemetry_registry.py`; `tests/unit/services/test_detection_spec_verifier.py` | implemented | high | Keep chain explicit in DetectionSpec and registry docs. |
| R-INV-05 | Required proof obligations proven before final candidate selection | `src/de_forge/services/proof_obligation_service.py`; `src/de_forge/services/gates.py`; `src/de_forge/services/export_gate.py` | `tests/unit/services/test_proof_obligations.py`; `tests/integration/api/test_export_routes.py` | implemented | high | Preserve final selection/export blocking semantics. |
| R-INV-06 | AST + compiler preferred over free-form Sigma generation | `src/de_forge/schemas/detection_ast.py`; `src/de_forge/services/detection_ast_service.py`; `src/de_forge/services/sigma_compiler.py` | `tests/unit/services/test_detection_ast.py`; `tests/unit/services/test_sigma_compiler.py`; `tests/integration/services/test_orchestrator_vertical_slice.py` | implemented | high | Treat older claims of compiler absence as stale. |
| R-INV-07 | Human review mandatory before export | `src/de_forge/services/review.py`; `src/de_forge/services/export_gate.py`; `src/de_forge/api/routes/exports.py` | `tests/integration/api/test_export_routes.py`; `tests/integration/api/test_review_product_route.py` | implemented | high | Keep export route hard-gated. |
| R-INV-08 | Bounded agent loops | `src/de_forge/core/config.py`; `src/de_forge/services/orchestrator.py`; `src/de_forge/agents/*.py` | `tests/unit/core/test_runtime_product_settings.py`; `tests/integration/services/test_orchestrator_product_path.py`; `tests/unit/agents/test_agent_contracts.py` | implemented | low | Bounded static/dynamic refinement defaults are asserted; rerun gates after loop-policy changes. |
| R-INV-09 | Feedback creates regression protection | `src/de_forge/services/feedback_learning.py`; `src/de_forge/services/regression.py`; `src/de_forge/schemas/regression.py` | `tests/unit/services/test_feedback_regression.py` | implemented | high | Keep regression gate before future candidate acceptance. |
| R-INV-10 | Full lineage and auditability | `src/de_forge/models/artifact.py`; `src/de_forge/models/agent_run.py`; `src/de_forge/services/product_artifacts.py`; `src/de_forge/services/agent_audit.py`; `src/de_forge/services/ops_repository.py` | `tests/integration/services/test_orchestrator_product_path.py`; `tests/integration/api/test_ops_routes.py`; `tests/integration/db/test_artifact_graph_persistence.py` | implemented | high | Keep lineage spanning artifacts, agents, run ops, and export gate. |

## Completion criteria for the matrix

- Every requirement ID from the inventory appears exactly once.
- Status is set per the rubric.
- `implemented` rows cite both code and test evidence.
- `partial`/`drifted` rows include a `Doc Action`.
- No row is empty.

## Summary

Current evidence indicates the repository is substantially beyond the stale skeleton-only claim. Full repository quality gates passed after the alignment package: 127 pytest tests passed with 93% coverage, mypy passed, ruff check passed, and ruff format check passed. The remaining release-level caution is manual runtime/UI smoke coverage before declaring UI/runtime release completion.

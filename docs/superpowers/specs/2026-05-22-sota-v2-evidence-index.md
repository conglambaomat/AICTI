# SOTA Core v2 Evidence Index (Read-Only)

Date: 2026-05-23
Scope: Read-only catalog of code and test evidence anchors used by the traceability matrix.

## Collection Status

`python -m pytest --collect-only -q` completed successfully.

Summary:

- 127 tests collected.
- Pytest root: `E:\Khoaluanfinal\ai-threat-detection`.
- Config: `pyproject.toml`.
- No collection errors observed.

## Source modules (src/de_forge)

```text
src/de_forge/__init__.py
src/de_forge/agents/attack_mapping_agent.py
src/de_forge/agents/base.py
src/de_forge/agents/critic_agent.py
src/de_forge/agents/detection_spec_agent.py
src/de_forge/agents/evidence_agent.py
src/de_forge/api/router.py
src/de_forge/api/routes/exports.py
src/de_forge/api/routes/metrics.py
src/de_forge/api/routes/reports.py
src/de_forge/api/routes/review.py
src/de_forge/api/routes/runs.py
src/de_forge/api/routes/ui.py
src/de_forge/cli.py
src/de_forge/core/config.py
src/de_forge/core/constants.py
src/de_forge/core/errors.py
src/de_forge/core/hashing.py
src/de_forge/core/idempotency.py
src/de_forge/db/base.py
src/de_forge/db/session.py
src/de_forge/main.py
src/de_forge/models/agent_run.py
src/de_forge/models/artifact.py
src/de_forge/models/evidence_graph.py
src/de_forge/models/run_record.py
src/de_forge/schemas/agent_io.py
src/de_forge/schemas/artifact.py
src/de_forge/schemas/attack_detection.py
src/de_forge/schemas/detection_ast.py
src/de_forge/schemas/detection_spec.py
src/de_forge/schemas/evidence_graph.py
src/de_forge/schemas/export.py
src/de_forge/schemas/feedback.py
src/de_forge/schemas/ingestion.py
src/de_forge/schemas/ops.py
src/de_forge/schemas/oracle.py
src/de_forge/schemas/proof_obligation.py
src/de_forge/schemas/regression.py
src/de_forge/schemas/report.py
src/de_forge/schemas/review.py
src/de_forge/schemas/rule_candidate.py
src/de_forge/schemas/run.py
src/de_forge/schemas/sigma.py
src/de_forge/schemas/telemetry.py
src/de_forge/schemas/test_event.py
src/de_forge/services/adversarial_validation.py
src/de_forge/services/agent_audit.py
src/de_forge/services/artifact_store.py
src/de_forge/services/attack_detection_registry.py
src/de_forge/services/broad_rule_detector.py
src/de_forge/services/chunking.py
src/de_forge/services/citation_verifier.py
src/de_forge/services/counterfactual_evaluation.py
src/de_forge/services/detection_ast_service.py
src/de_forge/services/detection_spec_verifier.py
src/de_forge/services/dynamic_validation.py
src/de_forge/services/evidence_graph.py
src/de_forge/services/export_gate.py
src/de_forge/services/feedback_learning.py
src/de_forge/services/gates.py
src/de_forge/services/graph_builder.py
src/de_forge/services/ingestion.py
src/de_forge/services/llm_client.py
src/de_forge/services/local_server.py
src/de_forge/services/metrics.py
src/de_forge/services/ops_repository.py
src/de_forge/services/oracle_evaluation.py
src/de_forge/services/orchestrator.py
src/de_forge/services/portfolio_service.py
src/de_forge/services/process_manager.py
src/de_forge/services/product_artifacts.py
src/de_forge/services/prompt_registry.py
src/de_forge/services/proof_obligation_service.py
src/de_forge/services/readiness.py
src/de_forge/services/regression.py
src/de_forge/services/review.py
src/de_forge/services/run_repository.py
src/de_forge/services/runtime_config.py
src/de_forge/services/runtime_database.py
src/de_forge/services/sigma_compiler.py
src/de_forge/services/sigma_validator.py
src/de_forge/services/state_machine.py
src/de_forge/services/static_validation.py
src/de_forge/services/telemetry_registry.py
src/de_forge/testing/fake_llm.py
src/de_forge/ui_support/review_view.py
```

## Test files

```text
tests/integration/agents/test_agent_audit.py
tests/integration/api/test_api_routes.py
tests/integration/api/test_export_routes.py
tests/integration/api/test_ops_routes.py
tests/integration/api/test_readiness.py
tests/integration/api/test_report_upload_routes.py
tests/integration/api/test_review_product_route.py
tests/integration/api/test_runtime_ui_routes.py
tests/integration/db/test_artifact_graph_persistence.py
tests/integration/db/test_run_repository.py
tests/integration/services/test_graph_builder.py
tests/integration/services/test_orchestrator_golden_path.py
tests/integration/services/test_orchestrator_product_path.py
tests/integration/services/test_orchestrator_vertical_slice.py
tests/unit/agents/test_agent_contracts.py
tests/unit/agents/test_fake_llm_contract.py
tests/unit/core/test_artifact_schema.py
tests/unit/core/test_hashing_idempotency.py
tests/unit/core/test_profile_thresholds.py
tests/unit/core/test_runtime_product_settings.py
tests/unit/services/test_attack_telemetry_registry.py
tests/unit/services/test_chunking_citation.py
tests/unit/services/test_detection_ast.py
tests/unit/services/test_detection_spec_verifier.py
tests/unit/services/test_dynamic_validation.py
tests/unit/services/test_feedback_regression.py
tests/unit/services/test_ingestion.py
tests/unit/services/test_llm_client.py
tests/unit/services/test_local_server.py
tests/unit/services/test_metrics.py
tests/unit/services/test_oracle_evaluation.py
tests/unit/services/test_process_manager.py
tests/unit/services/test_product_artifacts.py
tests/unit/services/test_proof_obligations.py
tests/unit/services/test_review_service.py
tests/unit/services/test_runtime_config.py
tests/unit/services/test_runtime_database.py
tests/unit/services/test_sigma_compiler.py
tests/unit/services/test_state_machine_gates.py
tests/unit/services/test_static_validation.py
tests/unit/test_cli.py
tests/unit/ui_support/test_review_view.py
```

## Symbol anchors (high-signal, read-only)

### Foundation anchors

- `src/de_forge/core/hashing.py` — `canonical_json`, `snapshot_hash`, `verify_snapshot_hash`.
- `src/de_forge/core/idempotency.py` — `make_idempotency_key`.
- `src/de_forge/core/errors.py` — `DeForgeError`, `ValidationGateError`, `CitationVerificationError`, `ProofObligationError`.
- `src/de_forge/db/base.py` — `Base`.
- `src/de_forge/db/session.py` — runtime engine/session helpers.
- `src/de_forge/models/artifact.py` — `Artifact`.
- `src/de_forge/models/evidence_graph.py` — `GraphNode`, `GraphEdge`.
- `src/de_forge/services/artifact_store.py` — `ArtifactStore`.
- `src/de_forge/services/evidence_graph.py` — `EvidenceGraphService`.
- `src/de_forge/services/chunking.py` — `TextChunk`, `chunk_text`.
- `src/de_forge/services/citation_verifier.py` — `verify_quote_span`.
- `src/de_forge/services/attack_detection_registry.py` — `AttackDetectionRegistry`.
- `src/de_forge/services/telemetry_registry.py` — `TelemetryRegistry`.
- `src/de_forge/services/detection_spec_verifier.py` — `DetectionSpecVerifier`.
- `src/de_forge/services/proof_obligation_service.py` — `ProofObligationService`.
- `src/de_forge/services/graph_builder.py` — `GraphBuildResult`, `GraphBuilder`.
- `src/de_forge/services/product_artifacts.py` — `ProductArtifactService`.

### Compiler anchors

- `src/de_forge/schemas/detection_ast.py` — typed Detection AST schema.
- `src/de_forge/schemas/sigma.py` — typed Sigma schema.
- `src/de_forge/services/detection_ast_service.py` — `DetectionAstService`.
- `src/de_forge/services/sigma_compiler.py` — `SigmaCompiler`.
- `src/de_forge/services/sigma_validator.py` — `SigmaValidator`.

### Validation, oracle, and regression anchors

- `src/de_forge/schemas/rule_candidate.py` — rule candidate and score schemas.
- `src/de_forge/schemas/test_event.py` — `TestEvent`, dynamic validation result schema.
- `src/de_forge/schemas/oracle.py` — oracle case/result schemas.
- `src/de_forge/schemas/feedback.py` — review feedback schema.
- `src/de_forge/schemas/regression.py` — regression schema.
- `src/de_forge/services/portfolio_service.py` — `PortfolioService`.
- `src/de_forge/services/static_validation.py` — `StaticValidationService`.
- `src/de_forge/services/broad_rule_detector.py` — `BroadRuleDetector`.
- `src/de_forge/services/dynamic_validation.py` — `DynamicValidationService`.
- `src/de_forge/services/adversarial_validation.py` — `AdversarialValidationService`.
- `src/de_forge/services/counterfactual_evaluation.py` — `CounterfactualEvaluationService`.
- `src/de_forge/services/oracle_evaluation.py` — `OracleEvaluationService`.
- `src/de_forge/services/feedback_learning.py` — `FeedbackLearningService`.
- `src/de_forge/services/regression.py` — `RegressionService`.

### Controlled agents anchors

- `src/de_forge/schemas/agent_io.py` — agent IO envelope and citation schemas.
- `src/de_forge/services/prompt_registry.py` — `PromptDefinition`, `PromptRegistry`.
- `src/de_forge/services/llm_client.py` — `LlmRequest`, `LlmResponse`, `LlmClient`.
- `src/de_forge/models/agent_run.py` — `AgentRun`.
- `src/de_forge/services/agent_audit.py` — `AgentAuditService`.
- `src/de_forge/agents/base.py` — `BaseAgent`.
- `src/de_forge/agents/evidence_agent.py` — `EvidenceAgent`.
- `src/de_forge/agents/attack_mapping_agent.py` — `AttackMappingAgent`.
- `src/de_forge/agents/detection_spec_agent.py` — `DetectionSpecAgent`.
- `src/de_forge/agents/critic_agent.py` — `CriticAgent`.
- `src/de_forge/testing/fake_llm.py` — fake LLM contract support.

### Orchestrator, API, UI, and runtime anchors

- `src/de_forge/schemas/run.py` — run state/mode schemas.
- `src/de_forge/schemas/review.py` — review schemas.
- `src/de_forge/schemas/export.py` — export response schema.
- `src/de_forge/schemas/ops.py` — runtime ops schemas.
- `src/de_forge/services/state_machine.py` — `StateMachine`.
- `src/de_forge/services/gates.py` — `can_generate_rule`, `can_enter_final_review`.
- `src/de_forge/services/orchestrator.py` — `Orchestrator`.
- `src/de_forge/services/review.py` — `ReviewService`.
- `src/de_forge/services/export_gate.py` — `ExportGateService`.
- `src/de_forge/services/run_repository.py` — `RunRepository`.
- `src/de_forge/services/ops_repository.py` — `OpsRepository`.
- `src/de_forge/services/metrics.py` — `MetricsService`.
- `src/de_forge/services/readiness.py` — `check_readiness`.
- `src/de_forge/services/local_server.py` — `LocalServerRunner`, `UvicornServerRunner`, `start_local_server`.
- `src/de_forge/services/process_manager.py` — `ProcessManager`, `SystemProcessManager`, `assert_port_free`, `replace_process_on_port`.
- `src/de_forge/services/runtime_config.py` — `LocalProductionConfig`, `validate_local_production_config`.
- `src/de_forge/services/runtime_database.py` — `normalize_database_url`, `initialize_runtime_database`, `verify_database_ready`.
- `src/de_forge/api/router.py` — aggregate API router.
- `src/de_forge/api/routes/runs.py` — run inspection/start routes.
- `src/de_forge/api/routes/reports.py` — report upload route.
- `src/de_forge/api/routes/review.py` — review submission route.
- `src/de_forge/api/routes/exports.py` — export route.
- `src/de_forge/api/routes/metrics.py` — metrics quality/history routes.
- `src/de_forge/api/routes/ui.py` — review, evidence graph, dashboard HTML routes.
- `src/de_forge/ui_support/review_view.py` — review/dashboard view helpers.

## Test anchors per area

### Foundation

- `tests/unit/core/test_hashing_idempotency.py`
- `tests/unit/core/test_artifact_schema.py`
- `tests/unit/services/test_chunking_citation.py`
- `tests/unit/services/test_attack_telemetry_registry.py`
- `tests/unit/services/test_detection_spec_verifier.py`
- `tests/unit/services/test_proof_obligations.py`
- `tests/integration/db/test_artifact_graph_persistence.py`
- `tests/integration/db/test_run_repository.py`
- `tests/integration/services/test_graph_builder.py`

### Compiler

- `tests/unit/services/test_detection_ast.py`
- `tests/unit/services/test_sigma_compiler.py`

### Validation, Oracle, Regression

- `tests/unit/services/test_static_validation.py`
- `tests/unit/services/test_dynamic_validation.py`
- `tests/unit/services/test_oracle_evaluation.py`
- `tests/unit/services/test_feedback_regression.py`

### Controlled Agents

- `tests/unit/agents/test_agent_contracts.py`
- `tests/unit/agents/test_fake_llm_contract.py`
- `tests/integration/agents/test_agent_audit.py`
- `tests/integration/services/test_orchestrator_product_path.py`

### Orchestrator, API, UI, Dashboard

- `tests/unit/services/test_state_machine_gates.py`
- `tests/unit/services/test_review_service.py`
- `tests/unit/services/test_metrics.py`
- `tests/unit/services/test_local_server.py`
- `tests/unit/services/test_process_manager.py`
- `tests/unit/services/test_runtime_config.py`
- `tests/unit/services/test_runtime_database.py`
- `tests/integration/services/test_orchestrator_golden_path.py`
- `tests/integration/services/test_orchestrator_vertical_slice.py`
- `tests/integration/api/test_api_routes.py`
- `tests/integration/api/test_export_routes.py`
- `tests/integration/api/test_ops_routes.py`
- `tests/integration/api/test_readiness.py`
- `tests/integration/api/test_report_upload_routes.py`
- `tests/integration/api/test_review_product_route.py`
- `tests/integration/api/test_runtime_ui_routes.py`
- `tests/unit/ui_support/test_review_view.py`

## Notable collected tests by invariant

- No raw-report-to-rule transition: `tests/unit/services/test_state_machine_gates.py::test_state_machine_rejects_raw_report_to_rule_candidate_transition`.
- DetectionSpec-first rule generation: `tests/unit/services/test_state_machine_gates.py::test_can_generate_rule_requires_verified_detection_spec` and `tests/unit/services/test_detection_ast.py::test_detection_ast_service_converts_verified_spec_to_ast`.
- Citation exactness: `tests/unit/services/test_chunking_citation.py::test_verify_quote_span_rejects_wrong_offsets` and `tests/integration/services/test_graph_builder.py::test_graph_builder_rejects_mismatched_evidence_quote`.
- Proof obligation blocking: `tests/unit/services/test_proof_obligations.py::test_candidate_cannot_be_selected_with_unknown_required_obligation`.
- Human review before export: `tests/integration/api/test_export_routes.py::test_export_route_rejects_run_before_approval` and `tests/integration/api/test_export_routes.py::test_export_route_creates_export_artifact_when_all_gates_pass`.
- Feedback regression protection: `tests/unit/services/test_feedback_regression.py::test_regression_service_blocks_rejected_pattern`.
- Lineage and auditability: `tests/integration/services/test_orchestrator_product_path.py::test_product_path_persists_run_agent_audits_and_lineage_artifacts` and `tests/integration/api/test_ops_routes.py::test_get_run_artifacts_returns_lineage_metadata`.

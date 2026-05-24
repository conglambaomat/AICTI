# DE-Forge SOTA Core v2 Quality Gates

Date: 2026-05-21
Purpose: Central pass/fail criteria for implementing DE-Forge SOTA Core v2.

## 1. Universal gates

Every implementation task must satisfy:

1. A failing test is written first.
2. The failing test is run and observed failing for the expected reason.
3. Minimal implementation is added.
4. The targeted test passes.
5. Affected area tests pass.
6. Spec compliance review passes.
7. Code quality review passes.
8. No unrelated files are changed.
9. No architecture invariant is weakened.

A task is not complete until all applicable gates pass.

## 2. Architecture invariant gates

These must remain true at all times:

1. No raw-report-to-production-rule path exists.
2. DetectionSpec is mandatory before rule generation.
3. Evidence citations are exact and verified.
4. ATT&CK modeling uses:

```text
Technique -> Detection Strategy -> Analytic -> Data Component -> Telemetry Source -> Field
```

5. Required proof obligations must be proven before final candidate selection.
6. Detection AST and compiler are the preferred source for Sigma YAML.
7. Human review is mandatory before export.
8. Agent/refinement loops are bounded.
9. Feedback creates regression protection.
10. Full artifact lineage and auditability are preserved.

Any change violating these gates fails immediately.

## 3. Foundation gates

Foundation phase passes only when:

- Stable hashing is deterministic.
- Idempotency keys include stage identifier and canonical payload.
- Artifact lineage includes run id, stage, input hash, output hash, parent artifacts, and creator.
- Evidence graph nodes and edges persist correctly.
- Chunking is deterministic and offset-preserving.
- Citation verifier rejects mismatched quotes or offsets.
- Telemetry registry rejects unknown fields.
- DetectionSpec verifier rejects missing evidence, missing telemetry, unknown fields, and unsupported logic.
- Proof obligation verifier blocks candidates with failed or unknown required obligations.

Required commands:

```bash
pytest tests/unit/core tests/unit/services tests/integration/db -v --cov=src --cov-report=term-missing
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

## 4. Compiler gates

Compiler phase passes only when:

- Verified DetectionSpec converts to Detection AST.
- Detection AST preserves evidence ids.
- Sigma rule is compiled from AST, not hand-written free-form model output.
- Unknown fields are rejected before YAML emission.
- Sigma logsource matches selected telemetry source.
- Sigma condition references valid selections.
- YAML serialization excludes internal provenance but preserves Sigma content.

Required commands:

```bash
pytest tests/unit/services/test_detection_ast.py tests/unit/services/test_sigma_compiler.py -v
pytest tests/unit/services -v
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

## 5. Validation, oracle, and regression gates

This phase passes only when:

- Candidate portfolio schemas track candidate type and score breakdown.
- Static validation rejects structurally invalid or overbroad rules.
- Dynamic validation counts TP, FP, TN, FN and computes precision/recall.
- Adversarial validation produces robustness score.
- Counterfactual evaluation reports condition importance.
- Oracle evaluation checks expected technique, telemetry, positive events, benign must-not-match events, and logic family.
- Feedback rejection creates do-not-repeat regression gates.
- Accepted/rejected regression gates are enforceable.

Required commands:

```bash
pytest tests/unit/services/test_static_validation.py tests/unit/services/test_dynamic_validation.py tests/unit/services/test_oracle_evaluation.py tests/unit/services/test_feedback_regression.py -v
pytest tests/unit/services -v
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

## 6. Controlled agent gates

Agent phase passes only when:

- Agent IO envelope validates metadata, confidence bounds, citations, abstain fields, and artifact ids.
- Prompt registry is versioned.
- LLM client contract returns structured JSON content and token/latency metadata.
- Agent runs are persisted with input/output hashes.
- Base agent wraps LLM response in strict envelope.
- Evidence agent extracts citation objects from evidence quotes.
- Citation-bearing outputs are ready for exact citation verification.
- Agent outputs cannot bypass deterministic validators.

Required commands:

```bash
pytest tests/unit/agents tests/integration/agents -v
pytest tests/ -v
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

## 7. Orchestrator, API, UI, and dashboard gates

This phase passes only when:

- State machine rejects illegal raw-report-to-rule transition.
- Gate predicates block rule generation without verified DetectionSpec.
- Auto mode can reach human review for golden path.
- Cautious mode pauses at DetectionSpec or uncertainty points.
- Human review approval is required for export.
- API routes exist for run and review operations.
- Metrics endpoint exposes quality summary.
- Minimal review UI displays evidence, logic, Sigma condition, proof status, and validation score.

Required commands:

```bash
pytest tests/unit/services/test_state_machine_gates.py tests/unit/services/test_review_service.py tests/unit/services/test_metrics.py tests/integration/services/test_orchestrator_golden_path.py tests/integration/api/test_api_routes.py -v
pytest tests/ -v --cov=src --cov-report=term-missing
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

Manual UI smoke test when UI changes:

```bash
uvicorn de_forge.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/api/ui/review
```

Expected page content:

- Evidence quote.
- Detection logic.
- Sigma condition.
- Proof status.
- Validation score.

## 8. Final end-to-end gates

The project is not end-to-end complete until:

1. English TXT report can run through golden path.
2. Evidence quote is verified exactly.
3. Behavior maps to ATT&CK technique.
4. Technique maps to Detection Strategy / Analytic / Data Component.
5. Telemetry fields validate.
6. DetectionSpec verifies.
7. Detection AST compiles to Sigma.
8. Candidate passes static validation.
9. Proof obligations are proven.
10. Human review approves final candidate.
11. Feedback can create regression protection.
12. Full audit trail exists for report -> evidence -> graph -> spec -> AST -> Sigma -> validation -> proof -> review.

## 9. Failure policy

A gate failure means:

- Do not claim completion.
- Do not bypass or weaken the gate.
- Fix the underlying issue if within the active plan.
- Escalate if fixing requires scope/architecture changes.

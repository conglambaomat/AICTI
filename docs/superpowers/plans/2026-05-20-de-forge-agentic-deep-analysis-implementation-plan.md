# DE-Forge Agentic Deep-Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a production-minded, no-OCR, RAG-first agentic upgrade that enables deep report analysis and high-quality rule generation with strict deterministic gates.

**Architecture:** Add real LLM-backed agents for evidence/ATT&CK/spec/rule stages, hybrid retrieval for grounding, and hard gates for schema, citation faithfulness, quality, and operations. Keep bounded refinement loops and mandatory human review.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, OpenAI-compatible API, pytest, mypy, ruff.

---

## Phase 0: Foundation and Contracts

### Task 1: Add new schema and prompt contract documents
**Files:**
- Create: `docs/schemas/evidence-output-contract.md`
- Create: `docs/schemas/attack-mapping-output-contract.md`
- Create: `docs/schemas/retrieval-faithfulness-contract.md`
- Create: `docs/prompts/agentic-deep-analysis-prompts.md`

- [ ] **Step 1: Write failing contract validation tests**
Add tests expecting strict keys for evidence, mapping, spec, rule outputs.

- [ ] **Step 2: Run tests to verify they fail**
Run: `python3 -m pytest tests/unit/services/test_agent_contracts.py -v`
Expected: FAIL due to missing contract validator module.

- [ ] **Step 3: Implement minimal contract validator scaffolding**
Create validator hooks to parse and validate required keys.

- [ ] **Step 4: Re-run targeted tests**
Run: `python3 -m pytest tests/unit/services/test_agent_contracts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**
Run:
```bash
git add docs/schemas docs/prompts tests/unit/services/test_agent_contracts.py src/de_forge/services

git commit -m "feat(contracts): add agentic deep-analysis output contracts"
```

### Task 2: Add configuration and constants for profile-driven gates
**Files:**
- Modify: `src/de_forge/core/config.py`
- Modify: `src/de_forge/core/constants.py`
- Modify: `.env.example`

- [ ] **Step 1: Write failing unit tests for profile thresholds and budget loading**
- [ ] **Step 2: Run failing tests**
Run: `python3 -m pytest tests/unit/core/test_profile_thresholds.py -v`
- [ ] **Step 3: Add strict/balanced/exploratory threshold config structures**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

## Phase 1: LLM Infrastructure and Retrieval

### Task 3: Implement unified LLM client service
**Files:**
- Create: `src/de_forge/services/llm_client.py`
- Create: `tests/integration/services/test_llm_client.py`

- [ ] **Step 1: Write failing integration tests for request/response parse, timeout, retry behavior**
- [ ] **Step 2: Run failing tests**
Run: `python3 -m pytest tests/integration/services/test_llm_client.py -v`
- [ ] **Step 3: Implement minimal client with typed request/response and retry policy**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 4: Implement retrieval service (hybrid skeleton)
**Files:**
- Create: `src/de_forge/services/retrieval.py`
- Create: `tests/integration/services/test_retrieval_service.py`

- [ ] **Step 1: Write failing tests for indexing, retrieval ordering, and deterministic behavior**
- [ ] **Step 2: Run failing tests**
Run: `python3 -m pytest tests/integration/services/test_retrieval_service.py -v`
- [ ] **Step 3: Implement sparse+dense score container and deterministic fusion/rerank stubs**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 5: Add retrieval faithfulness validator
**Files:**
- Modify: `src/de_forge/services/static_validation.py`
- Create: `tests/integration/services/test_retrieval_faithfulness.py`

- [ ] **Step 1: Write failing tests for citation mismatch and unsupported claim rejection**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement faithfulness checks as hard gate**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

## Phase 2: Agent Implementations (Evidence, ATT&CK, DetectionSpec)

### Task 6: Upgrade evidence service to LLM+retrieval grounded extraction
**Files:**
- Modify: `src/de_forge/services/evidence.py`
- Create: `tests/integration/services/test_evidence_agent.py`

- [ ] **Step 1: Add failing tests for quote-grounded extraction and abstain on weak evidence**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement retrieval query planning, LLM extraction, schema parsing, grounding checks**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 7: Upgrade ATT&CK mapping to confidence-calibrated structured output
**Files:**
- Modify: `src/de_forge/services/attack_mapping.py`
- Create: `tests/integration/services/test_attack_mapping_agent.py`

- [ ] **Step 1: Add failing tests for mapping format, confidence bounds, and abstain behavior**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement LLM mapping with strict schema and evidence linkage**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 8: Upgrade DetectionSpec synthesis with strict branch rules
**Files:**
- Modify: `src/de_forge/services/detection_spec.py`
- Create: `tests/integration/services/test_detection_spec_agent.py`

- [ ] **Step 1: Add failing tests for behavior branch completeness and abstain branch strictness**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement LLM synthesis + deterministic post-validation**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

## Phase 3: Rule Authoring, Validation, and Refinement

### Task 9: Upgrade rule generation and versioned refinement
**Files:**
- Modify: `src/de_forge/services/rule_generation.py`
- Create: `tests/integration/services/test_rule_authoring_agent.py`

- [ ] **Step 1: Add failing tests for field/operator constraints and immutable versions**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement LLM-driven rule authoring constrained by DetectionSpec**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 10: Strengthen bounded refinement controller
**Files:**
- Modify: `src/de_forge/services/refinement.py`
- Create: `tests/integration/services/test_refinement_loop.py`

- [ ] **Step 1: Add failing tests for plateau stop and deterministic abort package**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement bounded loop with early-stop and abstain fallback**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

## Phase 4: KPI Hard Gates and Operations Safety

### Task 11: Implement KPI evaluator for quality/abstain/faithfulness/cost-latency
**Files:**
- Create: `src/de_forge/services/kpi_evaluator.py`
- Create: `tests/integration/services/test_kpi_evaluator.py`

- [ ] **Step 1: Add failing tests for profile-specific pass/fail logic**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement evaluator and profile threshold checks**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 12: Add canary + rollback policy hooks
**Files:**
- Create: `src/de_forge/services/canary_ops.py`
- Create: `tests/integration/services/test_canary_rollback.py`

- [ ] **Step 1: Add failing tests for rollback trigger conditions**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement canary decision and rollback trigger logic**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

## Phase 5: Orchestrator Integration and End-to-End Proof

### Task 13: Integrate upgraded services into orchestrator
**Files:**
- Modify: `src/de_forge/services/orchestrator.py`
- Modify: `src/de_forge/api/routes/pipeline.py`
- Create: `tests/e2e/test_agentic_pipeline_profiles.py`

- [ ] **Step 1: Add failing e2e tests for strict/balanced/exploratory runs**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Integrate retrieval + agents + KPI gate + review gate transitions**
- [ ] **Step 4: Re-run tests**
- [ ] **Step 5: Commit**

### Task 14: Verify deterministic replay and full quality gates
**Files:**
- Modify: `tests/e2e/test_pipeline_e2e.py`
- Create: `tests/e2e/test_canary_rollback_triggers.py`

- [ ] **Step 1: Add failing tests for deterministic replay plus canary regression handling**
- [ ] **Step 2: Run failing tests**
- [ ] **Step 3: Implement missing integration glue**
- [ ] **Step 4: Re-run full verification suite**
Run:
```bash
python3 -m pytest tests/ -v --cov=src --cov-report=term-missing
python3 -m mypy src/
python3 -m ruff check src/
python3 -m ruff format --check src/
```
- [ ] **Step 5: Commit**

## Final Definition of Done
- [ ] Evidence/ATT&CK/DetectionSpec/Rule stages use real LLM calls.
- [ ] Retrieval grounding is active and citation faithfulness is hard-gated.
- [ ] Profile-specific KPI thresholds are enforced.
- [ ] Abstain quality metrics are tracked and gated.
- [ ] Cost/latency thresholds are tracked and gated.
- [ ] Canary + rollback hooks exist and pass tests.
- [ ] Full verification commands pass.

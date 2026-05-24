# Module Traceability Matrix

Date: 2026-05-20
Scope: Map requirements → modules → tests → KPIs for agentic deep-analysis upgrade

## 1. Purpose
Ensure every requirement is implemented, tested, and measured.

## 2. Matrix

| Requirement ID | Requirement | Module(s) | Test(s) | KPI(s) | Status |
|---|---|---|---|---|---|
| REQ-001 | Evidence extraction with LLM | `src/de_forge/services/evidence.py` (upgrade existing with LLM-backed extraction) | `tests/integration/services/test_evidence_agent.py` | Evidence Recall@5 ≥ 0.85 | Not Started |
| REQ-002 | ATT&CK mapping with semantic reasoning | `src/de_forge/services/attack_mapper.py` (new service or upgrade existing) | `tests/integration/services/test_attack_mapping_agent.py` | ATT&CK Precision ≥ 0.90 | Not Started |
| REQ-003 | Hybrid retrieval (BM25+dense+RRF) | `src/de_forge/services/retrieval.py`, `src/de_forge/core/chunking.py`, `src/de_forge/core/embeddings.py`, `src/de_forge/core/fusion.py` | `tests/integration/services/test_retrieval_service.py`, `tests/unit/core/test_chunking.py`, `tests/unit/core/test_fusion.py` | Retrieval Recall@5 ≥ 0.85, Citation Accuracy = 1.0 | Not Started |
| REQ-004 | DetectionSpec synthesis with grounding | `src/de_forge/services/detection_spec.py` (new service) | `tests/integration/services/test_detection_spec_agent.py` | Spec Completeness ≥ 0.95 | Not Started |
| REQ-005 | Sigma rule generation and refinement | `src/de_forge/services/rule_generator.py` (upgrade existing), `src/de_forge/services/orchestrator.py` (refinement loop) | `tests/integration/services/test_rule_agent.py`, `tests/integration/services/test_rule_refiner_agent.py` | Rule Precision ≥ 0.85, Rule Recall ≥ 0.80 | Not Started |
| REQ-006 | Abstain policy enforcement | `src/de_forge/services/orchestrator.py` | `tests/integration/services/test_orchestrator.py` | Abstain Precision ≥ 0.90, Abstain Coverage ≥ 0.85 | Implemented (MVP) |
| REQ-007 | Bounded refinement loops | `src/de_forge/services/orchestrator.py` | `tests/integration/services/test_orchestrator.py` | Token budget by profile | Implemented (MVP) |
| REQ-008 | Static validation gates | `src/de_forge/services/static_validation.py` | `tests/integration/services/test_static_validation.py` | Static pass rate ≥ 0.95 | Implemented (MVP) |
| REQ-009 | Dynamic synthetic validation | `src/de_forge/services/dynamic_validation.py` | `tests/integration/services/test_dynamic_validation.py` | Dynamic pass rate ≥ 0.90 | Implemented (MVP) |
| REQ-010 | LLM client retry/timeout/schema contract | `src/de_forge/services/llm_client.py` | `tests/integration/services/test_llm_client.py` | p95 latency <= stage timeout, error rate <= 1% | Not Started |
| REQ-011 | Token accounting and budget gates | `src/de_forge/services/llm_client.py`, `src/de_forge/services/orchestrator.py` | `tests/integration/services/test_llm_client.py`, `tests/integration/services/test_orchestrator.py` | Tokens/report within profile budgets | Not Started |

## 3. Coverage Rules
- Every requirement must map to module(s), test(s), and KPI(s).
- Every module added for deep-analysis must trace back to at least one REQ.
- Every KPI threshold must exist in `docs/implementation/kpi-threshold-matrix.md`.

## 4. Status Definitions
- Not Started
- In Progress
- Implemented
- Validated
- Blocked

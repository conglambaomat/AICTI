# DE-Forge Agentic Deep-Analysis Design Spec (No-OCR, RAG-First)

Date: 2026-05-20
Status: Draft for implementation handoff
Approach: Contract-first, retrieval-grounded, bounded multi-agent orchestration

## 1. Goal
Upgrade DE-Forge from MVP scaffolding into a production-minded agentic system that can analyze report text deeply, preserve evidence traceability, and generate high-quality detection rules with strict safety gates.

Scope for this upgrade excludes OCR. Input sources are TXT and text-extractable PDF only.

## 2. Non-Negotiable Invariants
1. DetectionSpec is mandatory before rule generation.
2. No raw-report-to-rule bypass path is allowed.
3. All major claims in downstream artifacts must be evidence-cited.
4. Agent outputs must conform to strict JSON schemas.
5. Bounded refinement loops are mandatory.
6. Human review remains mandatory before export.
7. Single provider/model policy remains active unless user changes it.

## 3. Architecture Upgrade Summary
Target flow:
1. Ingest report (TXT/PDF text)
2. Normalize + chunk + persist lineage
3. Hybrid retrieval (sparse + dense + rerank)
4. Evidence Agent (retrieval-grounded extraction)
5. ATT&CK Mapping Agent
6. DetectionSpec Agent
7. Rule Authoring Agent
8. Static Validation
9. Dynamic Validation
10. Verifier/Refiner loop (bounded)
11. Human review gate
12. Export assertion gate

## 4. Agent Set and Contracts
### A1 Evidence Agent
Input: report_id, top retrieval chunks, profile
Output schema: evidence spans with quote, chunk_id, offsets, behavior label, confidence, rationale
Hard constraints:
- no claim without quote
- no quote without chunk reference
- abstain when insufficient evidence

### A2 ATT&CK Mapping Agent
Input: normalized evidence set
Output schema: technique mappings (top-k), confidence, evidence references, abstain fields
Hard constraints:
- ATT&CK ID format validation
- no mapping without linked evidence

### A3 DetectionSpec Agent
Input: evidence + ATT&CK + telemetry constraints
Output schema: strict DetectionSpec (behavior rule or abstain branch)
Hard constraints:
- behavior spec requires complete evidence/attack/telemetry/test-plan fields
- abstain branch requires structured abstain code/context

### A4 Rule Authoring/Refiner Agent
Input: validated DetectionSpec + validation feedback
Output schema: Sigma rule payload + metadata + optional refinement delta
Hard constraints:
- only allowed telemetry fields/operators
- no speculative logic outside DetectionSpec
- immutable versioning

## 5. Retrieval Architecture (No-OCR)
### Indexing
- Persist deterministic chunks with offsets and token counts.
- Build dual index:
  - Sparse lexical index for exact phrase behavior
  - Dense embedding index for semantic retrieval

### Querying
- Planner emits retrieval queries from stage intent.
- Hybrid score fusion (e.g., RRF) combines sparse + dense candidates.
- Reranker reorders top-k before agent consumption.

### Retrieval Faithfulness Guarantees
- Every agent claim must point to retrieved chunk IDs.
- Citation mismatch is a hard validation failure.

## 6. Deterministic Gate Design
### Schema Gate
Validate each agent output against strict JSON schema.

### Grounding Gate
Validate that claims are backed by retrieved evidence and valid offsets.

### State Gate
Validate canonical transition preconditions before stage advancement.

### Quality Gate
Validate static/dynamic detection quality against profile thresholds.

## 7. Abstain Policy
Abstain is a first-class valid outcome, not an error path.

Required structured fields:
- abstain_code
- abstain_context
- human_message

Primary codes:
- NO_EVIDENCE_BACKED_BEHAVIOR
- NO_TELEMETRY_SUPPORT
- ONLY_CVE_WITHOUT_OBSERVABLES
- ONLY_TOOL_OR_MALWARE_NAME_NO_BEHAVIOR
- OVERBROAD_AFTER_BOUNDED_REFINEMENT
- CONTRACT_VALIDATION_EXHAUSTED

## 8. Risk Profiles
### Strict
Use for high-risk detections. Prioritize precision and low FP, tolerate higher abstain.

### Balanced
Use for normal production rollout. Balance precision/recall and operational cost.

### Exploratory
Use for analyst exploration. Higher recall tolerated with stronger review burden.

## 9. KPI Framework (Hard Gates)
### Quality
- static_validity_rate
- dynamic_precision
- dynamic_recall
- dynamic_f1
- overbroad_rule_rate

### Abstain Quality
- abstain_precision
- abstain_coverage
- abstain_abuse_guard (coverage cannot inflate while quality degrades)

### Retrieval Faithfulness
- claim_supported_rate
- citation_mismatch_rate
- provenance_completeness_rate

### Cost/Latency
- tokens_per_report
- seconds_per_report
- cost_per_report
- p95_stage_latency

### Operations
- reviewer_acceptance_rate
- mttd_regression
- mttr_rollback

## 10. Persistence and Audit Enhancements
Persist per-stage:
- input snapshot hash
- output snapshot hash
- prompt version id
- model id
- retrieval set hash
- token/cost/latency metrics

Any hash mismatch on read is treated as integrity failure.

## 11. Canary and Rollback Policy
Rollout new agentic stack via canary subset before broad enablement.

Rollback triggers:
- FP spike above profile threshold
- citation mismatch spike above threshold
- reviewer reject spike above threshold
- sustained cost/latency budget breach

## 12. Out of Scope
- OCR and scanned image extraction
- automatic production SIEM deployment
- replacing human detection engineering judgment

## 13. Definition of Done for This Upgrade
Done when all are true:
1. Real LLM-backed agent calls are active for Evidence, ATT&CK, DetectionSpec, Rule stages.
2. Hybrid retrieval is active and feeding agents with traceable citations.
3. All stage gates (schema, grounding, state, quality) are enforced.
4. Profile-specific KPI thresholds are configured and tested.
5. Abstain quality metrics are implemented and reported.
6. Canary + rollback runbook is operational.
7. Full verification passes (tests/type/lint/format).

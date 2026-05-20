# 04 - Architecture Decisions

## ADR-001: DetectionSpec is mandatory

### Decision
All detection rules must be generated from DetectionSpec, not directly from raw threat report text.

### Rationale
Threat reports are unstructured and often ambiguous. Direct LLM-to-rule generation can hallucinate fields, log sources, ATT&CK mappings, or unsupported detection logic.

DetectionSpec provides a controlled intermediate representation containing:
- report evidence
- ATT&CK mapping
- telemetry requirements
- allowed fields
- detection logic
- false positive hypotheses
- test plan
- abstain reason

### Consequence
Rule generation is more reliable, inspectable, testable, and benchmarkable.

---

## ADR-002: Sigma is the primary rule format for MVP

### Decision
The MVP generates Sigma rules first.

### Rationale
Sigma is backend-neutral, human-readable, and suitable for detection-as-code workflows. It can later be converted to Splunk, Elastic, Sentinel, or other backends.

### Deferred
Direct Wazuh XML, Suricata, YARA, and Splunk SPL generation are deferred unless required by benchmark mode.

---

## ADR-003: Controlled multi-agent workflow

### Decision
Use a controlled multi-agent workflow with typed inputs and outputs.

MVP agents:
1. CTI Evidence Agent
2. ATT&CK Mapping Agent
3. Telemetry Scout Agent
4. Detection Architect Agent
5. Rule Writer Agent
6. Rule Reviewer Agent
7. Rule Refiner Agent

### Rationale
Detection engineering is multi-role by nature. Separating roles improves traceability, debugging, and evaluation.

### Constraint
Agents do not freely debate. The orchestrator controls execution.

---

## ADR-004: Deterministic validators are required

### Decision
LLMs are not trusted as validators.

The system must use deterministic validation for:
- JSON schema
- YAML parsing
- Sigma structure
- ATT&CK ID validity
- telemetry field validity
- evidence span existence
- broad-rule detection

### Rationale
LLM self-evaluation is unreliable for production-like detection engineering.

---

## ADR-005: Refinement loop is bounded

### Decision
The rule refinement loop is bounded.

Defaults:
- max_static_refinement_iterations = 3
- max_dynamic_refinement_iterations = 2

### Rationale
Unbounded agent loops are expensive, hard to debug, and may degrade output quality.

### Failure handling
If the rule still fails after the maximum iterations, transition to `FAILED_VALIDATION` and escalate with a human-review context package.
Canonical source: `docs/architecture/08-canonical-retry-state.md`.

---

## ADR-006: The system must support abstain

### Decision
The system must be able to refuse rule generation.

### Abstain conditions
Abstain when:
- no evidence quote exists
- no detectable behavior is present
- only a CVE is mentioned without exploit behavior
- only a malware/tool name is mentioned without procedure
- required telemetry is unavailable
- generated logic would be too broad

### Rationale
Abstention is safer than hallucinated detection rules.

---

## ADR-007: Benchmark mode must remain compatible with CTI-REALM

### Decision
The project must include benchmark mode that can output CTI-REALM-compatible final JSON:

```json
{
  "sigma_rule": "...",
  "kql_query": "...",
  "query_results": []
}
```

### Rationale
The project aims to compare against CTI-REALM using the same dataset and scoring framework.

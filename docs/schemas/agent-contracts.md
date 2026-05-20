# Agent Contracts

## Purpose
Define strict JSON input/output schemas for each agent to enforce contract-based handoff and prevent semantic drift.

## Canonical references
- Retry/state policy: `docs/architecture/08-canonical-retry-state.md`
- Machine-readable envelope: `docs/schemas/json-schemas/AgentIO.schema.json`
- DetectionSpec schema: `docs/schemas/json-schemas/DetectionSpec.schema.json`

## Common envelope (all agents)
Each agent output must be wrapped in a canonical envelope:
- `agent_name`
- `run_id`
- `trace_id`
- `status` (`success|abstain|failed`)
- `error` (if failed)
- `retry` metadata (`attempt`, `max_attempts`, `policy`)
- `output`

## A1. Objective Decomposer

### Input
```json
{
  "detection_objective": "string (user-provided or report title)",
  "report_context": "string (optional preview/summary)"
}
```

### Output
```json
{
  "likely_platform": "string (windows/linux/cloud/aks/macos/unknown)",
  "likely_tactics": ["array of tactic names"],
  "likely_techniques": ["array of technique IDs if obvious from objective"],
  "search_terms": ["array of keywords for CTI/ATT&CK search"],
  "required_analysis": ["array: cti/mitre/telemetry/rule"]
}
```

### Validation
- `likely_platform` must be one of allowed values.
- `search_terms` must be non-empty.

---

## A2. CTI Evidence Agent

### Input
```json
{
  "report_id": "string",
  "chunks": [
    {
      "chunk_id": "string",
      "text": "string",
      "char_start": "integer",
      "char_end": "integer"
    }
  ]
}
```

### Output
```json
{
  "procedures": [
    {
      "behavior": "string",
      "evidence_quote": "string",
      "chunk_id": "string",
      "char_start": "integer",
      "char_end": "integer",
      "confidence": "float [0.0-1.0]"
    }
  ],
  "iocs": [
    {
      "type": "string (ip/domain/hash/url/email/file_path)",
      "value": "string",
      "evidence_quote": "string",
      "chunk_id": "string"
    }
  ],
  "cves": [
    {
      "cve_id": "string",
      "evidence_quote": "string",
      "chunk_id": "string"
    }
  ],
  "tools": [
    {
      "tool_name": "string",
      "evidence_quote": "string",
      "chunk_id": "string"
    }
  ]
}
```

### Validation
- Every `evidence_quote` must be non-empty.
- Every `chunk_id` must reference a valid input chunk.

---

## A3. ATT&CK Mapper Agent

### Input
```json
{
  "evidence": {
    "procedures": ["array from A2 output"],
    "tools": ["array from A2 output"]
  },
  "attack_candidates": [
    {
      "technique_id": "string",
      "technique_name": "string",
      "tactic": "string",
      "description": "string"
    }
  ]
}
```

### Output
```json
{
  "mappings": [
    {
      "technique_id": "string",
      "technique_name": "string",
      "tactic": "string",
      "confidence": "float [0.0-1.0]",
      "mapping_reason": "string (must reference evidence)",
      "evidence_ids": ["array of procedure/tool references"]
    }
  ],
  "abstain": "boolean",
  "abstain_reason": "string or null"
}
```

### Validation
- If `abstain` is true, `abstain_reason` must be non-empty.
- If `abstain` is false, `mappings` must have at least 1 entry.
- Each `mapping_reason` must reference at least one evidence item.

---

## A4. Telemetry Scout Agent

### Input
```json
{
  "attack_mappings": ["array from A3 output"],
  "platform": "string",
  "available_telemetry_sources": [
    {
      "source_id": "string",
      "platform": "string",
      "source": "string",
      "event_id": "string or integer or null",
      "category": "string",
      "fields": ["array of field names"]
    }
  ]
}
```

### Output
```json
{
  "selected_telemetry": [
    {
      "source_id": "string",
      "platform": "string",
      "source": "string",
      "event_id": "string or integer or null",
      "category": "string",
      "fields": ["array of attested field names"],
      "attestation_method": "string (schema_verified/sample_verified/tool_verified)",
      "selection_reason": "string"
    }
  ],
  "abstain": "boolean",
  "abstain_reason": "string or null"
}
```

### Validation
- If `abstain` is true, `abstain_reason` must be non-empty.
- If `abstain` is false, `selected_telemetry` must have at least 1 entry.
- All `fields` arrays must be non-empty.
- All `fields` must exist in corresponding `available_telemetry_sources` entry.

---

## A5. Detection Architect Agent

### Input
```json
{
  "report_id": "string",
  "evidence": "object (from A2)",
  "attack_mappings": "array (from A3)",
  "telemetry": "array (from A4)"
}
```

### Output
```json
{
  "detection_spec": "DetectionSpec object (see DetectionSpec.schema.json)"
}
```

### Validation
- Output must pass full DetectionSpec schema validation.

---

## A6. Query/Rule Builder Agent

### Input
```json
{
  "detection_spec": "DetectionSpec object"
}
```

### Output
```json
{
  "query_portfolio": [
    {
      "query_id": "string",
      "query_type": "string (high_precision/high_recall/balanced)",
      "query_language": "string (kql/spl/eql)",
      "query_text": "string",
      "expected_signal": "string"
    }
  ],
  "selected_query_id": "string or null (set after execution)",
  "sigma_rule": "string (YAML format)",
  "kql_query": "string (if applicable)",
  "splunk_query": "string (if applicable)"
}
```

### Validation
- `query_portfolio` must have at least 1 entry.
- `sigma_rule` must be valid YAML.
- Sigma rule must include all ATT&CK tags from DetectionSpec.

---

## A7. Verifier/Refiner Agent

### Input
```json
{
  "detection_spec": "DetectionSpec object",
  "generated_artifacts": {
    "sigma_rule": "string",
    "kql_query": "string or null",
    "query_results": "array or null"
  },
  "validation_results": {
    "static_validation": {
      "passed": "boolean",
      "errors": ["array of error messages"]
    },
    "dynamic_validation": {
      "passed": "boolean",
      "errors": ["array of error messages"]
    }
  },
  "iteration": "integer (current refinement iteration)",
  "refinement_type": "string (query|rule|dynamic)"
}
```

### Output
```json
{
  "critique": {
    "issues": [
      {
        "category": "string (evidence/attack/telemetry/logic/broadness/fp)",
        "severity": "string (critical/major/minor)",
        "description": "string",
        "suggested_fix": "string"
      }
    ]
  },
  "revised_detection_spec": "DetectionSpec object or null",
  "should_abort": "boolean",
  "abort_reason": "string or null"
}
```

### Validation
- If `should_abort` is true, `abort_reason` must be non-empty.
- If `revised_detection_spec` is provided, it must pass DetectionSpec schema validation.

### Retry/loop bounds (authoritative)
- Query refinement max: 3 iterations.
- Rule refinement max: 2 iterations.
- Dynamic refinement max: 2 iterations.
- Parse retry max: 1.

---

## Inter-agent validation rules

1. **Evidence propagation**: Evidence IDs from A2 must be traceable through A3 → A5 → A6.
2. **Telemetry field constraint**: A6 must only use fields attested by A4.
3. **ATT&CK tag consistency**: Sigma rule tags must match A3 mappings.
4. **Abstain propagation**: If A3 or A4 abstains, A5 must produce abstain DetectionSpec.
5. **Refinement bounds**: A7 invocation must obey canonical loop limits in `08-canonical-retry-state.md`.

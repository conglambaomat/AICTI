# DetectionSpec Schema

## Purpose
DetectionSpec is the mandatory intermediate contract between threat intelligence analysis and rule generation. It enforces evidence grounding, telemetry attestation, and detection logic clarity.

## Schema version
v1.0

## Required fields

### spec_id
- Type: string
- Format: `ds-{uuid}`
- Description: Unique identifier for this detection specification.

### source_report_id
- Type: string
- Description: Reference to the source threat report.

### detection_type
- Type: enum
- Values: `behavior_rule`, `ioc_watchlist`, `cve_exposure`, `abstain`
- Description: Classification of detection opportunity.

### evidence
- Type: array of evidence objects
- Required for: `behavior_rule`, `ioc_watchlist`
- Description: Evidence supporting this detection.

Evidence object schema:
```json
{
  "chunk_id": "string",
  "quote": "string (exact text from report)",
  "char_start": "integer",
  "char_end": "integer",
  "supports": "string (what this evidence proves)"
}
```

### attack_mapping
- Type: object or null
- Required for: `behavior_rule`
- Description: ATT&CK technique mapping.

ATT&CK mapping schema:
```json
{
  "technique_id": "string (e.g., T1059.001)",
  "technique_name": "string",
  "tactic": "string",
  "confidence": "float [0.0-1.0]",
  "mapping_reason": "string (justification with evidence reference)"
}
```

### required_telemetry
- Type: array of telemetry requirement objects
- Required for: `behavior_rule`
- Description: Attested telemetry sources and fields.

Telemetry requirement schema:
```json
{
  "platform": "string (windows/linux/cloud/aks/macos)",
  "source": "string (sysmon/auditd/cloudtrail/k8s_audit/...)",
  "event_id": "string or integer or null",
  "category": "string (process_creation/network_connection/file_creation/...)",
  "fields": ["array of attested field names"],
  "attestation_method": "string (schema_verified/sample_verified/tool_verified)"
}
```

### detection_logic
- Type: object
- Required for: `behavior_rule`
- Description: Logical detection conditions in Sigma-compatible structure.

Detection logic schema:
```json
{
  "selection": {
    "field_name|modifier": ["value1", "value2"]
  },
  "filter": {
    "field_name": "value"
  },
  "condition": "string (e.g., selection and not filter)"
}
```

### false_positive_hypotheses
- Type: array of strings
- Required for: `behavior_rule`
- Description: Known or anticipated false positive scenarios.

### test_plan
- Type: object
- Required for: `behavior_rule`
- Description: Validation and testing strategy.

Test plan schema:
```json
{
  "static_validation": "boolean",
  "dynamic_test_method": "string (synthetic_log/replay/atomic_red_team/none)",
  "expected_attack_behavior": "string (description of what should trigger)"
}
```

### abstain_reason
- Type: string or null
- Required for: `abstain`
- Description: Explanation why detection cannot be built.

## Optional fields

### ioc_list
- Type: array of IOC objects
- Used for: `ioc_watchlist`

IOC object schema:
```json
{
  "type": "string (ip/domain/hash/url/email)",
  "value": "string",
  "evidence_quote": "string"
}
```

### cve_id
- Type: string
- Used for: `cve_exposure`

### metadata
- Type: object
- Description: Additional context (author, timestamp, version, etc.)

## Validation rules
1. If `detection_type` is `behavior_rule`:
   - `evidence` must have at least 1 entry.
   - `attack_mapping` must be present.
   - `required_telemetry` must have at least 1 entry.
   - `detection_logic` must be present.
   - `false_positive_hypotheses` must be present (can be empty array).
   - `test_plan` must be present.

2. If `detection_type` is `abstain`:
   - `abstain_reason` must be present and non-empty.

3. All `evidence.quote` must be non-empty strings.

4. All `required_telemetry.fields` must be non-empty arrays.

5. `detection_logic.condition` must reference only keys defined in `selection`/`filter`.

## Example: Behavior rule DetectionSpec

```json
{
  "spec_id": "ds-a1b2c3d4",
  "source_report_id": "report-001",
  "detection_type": "behavior_rule",
  "evidence": [
    {
      "chunk_id": "chunk-012",
      "quote": "The actor used encoded PowerShell commands to download payloads.",
      "char_start": 1205,
      "char_end": 1278,
      "supports": "encoded PowerShell execution"
    }
  ],
  "attack_mapping": {
    "technique_id": "T1059.001",
    "technique_name": "PowerShell",
    "tactic": "Execution",
    "confidence": 0.91,
    "mapping_reason": "Report explicitly describes encoded PowerShell command execution."
  },
  "required_telemetry": [
    {
      "platform": "windows",
      "source": "sysmon",
      "event_id": 1,
      "category": "process_creation",
      "fields": ["Image", "CommandLine", "ParentImage", "User"],
      "attestation_method": "schema_verified"
    }
  ],
  "detection_logic": {
    "selection": {
      "Image|endswith": ["\\\\powershell.exe", "\\\\pwsh.exe"],
      "CommandLine|contains": ["-enc", "-encodedcommand"]
    },
    "condition": "selection"
  },
  "false_positive_hypotheses": [
    "Administrative PowerShell scripts",
    "Software deployment automation"
  ],
  "test_plan": {
    "static_validation": true,
    "dynamic_test_method": "synthetic_log",
    "expected_attack_behavior": "PowerShell process with encoded command line"
  },
  "abstain_reason": null
}
```

## Example: Abstain DetectionSpec

```json
{
  "spec_id": "ds-e5f6g7h8",
  "source_report_id": "report-002",
  "detection_type": "abstain",
  "evidence": [],
  "attack_mapping": null,
  "required_telemetry": [],
  "detection_logic": null,
  "false_positive_hypotheses": [],
  "test_plan": null,
  "abstain_reason": "Report mentions CVE-2026-XXXX but provides no exploit behavior or observable telemetry patterns."
}
```

# Validation Pipeline

## Validation philosophy
Validation is a hard gate, not a soft recommendation. Artifacts must pass each stage before moving forward.

## Stage A — DetectionSpec validation

Checks:
1. JSON schema validity.
2. Required field completeness by detection type.
3. Evidence integrity (quote non-empty, chunk reference exists).
4. ATT&CK mapping integrity (ID format, confidence range).
5. Telemetry integrity (source/fields attested).
6. Detection logic integrity (condition references existing blocks).

Fail behavior:
- Stop progression and return structured errors.

## Stage B — Rule static validation

Checks:
1. Sigma YAML parse.
2. Sigma required sections present.
3. Sigma `logsource` consistency with telemetry.
4. Sigma ATT&CK tags consistency with mappings.
5. KQL parse sanity checks.
6. Field grounding check (all referenced fields attested).
7. Broad-rule heuristic checks.
8. Sigma-KQL semantic consistency.

Fail behavior:
- Send issues to refiner with severity tags.

## Stage C — Dynamic validation

Modes:
- Synthetic log testing (MVP mandatory).
- Log replay testing.
- Tool-based query execution testing.

Checks:
1. Attack sample triggers detection.
2. Benign samples controlled for false positives.
3. Query runtime/row quality sanity.

Metrics:
- attack_detected (bool)
- false_positive_count
- precision
- recall

Fail behavior:
- Refiner loop if retries available.
- Abort with `FAILED_VALIDATION` if retries exhausted.

## Broad-rule checker heuristics
Flag as broad/high-risk when:
- Single generic executable only (e.g., powershell.exe) without context.
- Rule depends only on event_id.
- Rule uses high-noise fields with no narrowing predicates.
- No behavior indicators from evidence.

## Severity model
- CRITICAL: blocks progression immediately.
- MAJOR: requires refiner iteration.
- MINOR: warning, can proceed if policy allows.

## Validation report contract

```json
{
  "artifact_id": "string",
  "stage": "spec|static|dynamic",
  "passed": "boolean",
  "issues": [
    {
      "code": "string",
      "severity": "critical|major|minor",
      "message": "string",
      "path": "string"
    }
  ],
  "metrics": {
    "precision": "number or null",
    "recall": "number or null",
    "false_positive_count": "number or null"
  },
  "created_at": "iso-datetime"
}
```

## Gating policy
- Must pass Stage A before Stage B.
- Must pass Stage B before Stage C.
- Must pass Stage C before human review.
- Human review approval required before export.

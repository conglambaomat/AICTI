# ATT&CK Mapping Output Contract

Date: 2026-05-20
Scope: ATT&CK Mapping Agent output schema

## Purpose
Define strict JSON schema for ATT&CK technique mappings with evidence linkage.

## Schema Definition

```json
{
  "type": "object",
  "required": ["mappings", "abstain", "metadata"],
  "properties": {
    "mappings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["technique_id", "technique_name", "confidence", "evidence_ids", "rationale"],
        "properties": {
          "technique_id": {
            "type": "string",
            "pattern": "^T[0-9]{4}(\\.[0-9]{3})?$",
            "description": "ATT&CK technique or sub-technique ID"
          },
          "technique_name": {
            "type": "string",
            "description": "Human-readable technique name"
          },
          "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Mapping confidence"
          },
          "evidence_ids": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "description": "IDs of evidence spans supporting this mapping"
          },
          "rationale": {
            "type": "string",
            "description": "Explanation linking evidence to technique"
          }
        }
      }
    },
    "abstain": {
      "type": "boolean",
      "description": "True if mapping is unsafe or ambiguous"
    },
    "abstain_reason": {
      "type": "string",
      "description": "Required if abstain is true"
    },
    "metadata": {
      "type": "object",
      "required": ["total_tokens"],
      "properties": {
        "total_tokens": {"type": "integer"}
      }
    }
  }
}
```

## Validation Rules
1. If `abstain` is true, `mappings` must be empty.
2. If `abstain` is false, `mappings` must have at least 1 item.
3. Every technique_id must match ATT&CK ID format.
4. Every evidence_id must reference a valid persisted evidence span.
5. Mappings should be ordered by confidence descending.

## Example Valid Output

```json
{
  "mappings": [
    {
      "technique_id": "T1059.001",
      "technique_name": "Command and Scripting Interpreter: PowerShell",
      "confidence": 0.95,
      "evidence_ids": ["evidence_xyz789"],
      "rationale": "Evidence explicitly describes PowerShell execution with encoded command"
    },
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "confidence": 0.88,
      "evidence_ids": ["evidence_xyz789"],
      "rationale": "PowerShell command downloads additional payload from remote server"
    }
  ],
  "abstain": false,
  "metadata": {
    "total_tokens": 2400
  }
}
```

## Example Valid Abstain Output

```json
{
  "mappings": [],
  "abstain": true,
  "abstain_reason": "Evidence is too ambiguous to confidently map to specific ATT&CK techniques",
  "metadata": {
    "total_tokens": 1500
  }
}
```

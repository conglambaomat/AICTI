# Evidence Output Contract

Date: 2026-05-20
Scope: Evidence Agent output schema for agentic deep-analysis

## Purpose
Define strict JSON schema that Evidence Agent must produce. Any deviation is a hard contract failure.

## Schema Definition

```json
{
  "type": "object",
  "required": ["evidence_spans", "abstain", "metadata"],
  "properties": {
    "evidence_spans": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["behavior_label", "quote", "chunk_id", "start_offset", "end_offset", "confidence", "rationale"],
        "properties": {
          "behavior_label": {
            "type": "string",
            "description": "Normalized behavior description (e.g., 'process_execution', 'file_write', 'network_connection')"
          },
          "quote": {
            "type": "string",
            "description": "Exact text from report supporting this behavior"
          },
          "chunk_id": {
            "type": "string",
            "description": "ID of chunk containing this quote"
          },
          "start_offset": {
            "type": "integer",
            "minimum": 0,
            "description": "Character offset where quote starts in chunk"
          },
          "end_offset": {
            "type": "integer",
            "minimum": 0,
            "description": "Character offset where quote ends in chunk"
          },
          "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Agent confidence in this evidence extraction"
          },
          "rationale": {
            "type": "string",
            "description": "Brief explanation of why this quote supports the behavior"
          }
        }
      }
    },
    "abstain": {
      "type": "boolean",
      "description": "True if agent cannot extract sufficient evidence"
    },
    "abstain_reason": {
      "type": "string",
      "description": "Required if abstain is true"
    },
    "metadata": {
      "type": "object",
      "required": ["retrieval_chunk_count", "total_tokens"],
      "properties": {
        "retrieval_chunk_count": {
          "type": "integer",
          "description": "Number of chunks retrieved for this extraction"
        },
        "total_tokens": {
          "type": "integer",
          "description": "Total tokens consumed by this agent call"
        }
      }
    }
  }
}
```

## Validation Rules
1. If `abstain` is true, `evidence_spans` must be empty array.
2. If `abstain` is false, `evidence_spans` must have at least 1 item.
3. Every quote must be verifiable against the chunk_id text.
4. start_offset must be < end_offset.
5. confidence must be in [0.0, 1.0].

## Grounding Check
After schema validation, run grounding check:
- Retrieve chunk by chunk_id.
- Verify quote exists at specified offsets.
- Fail hard if mismatch detected.

## Example Valid Output

```json
{
  "evidence_spans": [
    {
      "behavior_label": "process_execution",
      "quote": "The malware executes powershell.exe with encoded command to download additional payload",
      "chunk_id": "chunk_abc123",
      "start_offset": 245,
      "end_offset": 342,
      "confidence": 0.92,
      "rationale": "Direct observation of process execution with command-line detail"
    }
  ],
  "abstain": false,
  "metadata": {
    "retrieval_chunk_count": 5,
    "total_tokens": 3200
  }
}
```

## Example Valid Abstain Output

```json
{
  "evidence_spans": [],
  "abstain": true,
  "abstain_reason": "Report contains only CVE references without observable behavior details",
  "metadata": {
    "retrieval_chunk_count": 3,
    "total_tokens": 1800
  }
}
```

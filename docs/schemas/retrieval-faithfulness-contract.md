# Retrieval Faithfulness Contract

Date: 2026-05-20
Scope: Validation rules for retrieval-grounded agent outputs

## Purpose
Ensure every agent claim is traceable to retrieved evidence with verifiable citations.

## Faithfulness Requirements

### 1. Citation Completeness
Every major claim in agent output must include:
- chunk_id reference
- exact quote or offset range
- confidence score

### 2. Citation Accuracy
For each cited chunk:
- chunk_id must exist in retrieval index
- quoted text must match chunk content at specified offsets
- no paraphrasing or summarization without explicit quote

### 3. Provenance Chain
Full lineage must be traceable:
- report_id → chunk_id → evidence_id → mapping_id → spec_id → rule_id

### 4. Mismatch Detection
Hard fail conditions:
- chunk_id not found in index
- quote text does not match chunk at offsets
- evidence_id referenced but not persisted
- confidence outside [0.0, 1.0] range

## Validation Algorithm

```python
def validate_faithfulness(agent_output, retrieval_index, evidence_store):
    """
    Returns (is_valid, issues)
    """
    issues = []
    
    # Check all evidence spans
    for span in agent_output.get("evidence_spans", []):
        chunk_id = span["chunk_id"]
        quote = span["quote"]
        start = span["start_offset"]
        end = span["end_offset"]
        
        # Retrieve chunk
        chunk = retrieval_index.get(chunk_id)
        if chunk is None:
            issues.append(f"chunk_id {chunk_id} not found in index")
            continue
        
        # Verify quote
        actual_text = chunk.text[start:end]
        if actual_text != quote:
            issues.append(f"quote mismatch in chunk {chunk_id}")
    
    # Check all mappings
    for mapping in agent_output.get("mappings", []):
        for evidence_id in mapping["evidence_ids"]:
            if not evidence_store.exists(evidence_id):
                issues.append(f"evidence_id {evidence_id} not found")
    
    return (len(issues) == 0, issues)
```

## Metrics

### claim_supported_rate
```
claim_supported_rate = valid_citations / total_citations
```

### citation_mismatch_rate
```
citation_mismatch_rate = mismatched_citations / total_citations
```

### provenance_completeness_rate
```
provenance_completeness_rate = complete_chains / total_artifacts
```

## Profile Thresholds
See `docs/implementation/kpi-threshold-matrix.md` for profile-specific thresholds.

## Hard Fail Policy
If citation_mismatch_rate exceeds profile threshold:
- Block stage advancement
- Mark run as FAILED_VALIDATION
- Persist failure reason with citation details
- Do not proceed to refinement

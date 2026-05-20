# Refinement Policy

## Canonical reference
All loop limits, retries, and terminal outcomes in this file MUST align with `docs/architecture/08-canonical-retry-state.md`.

## Goal
Improve artifact quality through bounded, explainable critique-and-repair loops without introducing uncontrolled drift.

## Loop limits (authoritative)
- max_query_refinement = 3
- max_rule_refinement = 2
- max_dynamic_refinement = 2
- max_parse_retry = 1

If loop limits are exhausted with unresolved issues, orchestrator must transition to FAILED_VALIDATION and escalate with human-review context package.

## Inputs to refiner
- Current DetectionSpec
- Current generated artifacts (Sigma/KQL/query results)
- Validation report(s)
- Previous critique history
- Current iteration counts

## Refiner rules
1. Apply minimal changes only.
2. Never remove evidence traceability.
3. Never introduce unattested telemetry fields.
4. Never add ATT&CK mappings without evidence support.
5. Preserve existing valid sections unless directly impacted by issue.
6. Produce idempotent output for same input payload.

## Critique structure

```json
{
  "issues": [
    {
      "id": "string",
      "category": "evidence|attack|telemetry|logic|broadness|fp|format",
      "severity": "critical|major|minor",
      "description": "string",
      "root_cause": "string",
      "suggested_fix": "string"
    }
  ],
  "priority_order": ["issue-id-1", "issue-id-2"]
}
```

## Repair strategy order
1. Fix CRITICAL format/schema issues.
2. Fix telemetry field grounding issues.
3. Fix ATT&CK and evidence consistency issues.
4. Fix logic precision/recall balance issues.
5. Optimize false positive control.

## Entry/exit guards

### Entry to refinement
- Trigger: validation report has issue severity >= MEDIUM.
- Guard: current_iteration < max_iterations for current refinement type.

### Exit from refinement
- Success: all issues resolved.
- Failure: max_iterations reached and issues remain.
- Abstain: refiner returns should_abort=true with abstain-compatible reason.

## Abort conditions
Abort immediately when:
- No valid evidence exists for behavior detection.
- Required telemetry is unavailable.
- Refiner attempts unsupported logic repeatedly.
- Conflicting validation requirements cannot be satisfied.

## Output contract

```json
{
  "revised_detection_spec": "object or null",
  "revised_artifacts": {
    "sigma_rule": "string or null",
    "kql_query": "string or null"
  },
  "change_log": [
    {
      "issue_id": "string",
      "change_summary": "string",
      "expected_effect": "string"
    }
  ],
  "should_abort": "boolean",
  "abort_reason": "string or null"
}
```

## Quality safeguard
If a repair degrades previously passing checks, rollback that repair and mark issue as unresolved for escalation.

## Human escalation policy
Escalate to human review when:
- Critical issue unresolved after max retries.
- Trade-off requires policy decision (precision vs recall).
- Ambiguous evidence interpretation affects ATT&CK mapping.
- Confidence score remains < 0.6 after refinement.

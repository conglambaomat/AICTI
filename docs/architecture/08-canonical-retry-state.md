# 08 - Canonical Retry Limits and State Outcomes

## Purpose
This document is the single source of truth for all retry limits, loop bounds, and terminal state outcomes across the entire system. All other documents (orchestration, refinement policy, agent contracts) must reference this file.

## Retry Limits (Authoritative)

### Static Refinement (Reviewer + Refiner loop)
- **Query refinement**: max 3 iterations
- **Rule refinement**: max 2 iterations
- **Parse retry**: max 1 attempt

### Dynamic Refinement (Test execution feedback)
- **Max dynamic refinement iterations**: 2

### Agent-Level Retries
- **Transient API errors** (rate limit, timeout): max 3 retries with exponential backoff
- **Validation failures**: no automatic retry (escalate to refinement loop)
- **Parse errors**: max 1 retry with error context

## State Machine Terminal Outcomes

### Success States
1. **RULE_VALIDATED**
   - All static + dynamic validation passed
   - Ready for human review
   - Next: AWAITING_REVIEW

2. **AWAITING_REVIEW**
   - Rule passed all automated checks
   - Waiting for human approval
   - Next: APPROVED or REJECTED

3. **APPROVED**
   - Human approved the rule
   - Ready for export
   - Terminal state (success)

### Failure States
4. **FAILED_VALIDATION**
   - Static or dynamic validation failed after max refinement iterations
   - Reason: validation issues exhausted retry budget
   - Next: NEEDS_HUMAN_REVIEW (escalation)

5. **ABSTAINED**
   - System determined rule generation is unsafe
   - Reason: insufficient evidence, no telemetry support, overbroad after refinement
   - Terminal state (safe failure)

6. **FAILED_GENERATION**
   - Agent failed to produce valid output after retries
   - Reason: persistent API errors, schema violations, extraction failure
   - Terminal state (hard failure)

7. **REJECTED**
   - Human rejected the rule during review
   - Terminal state (human decision)

## Transition Guards (Quantitative)

### Entry to Refinement Loop
- **Trigger**: validation report contains issues with severity >= MEDIUM
- **Guard**: current_iteration < max_iterations for refinement type

### Exit from Refinement Loop
- **Success exit**: validation report shows all issues resolved
- **Failure exit**: current_iteration >= max_iterations AND issues remain
- **Abstain exit**: Refiner returns abstain decision

### Escalation to Human Review
- **Automatic escalation conditions**:
  - Refinement exhausted (FAILED_VALIDATION)
  - Conflicting validation issues (cannot satisfy all constraints)
  - Confidence score < 0.6 after refinement

## Retry Backoff Policy

### Transient API Errors
```
attempt 1: immediate
attempt 2: 2s delay
attempt 3: 4s delay
attempt 4: fail
```

### Rate Limit Errors
```
attempt 1: wait for retry-after header (max 60s)
attempt 2: 30s delay
attempt 3: 60s delay
attempt 4: fail
```

## Idempotency Requirements

### Refinement Operations
- Each refinement iteration must be idempotent
- Refiner receives: previous spec + validation report + iteration count
- Refiner must not depend on external mutable state

### Validation Operations
- Validation must be deterministic for same input
- Dynamic validation may use cached test results within same run_id

## Conflict Resolution

### Multiple Issues Same Priority
- Process in order: evidence integrity → telemetry validity → logic correctness → broadness
- If still conflicting, escalate to human review

### Contradictory Validation Feedback
- Example: "too broad" vs "missing detection case"
- Resolution: abstain and escalate to human review

## Cross-Reference Compliance

All documents must align with this file:
- `docs/architecture/02-orchestration-state-machine.md` → state names and transitions
- `docs/implementation/refinement-policy.md` → iteration limits and exit conditions
- `docs/schemas/agent-contracts.md` → retry behavior in agent I/O
- `docs/architecture/05-error-taxonomy-retry-matrix.md` → retry classes and backoff

## Version
- **Version**: 1.0
- **Last Updated**: 2026-05-20
- **Status**: Canonical

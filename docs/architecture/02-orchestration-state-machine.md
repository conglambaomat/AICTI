# Orchestration State Machine

## Canonical reference
This state machine MUST align with `docs/architecture/08-canonical-retry-state.md`.

## States
1. INGESTED
2. CHUNKED
3. EVIDENCE_EXTRACTED
4. ATTACK_MAPPED
5. TELEMETRY_GROUNDED
6. SPEC_BUILT
7. QUERY_PORTFOLIO_READY
8. QUERY_SELECTED
9. RULE_DRAFTED
10. STATIC_VALIDATED
11. DYNAMIC_VALIDATED
12. RULE_VALIDATED
13. AWAITING_REVIEW
14. APPROVED
15. EXPORTED

Terminal failure states:
- ABSTAINED
- FAILED_VALIDATION
- FAILED_GENERATION
- REJECTED

## Transition rules
- INGESTED -> CHUNKED: parser/chunker success.
- CHUNKED -> EVIDENCE_EXTRACTED: evidence extractor returns valid evidence payload.
- EVIDENCE_EXTRACTED -> ATTACK_MAPPED: mapping confidence above threshold or abstain.
- ATTACK_MAPPED -> TELEMETRY_GROUNDED: telemetry scout attests required fields.
- TELEMETRY_GROUNDED -> SPEC_BUILT: DetectionSpec schema validation passes.
- SPEC_BUILT -> QUERY_PORTFOLIO_READY: query portfolio generated.
- QUERY_PORTFOLIO_READY -> QUERY_SELECTED: executor ranks and selects viable query.
- QUERY_SELECTED -> RULE_DRAFTED: rule writer outputs Sigma/KQL artifacts.
- RULE_DRAFTED -> STATIC_VALIDATED: static checks pass.
- STATIC_VALIDATED -> DYNAMIC_VALIDATED: dynamic test execution pass threshold.
- DYNAMIC_VALIDATED -> RULE_VALIDATED: all validation gates passed.
- RULE_VALIDATED -> AWAITING_REVIEW: automated checks complete.
- AWAITING_REVIEW -> APPROVED: human approval recorded.
- AWAITING_REVIEW -> REJECTED: human rejection recorded.
- APPROVED -> EXPORTED: export policy passes.

## Transition guards (quantitative)
- EVIDENCE_EXTRACTED -> ATTACK_MAPPED guard:
  - mapping confidence >= 0.6 OR abstain decision.
- STATIC_VALIDATED -> DYNAMIC_VALIDATED guard:
  - static validator has no CRITICAL issues.
- DYNAMIC_VALIDATED -> RULE_VALIDATED guard:
  - dynamic score >= configured threshold and no MAJOR unresolved issues.

## Retry policy (authoritative)
- Query refinement retries: max 3.
- Rule refinement retries: max 2.
- Parsing retry: max 1 with error context.
- Dynamic refinement retries: max 2.
- Transient API errors: max 3 retries with exponential backoff.

## Abort and escalation policy
- If evidence is insufficient for behavior detection, transition to ABSTAINED.
- If telemetry grounding fails, transition to ABSTAINED.
- If validation fails after retry limits, transition to FAILED_VALIDATION then escalate to human review context package.
- If agent cannot produce valid output after retry policy, transition to FAILED_GENERATION.

## Observability requirements
Each transition must log:
- state_from, state_to
- actor/agent id
- input artifact id
- output artifact id
- validation result summary
- duration_ms
- run_id, trace_id, agent_run_id

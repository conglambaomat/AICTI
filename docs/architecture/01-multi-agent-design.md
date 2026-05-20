# Multi-Agent Design

## Design target
Use a controlled specialist-agent architecture that maximizes precision while keeping orchestration deterministic.

## Core agent set

### A1. Objective Decomposer
Input: detection objective/report context.
Output: platform hypotheses, tactic hypotheses, search terms, analysis requirements.
Constraint: must not generate rules.

### A2. CTI Evidence Agent
Input: report chunks.
Output: evidence-backed procedures/IOC/CVE entities with exact quotes.
Constraint: no unsupported inference.

### A3. ATT&CK Mapper Agent
Input: extracted evidence + ATT&CK candidates.
Output: mapped techniques with confidence and justification, or abstain.
Constraint: only use allowed ATT&CK IDs.

### A4. Telemetry Scout Agent
Input: mapping + available telemetry schema/tool outputs.
Output: selected data sources/tables/fields with rationale.
Constraint: only attest fields observed in schema/sample.

### A5. Detection Architect Agent
Input: evidence + ATT&CK mapping + telemetry attestation.
Output: canonical DetectionSpec.
Constraint: no rule writing.

### A6. Query/Rule Builder Agent
Input: DetectionSpec.
Output: query portfolio, selected query, Sigma rule draft.
Constraint: must stay inside DetectionSpec semantics.

### A7. Verifier/Refiner Agent
Input: artifacts + validation failures.
Output: critique and minimal spec/rule revisions.
Constraint: bounded loops, fail-fast policy.

## Orchestrator policy
- Contract-based handoff only (strict JSON payloads).
- Hard gates between phases.
- Abort path when evidence or telemetry is insufficient.

## Bounded refinement
- max_query_refinement: 3
- max_rule_refinement: 2
- max_dynamic_refinement: 2
- If unresolved after limits: emit abstain/failure package with reasons.
- Canonical source: `docs/architecture/08-canonical-retry-state.md`.

## Failure boundaries
- Missing evidence → do not proceed to spec.
- Missing telemetry fields → do not proceed to query/rule.
- Invalid DetectionSpec schema → stop and repair spec.
- Invalid final output contract → block submission/export.

## Why this design
- Strong specialization improves factual accuracy.
- Contract enforcement limits hallucination spread.
- Bounded loops preserve reliability and runtime predictability.

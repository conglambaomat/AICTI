# CTI-REALM Adapter Design (Deferred Phase)

## Purpose
Enable formal comparison against CTI-REALM only after product-mode core quality is stable.

## Scope
- Build an Inspect-compatible solver adapter.
- Preserve DE-Forge internals while meeting CTI-REALM output contract.

## Compatibility targets
1. Input objective format from CTI-REALM tasks.
2. Tool usage behavior compatible with CTI-REALM sandbox.
3. Final output JSON contract:
```json
{
  "sigma_rule": "string",
  "kql_query": "string",
  "query_results": [
    {"column": "value"}
  ]
}
```
4. Message budget awareness for benchmark runtime.

## Adapter architecture

### Layer 1: Objective translator
- Convert CTI-REALM task objective into internal orchestration input.

### Layer 2: Tool bridge
- Map internal telemetry/CTI operations to benchmark tools where required.
- Ensure results used in final `query_results` are actual tool outputs.

### Layer 3: Contract packer
- Transform internal artifacts into strict CTI-REALM submission JSON.
- Run final output validator before submit.

## Runtime policy in benchmark mode
- Keep bounded loops conservative.
- Prioritize C4 outcome quality while maintaining trajectory checkpoints.
- Ensure at least two unique successful query executions when possible.

## Evaluation plan
Compare:
- Baseline A: CTI-REALM default setup.
- Baseline B: CTI-REALM seeded setup.
- Proposed: DE-Forge adapter.

Track:
- total reward
- C0/C1/C2/C3/C4
- KQL F1
- Sigma judge score
- runtime and tool calls
- failure categories

## Deferred implementation prerequisites
Adapter work starts only when these are true:
1. Product mode pipeline completes end-to-end reliably.
2. Static validation pass rate is stable.
3. Dynamic validation works for at least one telemetry profile.
4. Artifact lineage and observability are complete.

## Risk controls
- Do not overfit prompts exclusively to benchmark wording.
- Keep shared core logic benchmark-agnostic.
- Isolate benchmark-specific packaging in adapter layer only.

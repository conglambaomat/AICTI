# Phase 1 Core Build Plan (Run-Robustly-First)

## Objective
Build a deterministic, end-to-end runnable core system before optimization/benchmarking.

## Build priorities
1. Deterministic orchestration and contracts.
2. DetectionSpec pipeline correctness.
3. Static validation reliability.
4. Minimal dynamic validation capability.
5. Traceability and observability.

## Delivery sequence

### Step 1 — Project skeleton
- Create base app structure (`src/` with api/services/schemas/models/utils).
- Add configuration loader and environment profile.
- Add health endpoint.

Done criteria:
- App starts with one health route.
- Config and logging initialize successfully.

### Step 2 — Report ingestion and chunking
- Implement TXT/MD ingestion first.
- Normalize text and preserve offsets.
- Create chunking pipeline with deterministic chunk IDs.

Done criteria:
- Ingested report is persisted.
- Chunks can be retrieved by API.

### Step 3 — Evidence extraction contract
- Implement CTI Evidence Agent adapter with strict JSON output.
- Persist evidence artifacts with quote offsets.
- Reject invalid extraction payloads.

Done criteria:
- Evidence records are traceable to chunks.
- No contract-violating payload reaches downstream.

### Step 4 — ATT&CK mapping contract
- Implement ATT&CK Mapper adapter.
- Validate mapped technique IDs format and confidence bounds.
- Support abstain pathway.

Done criteria:
- Mapping is produced or abstain reason returned deterministically.

### Step 5 — Telemetry grounding
- Implement telemetry schema registry reader.
- Implement Telemetry Scout adapter.
- Enforce attested field list only.

Done criteria:
- Required telemetry returned with attestation method.
- Unsupported fields are blocked.

### Step 6 — DetectionSpec builder
- Implement DetectionSpec schema model and validator.
- Build DetectionSpec from upstream artifacts.
- Enforce behavior-rule vs abstain branches.

Done criteria:
- Valid DetectionSpec persisted.
- Invalid DetectionSpec returns actionable errors.

### Step 7 — Query and rule generation
- Implement Query/Rule Builder adapter.
- Generate Sigma-first plus KQL candidate set.
- Keep generation constrained to DetectionSpec.

Done criteria:
- Query portfolio and Sigma draft generated for valid specs.

### Step 8 — Static validation gates
- Implement validators (schema, YAML, field checks, broad-rule checks).
- Block progression if static checks fail.

Done criteria:
- Validation report created with pass/fail + issues.

### Step 9 — Minimal dynamic validation
- Implement synthetic dynamic test harness for one telemetry profile.
- Compute basic TP/FP summary.

Done criteria:
- At least one dynamic validation path executes end-to-end.

### Step 10 — Reviewer/refiner bounded loop
- Implement critique payload contract.
- Enforce max refinement loops.
- Abort gracefully with reason when unresolved.

Done criteria:
- Pipeline completes with approved artifact or bounded failure.

## Engineering constraints
- No direct rule generation without DetectionSpec.
- No unbounded retries.
- No export without human approval state.

## Required telemetry profile for MVP
- Start with `windows/sysmon_event_1` only.
- Add Linux/AKS/Cloud profiles after phase-1 stability.

## Exit criteria for Phase 1
- One full run from report to validated Sigma/KQL completes deterministically.
- All artifacts have lineage IDs.
- Failures are explainable and reproducible from logs.
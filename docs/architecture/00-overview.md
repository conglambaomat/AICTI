# DE-Forge Architecture Overview

## Mission
DE-Forge is an evidence-grounded multi-agent detection engineering system that transforms threat intelligence reports into validated detection artifacts.

Primary objective:
- Maximize practical detection quality, robustness, and correctness in real workflows.

Secondary objective:
- Support benchmark comparison mode (including CTI-REALM compatibility) after core system quality is stable.

## Core principles
1. Evidence before generation.
2. Schema grounding before query/rule writing.
3. DetectionSpec as mandatory intermediate contract.
4. Deterministic orchestration with bounded loops.
5. Validation-first release policy.
6. Human review gate before production export.

## Operating modes

### Product mode (priority)
Used for real analyst workflows:
- ingest report
- extract evidence/TTP/IOC/CVE
- map ATT&CK
- discover telemetry
- create DetectionSpec
- generate Sigma/KQL
- static and dynamic validation
- reviewer/refiner loop
- human accept/edit/reject

### Benchmark mode (deferred)
Used for formal comparison:
- strict output contract
- task adapter and scorer integration
- reproducible runs and ablation

## High-level pipeline
1. Report Ingestion
2. Parsing and Chunking
3. Evidence Extraction
4. ATT&CK Mapping
5. Telemetry Grounding
6. Detection Opportunity Classification
7. DetectionSpec Build
8. Query Portfolio Generation
9. Rule Generation
10. Validation (Static + Dynamic)
11. Reviewer/Refiner Loop
12. Human Review + Export

## Non-goals
- Direct rule generation without evidence/telemetry grounding.
- Unbounded autonomous loops.
- Production deployment without human gate.

## Success criteria
- End-to-end runs complete deterministically.
- Generated artifacts pass static validation consistently.
- Dynamic tests show useful precision/recall.
- Analyst can trace each rule back to evidence and telemetry rationale.

# Dataflow

## End-to-end flow

1. Report ingestion
- Inputs: PDF/HTML/TXT/MD/URL.
- Outputs: normalized report record.

2. Parsing and chunking
- Split into structured chunks (section/paragraph/table/code).
- Preserve traceability offsets.

3. Evidence extraction
- Extract procedure, IOC, CVE, tool, command candidates.
- Attach exact evidence quotes and offsets.

4. ATT&CK mapping
- Retrieve and rank ATT&CK candidates.
- Produce confidence-scored mapping artifacts.

5. Telemetry grounding
- Resolve data source/table/field availability.
- Attach attested field list and source rationale.

6. Detection opportunity classification
- Classify into behavior_rule / ioc_watchlist / cve_exposure / abstain.

7. DetectionSpec build
- Build schema-valid intermediate artifact.
- Include evidence, ATT&CK, telemetry, detection logic, FP hypotheses, test plan.

8. Query portfolio and selection
- Generate multiple query candidates.
- Execute candidates and select best-performing query.

9. Rule generation
- Generate Sigma-first artifact and corresponding query artifact.

10. Validation
- Static: schema, YAML, field, logic, broadness checks.
- Dynamic: query execution/synthetic or replay evaluation.

11. Review/refine loop
- Reviewer emits critique JSON.
- Refiner applies minimal changes within loop limits.

12. Human review and export
- Analyst accepts, edits, or rejects.
- Export approved artifacts.

## Artifact lineage
Every output must preserve lineage pointers:
- report_id
- chunk_ids
- evidence_ids
- mapping_id
- telemetry_selection_id
- spec_id
- query_candidate_ids
- selected_query_id
- rule_id
- validation_run_id

## Integrity checks
- No lineage break allowed between DetectionSpec and rule artifacts.
- Any missing lineage reference blocks progression to export.

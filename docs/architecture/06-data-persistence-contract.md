# 06 - Data Persistence Contract

## Design principles
1. Every generated artifact must be traceable to a report.
2. Every rule must be traceable to a DetectionSpec.
3. Every DetectionSpec must be traceable to evidence spans.
4. Every agent run must have run_id and trace_id.
5. Generated rules are immutable; edits create new versions.
6. Human decisions are append-only.
7. All state transitions must be idempotent.
8. All writes must include idempotency_key for retry safety.

## Tables

### reports
- id UUID primary key
- source_type text not null check(source_type in ('pdf', 'txt', 'html', 'markdown', 'url'))
- source_uri text nullable
- title text nullable
- raw_text text not null
- content_hash text unique not null
- metadata_json jsonb not null default '{}'
- status text not null default 'ingested' check(status in ('ingested', 'chunked', 'processing', 'completed', 'failed'))
- created_at timestamptz not null
- updated_at timestamptz not null

Indexes:
- unique(content_hash)
- index(created_at)
- index(status)

### report_chunks
- id UUID primary key
- report_id UUID not null references reports(id) on delete cascade
- chunk_index integer not null
- section_title text nullable
- chunk_text text not null
- char_start integer not null
- char_end integer not null
- chunk_type text not null default 'paragraph' check(chunk_type in ('paragraph', 'section', 'list', 'code', 'table'))
- created_at timestamptz not null

Constraints:
- unique(report_id, chunk_index)
- check(char_start <= char_end)
- check(char_start >= 0)

Indexes:
- index(report_id)
- index(report_id, chunk_index)

### evidence_spans
- id UUID primary key
- report_id UUID not null references reports(id)
- chunk_id UUID not null references report_chunks(id)
- quote text not null check(length(quote) > 0)
- char_start integer not null check(char_start >= 0)
- char_end integer not null check(char_end >= char_start)
- supports_claim text not null check(length(supports_claim) > 0)
- confidence numeric not null check(confidence >= 0 and confidence <= 1)
- created_by_agent text not null
- run_id UUID not null
- created_at timestamptz not null

Indexes:
- index(report_id)
- index(chunk_id)
- index(run_id)

### extracted_iocs
- id UUID primary key
- report_id UUID not null references reports(id)
- evidence_id UUID nullable references evidence_spans(id)
- ioc_type text not null check(ioc_type in ('ip', 'domain', 'hash', 'url', 'email', 'file_path'))
- raw_value text not null
- normalized_value text not null
- confidence numeric not null check(confidence >= 0 and confidence <= 1)
- extractor text not null
- created_at timestamptz not null

Constraints:
- unique(report_id, ioc_type, normalized_value)

Indexes:
- index(report_id)
- index(ioc_type)
- index(normalized_value)

### attack_mappings
- id UUID primary key
- report_id UUID not null references reports(id)
- evidence_id UUID not null references evidence_spans(id)
- technique_id text not null check(technique_id ~ '^T\\d{4}(\\.\\d{3})?$')
- technique_name text not null
- tactic text nullable
- confidence numeric not null check(confidence >= 0 and confidence <= 1)
- mapping_reason text not null check(length(mapping_reason) > 0)
- candidate_json jsonb not null default '[]'
- run_id UUID not null
- created_at timestamptz not null

Indexes:
- index(report_id)
- index(technique_id)
- index(run_id)

### telemetry_selections
- id UUID primary key
- report_id UUID not null references reports(id)
- attack_mapping_id UUID not null references attack_mappings(id)
- platform text not null check(platform in ('windows', 'linux', 'cloud', 'aks', 'macos'))
- source text not null
- event_id text nullable
- category text not null
- fields_json jsonb not null
- attestation_method text not null check(attestation_method in ('schema_verified', 'sample_verified', 'tool_verified'))
- selection_reason text not null
- run_id UUID not null
- created_at timestamptz not null

Indexes:
- index(report_id)
- index(attack_mapping_id)
- index(run_id)

### detection_specs
- id UUID primary key
- report_id UUID not null references reports(id)
- attack_mapping_id UUID nullable references attack_mappings(id)
- telemetry_selection_id UUID nullable references telemetry_selections(id)
- detection_type text not null check(detection_type in ('behavior_rule', 'ioc_watchlist', 'cve_exposure', 'abstain'))
- required_telemetry_json jsonb not null
- detection_logic_json jsonb not null
- false_positive_json jsonb not null default '[]'
- test_plan_json jsonb not null default '{}'
- abstain_reason text nullable
- status text not null check(status in ('draft', 'validated', 'failed', 'abstained'))
- spec_version integer not null default 1
- run_id UUID not null
- created_at timestamptz not null

Indexes:
- index(report_id)
- index(attack_mapping_id)
- index(telemetry_selection_id)
- index(status)
- index(run_id)

### query_candidates
- id UUID primary key
- detection_spec_id UUID not null references detection_specs(id)
- query_id text not null
- query_type text not null check(query_type in ('high_precision', 'high_recall', 'balanced'))
- query_language text not null check(query_language in ('kql', 'spl', 'eql'))
- query_text text not null
- expected_signal text not null
- selected boolean not null default false
- run_id UUID not null
- created_at timestamptz not null

Constraints:
- unique(detection_spec_id, query_id)

Indexes:
- index(detection_spec_id)
- index(selected)
- index(run_id)

### generated_rules
- id UUID primary key
- detection_spec_id UUID not null references detection_specs(id)
- query_candidate_id UUID nullable references query_candidates(id)
- rule_format text not null check(rule_format in ('sigma', 'kql', 'spl', 'eql'))
- rule_content text not null
- rule_hash text not null
- generator_model text not null
- prompt_version text not null
- status text not null check(status in ('draft', 'validated', 'failed', 'approved', 'rejected', 'exported'))
- version integer not null check(version > 0)
- parent_rule_id UUID nullable references generated_rules(id)
- run_id UUID not null
- created_at timestamptz not null

Constraints:
- unique(detection_spec_id, rule_format, version)
- unique(rule_hash)

Indexes:
- index(detection_spec_id)
- index(query_candidate_id)
- index(rule_format)
- index(status)
- index(run_id)

### validation_results
- id UUID primary key
- rule_id UUID not null references generated_rules(id)
- validation_run_id UUID not null
- validation_type text not null check(validation_type in ('static', 'dynamic'))
- passed boolean not null
- score numeric nullable check(score is null or (score >= 0 and score <= 1))
- errors_json jsonb not null default '[]'
- warnings_json jsonb not null default '[]'
- validator_version text not null
- idempotency_key text not null
- created_at timestamptz not null

Constraints:
- unique(rule_id, validation_type, idempotency_key)

Indexes:
- index(rule_id)
- index(validation_run_id)
- index(validation_type)
- index(passed)

### test_runs
- id UUID primary key
- rule_id UUID not null references generated_rules(id)
- validation_run_id UUID not null
- test_method text not null check(test_method in ('synthetic_log', 'replay', 'atomic_red_team', 'none'))
- dataset_name text nullable
- attack_detected boolean nullable
- false_positive_count integer nullable check(false_positive_count is null or false_positive_count >= 0)
- precision numeric nullable check(precision is null or (precision >= 0 and precision <= 1))
- recall numeric nullable check(recall is null or (recall >= 0 and recall <= 1))
- f1 numeric nullable check(f1 is null or (f1 >= 0 and f1 <= 1))
- raw_result_json jsonb not null default '{}'
- idempotency_key text not null
- created_at timestamptz not null

Constraints:
- unique(rule_id, test_method, idempotency_key)

Indexes:
- index(rule_id)
- index(validation_run_id)
- index(test_method)

### agent_runs
- id UUID primary key
- run_id UUID not null
- trace_id UUID not null
- agent_name text not null check(agent_name in ('ObjectiveDecomposerAgent', 'CTIEvidenceAgent', 'AttackMapperAgent', 'TelemetryScoutAgent', 'DetectionArchitectAgent', 'QueryRuleBuilderAgent', 'VerifierRefinerAgent'))
- input_hash text not null
- output_hash text nullable
- model_name text nullable
- prompt_version text nullable
- status text not null check(status in ('started', 'success', 'abstain', 'failed', 'retrying'))
- error_code text nullable
- retry_attempt integer not null default 0 check(retry_attempt >= 0)
- started_at timestamptz not null
- ended_at timestamptz nullable
- metadata_json jsonb not null default '{}'

Constraints:
- check(ended_at is null or ended_at >= started_at)

Indexes:
- index(run_id)
- index(trace_id)
- index(agent_name)
- index(status)
- index(started_at)

### review_decisions
- id UUID primary key
- rule_id UUID not null references generated_rules(id)
- reviewer text not null
- decision text not null check(decision in ('accept', 'reject', 'needs_changes', 'export'))
- comment text nullable
- edited_rule_content text nullable
- created_at timestamptz not null

Indexes:
- index(rule_id)
- index(decision)
- index(created_at)

### refinement_iterations
- id UUID primary key
- detection_spec_id UUID nullable references detection_specs(id)
- rule_id UUID nullable references generated_rules(id)
- refinement_type text not null check(refinement_type in ('query', 'rule', 'parse'))
- iteration integer not null check(iteration > 0)
- max_iterations integer not null check(max_iterations > 0)
- validation_report_json jsonb not null
- change_log_json jsonb not null default '[]'
- should_abort boolean not null default false
- abort_reason text nullable
- run_id UUID not null
- created_at timestamptz not null

Constraints:
- check((detection_spec_id is not null) or (rule_id is not null))
- check(iteration <= max_iterations)

Indexes:
- index(detection_spec_id)
- index(rule_id)
- index(refinement_type)
- index(run_id)

## Lineage Integrity Rules

1. **Evidence → DetectionSpec**: Every DetectionSpec must reference at least one evidence_span (via evidence_json field).
2. **ATT&CK → DetectionSpec**: Every behavior_rule DetectionSpec must reference one attack_mapping.
3. **Telemetry → DetectionSpec**: Every behavior_rule DetectionSpec must reference one telemetry_selection.
4. **DetectionSpec → Rule**: Every generated_rule must reference one detection_spec.
5. **Query → Rule**: If query portfolio was used, generated_rule must reference selected query_candidate.
6. **Rule → Validation**: Every validation_result must reference one generated_rule.
7. **Validation → Test**: Every test_run must reference same validation_run_id as corresponding validation_result.

## Idempotency Strategy

### Write Operations
All write operations must include `idempotency_key` (UUID or hash of operation parameters).

### Retry-Safe Inserts
```sql
INSERT INTO validation_results (id, rule_id, validation_run_id, validation_type, ..., idempotency_key)
VALUES (...)
ON CONFLICT (rule_id, validation_type, idempotency_key) DO NOTHING;
```

### State Transitions
State transitions must be idempotent:
```sql
UPDATE generated_rules
SET status = 'validated', updated_at = now()
WHERE id = ? AND status IN ('draft', 'validated');
```

## Transaction Boundaries

### Atomic Operations
1. **Report ingestion**: INSERT reports + INSERT report_chunks (single transaction).
2. **Evidence extraction**: INSERT evidence_spans + INSERT extracted_iocs (single transaction).
3. **DetectionSpec creation**: INSERT detection_specs + INSERT telemetry_selections (single transaction).
4. **Rule generation**: INSERT generated_rules + INSERT query_candidates (single transaction).
5. **Validation**: INSERT validation_results + INSERT test_runs (single transaction).

### Rollback Policy
If any step in atomic operation fails, rollback entire transaction and mark agent_run as failed.

## Version History

- **Version**: 2.0
- **Last Updated**: 2026-05-20
- **Changes**: Added enum constraints, check constraints, idempotency_key fields, telemetry_selections table, query_candidates table, refinement_iterations table, validation_run_id linkage, transaction boundaries.

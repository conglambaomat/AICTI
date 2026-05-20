# 07 - Observability Specification

## Goals
The system must allow developers to answer:
1. Which agent produced this rule?
2. Which evidence quote supported this rule?
3. Which model and prompt version were used?
4. Which validation failed?
5. How many retries happened?
6. Why did the system abstain?
7. How much did the run cost?
8. Which stage is the bottleneck?

## Required identifiers
Every request must include:
- request_id
- run_id
- trace_id
- report_id
- agent_run_id where applicable
- detection_spec_id where applicable
- rule_id where applicable

## Structured log fields
Every log event must include:
```json
{
  "timestamp": "...",
  "level": "INFO",
  "event": "agent.completed",
  "request_id": "...",
  "run_id": "...",
  "trace_id": "...",
  "agent_name": "DetectionArchitectAgent",
  "report_id": "...",
  "duration_ms": 1250,
  "status": "success",
  "error_code": null
}
```

## Event taxonomy
Required events:
- report.ingested
- report.chunked
- agent.started
- agent.completed
- agent.failed
- llm.requested
- llm.completed
- llm.failed
- detection_spec.created
- rule.generated
- validation.started
- validation.completed
- validation.failed
- test.started
- test.completed
- review.submitted
- export.completed
- pipeline.abstained
- pipeline.failed

## Required metrics
### Pipeline metrics
- reports_processed_total
- rules_generated_total
- rules_validated_total
- rules_failed_validation_total
- abstentions_total
- pipeline_success_rate
- average_pipeline_latency_ms

### Agent metrics
- agent_success_rate by agent_name
- agent_retry_count by agent_name
- agent_latency_ms by agent_name
- agent_error_count by error_code
- llm_tokens_input_total
- llm_tokens_output_total
- llm_cost_estimate_total

### Rule quality metrics
- sigma_yaml_valid_rate
- sigma_required_fields_pass_rate
- telemetry_field_validity_rate
- broad_rule_rejection_rate
- evidence_coverage_rate
- unsupported_claim_rate
- validation_pass_rate

### Benchmark metrics
- benchmark_total_reward
- cti_analysis_score
- mitre_mapping_score
- data_exploration_score
- query_execution_score
- detection_quality_score
- kql_precision
- kql_recall
- kql_f1
- sigma_quality_score

## Minimal dashboard
Dashboard must show:
1. Recent runs
2. Pipeline success/failure count
3. Agent failure breakdown
4. Validation failure breakdown
5. Average latency per stage
6. Rule quality metrics
7. Benchmark scores
8. Cost estimate per run

## Tracing requirement
Each pipeline run must produce a trace tree:
```text
run_id
  ├── ingestion
  ├── chunking
  ├── CTI Evidence Agent
  ├── ATT&CK Mapping Agent
  ├── Telemetry Scout Agent
  ├── Detection Architect Agent
  ├── Rule Writer Agent
  ├── Static Validator
  ├── Reviewer Agent
  └── Refiner Agent
```

Each node must include:
- input hash
- output hash
- start time
- end time
- status
- error code
- retry count

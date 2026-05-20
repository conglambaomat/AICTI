# 05 - Error Taxonomy and Retry Matrix

## Canonical reference
Retry classes and max attempts in this document MUST align with `docs/architecture/08-canonical-retry-state.md`.

## Error classes

| Error code | Error type | Description | Default action |
|---|---|---|---|
| E_PARSE_001 | Report parse failure | PDF/TXT/HTML cannot be parsed | retry once with error context |
| E_CHUNK_001 | Empty chunks | Parser returns no meaningful text | fail-fast |
| E_LLM_001 | LLM timeout | Model/API timeout | retry with transient backoff |
| E_LLM_002 | Invalid JSON | LLM output is not valid JSON | parse retry (max 1) |
| E_LLM_003 | Unsupported claim | LLM produced claim without evidence | reject claim |
| E_EVID_001 | Missing evidence | DetectionSpec has no evidence quote | abstain |
| E_ATTACK_001 | Invalid ATT&CK ID | Technique ID not in ATT&CK index | retry mapping |
| E_TELEM_001 | Missing telemetry | No telemetry supports the behavior | abstain |
| E_FIELD_001 | Invalid field | Rule uses field outside telemetry schema | refine DetectionSpec |
| E_RULE_001 | Invalid Sigma YAML | YAML parse fails | refine rule |
| E_RULE_002 | Missing Sigma fields | Required Sigma fields missing | refine rule |
| E_RULE_003 | Overbroad rule | Rule too generic/noisy | refine DetectionSpec |
| E_TEST_001 | Attack not detected | Rule does not match attack log | dynamic refinement |
| E_TEST_002 | High false positives | Rule matches too many benign logs | dynamic refinement |
| E_DB_001 | Database write failure | Insert/update transaction fails | fail-fast |
| E_DB_002 | Deadlock/timeout | DB lock timeout/deadlock | retry with transient backoff |
| E_RATE_001 | Provider rate-limited | Upstream API 429 | retry with rate-limit backoff |
| E_RUNTIME_001 | Persistent generation failure | Agent output invalid after retries | FAILED_GENERATION |

## Retry matrix

| Stage | Error | Retry? | Max attempts | Backoff policy | Next action |
|---|---|---:|---:|---|---|
| Ingestion | E_PARSE_001 | yes | 1 | parse_once | retry parse with error context |
| Ingestion | E_CHUNK_001 | no | 0 | none | fail-fast |
| LLM extraction | E_LLM_001 | yes | 3 | transient_backoff | retry same prompt |
| LLM extraction | E_LLM_002 | yes | 1 | parse_once | retry with JSON repair context |
| Evidence validation | E_EVID_001 | no | 0 | none | abstain |
| ATT&CK mapping | E_ATTACK_001 | yes | 2 | transient_backoff | rerank candidates |
| Telemetry | E_TELEM_001 | no | 0 | none | abstain |
| DetectionSpec | E_FIELD_001 | no | 0 | none | enter refinement loop |
| Rule generation | E_RULE_001 | no | 0 | none | enter rule refinement loop |
| Rule validation | E_RULE_003 | no | 0 | none | enter rule refinement loop |
| Dynamic test | E_TEST_001 | no | 0 | none | enter dynamic refinement loop |
| Dynamic test | E_TEST_002 | no | 0 | none | enter dynamic refinement loop |
| Storage | E_DB_002 | yes | 3 | transient_backoff | retry transaction |
| Provider | E_RATE_001 | yes | 3 | rate_limit_backoff | wait + retry |
| Generation runtime | E_RUNTIME_001 | no | 0 | none | FAILED_GENERATION |

## Backoff definitions

### transient_backoff
- attempt 1: immediate
- attempt 2: 2s delay
- attempt 3: 4s delay
- attempt 4: fail

### rate_limit_backoff
- attempt 1: wait retry-after (max 60s)
- attempt 2: 30s delay
- attempt 3: 60s delay
- attempt 4: fail

### parse_once
- attempt 1: immediate repair attempt
- attempt 2: fail

## Refinement-loop limits (from canonical 08)
- Query refinement: max 3 iterations.
- Rule refinement: max 2 iterations.
- Dynamic refinement: max 2 iterations.

## Fail-fast conditions
Pipeline must fail-fast when:
- uploaded report is empty
- no meaningful text can be extracted
- database write fails persistently
- output schema is structurally impossible
- retry budget for transient failures is exhausted

## Abstain conditions
Pipeline must abstain when:
- no evidence supports detection logic
- only a CVE is mentioned without exploit behavior
- only an IOC is present but no behavior is described
- no required telemetry is available
- rule would be too broad after bounded refinement

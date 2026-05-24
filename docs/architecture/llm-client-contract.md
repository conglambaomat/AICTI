# LLM Client Contract

Date: 2026-05-20
Scope: Unified OpenAI-compatible LLM client for all agent calls

## 1. Purpose
Standardize request envelope, retry/backoff, timeout budgets, error handling, and token accounting for all LLM interactions.

## 2. Provider Configuration

### Single Provider Policy (Mandatory)
- Provider type: OpenAI-compatible
- Base URL: `https://shopapikey.com/v1`
- API key: from `OPENAI_API_KEY` environment variable
- Model: `cx/gpt-5.5` (all agent roles)

### No Fallback
Do not implement fallback provider/model logic unless explicitly requested by user.

## 3. Request Envelope

### Standard Request
```python
@dataclass
class LLMRequest:
    prompt: str
    model: str
    temperature: float = 0.0  # deterministic by default
    max_tokens: int = 4096
    response_format: dict | None = None  # {"type": "json_object"} for structured output
    timeout_seconds: int = 60
    metadata: dict = field(default_factory=dict)
```

### Metadata Fields (Required)
- `agent_name`: str
- `stage`: str
- `run_id`: str
- `trace_id`: str
- `prompt_version`: str

## 4. Response Envelope

### Standard Response
```python
@dataclass
class LLMResponse:
    content: str
    model: str
    usage: TokenUsage
    finish_reason: str
    latency_ms: int
    metadata: dict
```

### TokenUsage
```python
@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

## 5. Error Classes

### Transient Errors (Retry)
- `RateLimitError`: 429 status
- `TimeoutError`: request timeout
- `ServiceUnavailableError`: 503 status
- `InternalServerError`: 500 status

### Permanent Errors (Fail Fast)
- `AuthenticationError`: 401 status
- `InvalidRequestError`: 400 status
- `ModelNotFoundError`: 404 status
- `ContentFilterError`: content policy violation

### Contract Errors (Fail Fast)
- `SchemaValidationError`: response does not match expected schema
- `ParseError`: cannot parse JSON response

## 6. Retry and Backoff Policy

### Retry Limits (from canonical retry doc)
- Transient API errors: max 3 retries
- Parse errors: max 1 retry with error context

### Backoff Strategy
```python
def calculate_backoff(attempt: int, error_type: str) -> float:
    """
    Transient errors:
      attempt 1: 0s (immediate)
      attempt 2: 2s
      attempt 3: 4s
      attempt 4: fail
    
    Rate limit errors:
      attempt 1: wait for retry-after header (max 60s)
      attempt 2: 30s
      attempt 3: 60s
      attempt 4: fail
    """
```

### Jitter
Add random jitter ±20% to backoff delays to avoid thundering herd.

## 7. Timeout Budgets

### Per-Stage Timeouts
| Stage | Timeout (seconds) |
|---|---:|
| Evidence extraction | 90 |
| ATT&CK mapping | 60 |
| DetectionSpec synthesis | 90 |
| Rule authoring | 60 |
| Rule refinement | 45 |
| Retrieval query planning | 30 |

### Timeout Behavior
- Hard timeout: cancel request and raise `TimeoutError`
- Retry budget applies after timeout

## 8. Token Accounting

### Per-Request Tracking
Persist for every LLM call:
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `cost_usd` (computed from model pricing)

### Aggregation
Track cumulative metrics per:
- `run_id`
- `agent_name`
- `report_id`

### Budget Gates (from KPI matrix)
Fail run if cumulative tokens exceed profile budget:
- strict: 120k tokens/report (p95)
- balanced: 90k tokens/report (p95)
- exploratory: 70k tokens/report (p95)

## 9. Structured Output Parsing

### JSON Mode
For all agent outputs, use:
```python
response_format = {"type": "json_object"}
```

### Schema Validation
After receiving response:
1. Parse JSON
2. Validate against agent-specific schema (from `docs/schemas/*.schema.json`)
3. Fail fast if validation fails

### Parse Retry
If parse fails:
- Retry once with error context appended to prompt
- If still fails, raise `ParseError` and mark agent run as failed

## 10. Observability

### Logging
Log every LLM call with:
- request metadata
- latency
- token usage
- error (if any)

### Metrics
Emit metrics for:
- `llm_call_count` (by agent, status)
- `llm_latency_ms` (p50, p95, p99)
- `llm_tokens_total` (by agent)
- `llm_cost_usd` (by agent)
- `llm_error_rate` (by error type)

## 11. Implementation

### Core Module
`src/de_forge/services/llm_client.py`

### Key Functions
```python
class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        ...
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        Execute LLM call with retry/backoff/timeout.
        Raises: LLMError subclasses on failure.
        """
    
    def call_with_schema(
        self,
        request: LLMRequest,
        schema: dict
    ) -> tuple[dict, LLMResponse]:
        """
        Execute call and validate response against JSON schema.
        Returns: (parsed_output, response_metadata)
        """
```

### Tests
- `tests/integration/services/test_llm_client.py`
  - test retry on transient errors
  - test timeout behavior
  - test schema validation
  - test token accounting

## 12. Cost Estimation

### Model Pricing (cx/gpt-5.5)
Assume pricing similar to GPT-4 class:
- Input: $0.01 / 1k tokens
- Output: $0.03 / 1k tokens

### Cost Calculation
```python
def calculate_cost(usage: TokenUsage) -> float:
    input_cost = (usage.prompt_tokens / 1000) * 0.01
    output_cost = (usage.completion_tokens / 1000) * 0.03
    return input_cost + output_cost
```

## 13. Security

### API Key Handling
- Never log API key
- Load from environment only
- Fail fast if missing

### Request Sanitization
- Strip PII from prompts if detected
- Validate prompt length before sending

### Response Handling
- Do not echo raw LLM output to logs
- Sanitize before persisting to database

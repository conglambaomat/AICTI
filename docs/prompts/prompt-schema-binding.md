# Prompt-Schema Binding Contract

Date: 2026-05-20
Scope: Hard binding between agent prompts and runtime JSON schemas

## 1. Purpose
Ensure every agent prompt is validated against a single machine-readable schema contract before stage advancement.

## 2. Binding Source of Truth
`docs/schemas/schema-registry.json`

## 3. Required Runtime Behavior
For each agent call:
1. Load schema id from registry by agent key.
2. Force JSON output mode.
3. Parse response JSON.
4. Validate against mapped schema.
5. If parse fails: retry once with parse error context.
6. If schema validation fails: fail-fast (`SchemaValidationError`).
7. If retry exhausted: raise `CONTRACT_VALIDATION_EXHAUSTED` abstain path where applicable.

## 4. Agent → Schema Mapping
- evidence -> `docs/schemas/evidence_output.schema.json`
- attack_mapping -> `docs/schemas/attack_mapping_output.schema.json`
- detection_spec -> `docs/schemas/detection_spec_output.schema.json`
- rule_authoring -> `docs/schemas/rule_output.schema.json`
- retrieval -> `docs/schemas/retrieval_result.schema.json`

## 5. Version Lock
- Provider/model must remain `cx/gpt-5.5`.
- Prompt pack version and schema registry version must be logged in metadata.

## 6. Gate Rule
No output is accepted by orchestration unless schema validation succeeds.

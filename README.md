# ai-threat-detection

DE-Forge là hệ thống multi-agent, evidence-grounded cho bài toán sinh detection rule từ threat report với ưu tiên độ chính xác, độ tin cậy và khả năng vận hành thực chiến.

## Setup

```bash
# Install dependencies
uv sync

# Run tests
pytest
```

## Development

```bash
# Planned backend command (placeholder until Milestone 1 creates app entrypoint)
uvicorn app.main:app --reload

# Alternative placeholder for src-based layout
# uv run python -m src.main
```

If `app.main` or `src.main` does not exist yet, these commands are placeholders until the core skeleton is implemented.

## Testing

```bash
# Unit + integration tests
pytest tests/ -v
```

## Documentation

### Project definition
- Project brief: `docs/project-brief.md`

### Architecture
- Overview: `docs/architecture/00-overview.md`
- Multi-agent design: `docs/architecture/01-multi-agent-design.md`
- Orchestration state machine: `docs/architecture/02-orchestration-state-machine.md`
- Dataflow: `docs/architecture/03-dataflow.md`

### Schemas and contracts
- DetectionSpec schema: `docs/schemas/detection-spec.md`
- Agent contracts: `docs/schemas/agent-contracts.md`
- Telemetry schema registry: `docs/schemas/telemetry-schema-registry.md`

### Implementation policy
- Core build plan: `docs/implementation/phase-1-core-build.md`
- Validation pipeline: `docs/implementation/validation-pipeline.md`
- Refinement policy: `docs/implementation/refinement-policy.md`

### Prompt pack
- Multi-agent prompts: `docs/prompts/multi-agent-prompts.md`

### Benchmark (deferred)
- CTI-REALM adapter design: `docs/benchmark/cti-realm-adapter-design.md`

### Superpowers workflow artifacts
- Design docs: `docs/superpowers/specs/`
- Implementation plans: `docs/superpowers/plans/`

## Current status
- Documentation foundation completed.
- Code implementation starts after design and planning approval flow.
- Priority: robust product-mode pipeline first, benchmark integration second.

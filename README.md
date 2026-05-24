# ai-threat-detection

DE-Forge is a single-user, production-grade, proof-carrying, evidence-graph controlled multi-agent detection engineering system for generating evidence-grounded Sigma detection artifacts from English TXT/PDF threat reports.

## Current implementation track

The active implementation track is **DE-Forge SOTA Core v2**.

Authoritative documentation layout is frozen to: `docs/canonical`, `docs/operational`, `docs/governance`, and `docs/legacy` (legacy is non-authoritative).

Before implementing, Claude CLI sessions must start with:

- `docs/operational/START_HERE_FOR_CLAUDE.md`

Then load governance policy:

- `docs/governance/canonical_manifest.yaml`
- `docs/governance/preflight_checklist.md`

Do not start implementation until preflight checks pass.

Source-of-truth documents:

- Execution kit: `docs/operational/SOTA_CORE_V2_EXECUTION_KIT.md`
- Quality gates: `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md`
- Blockers and escalation: `docs/operational/BLOCKERS_AND_ESCALATION.md`
- Approved design: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- Implementation plans: `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-*.md`

Older 2026-05-20 MVP/Agentic Deep-Analysis documents are superseded for implementation.

## Current status

The repository now contains substantial implementation beyond the initial skeleton phase. Treat status assertions as verification-bound: establish current truth from up-to-date verification commands and the current code and test tree, not from older progress claims.

## Setup

```bash
uv sync
```

If `uv` is unavailable, use the project virtual environment or ask before installing tooling.

## Run backend

```bash
uvicorn de_forge.main:app --reload
```

## Testing

```bash
pytest tests/ -v
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

Phase-specific commands are defined in `docs/operational/QUALITY_GATES_SOTA_CORE_V2.md` and the active implementation plan.

## Architecture invariant

Production detection artifacts must follow this path:

```text
raw report -> evidence graph -> verified DetectionSpec -> detection AST -> compiled Sigma -> validation/proof -> human review
```

There must be no raw-report-to-production-rule path.

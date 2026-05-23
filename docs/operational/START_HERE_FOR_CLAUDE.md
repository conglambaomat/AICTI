# START HERE FOR CLAUDE

This is the mandatory startup entrypoint for autonomous DE-Forge execution.

## Required Startup Order

1. Read `docs/governance/canonical_manifest.yaml`.
2. Run preflight from `docs/governance/preflight_checklist.md`.
3. Load authoritative operational docs listed in manifest.
4. Confirm canonical SOTA doc is available:
   - `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
5. Continue with active SOTA Core v2 plans under `docs/superpowers/plans/`.

## Non-Negotiable Rule

If canonical SOTA conflicts with code or other docs, canonical SOTA wins. Do not weaken architecture to match drift.

## Escalation Rule

Only escalate to user when:
- canonical file change is required, or
- change may weaken SOTA architecture invariants.

Otherwise continue autonomously with fail-closed governance gates.

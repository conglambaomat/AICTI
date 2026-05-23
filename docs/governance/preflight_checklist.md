# Preflight Checklist (Required Before Any Implementation)

## Session Startup Contract

Before coding, Claude CLI must execute this order:

1. Read `docs/governance/canonical_manifest.yaml`.
2. Resolve authoritative doc set by tier precedence.
3. Read `docs/operational/START_HERE_FOR_CLAUDE.md`.
4. Verify canonical doc exists and is reachable.
5. Verify all required operational docs exist.
6. Verify no active docs reference legacy docs as authority.
7. Verify no unresolved conflicts among authoritative docs.

## Fail-Closed Triggers

Stop immediately when any of the following is true:

- Missing canonical doc
- Missing required operational startup docs
- Conflicting architecture instructions in authoritative docs
- Required quality-gate/decision-policy docs missing

## Proceed Condition

Proceed only when all checks pass.

# Docs Governance Policy (Fail-Closed, Canonical-First)

## Purpose

Ensure Claude CLI can autonomously execute DE-Forge end-to-end with maximal correctness while preserving the original SOTA architecture.

## Core Rules

1. Canonical SOTA is supreme.
2. Operational docs can change autonomously only via two-step validation gate.
3. Legacy docs are never execution authority.
4. If required docs are missing or contradictory, stop execution (fail-closed).
5. Human escalation is only for canonical changes or SOTA weakening risk.

## Two-Step Update Gate

1. Propose patch in operational/governance docs.
2. Validate patch against required checks before applying.

If validation fails:
- rollback doc patch,
- continue code task,
- append warning entry in `docs/governance/doc_drift_warnings.md`.

## Required Validation Checks

- Canonical conflict check
- Active reference path check
- Stale phrase check in active docs
- Startup sequence integrity check
- Progress documentation schema check

## Progress Logging Requirement

A task is not complete until implementation progress is logged in:

- `docs/operational/IMPLEMENTATION_PROGRESS.md`
- `docs/operational/CHANGELOG_AUTONOMOUS.md`

with evidence (tests/gates + commit SHA).

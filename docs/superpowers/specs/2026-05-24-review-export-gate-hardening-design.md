---
title: Review and Export Gate Hardening Design
date: 2026-05-24
status: approved-for-planning
scope: P0 review/export gate hardening
---

# Review and Export Gate Hardening Design

## Problem

The review/export gate must enforce the SOTA Core v2 invariant that human review is mandatory before export. Current implementation has review persistence and export checks, but the handoff gate can be weakened by non-exact memory scope matching and review handoff payloads that do not truthfully represent the recorded decision.

Confirmed risks:

1. Review handoff memory is written with `{"approved": true}` regardless of whether the recorded decision is approved or rejected.
2. Review handoff lookup scans all latest memory scopes and checks `rule_id in scope`, allowing substring-based spoofing.
3. Review decision persistence loses API-level `run_id` and `comments` by storing `run_unknown` and empty comments through `ReviewService.record_decision`.
4. Review decision inputs are plain strings in the persistence API, so invalid decision values are not rejected at the service boundary.

## Goals

- Require exact review handoff identity before export.
- Persist human reviewer decisions with meaningful `run_id`, `decision`, `reviewer`, `comments`, and `created_at` values.
- Reject invalid review decisions before persistence.
- Preserve append-only review decision semantics.
- Preserve proof obligation checks before export.
- Add regression tests for spoofed handoff scope and rejected-review handoff semantics.

## Non-goals

- Do not redesign the full pipeline orchestrator.
- Do not change canonical architecture documents.
- Do not rewrite historical Alembic migrations.
- Do not introduce multi-user review or RBAC.
- Do not add external services or model/provider changes.

## Architecture

`ReviewService` remains the deterministic enforcement point for review/export policy. The service will accept a richer persisted decision request containing `rule_id`, `run_id`, `decision`, `reviewer`, and optional `comments`.

Review handoff memory will use an exact scope derived from the reviewed rule id. Export checks will query that exact scope instead of scanning all scopes with substring matching. The memory payload will mirror the actual decision and include the reviewer and decision id for auditability.

The latest append-only decision remains the source of truth for approval. Handoff memory is a required audit artifact, not a substitute for the latest decision. Export succeeds only when:

1. rule status is `awaiting_review`,
2. exact handoff memory exists for the rule,
3. latest decision for the rule is `approved`,
4. proof obligations are all acceptable under existing proof gate policy.

## Components

### Review API

The review decision request will include `run_id` and optional `comments`. The API will pass all fields to `ReviewService.record_decision`.

### ReviewService

`record_decision` will validate the decision value, persist the append-only row, and write exact review handoff memory. It will no longer hardcode `run_unknown`, empty comments, or approved handoff for rejected decisions.

`_has_review_handoff_memory` will query the exact handoff scope for a rule id and return true only when the payload exists and corresponds to an approved handoff.

### Export gate

`assert_can_export` keeps its current order: require handoff memory, require latest human approval, then enforce proof obligations. Error messages remain fail-closed and should not expose sensitive data.

## Data flow

1. Human reviewer submits a review decision through API or service.
2. Service validates the decision.
3. Service appends a row to `review_decisions`.
4. Service writes or updates the exact latest review handoff memory for that rule.
5. Export calls `assert_can_export`.
6. Export is blocked unless exact approved handoff, latest approved decision, valid status, and proof gates all pass.

## Testing

Add or update tests to cover:

- approved decision persists `run_id`, `reviewer`, `comments`, and `decision`,
- rejected decision writes non-approved handoff and blocks export,
- invalid decision value is rejected before persistence,
- handoff scope spoofing via substring does not satisfy export gate,
- latest rejected decision still blocks export after prior approval,
- existing proof-obligation export blocks continue to pass.

Target verification commands:

```bash
python -m pytest tests/unit/services/test_review_service.py tests/integration/services/test_review_gate.py tests/e2e/test_api_review_and_export.py -q
python -m pytest tests/integration/db tests/docs/test_manifest_freeze.py tests/docs/test_docs_preflight.py tests/docs/test_docs_references.py tests/docs/test_progress_templates.py -q
python scripts/docs_preflight.py
```

## Rollout

No migration is required unless implementation discovers a missing column at Alembic head. Current model and migration-chain tests pass, so changes should be service/API/test only.

## Acceptance criteria

- Review handoff cannot be spoofed by substring scope matching.
- Rejected reviews cannot create an approved handoff artifact.
- Review decision audit fields are persisted from caller input.
- Existing review/export/proof gates remain green.
- No SOTA Core v2 invariant is weakened.

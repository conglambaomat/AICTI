# DE-Forge UI Dashboard Enhancements Design

Date: 2026-05-22
Status: Approved for unattended low-risk implementation
Architecture name: Server-rendered Trust Review and Dashboard Add-on

## Goal

Extend the existing minimal DE-Forge review UI into a fuller trust-oriented server-rendered interface without changing the core SOTA Core v2 pipeline, model strategy, or validation gates.

This add-on implements the deferred UI/dashboard items from the orchestrator/UI plan in a reversible way:

- richer human review page,
- simple evidence graph visualization,
- editable Sigma review form,
- historical quality trend endpoint/page backed by in-memory sample snapshots for now.

## Scope

The implementation remains backend-only FastAPI with simple HTML responses and JSON endpoints. It does not introduce a frontend framework, authentication, multi-user behavior, persistent dashboard storage migrations, or external publishing.

## Architecture

Add a small UI support layer under `src/de_forge/ui_support/` that provides deterministic sample view models for the UI. FastAPI UI routes render those models into server-side HTML.

The existing `/api/ui/review` route remains the main review surface and is expanded to show:

- evidence quotes,
- evidence graph path,
- DetectionSpec summary,
- detection logic,
- Sigma condition,
- proof status,
- validation score,
- editable Sigma YAML textarea,
- review action controls.

Add `/api/ui/evidence-graph` as a simple text/HTML graph view and `/api/ui/dashboard` as a quality trend page. Add `/api/metrics/history` as a JSON source for historical quality snapshots.

## Data flow

Current deterministic services remain authoritative. The UI support layer only shapes data for display:

```text
services / schemas -> ui_support view models -> FastAPI HTML/JSON routes -> browser
```

No UI route may generate rules, bypass DetectionSpec verification, bypass proof obligations, or approve export without the existing review service.

## Error handling

The add-on uses static deterministic sample data until persistence-backed snapshots are implemented. Missing optional data renders as empty sections, not failed gates. Validation and export decisions remain controlled by existing services.

## Testing

Use TDD for each route/support addition:

1. tests fail for missing endpoint/content,
2. add minimal support model/route rendering,
3. target tests pass,
4. affected API/UI tests pass,
5. mypy, Ruff lint, Ruff format pass,
6. manual smoke test page load for the new UI pages.

## Invariants

This design preserves all SOTA Core v2 invariants:

1. no raw-report-to-production-rule path,
2. DetectionSpec remains mandatory before rule generation,
3. citations remain exact and verified by backend gates,
4. ATT&CK mapping chain remains unchanged,
5. proof obligations gate final selection,
6. Detection AST and compiler remain the source for Sigma YAML,
7. human review remains mandatory before export,
8. agent loops remain bounded,
9. feedback remains regression-oriented,
10. lineage/auditability remains visible rather than weakened.

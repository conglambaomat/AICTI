# Docs Precheck Commands

Run these checks before claiming doc readiness:

- Confirm startup doc exists: `docs/operational/START_HERE_FOR_CLAUDE.md`
- Confirm manifest exists: `docs/governance/canonical_manifest.yaml`
- Confirm canonical design exists: `docs/canonical/2026-05-21-de-forge-sota-core-v2-design.md`
- Confirm required operational docs exist per manifest
- Confirm no active references to legacy authority

## Final Readiness Command Sequence

```bash
python scripts/docs_preflight.py
pytest tests/docs/test_manifest_freeze.py tests/docs/test_docs_preflight.py tests/docs/test_docs_references.py tests/docs/test_progress_templates.py -v
```

## Required Success Markers

- `DOCS_PREFLIGHT: PASS`
- all tests pass

If any check fails, stop and repair docs first.

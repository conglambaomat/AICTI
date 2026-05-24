# DE-Forge Local Production Server Design

## Goal

Move DE-Forge from a verified runtime product path to a single-machine production-local server that starts reliably with SQLite, exposes operational inspection APIs, and can restart cleanly when an old process is occupying the configured port.

## Scope

This design targets local/server production use on one machine with SQLite. It intentionally excludes OCR for scanned PDFs, multi-user/auth/RBAC, multi-model/provider fallback, SIEM auto-deploy/export, CTI-REALM benchmark adapters, Docker/Postgres-first deployment, and a `de-forge doctor` command.

## Product entrypoint

The official runtime entrypoint becomes:

```bash
de-forge serve
```

The command performs a deterministic startup sequence:

1. Load settings from environment and defaults.
2. Validate required runtime configuration:
   - OpenAI-compatible base URL is present.
   - `OPENAI_API_KEY` is present.
   - model is the configured single model.
   - database URL uses the configured SQLite runtime path for local production.
3. Initialize SQLite schema if tables are missing.
4. Check the configured host/port.
5. If the port is occupied, aggressively terminate the process occupying that port.
6. Verify the port is free.
7. Start the FastAPI app with uvicorn.

The startup sequence must not delete or reset the SQLite database, artifacts, runs, audit records, review decisions, exports, `.env`, secrets, or Claude/session files.

## Aggressive auto-replace behavior

`de-forge serve` aggressively handles a stale server process by default. If the configured port is busy, the CLI locates the listening process, requests termination, waits briefly, then force-kills if the process remains. If the port remains occupied after this sequence, startup fails with a clear error.

This behavior is limited to process replacement. It is not a data reset mechanism. DB cleanup requires a separate future design and is not part of this scope.

The implementation should isolate process discovery and termination behind a `ProcessManager` interface so tests can verify behavior without killing real processes.

## SQLite local production hardening

SQLite remains the local production default. Startup must initialize missing schema through SQLAlchemy metadata creation, then verify the database connection can execute a trivial query.

For local robustness, the SQLite engine/session setup should support:

- connection-level `PRAGMA busy_timeout`;
- `PRAGMA journal_mode=WAL` when using a file-backed SQLite database;
- no schema drop or destructive reset;
- no migration fallback that silently changes architecture.

## Readiness endpoint

Add a readiness endpoint separate from liveness:

```http
GET /ready
```

`/health` remains a lightweight liveness check. `/ready` verifies:

- required runtime config is present;
- database session can connect and execute a simple query;
- application can serve runtime requests.

If readiness fails, it returns HTTP 503 with a sanitized reason. It must not leak API keys, raw report content, or secret values.

## Operations APIs

Add read-only runtime inspection APIs under the existing `/api` router:

```http
GET /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/artifacts
GET /api/runs/{run_id}/agent-runs
```

These APIs let a single-machine operator inspect runtime state without reading the SQLite database manually.

Expected behavior:

- `GET /api/runs` returns persisted runs ordered newest first or oldest first consistently.
- Optional state filtering may be included if small and test-covered.
- `GET /api/runs/{run_id}` returns run id, report id, mode, state, failure reason, and timestamps.
- `GET /api/runs/{run_id}/artifacts` returns artifact id, kind, stage, parent artifact ids, created_by, timestamps, and sanitized payload metadata. It must not expose raw full report text by default.
- `GET /api/runs/{run_id}/agent-runs` returns agent audit metadata: agent name, run id, input/output artifact ids, prompt/schema metadata when safe, success/failure status if available, and timestamps. It must not leak API keys.

## Runtime invariants

The design preserves all existing DE-Forge invariants:

- no raw-report-to-production-rule path;
- DetectionSpec remains mandatory before rule generation;
- evidence citations stay verified;
- proof obligations remain required before selectable/exportable candidates;
- human review remains mandatory before export;
- export remains separate from orchestration;
- runtime does not use fake LLM clients;
- runtime does not use state-only fallback;
- no model/provider fallback is introduced.

## Testing strategy

Implementation must use TDD.

Required test areas:

- CLI startup validates missing API key and fails before server start.
- CLI initializes missing SQLite schema.
- CLI aggressively terminates a fake occupied-port process via a fake process manager.
- CLI fails clearly when port remains occupied after termination attempts.
- CLI starts uvicorn through an injectable runner in tests, not by launching a real long-running server.
- `/ready` returns 200 when config and DB are usable.
- `/ready` returns 503 with sanitized detail when DB/config fails.
- ops APIs return persisted runs, run detail, artifact lineage, and agent audit metadata.
- ops APIs do not expose raw report text in artifact list payloads.
- full runtime product path tests still pass.

## Verification gates

Final verification must run:

```bash
python -m pytest tests/ -q
python -m mypy src/
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
DE_FORGE_DATABASE_URL="sqlite+pysqlite:////tmp/de_forge_runtime_clean.db" python - <<'PY'
from fastapi.testclient import TestClient
from de_forge.main import app

client = TestClient(app)
health = client.get("/health")
ready = client.get("/ready")
assert health.status_code == 200, health.text
assert ready.status_code == 200, ready.text
PY
```

Git commits must only stage files for the current task. Protected local files such as `.claude/settings.json`, `.claude/scheduled_tasks.lock`, `.claude/worktrees/`, `.env`, local DB files, caches, and secrets must remain unstaged and uncommitted.

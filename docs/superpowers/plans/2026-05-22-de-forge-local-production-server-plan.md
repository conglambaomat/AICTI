# DE-Forge Local Production Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-machine SQLite production server mode with `de-forge serve`, aggressive port process replacement, readiness checks, and read-only operational inspection APIs.

**Architecture:** Add a focused CLI layer that performs startup orchestration before launching uvicorn: validate runtime config, initialize SQLite schema, replace any process occupying the configured port, verify the port is free, and start the FastAPI app. Add small services for runtime startup, port/process management, readiness checks, and operational API read models while preserving the existing runtime product path and strict review/export gates.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, SQLAlchemy, SQLite, Pydantic v2, pytest, mypy, Ruff.

---

## File structure

- Modify `pyproject.toml` — add `de-forge` console script entrypoint.
- Create `src/de_forge/cli.py` — CLI command parser and `serve` entrypoint.
- Create `src/de_forge/services/runtime_config.py` — runtime config validation without leaking secrets.
- Create `src/de_forge/services/runtime_database.py` — SQLite schema init and connection verification.
- Create `src/de_forge/services/process_manager.py` — injectable port process discovery/termination abstraction.
- Create `src/de_forge/services/local_server.py` — startup sequence coordinator and uvicorn runner adapter.
- Modify `src/de_forge/db/session.py` — apply SQLite pragmas for file-backed SQLite engines.
- Modify `src/de_forge/main.py` — add `/ready` endpoint.
- Create `src/de_forge/schemas/ops.py` — response schemas for run/artifact/agent audit inspection.
- Create `src/de_forge/services/ops_repository.py` — read-only queries for runs, artifacts, and agent runs.
- Modify `src/de_forge/api/routes/runs.py` — add list/detail/artifacts/agent-runs endpoints.
- Add tests under `tests/unit/services/`, `tests/unit/cli/`, and `tests/integration/api/`.

---

### Task 1: Runtime config validation

**Files:**
- Create: `src/de_forge/services/runtime_config.py`
- Test: `tests/unit/services/test_runtime_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_runtime_config.py`:

```python
import pytest

from de_forge.core.config import Settings
from de_forge.core.errors import ValidationGateError
from de_forge.services.runtime_config import validate_local_production_config


def test_validate_local_production_config_requires_api_key() -> None:
    settings = Settings(openai_api_key=None)

    with pytest.raises(ValidationGateError, match="OPENAI_API_KEY is required"):
        validate_local_production_config(settings)


def test_validate_local_production_config_accepts_single_openai_compatible_model() -> None:
    settings = Settings(
        openai_api_key="test-key",
        openai_base_url="https://shopapikey.com/v1",
        openai_model="cx/gpt-5.5",
        database_url="sqlite+pysqlite:///./de_forge.db",
    )

    result = validate_local_production_config(settings)

    assert result.openai_base_url == "https://shopapikey.com/v1"
    assert result.openai_model == "cx/gpt-5.5"
    assert result.database_url == "sqlite+pysqlite:///./de_forge.db"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.runtime_config'`.

- [ ] **Step 3: Implement runtime config validation**

Create `src/de_forge/services/runtime_config.py`:

```python
from dataclasses import dataclass

from de_forge.core.config import Settings
from de_forge.core.errors import ValidationGateError


@dataclass(frozen=True)
class LocalProductionConfig:
    openai_base_url: str
    openai_model: str
    database_url: str
    host: str
    port: int


def validate_local_production_config(settings: Settings) -> LocalProductionConfig:
    if not settings.openai_api_key:
        raise ValidationGateError("OPENAI_API_KEY is required")
    if not settings.openai_base_url:
        raise ValidationGateError("OpenAI-compatible base URL is required")
    if not settings.openai_model:
        raise ValidationGateError("OpenAI-compatible model is required")
    if not settings.database_url.startswith("sqlite"):
        raise ValidationGateError("local production mode requires SQLite database URL")
    return LocalProductionConfig(
        openai_base_url=str(settings.openai_base_url),
        openai_model=settings.openai_model,
        database_url=settings.database_url,
        host=settings.host,
        port=settings.port,
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_config.py tests/unit/core/test_runtime_product_settings.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/runtime_config.py tests/unit/services/test_runtime_config.py
git commit -m "$(cat <<'EOF'
feat(runtime): validate local production config

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: SQLite runtime database initialization

**Files:**
- Create: `src/de_forge/services/runtime_database.py`
- Modify: `src/de_forge/db/session.py`
- Test: `tests/unit/services/test_runtime_database.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_runtime_database.py`:

```python
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from de_forge.models.run_record import RunRecord
from de_forge.services.runtime_database import initialize_runtime_database, verify_database_ready


def test_initialize_runtime_database_creates_missing_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime.db"
    database_url = f"sqlite+pysqlite:///{db_path}"

    initialize_runtime_database(database_url)

    engine = create_engine(database_url)
    with Session(engine) as session:
        session.add(RunRecord(id="run_1", report_id="report_1", mode="auto", state="created"))
        session.commit()


def test_verify_database_ready_executes_query(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    initialize_runtime_database(database_url)

    assert verify_database_ready(database_url) is True

    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert connection.execute(text("select 1")).scalar_one() == 1
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_database.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.runtime_database'`.

- [ ] **Step 3: Implement database init service**

Create `src/de_forge/services/runtime_database.py`:

```python
from sqlalchemy import create_engine, text

from de_forge.db.base import Base


def initialize_runtime_database(database_url: str) -> None:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    engine.dispose()


def verify_database_ready(database_url: str) -> bool:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1")).scalar_one()
        return True
    finally:
        engine.dispose()
```

Modify `src/de_forge/db/session.py` to apply SQLite pragmas:

```python
from sqlalchemy import create_engine, event
...
engine = create_engine(settings.database_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection: object, connection_record: object) -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA busy_timeout=5000")
    if settings.database_url not in {"sqlite+pysqlite://", "sqlite+pysqlite:///:memory:"}:
        cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

Use `Any` or protocol-compatible typing if mypy requires it:

```python
from typing import Any
...
def _set_sqlite_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_database.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_database.py tests/integration/db/test_run_repository.py tests/integration/db/test_artifact_graph_persistence.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/runtime_database.py src/de_forge/db/session.py tests/unit/services/test_runtime_database.py
git commit -m "$(cat <<'EOF'
feat(runtime): initialize local sqlite database

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Aggressive port process replacement

**Files:**
- Create: `src/de_forge/services/process_manager.py`
- Test: `tests/unit/services/test_process_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_process_manager.py`:

```python
from de_forge.services.process_manager import ProcessManager, replace_process_on_port


class RecordingProcessManager(ProcessManager):
    def __init__(self, pids: list[int]) -> None:
        self.pids = pids
        self.terminated: list[int] = []
        self.killed: list[int] = []
        self.waited: list[int] = []

    def find_listening_pids(self, host: str, port: int) -> list[int]:
        return list(self.pids)

    def terminate(self, pid: int) -> None:
        self.terminated.append(pid)

    def wait_for_exit(self, pid: int, timeout_seconds: float) -> bool:
        self.waited.append(pid)
        return False

    def kill(self, pid: int) -> None:
        self.killed.append(pid)
        self.pids.remove(pid)


def test_replace_process_on_port_terminates_and_kills_busy_port() -> None:
    manager = RecordingProcessManager([1234])

    replace_process_on_port("127.0.0.1", 8000, manager)

    assert manager.terminated == [1234]
    assert manager.waited == [1234]
    assert manager.killed == [1234]


def test_replace_process_on_port_does_nothing_when_port_free() -> None:
    manager = RecordingProcessManager([])

    replace_process_on_port("127.0.0.1", 8000, manager)

    assert manager.terminated == []
    assert manager.killed == []
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/unit/services/test_process_manager.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.process_manager'`.

- [ ] **Step 3: Implement process manager abstraction**

Create `src/de_forge/services/process_manager.py`:

```python
import os
import signal
import socket
import subprocess
import sys
import time
from abc import ABC, abstractmethod

from de_forge.core.errors import ValidationGateError


class ProcessManager(ABC):
    @abstractmethod
    def find_listening_pids(self, host: str, port: int) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def terminate(self, pid: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def wait_for_exit(self, pid: int, timeout_seconds: float) -> bool:
        raise NotImplementedError

    @abstractmethod
    def kill(self, pid: int) -> None:
        raise NotImplementedError


class SystemProcessManager(ProcessManager):
    def find_listening_pids(self, host: str, port: int) -> list[int]:
        if sys.platform.startswith("win"):
            return self._find_windows_pids(port)
        return self._find_unix_pids(port)

    def terminate(self, pid: int) -> None:
        os.kill(pid, signal.SIGTERM)

    def wait_for_exit(self, pid: int, timeout_seconds: float) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if not self._pid_exists(pid):
                return True
            time.sleep(0.05)
        return not self._pid_exists(pid)

    def kill(self, pid: int) -> None:
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
            return
        os.kill(pid, signal.SIGKILL)

    def _pid_exists(self, pid: int) -> bool:
        if sys.platform.startswith("win"):
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"], check=False, capture_output=True, text=True
            )
            return str(pid) in result.stdout
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    def _find_unix_pids(self, port: int) -> list[int]:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], check=False, capture_output=True, text=True
        )
        return [int(line) for line in result.stdout.splitlines() if line.strip().isdigit()]

    def _find_windows_pids(self, port: int) -> list[int]:
        result = subprocess.run(["netstat", "-ano"], check=False, capture_output=True, text=True)
        pids: set[int] = set()
        marker = f":{port}"
        for line in result.stdout.splitlines():
            if marker not in line or "LISTENING" not in line:
                continue
            parts = line.split()
            if parts and parts[-1].isdigit():
                pids.add(int(parts[-1]))
        return sorted(pids)


def assert_port_free(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        if sock.connect_ex((host, port)) == 0:
            raise ValidationGateError(f"port {port} is still occupied")


def replace_process_on_port(host: str, port: int, manager: ProcessManager) -> None:
    pids = manager.find_listening_pids(host, port)
    for pid in pids:
        manager.terminate(pid)
        if not manager.wait_for_exit(pid, timeout_seconds=2.0):
            manager.kill(pid)
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python -m pytest tests/unit/services/test_process_manager.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected checks**

Run:

```bash
python -m pytest tests/unit/services/test_process_manager.py -v
python -m mypy src/de_forge/services/process_manager.py
```

Expected: PASS and mypy success.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/process_manager.py tests/unit/services/test_process_manager.py
git commit -m "$(cat <<'EOF'
feat(runtime): replace process occupying server port

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Local production server coordinator and CLI

**Files:**
- Create: `src/de_forge/services/local_server.py`
- Create: `src/de_forge/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/services/test_local_server.py`
- Test: `tests/unit/test_cli.py`

- [ ] **Step 1: Write failing service tests**

Create `tests/unit/services/test_local_server.py`:

```python
from dataclasses import dataclass

from de_forge.core.config import Settings
from de_forge.services.local_server import LocalServerRunner, UvicornServerRunner, start_local_server
from de_forge.services.process_manager import ProcessManager


class RecordingProcessManager(ProcessManager):
    def __init__(self) -> None:
        self.replaced: list[tuple[str, int]] = []

    def find_listening_pids(self, host: str, port: int) -> list[int]:
        self.replaced.append((host, port))
        return []

    def terminate(self, pid: int) -> None:
        raise AssertionError("no pid expected")

    def wait_for_exit(self, pid: int, timeout_seconds: float) -> bool:
        raise AssertionError("no pid expected")

    def kill(self, pid: int) -> None:
        raise AssertionError("no pid expected")


@dataclass
class RecordingRunner(LocalServerRunner):
    calls: list[tuple[str, int]]

    def run(self, host: str, port: int) -> None:
        self.calls.append((host, port))


def test_start_local_server_initializes_replaces_port_and_runs_server(tmp_path, monkeypatch) -> None:
    initialized: list[str] = []
    verified: list[str] = []

    monkeypatch.setattr(
        "de_forge.services.local_server.initialize_runtime_database", lambda url: initialized.append(url)
    )
    monkeypatch.setattr(
        "de_forge.services.local_server.verify_database_ready", lambda url: verified.append(url) or True
    )
    monkeypatch.setattr("de_forge.services.local_server.assert_port_free", lambda host, port: None)

    manager = RecordingProcessManager()
    runner = RecordingRunner([])
    settings = Settings(
        openai_api_key="test-key",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}",
        host="127.0.0.1",
        port=8123,
    )

    start_local_server(settings=settings, process_manager=manager, runner=runner)

    assert initialized == [settings.database_url]
    assert verified == [settings.database_url]
    assert manager.replaced == [("127.0.0.1", 8123)]
    assert runner.calls == [("127.0.0.1", 8123)]


def test_uvicorn_runner_targets_de_forge_app(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    monkeypatch.setattr("de_forge.services.local_server.uvicorn.run", lambda *args, **kwargs: calls.append(kwargs))

    UvicornServerRunner().run("127.0.0.1", 8123)

    assert calls == [{"host": "127.0.0.1", "port": 8123}]
```

- [ ] **Step 2: Run service tests to verify failure**

Run:

```bash
python -m pytest tests/unit/services/test_local_server.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'de_forge.services.local_server'`.

- [ ] **Step 3: Implement local server coordinator**

Create `src/de_forge/services/local_server.py`:

```python
from abc import ABC, abstractmethod

import uvicorn

from de_forge.core.config import Settings, settings as default_settings
from de_forge.core.errors import ValidationGateError
from de_forge.services.process_manager import (
    ProcessManager,
    SystemProcessManager,
    assert_port_free,
    replace_process_on_port,
)
from de_forge.services.runtime_config import validate_local_production_config
from de_forge.services.runtime_database import initialize_runtime_database, verify_database_ready


class LocalServerRunner(ABC):
    @abstractmethod
    def run(self, host: str, port: int) -> None:
        raise NotImplementedError


class UvicornServerRunner(LocalServerRunner):
    def run(self, host: str, port: int) -> None:
        uvicorn.run("de_forge.main:app", host=host, port=port)


def start_local_server(
    settings: Settings = default_settings,
    process_manager: ProcessManager | None = None,
    runner: LocalServerRunner | None = None,
) -> None:
    config = validate_local_production_config(settings)
    initialize_runtime_database(config.database_url)
    if not verify_database_ready(config.database_url):
        raise ValidationGateError("database is not ready")
    active_process_manager = process_manager or SystemProcessManager()
    replace_process_on_port(config.host, config.port, active_process_manager)
    assert_port_free(config.host, config.port)
    active_runner = runner or UvicornServerRunner()
    active_runner.run(config.host, config.port)
```

- [ ] **Step 4: Write failing CLI tests**

Create `tests/unit/test_cli.py`:

```python
from de_forge import cli


def test_cli_serve_calls_local_server(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(cli, "start_local_server", lambda: calls.append("serve"))

    assert cli.main(["serve"]) == 0
    assert calls == ["serve"]


def test_cli_rejects_unknown_command() -> None:
    assert cli.main(["unknown"]) == 2
```

Run:

```bash
python -m pytest tests/unit/test_cli.py -v
```

Expected: FAIL because `de_forge.cli` does not exist.

- [ ] **Step 5: Implement CLI and console script**

Create `src/de_forge/cli.py`:

```python
import argparse
from collections.abc import Sequence

from de_forge.core.errors import ValidationGateError
from de_forge.services.local_server import start_local_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="de-forge")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("serve")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            start_local_server()
            return 0
    except ValidationGateError as exc:
        parser.exit(1, f"de-forge: {exc}\n")
    return 2
```

Modify `pyproject.toml` under `[project]` metadata by adding:

```toml
[project.scripts]
de-forge = "de_forge.cli:main"
```

- [ ] **Step 6: Run tests to verify pass**

Run:

```bash
python -m pytest tests/unit/services/test_local_server.py tests/unit/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 7: Run affected checks**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_config.py tests/unit/services/test_runtime_database.py tests/unit/services/test_process_manager.py tests/unit/services/test_local_server.py tests/unit/test_cli.py -v
python -m mypy src/de_forge/cli.py src/de_forge/services/local_server.py
```

Expected: PASS and mypy success.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/de_forge/cli.py src/de_forge/services/local_server.py tests/unit/test_cli.py tests/unit/services/test_local_server.py
git commit -m "$(cat <<'EOF'
feat(runtime): add local production serve cli

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Readiness endpoint

**Files:**
- Modify: `src/de_forge/main.py`
- Create: `src/de_forge/services/readiness.py`
- Test: `tests/integration/api/test_readiness.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/api/test_readiness.py`:

```python
from fastapi.testclient import TestClient

from de_forge import main
from de_forge.main import app


def test_ready_returns_200_when_runtime_ready(monkeypatch) -> None:
    monkeypatch.setattr(main, "check_readiness", lambda: None)
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_returns_503_with_sanitized_detail(monkeypatch) -> None:
    def fail() -> None:
        raise RuntimeError("database unavailable for key secret-value")

    monkeypatch.setattr(main, "check_readiness", fail)
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "runtime is not ready"}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/integration/api/test_readiness.py -v
```

Expected: FAIL with 404 for `/ready` or missing `check_readiness`.

- [ ] **Step 3: Implement readiness service and endpoint**

Create `src/de_forge/services/readiness.py`:

```python
from de_forge.core.config import settings
from de_forge.services.runtime_config import validate_local_production_config
from de_forge.services.runtime_database import verify_database_ready


def check_readiness() -> None:
    config = validate_local_production_config(settings)
    verify_database_ready(config.database_url)
```

Modify `src/de_forge/main.py`:

```python
from fastapi import FastAPI, HTTPException
...
from de_forge.services.readiness import check_readiness
...
@app.get("/ready")
def ready() -> dict[str, str]:
    try:
        check_readiness()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="runtime is not ready") from exc
    return {"status": "ready"}
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
python -m pytest tests/integration/api/test_readiness.py -v
```

Expected: PASS.

- [ ] **Step 5: Run affected tests**

Run:

```bash
python -m pytest tests/integration/api/test_readiness.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/main.py src/de_forge/services/readiness.py tests/integration/api/test_readiness.py
git commit -m "$(cat <<'EOF'
feat(runtime): add readiness endpoint

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Operational run inspection APIs

**Files:**
- Create: `src/de_forge/schemas/ops.py`
- Create: `src/de_forge/services/ops_repository.py`
- Modify: `src/de_forge/api/routes/runs.py`
- Test: `tests/integration/api/test_ops_routes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/api/test_ops_routes.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes import runs
from de_forge.db.base import Base
from de_forge.main import app
from de_forge.schemas.artifact import ArtifactKind
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.agent_audit import AgentAuditService
from de_forge.services.product_artifacts import ProductArtifactService
from de_forge.services.run_repository import RunRepository


def _session_factory():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_ops_routes_return_run_detail_artifacts_and_agent_audits(monkeypatch) -> None:
    session_testing = _session_factory()
    with session_testing() as session:
        repository = RunRepository(session)
        repository.create_run("run_1", "report_1", RunMode.AUTO, RunState.AWAITING_REVIEW)
        artifact = ProductArtifactService(session).create_artifact(
            "run_1",
            ArtifactKind.REPORT,
            "ingestion",
            {"report_id": "report_1", "text": "raw report should not leak"},
            [],
            "test",
        )
        AgentAuditService(session).persist(
            input_payload={"input_artifact_ids": [artifact.id]},
            result=type(
                "AgentResult",
                (),
                {
                    "run_id": "run_1",
                    "agent_name": "evidence_agent",
                    "input_artifact_ids": [artifact.id],
                    "output": {"ok": True},
                },
            )(),
        )
        session.commit()

    monkeypatch.setattr(runs, "SessionLocal", session_testing)
    client = TestClient(app)

    list_response = client.get("/api/runs")
    detail_response = client.get("/api/runs/run_1")
    artifacts_response = client.get("/api/runs/run_1/artifacts")
    agents_response = client.get("/api/runs/run_1/agent-runs")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == "run_1"
    assert detail_response.status_code == 200
    assert detail_response.json()["state"] == "awaiting_review"
    assert artifacts_response.status_code == 200
    assert artifacts_response.json()[0]["kind"] == "report"
    assert "raw report should not leak" not in artifacts_response.text
    assert agents_response.status_code == 200
    assert agents_response.json()[0]["agent_name"] == "evidence_agent"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/integration/api/test_ops_routes.py -v
```

Expected: FAIL because ops endpoints do not exist.

- [ ] **Step 3: Implement schemas**

Create `src/de_forge/schemas/ops.py`:

```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RunOpsResponse(BaseModel):
    id: str
    report_id: str
    mode: str
    state: str
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime


class ArtifactOpsResponse(BaseModel):
    id: str
    run_id: str
    kind: str
    stage: str
    parent_artifact_ids: list[str]
    created_by: str
    payload_keys: list[str]
    created_at: datetime


class AgentRunOpsResponse(BaseModel):
    id: str
    run_id: str
    agent_name: str
    input_artifact_ids: list[str]
    output_keys: list[str]
    created_at: datetime
```

- [ ] **Step 4: Implement ops repository**

Create `src/de_forge/services/ops_repository.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models.agent_run import AgentRun
from de_forge.models.artifact import Artifact
from de_forge.models.run_record import RunRecord
from de_forge.schemas.ops import AgentRunOpsResponse, ArtifactOpsResponse, RunOpsResponse


class OpsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_runs(self) -> list[RunOpsResponse]:
        records = self.session.scalars(select(RunRecord).order_by(RunRecord.created_at)).all()
        return [self._run_response(record) for record in records]

    def get_run(self, run_id: str) -> RunOpsResponse:
        record = self.session.get(RunRecord, run_id)
        if record is None:
            raise KeyError(run_id)
        return self._run_response(record)

    def artifacts_for_run(self, run_id: str) -> list[ArtifactOpsResponse]:
        records = self.session.scalars(
            select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at)
        ).all()
        return [
            ArtifactOpsResponse(
                id=record.id,
                run_id=record.run_id,
                kind=record.kind,
                stage=record.stage,
                parent_artifact_ids=record.parent_artifact_ids,
                created_by=record.created_by,
                payload_keys=sorted(record.payload.keys()),
                created_at=record.created_at,
            )
            for record in records
        ]

    def agent_runs_for_run(self, run_id: str) -> list[AgentRunOpsResponse]:
        records = self.session.scalars(
            select(AgentRun).where(AgentRun.run_id == run_id).order_by(AgentRun.created_at)
        ).all()
        return [
            AgentRunOpsResponse(
                id=record.id,
                run_id=record.run_id,
                agent_name=record.agent_name,
                input_artifact_ids=record.input_artifact_ids,
                output_keys=sorted(record.output_payload.keys()),
                created_at=record.created_at,
            )
            for record in records
        ]

    def _run_response(self, record: RunRecord) -> RunOpsResponse:
        return RunOpsResponse(
            id=record.id,
            report_id=record.report_id,
            mode=record.mode,
            state=record.state,
            failure_reason=record.failure_reason,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
```

- [ ] **Step 5: Implement route endpoints**

Modify `src/de_forge/api/routes/runs.py`:

```python
from fastapi import APIRouter, HTTPException
...
from de_forge.db.session import SessionLocal
from de_forge.schemas.ops import AgentRunOpsResponse, ArtifactOpsResponse, RunOpsResponse
from de_forge.services.ops_repository import OpsRepository
...
@router.get("", response_model=list[RunOpsResponse])
def list_runs() -> list[RunOpsResponse]:
    with SessionLocal() as session:
        return OpsRepository(session).list_runs()


@router.get("/{run_id}", response_model=RunOpsResponse)
def get_run(run_id: str) -> RunOpsResponse:
    try:
        with SessionLocal() as session:
            return OpsRepository(session).get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc


@router.get("/{run_id}/artifacts", response_model=list[ArtifactOpsResponse])
def get_run_artifacts(run_id: str) -> list[ArtifactOpsResponse]:
    with SessionLocal() as session:
        repository = OpsRepository(session)
        repository.get_run(run_id)
        return repository.artifacts_for_run(run_id)


@router.get("/{run_id}/agent-runs", response_model=list[AgentRunOpsResponse])
def get_run_agent_runs(run_id: str) -> list[AgentRunOpsResponse]:
    with SessionLocal() as session:
        repository = OpsRepository(session)
        repository.get_run(run_id)
        return repository.agent_runs_for_run(run_id)
```

Keep the existing `/golden` route intact. Define static `/golden` route before `/{run_id}` so route matching remains correct.

- [ ] **Step 6: Run tests to verify pass**

Run:

```bash
python -m pytest tests/integration/api/test_ops_routes.py -v
```

Expected: PASS.

- [ ] **Step 7: Run affected tests**

Run:

```bash
python -m pytest tests/integration/api/test_ops_routes.py tests/integration/api/test_api_routes.py tests/integration/api/test_runtime_ui_routes.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/de_forge/schemas/ops.py src/de_forge/services/ops_repository.py src/de_forge/api/routes/runs.py tests/integration/api/test_ops_routes.py
git commit -m "$(cat <<'EOF'
feat(ops): expose local runtime inspection APIs

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Final local production verification

**Files:**
- Modify only files required to fix failures found by verification.
- Do not stage protected local files.

- [ ] **Step 1: Run runtime-focused tests**

Run:

```bash
python -m pytest tests/unit/services/test_runtime_config.py tests/unit/services/test_runtime_database.py tests/unit/services/test_process_manager.py tests/unit/services/test_local_server.py tests/unit/test_cli.py tests/integration/api/test_readiness.py tests/integration/api/test_ops_routes.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest tests/ -q
```

Expected: `110+ passed` with no failures. The exact count may increase as this plan adds tests.

- [ ] **Step 3: Run type checking**

Run:

```bash
python -m mypy src/
```

Expected: `Success: no issues found`.

- [ ] **Step 4: Run lint**

Run:

```bash
python -m ruff check src/ tests/
```

Expected: `All checks passed!`.

- [ ] **Step 5: Run format check**

Run:

```bash
python -m ruff format --check src/ tests/
```

Expected: all files already formatted.

- [ ] **Step 6: Run clean SQLite startup readiness check**

Run:

```bash
DE_FORGE_DATABASE_URL="sqlite+pysqlite:////tmp/de_forge_runtime_clean.db" OPENAI_API_KEY="test-placeholder-api-key" python - <<'PY'
from fastapi.testclient import TestClient
from de_forge.main import app

client = TestClient(app)
health = client.get("/health")
ready = client.get("/ready")
assert health.status_code == 200, health.text
assert ready.status_code == 200, ready.text
PY
```

Expected: command exits 0.

- [ ] **Step 7: Verify protected files remain unstaged**

Run:

```bash
git status --short
```

Expected: any `.claude/settings.json`, `.claude/scheduled_tasks.lock`, `.claude/worktrees/`, `.env`, cache files, or local DB files remain unstaged/untracked and are not included in commits.

- [ ] **Step 8: Commit verification fixes if any**

If verification required lint/format/test fixes, commit only those source/test files:

```bash
git add <specific verified files>
git commit -m "$(cat <<'EOF'
chore(runtime): complete local production verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

If no files changed, do not create an empty commit.

---

## Self-review

Spec coverage:
- `de-forge serve` CLI is covered by Task 4.
- Runtime config validation is covered by Task 1.
- SQLite schema init and DB readiness are covered by Task 2 and Task 5.
- Aggressive process replacement is covered by Task 3 and integrated in Task 4.
- No `de-forge doctor` command is included.
- Ops APIs are covered by Task 6.
- Final verification and protected file handling are covered by Task 7.

Placeholder scan:
- No TBD/TODO/fill-in placeholders remain.
- All test and implementation steps include concrete file paths, commands, and expected results.

Type consistency:
- `LocalProductionConfig`, `ProcessManager`, `LocalServerRunner`, `OpsRepository`, and ops response schema names are defined before use.
- Route names and endpoint paths match the approved design.

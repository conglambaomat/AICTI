from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from de_forge.services.schema_guard import SchemaContractError, SchemaGuard

REQUIRED_AGENT_RUNS_DDL = """
CREATE TABLE agent_runs (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    prompt_version VARCHAR(64) NOT NULL DEFAULT 'unknown',
    model_id VARCHAR(120) NOT NULL DEFAULT 'unknown',
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    cost_usd FLOAT NOT NULL DEFAULT 0,
    input_payload_json TEXT NOT NULL DEFAULT '{}',
    output_payload_json TEXT NOT NULL DEFAULT '{}',
    artifact_ids_json TEXT NOT NULL DEFAULT '[]'
)
"""


def _build_engine_with_required_agent_runs_table() -> object:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text(REQUIRED_AGENT_RUNS_DDL))
        conn.execute(text("CREATE INDEX ix_agent_runs_run_id ON agent_runs (run_id)"))
        conn.execute(text("CREATE INDEX ix_agent_runs_trace_id ON agent_runs (trace_id)"))
        conn.execute(text("CREATE INDEX ix_agent_runs_agent_name ON agent_runs (agent_name)"))
    return engine


def test_schema_guard_passes_when_agent_runs_contract_is_complete() -> None:
    engine = _build_engine_with_required_agent_runs_table()

    SchemaGuard(engine).assert_contract_current()


def test_schema_guard_fails_when_required_agent_runs_column_missing() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE agent_runs (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX ix_agent_runs_run_id ON agent_runs (run_id)"))
        conn.execute(text("CREATE INDEX ix_agent_runs_trace_id ON agent_runs (trace_id)"))
        conn.execute(text("CREATE INDEX ix_agent_runs_agent_name ON agent_runs (agent_name)"))

    with pytest.raises(SchemaContractError, match="missing agent_runs columns"):
        SchemaGuard(engine).assert_contract_current()


def test_schema_guard_fails_when_required_agent_runs_index_missing() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text(REQUIRED_AGENT_RUNS_DDL))
        conn.execute(text("CREATE INDEX ix_agent_runs_run_id ON agent_runs (run_id)"))
        conn.execute(text("CREATE INDEX ix_agent_runs_trace_id ON agent_runs (trace_id)"))

    with pytest.raises(SchemaContractError, match="missing agent_runs indexes"):
        SchemaGuard(engine).assert_contract_current()

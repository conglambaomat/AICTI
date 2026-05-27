from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from de_forge.db.base import Base
from de_forge.models import *  # noqa: F403
from de_forge.models.artifact import Artifact, ArtifactLink  # noqa: F401
from de_forge.models.evidence_graph import EvidenceEdge, EvidenceNode  # noqa: F401
from de_forge.services.schema_guard import SchemaContractError, SchemaGuard


def _build_complete_schema_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine


def test_schema_guard_passes_when_critical_schema_is_complete() -> None:
    engine = _build_complete_schema_engine()

    SchemaGuard(engine).assert_contract_current()


def test_schema_guard_fails_when_critical_table_missing() -> None:
    engine = _build_complete_schema_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE graph_nodes"))

    with pytest.raises(SchemaContractError, match="missing table graph_nodes"):
        SchemaGuard(engine).assert_contract_current()


def test_schema_guard_fails_when_required_agent_runs_column_missing() -> None:
    engine = _build_complete_schema_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE agent_runs"))
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
    engine = _build_complete_schema_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX ix_agent_runs_agent_name"))

    with pytest.raises(SchemaContractError, match="missing agent_runs indexes"):
        SchemaGuard(engine).assert_contract_current()

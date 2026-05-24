from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine.interfaces import ReflectedIndex
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import Session


class SchemaContractError(RuntimeError):
    pass


_REQUIRED_AGENT_RUNS_COLUMNS = {
    "prompt_version",
    "model_id",
    "tokens_in",
    "tokens_out",
    "latency_ms",
    "cost_usd",
    "input_payload_json",
    "output_payload_json",
    "artifact_ids_json",
}

_REQUIRED_AGENT_RUNS_INDEXES = {
    "ix_agent_runs_run_id",
    "ix_agent_runs_trace_id",
    "ix_agent_runs_agent_name",
}


class SchemaGuard:
    def __init__(self, engine: Engine | Connection) -> None:
        self.engine = engine

    def assert_contract_current(self) -> None:
        inspector = inspect(self.engine)
        table_names = set(inspector.get_table_names())
        if "agent_runs" not in table_names:
            raise SchemaContractError("schema drift: missing table agent_runs")

        self._assert_agent_runs_columns(inspector)
        self._assert_agent_runs_indexes(inspector)

    def _assert_agent_runs_columns(self, inspector: Inspector) -> None:
        try:
            columns = {column["name"] for column in inspector.get_columns("agent_runs")}
        except NoSuchTableError as exc:
            raise SchemaContractError("schema drift: missing table agent_runs") from exc

        missing = sorted(_REQUIRED_AGENT_RUNS_COLUMNS - columns)
        if missing:
            raise SchemaContractError(
                f"schema drift: missing agent_runs columns: {', '.join(missing)}"
            )

    def _assert_agent_runs_indexes(self, inspector: Inspector) -> None:
        index_rows: list[ReflectedIndex] = inspector.get_indexes("agent_runs")
        index_names = {index["name"] for index in index_rows}
        missing = sorted(_REQUIRED_AGENT_RUNS_INDEXES - index_names)
        if missing:
            raise SchemaContractError(
                f"schema drift: missing agent_runs indexes: {', '.join(missing)}"
            )


def assert_schema_contract_current(db: Session) -> None:
    SchemaGuard(db.get_bind()).assert_contract_current()

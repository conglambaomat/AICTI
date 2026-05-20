"""Integration tests for Alembic migration persistence contract."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.fixture()
def migrated_engine(tmp_path: Path):
    """Apply migrations to a temporary SQLite database and return engine."""
    db_path = tmp_path / "contract.db"
    alembic_ini_path = Path(__file__).resolve().parents[3] / "alembic.ini"

    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[3] / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        yield engine
    finally:
        engine.dispose()


def test_expected_core_tables_exist(migrated_engine) -> None:
    """Expected core persistence tables must exist after migration."""
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())

    expected = {
        "reports",
        "report_chunks",
        "evidence_spans",
        "attack_mappings",
        "telemetry_selections",
        "detection_specs",
        "generated_rules",
        "validation_results",
        "test_runs",
        "agent_runs",
        "review_decisions",
        "refinement_iterations",
    }

    assert expected.issubset(tables)


def test_foreign_keys_match_core_contract(migrated_engine) -> None:
    """Implemented tables must have required foreign key relationships."""
    inspector = inspect(migrated_engine)

    chunks_fks = inspector.get_foreign_keys("report_chunks")
    assert any(
        fk["referred_table"] == "reports" and fk["constrained_columns"] == ["report_id"]
        for fk in chunks_fks
    )

    evidence_fks = inspector.get_foreign_keys("evidence_spans")
    assert any(
        fk["referred_table"] == "reports" and fk["constrained_columns"] == ["report_id"]
        for fk in evidence_fks
    )
    assert any(
        fk["referred_table"] == "report_chunks" and fk["constrained_columns"] == ["chunk_id"]
        for fk in evidence_fks
    )

    attack_fks = inspector.get_foreign_keys("attack_mappings")
    assert any(
        fk["referred_table"] == "reports" and fk["constrained_columns"] == ["report_id"]
        for fk in attack_fks
    )
    assert any(
        fk["referred_table"] == "evidence_spans" and fk["constrained_columns"] == ["evidence_id"]
        for fk in attack_fks
    )


def test_indexes_match_core_contract(migrated_engine) -> None:
    """Implemented tables must expose required indexes/uniques."""
    inspector = inspect(migrated_engine)

    reports_indexes = {idx["name"] for idx in inspector.get_indexes("reports")}
    reports_uniques = {tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("reports")}

    assert ("content_hash",) in reports_uniques
    assert "ix_reports_created_at" in reports_indexes
    assert "ix_reports_status" in reports_indexes

    chunks_indexes = {idx["name"] for idx in inspector.get_indexes("report_chunks")}
    chunks_uniques = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("report_chunks")
    }

    assert "ix_report_chunks_report_id" in chunks_indexes
    assert "ix_report_chunks_report_id_chunk_index" in chunks_indexes
    assert ("report_id", "chunk_index") in chunks_uniques

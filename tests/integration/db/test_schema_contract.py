"""Integration tests for database schema contract."""

from sqlalchemy import create_engine, inspect

from de_forge.db.base import Base


def test_reports_content_hash_has_unique_constraint() -> None:
    """Ensure reports.content_hash enforces uniqueness."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    unique_constraints = inspector.get_unique_constraints("reports")
    unique_columns = {tuple(constraint["column_names"]) for constraint in unique_constraints}

    assert ("content_hash",) in unique_columns


def test_agent_runs_has_input_output_hash_columns() -> None:
    """Ensure agent_runs includes input_hash and output_hash columns."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "input_hash" in columns
    assert "output_hash" in columns

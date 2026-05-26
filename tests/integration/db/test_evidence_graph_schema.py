"""Integration tests for evidence graph persistence schema."""

from sqlalchemy import create_engine, inspect

import de_forge.models  # noqa: F401
from de_forge.db.base import Base


def test_evidence_graph_tables_exist_with_required_columns() -> None:
    """Evidence graph nodes and edges must be first-class persisted tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert "graph_nodes" in tables
    assert "graph_edges" in tables

    node_columns = {column["name"] for column in inspector.get_columns("graph_nodes")}
    edge_columns = {column["name"] for column in inspector.get_columns("graph_edges")}

    assert {
        "id",
        "run_id",
        "node_type",
        "ref_table",
        "ref_id",
        "payload_json",
        "created_at",
    }.issubset(node_columns)
    assert {
        "id",
        "run_id",
        "source_node_id",
        "target_node_id",
        "edge_type",
        "payload_json",
        "created_at",
    }.issubset(edge_columns)

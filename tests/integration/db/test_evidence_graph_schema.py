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

    node_indexes = {index["name"]: tuple(index["column_names"]) for index in inspector.get_indexes("graph_nodes")}
    assert node_indexes["ix_graph_nodes_run_id"] == ("run_id",)
    assert node_indexes["ix_graph_nodes_node_type"] == ("node_type",)
    assert node_indexes["ix_graph_nodes_ref_lookup"] == ("ref_table", "ref_id")

    edge_foreign_keys = {
        tuple(foreign_key["constrained_columns"]): (
            foreign_key["referred_table"],
            tuple(foreign_key["referred_columns"]),
        )
        for foreign_key in inspector.get_foreign_keys("graph_edges")
    }
    assert edge_foreign_keys[("source_node_id",)] == ("graph_nodes", ("id",))
    assert edge_foreign_keys[("target_node_id",)] == ("graph_nodes", ("id",))

    edge_indexes = {index["name"]: tuple(index["column_names"]) for index in inspector.get_indexes("graph_edges")}
    assert edge_indexes["ix_graph_edges_run_id"] == ("run_id",)
    assert edge_indexes["ix_graph_edges_edge_type"] == ("edge_type",)

    edge_unique_constraints = {
        constraint["name"]: tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("graph_edges")
    }
    assert edge_unique_constraints["uq_graph_edges_run_source_target_type"] == (
        "run_id",
        "source_node_id",
        "target_node_id",
        "edge_type",
    )

    node_check_constraints = {
        constraint["name"]: constraint["sqltext"] for constraint in inspector.get_check_constraints("graph_nodes")
    }
    edge_check_constraints = {
        constraint["name"]: constraint["sqltext"] for constraint in inspector.get_check_constraints("graph_edges")
    }
    assert "ck_graph_nodes_node_type_allowed" in node_check_constraints
    assert "node_type in" in node_check_constraints["ck_graph_nodes_node_type_allowed"]
    assert "ck_graph_edges_edge_type_allowed" in edge_check_constraints
    assert "edge_type in" in edge_check_constraints["ck_graph_edges_edge_type_allowed"]
    assert edge_check_constraints["ck_graph_edges_no_self_edge"] == "source_node_id != target_node_id"

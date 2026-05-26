"""Integration tests for evidence graph persistence schema."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import de_forge.models  # noqa: F401
from de_forge.db.base import Base
from de_forge.models.contract import GraphEdge, GraphNode


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
    node_unique_constraints = {
        constraint["name"]: tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("graph_nodes")
    }
    assert node_unique_constraints["uq_graph_nodes_run_type_ref"] == (
        "run_id",
        "node_type",
        "ref_table",
        "ref_id",
    )

    assert edge_check_constraints["ck_graph_edges_no_self_edge"] == "source_node_id != target_node_id"


def test_graph_node_ref_columns_are_non_nullable_for_portable_uniqueness() -> None:
    """Unreferenced nodes must use a non-null sentinel so uniqueness is portable."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    node_columns = {column["name"]: column for column in inspector.get_columns("graph_nodes")}

    assert node_columns["ref_table"]["nullable"] is False
    assert node_columns["ref_id"]["nullable"] is False


def test_invalid_node_type_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        session.add(
            GraphNode(
                id="node-invalid-type",
                run_id="run-1",
                node_type="invalid",
                ref_table="reports",
                ref_id="report-1",
                created_at="2026-05-27T00:00:00Z",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_invalid_edge_type_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        source = GraphNode(
            id="node-source",
            run_id="run-1",
            node_type="report",
            ref_table="reports",
            ref_id="report-1",
            created_at="2026-05-27T00:00:00Z",
        )
        target = GraphNode(
            id="node-target",
            run_id="run-1",
            node_type="chunk",
            ref_table="report_chunks",
            ref_id="chunk-1",
            created_at="2026-05-27T00:00:00Z",
        )
        session.add_all([source, target])
        session.flush()
        session.add(
            GraphEdge(
                id="edge-invalid-type",
                run_id="run-1",
                source_node_id=source.id,
                target_node_id=target.id,
                edge_type="invalid",
                created_at="2026-05-27T00:00:00Z",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_self_edge_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        node = GraphNode(
            id="node-self",
            run_id="run-1",
            node_type="report",
            ref_table="reports",
            ref_id="report-1",
            created_at="2026-05-27T00:00:00Z",
        )
        session.add(node)
        session.flush()
        session.add(
            GraphEdge(
                id="edge-self",
                run_id="run-1",
                source_node_id=node.id,
                target_node_id=node.id,
                edge_type="mentions",
                created_at="2026-05-27T00:00:00Z",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_duplicate_graph_node_with_same_run_type_ref_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        session.add_all(
            [
                GraphNode(
                    id="node-1",
                    run_id="run-1",
                    node_type="behavior",
                    created_at="2026-05-27T00:00:00Z",
                ),
                GraphNode(
                    id="node-2",
                    run_id="run-1",
                    node_type="behavior",
                    created_at="2026-05-27T00:00:00Z",
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_duplicate_graph_edge_with_same_run_source_target_type_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        source = GraphNode(
            id="edge-source",
            run_id="run-1",
            node_type="report",
            ref_table="reports",
            ref_id="report-1",
            created_at="2026-05-27T00:00:00Z",
        )
        target = GraphNode(
            id="edge-target",
            run_id="run-1",
            node_type="chunk",
            ref_table="report_chunks",
            ref_id="chunk-1",
            created_at="2026-05-27T00:00:00Z",
        )
        session.add_all([source, target])
        session.flush()
        session.add_all(
            [
                GraphEdge(
                    id="edge-1",
                    run_id="run-1",
                    source_node_id=source.id,
                    target_node_id=target.id,
                    edge_type="mentions",
                    created_at="2026-05-27T00:00:00Z",
                ),
                GraphEdge(
                    id="edge-2",
                    run_id="run-1",
                    source_node_id=source.id,
                    target_node_id=target.id,
                    edge_type="mentions",
                    created_at="2026-05-27T00:00:00Z",
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            session.commit()

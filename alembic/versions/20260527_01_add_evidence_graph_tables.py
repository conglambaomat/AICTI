"""add evidence graph tables

Revision ID: 20260527_01
Revises: 20260526_01
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260527_01"
down_revision: str | None = "20260526_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NODE_TYPE_CHECK = (
    "node_type in ('report', 'chunk', 'evidence_quote', 'behavior', "
    "'attack_technique', 'detection_strategy', 'analytic', 'data_component', "
    "'telemetry_source', 'telemetry_field', 'detection_spec', 'detection_ast', "
    "'compiled_sigma', 'generated_rule', 'validation_result', 'proof_obligation', "
    "'review_decision', 'feedback_pattern', 'regression_test')"
)

EDGE_TYPE_CHECK = (
    "edge_type in ('supports', 'mentions', 'maps_to', 'requires', 'implements', "
    "'validated_by', 'derived_from', 'satisfies', 'failed_by', 'contradicts')"
)


def upgrade() -> None:
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("node_type", sa.String(length=64), nullable=False),
        sa.Column("ref_table", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("ref_id", sa.String(length=36), nullable=False, server_default=""),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.CheckConstraint(NODE_TYPE_CHECK, name="ck_graph_nodes_node_type_allowed"),
        sa.UniqueConstraint(
            "run_id", "node_type", "ref_table", "ref_id", name="uq_graph_nodes_run_type_ref"
        ),
        sa.UniqueConstraint("id", "run_id", name="uq_graph_nodes_id_run"),
    )
    op.create_index("ix_graph_nodes_run_id", "graph_nodes", ["run_id"])
    op.create_index("ix_graph_nodes_node_type", "graph_nodes", ["node_type"])
    op.create_index("ix_graph_nodes_ref_lookup", "graph_nodes", ["ref_table", "ref_id"])

    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("source_node_id", sa.String(length=36), nullable=False),
        sa.Column("target_node_id", sa.String(length=36), nullable=False),
        sa.Column("edge_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.CheckConstraint("source_node_id != target_node_id", name="ck_graph_edges_no_self_edge"),
        sa.CheckConstraint(EDGE_TYPE_CHECK, name="ck_graph_edges_edge_type_allowed"),
        sa.UniqueConstraint(
            "run_id",
            "source_node_id",
            "target_node_id",
            "edge_type",
            name="uq_graph_edges_run_source_target_type",
        ),
        sa.ForeignKeyConstraint(
            ["source_node_id", "run_id"],
            ["graph_nodes.id", "graph_nodes.run_id"],
            name="fk_graph_edges_source_node_id_run_graph_nodes",
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id", "run_id"],
            ["graph_nodes.id", "graph_nodes.run_id"],
            name="fk_graph_edges_target_node_id_run_graph_nodes",
        ),
    )
    op.create_index("ix_graph_edges_run_id", "graph_edges", ["run_id"])
    op.create_index("ix_graph_edges_edge_type", "graph_edges", ["edge_type"])


def downgrade() -> None:
    op.drop_index("ix_graph_edges_edge_type", table_name="graph_edges")
    op.drop_index("ix_graph_edges_run_id", table_name="graph_edges")
    op.drop_table("graph_edges")
    op.drop_index("ix_graph_nodes_ref_lookup", table_name="graph_nodes")
    op.drop_index("ix_graph_nodes_node_type", table_name="graph_nodes")
    op.drop_index("ix_graph_nodes_run_id", table_name="graph_nodes")
    op.drop_table("graph_nodes")

"""Add retrieval audit lineage tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_02"
down_revision = "20260524_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retrieval_audit_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("query_hash", sa.String(length=64), nullable=False),
        sa.Column("retrieval_mode", sa.String(length=40), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.CheckConstraint("length(query_hash) > 0", name="ck_retrieval_audit_runs_query_hash_non_empty"),
        sa.CheckConstraint("top_k > 0", name="ck_retrieval_audit_runs_top_k_positive"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retrieval_audit_runs_run_id", "retrieval_audit_runs", ["run_id"])
    op.create_index("ix_retrieval_audit_runs_report_id", "retrieval_audit_runs", ["report_id"])

    op.create_table(
        "retrieval_candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("retrieval_run_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=36), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score_sparse", sa.Float(), nullable=False),
        sa.Column("score_dense", sa.Float(), nullable=False),
        sa.Column("score_fused", sa.Float(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.CheckConstraint("rank > 0", name="ck_retrieval_candidates_rank_positive"),
        sa.CheckConstraint("score_sparse >= 0", name="ck_retrieval_candidates_score_sparse_non_negative"),
        sa.CheckConstraint("score_dense >= 0", name="ck_retrieval_candidates_score_dense_non_negative"),
        sa.CheckConstraint("score_fused >= 0", name="ck_retrieval_candidates_score_fused_non_negative"),
        sa.ForeignKeyConstraint(["chunk_id"], ["report_chunks.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["retrieval_run_id"], ["retrieval_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("retrieval_run_id", "chunk_id", name="uq_retrieval_candidates_run_chunk"),
    )
    op.create_index("ix_retrieval_candidates_retrieval_run_id", "retrieval_candidates", ["retrieval_run_id"])
    op.create_index("ix_retrieval_candidates_run_id", "retrieval_candidates", ["run_id"])
    op.create_index("ix_retrieval_candidates_report_id", "retrieval_candidates", ["report_id"])
    op.create_index("ix_retrieval_candidates_chunk_id", "retrieval_candidates", ["chunk_id"])


def downgrade() -> None:
    op.drop_index("ix_retrieval_candidates_chunk_id", table_name="retrieval_candidates")
    op.drop_index("ix_retrieval_candidates_report_id", table_name="retrieval_candidates")
    op.drop_index("ix_retrieval_candidates_run_id", table_name="retrieval_candidates")
    op.drop_index("ix_retrieval_candidates_retrieval_run_id", table_name="retrieval_candidates")
    op.drop_table("retrieval_candidates")
    op.drop_index("ix_retrieval_audit_runs_report_id", table_name="retrieval_audit_runs")
    op.drop_index("ix_retrieval_audit_runs_run_id", table_name="retrieval_audit_runs")
    op.drop_table("retrieval_audit_runs")

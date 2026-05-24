# Schema Contract Parity Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring Alembic-created databases into parity with the current SQLAlchemy persistence contract so review/export and pipeline runtime code work against migrated databases, not only `Base.metadata.create_all()` test databases.

**Architecture:** Add one forward Alembic revision after `20260523_04` that fills remaining model/migration drift without rewriting existing migrations. Add focused parity tests that compare Alembic-upgraded schema against current model expectations for the drift-prone runtime tables, then verify the hardened review/export gate on an Alembic-created DB.

**Tech Stack:** Python 3.11, SQLAlchemy, Alembic, SQLite temp DBs, pytest, FastAPI service-layer integration tests.

---

## File Structure

- Create: `alembic/versions/20260524_01_schema_contract_parity_hardening.py`
  - Forward migration from `20260523_04` to add remaining columns/tables/indexes/checks required by `src/de_forge/models/contract.py`.
  - Must be idempotent for partially-upgraded local SQLite DBs by checking existing columns/tables/indexes before adding.
- Modify: `tests/integration/db/test_migrations_contract.py`
  - Add Alembic-created schema parity coverage for tables/columns still missing after current migrations.
  - Add review/export integration test that uses Alembic migration, inserts required FK rows, records an approval through `ReviewService`, and verifies export succeeds.
- No runtime service/model changes in this phase.

## Current Drift to Close

The current model `src/de_forge/models/contract.py` contains schema elements not guaranteed by the migration chain through `20260523_04`:

- `detection_specs`: `abstain_code`, `abstain_context`, `abstain_human_message`, `spec_payload`, `is_validated`
- `generated_rules`: `rule_content`
- current breadth tables absent from migrations: `pipeline_runs`, `proof_obligations`, `candidate_scores`, `oracle_evaluation_results`, `regression_runs`, `quality_snapshots`
- existing lineage tables already partially hardened by `20260523_04`: `validation_results`, `test_runs`, `review_decisions`, `refinement_iterations`; this task should add only missing constraints/tables not already covered and must not duplicate `20260523_04` behavior.

---

### Task 1: Add failing migration parity tests for remaining drift

**Files:**
- Modify: `tests/integration/db/test_migrations_contract.py`
- Test: `tests/integration/db/test_migrations_contract.py`

- [ ] **Step 1: Write failing tests for DetectionSpec and GeneratedRule migrated columns**

Append this test to `tests/integration/db/test_migrations_contract.py`:

```python
def test_migrated_detection_spec_and_generated_rule_columns_match_models(migrated_engine) -> None:
    inspector = inspect(migrated_engine)

    detection_columns = {column["name"] for column in inspector.get_columns("detection_specs")}
    generated_rule_columns = {column["name"] for column in inspector.get_columns("generated_rules")}

    assert {
        "id",
        "report_id",
        "abstain_code",
        "abstain_context",
        "abstain_human_message",
        "spec_payload",
        "is_validated",
    }.issubset(detection_columns)
    assert {"id", "detection_spec_id", "query_candidate_id", "rule_content"}.issubset(
        generated_rule_columns
    )
```

- [ ] **Step 2: Write failing tests for missing breadth tables**

Append this test to `tests/integration/db/test_migrations_contract.py`:

```python
def test_migrated_breadth_tables_match_current_models(migrated_engine) -> None:
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())

    assert {
        "pipeline_runs",
        "proof_obligations",
        "candidate_scores",
        "oracle_evaluation_results",
        "regression_runs",
        "quality_snapshots",
    }.issubset(tables)

    pipeline_columns = {column["name"] for column in inspector.get_columns("pipeline_runs")}
    proof_columns = {column["name"] for column in inspector.get_columns("proof_obligations")}
    candidate_columns = {column["name"] for column in inspector.get_columns("candidate_scores")}
    oracle_columns = {column["name"] for column in inspector.get_columns("oracle_evaluation_results")}
    regression_columns = {column["name"] for column in inspector.get_columns("regression_runs")}
    quality_columns = {column["name"] for column in inspector.get_columns("quality_snapshots")}

    assert {
        "id",
        "run_id",
        "report_id",
        "status",
        "stage",
        "detection_spec_id",
        "rule_id",
        "created_at",
    }.issubset(pipeline_columns)
    assert {
        "id",
        "run_id",
        "rule_candidate_id",
        "claim_type",
        "claim_text",
        "required_artifact_types",
        "status",
        "justification",
    }.issubset(proof_columns)
    assert {
        "id",
        "rule_id",
        "run_id",
        "score_type",
        "score_value",
        "score_breakdown_json",
        "created_at",
    }.issubset(candidate_columns)
    assert {
        "id",
        "rule_id",
        "run_id",
        "oracle_case_id",
        "score",
        "details_json",
        "created_at",
    }.issubset(oracle_columns)
    assert {"id", "rule_id", "run_id", "status", "result_json", "created_at"}.issubset(
        regression_columns
    )
    assert {"id", "run_id", "snapshot_type", "metrics_json", "created_at"}.issubset(
        quality_columns
    )
```

- [ ] **Step 3: Write failing tests for breadth indexes, FKs, and check constraints**

Append this test to `tests/integration/db/test_migrations_contract.py`:

```python
def test_migrated_breadth_tables_have_required_indexes_fks_and_checks(migrated_engine) -> None:
    inspector = inspect(migrated_engine)

    pipeline_indexes = {idx["name"] for idx in inspector.get_indexes("pipeline_runs")}
    proof_indexes = {idx["name"] for idx in inspector.get_indexes("proof_obligations")}
    candidate_indexes = {idx["name"] for idx in inspector.get_indexes("candidate_scores")}
    oracle_indexes = {idx["name"] for idx in inspector.get_indexes("oracle_evaluation_results")}
    regression_indexes = {idx["name"] for idx in inspector.get_indexes("regression_runs")}
    quality_indexes = {idx["name"] for idx in inspector.get_indexes("quality_snapshots")}

    assert "ix_pipeline_runs_run_id" in pipeline_indexes
    assert "ix_pipeline_runs_report_id" in pipeline_indexes
    assert "ix_pipeline_runs_detection_spec_id" in pipeline_indexes
    assert "ix_proof_obligations_rule_candidate_id" in proof_indexes
    assert "ix_proof_obligations_run_id" in proof_indexes
    assert "ix_candidate_scores_rule_id" in candidate_indexes
    assert "ix_candidate_scores_run_id" in candidate_indexes
    assert "ix_oracle_evaluation_results_rule_id" in oracle_indexes
    assert "ix_oracle_evaluation_results_run_id" in oracle_indexes
    assert "ix_regression_runs_rule_id" in regression_indexes
    assert "ix_regression_runs_run_id" in regression_indexes
    assert "ix_quality_snapshots_run_id" in quality_indexes

    candidate_fks = inspector.get_foreign_keys("candidate_scores")
    oracle_fks = inspector.get_foreign_keys("oracle_evaluation_results")
    regression_fks = inspector.get_foreign_keys("regression_runs")
    quality_fks = inspector.get_foreign_keys("quality_snapshots")

    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in candidate_fks
    )
    assert any(fk["referred_table"] == "pipeline_runs" for fk in candidate_fks)
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in oracle_fks
    )
    assert any(fk["referred_table"] == "pipeline_runs" for fk in oracle_fks)
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in regression_fks
    )
    assert any(fk["referred_table"] == "pipeline_runs" for fk in regression_fks)
    assert any(fk["referred_table"] == "pipeline_runs" for fk in quality_fks)

    candidate_checks = {check["name"] for check in inspector.get_check_constraints("candidate_scores")}
    oracle_checks = {
        check["name"] for check in inspector.get_check_constraints("oracle_evaluation_results")
    }
    regression_checks = {check["name"] for check in inspector.get_check_constraints("regression_runs")}
    quality_checks = {check["name"] for check in inspector.get_check_constraints("quality_snapshots")}

    assert "ck_candidate_scores_score_value_between_0_and_1" in candidate_checks
    assert "ck_candidate_scores_score_type_non_empty" in candidate_checks
    assert "ck_oracle_evaluation_results_score_between_0_and_1" in oracle_checks
    assert "ck_oracle_evaluation_results_oracle_case_id_non_empty" in oracle_checks
    assert "ck_regression_runs_status_allowed" in regression_checks
    assert "ck_quality_snapshots_snapshot_type_non_empty" in quality_checks
```

- [ ] **Step 4: Run failing tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py::test_migrated_detection_spec_and_generated_rule_columns_match_models tests/integration/db/test_migrations_contract.py::test_migrated_breadth_tables_match_current_models tests/integration/db/test_migrations_contract.py::test_migrated_breadth_tables_have_required_indexes_fks_and_checks -q
```

Expected: FAIL because the current migration head does not yet create all required columns/tables.

- [ ] **Step 5: Commit failing tests only**

```bash
git add tests/integration/db/test_migrations_contract.py
git commit -m "test(db): expose schema migration parity drift"
```

---

### Task 2: Add Alembic revision for schema parity

**Files:**
- Create: `alembic/versions/20260524_01_schema_contract_parity_hardening.py`
- Test: `tests/integration/db/test_migrations_contract.py`

- [ ] **Step 1: Create migration file**

Create `alembic/versions/20260524_01_schema_contract_parity_hardening.py` with this content:

```python
"""Bring Alembic schema into parity with current persistence models.

Revision ID: 20260524_01
Revises: 20260523_04
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260524_01"
down_revision = "20260523_04"
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return _has_table(inspector, table_name) and any(
        column["name"] == column_name for column in inspector.get_columns(table_name)
    )


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return _has_table(inspector, table_name) and any(
        index["name"] == index_name for index in inspector.get_indexes(table_name)
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    with op.batch_alter_table("detection_specs") as batch_op:
        if not _has_column(inspector, "detection_specs", "abstain_code"):
            batch_op.add_column(sa.Column("abstain_code", sa.String(length=80), nullable=True))
        if not _has_column(inspector, "detection_specs", "abstain_context"):
            batch_op.add_column(sa.Column("abstain_context", sa.Text(), nullable=True))
        if not _has_column(inspector, "detection_specs", "abstain_human_message"):
            batch_op.add_column(sa.Column("abstain_human_message", sa.Text(), nullable=True))
        if not _has_column(inspector, "detection_specs", "spec_payload"):
            batch_op.add_column(sa.Column("spec_payload", sa.Text(), nullable=True))
        if not _has_column(inspector, "detection_specs", "is_validated"):
            batch_op.add_column(
                sa.Column("is_validated", sa.Boolean(), nullable=False, server_default=sa.false())
            )

    with op.batch_alter_table("generated_rules") as batch_op:
        if not _has_column(inspector, "generated_rules", "rule_content"):
            batch_op.add_column(sa.Column("rule_content", sa.Text(), nullable=True))

    inspector = sa.inspect(bind)

    if not _has_table(inspector, "pipeline_runs"):
        op.create_table(
            "pipeline_runs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=36), nullable=False, unique=True),
            sa.Column("report_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("stage", sa.String(length=40), nullable=False),
            sa.Column("detection_spec_id", sa.String(length=36), nullable=True),
            sa.Column("rule_id", sa.String(length=36), nullable=True),
            sa.Column("created_at", sa.String(length=40), nullable=False),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "pipeline_runs", "ix_pipeline_runs_run_id"):
        op.create_index("ix_pipeline_runs_run_id", "pipeline_runs", ["run_id"])
    if not _has_index(inspector, "pipeline_runs", "ix_pipeline_runs_report_id"):
        op.create_index("ix_pipeline_runs_report_id", "pipeline_runs", ["report_id"])
    if not _has_index(inspector, "pipeline_runs", "ix_pipeline_runs_detection_spec_id"):
        op.create_index(
            "ix_pipeline_runs_detection_spec_id", "pipeline_runs", ["detection_spec_id"]
        )

    if not _has_table(inspector, "proof_obligations"):
        op.create_table(
            "proof_obligations",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=36), nullable=False),
            sa.Column("rule_candidate_id", sa.String(length=36), nullable=False),
            sa.Column("claim_type", sa.String(length=64), nullable=False),
            sa.Column("claim_text", sa.Text(), nullable=False),
            sa.Column("required_artifact_types", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("justification", sa.Text(), nullable=True),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "proof_obligations", "ix_proof_obligations_rule_candidate_id"):
        op.create_index(
            "ix_proof_obligations_rule_candidate_id",
            "proof_obligations",
            ["rule_candidate_id"],
        )
    if not _has_index(inspector, "proof_obligations", "ix_proof_obligations_run_id"):
        op.create_index("ix_proof_obligations_run_id", "proof_obligations", ["run_id"])

    if not _has_table(inspector, "candidate_scores"):
        op.create_table(
            "candidate_scores",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("score_type", sa.String(length=64), nullable=False),
            sa.Column("score_value", sa.Float(), nullable=False),
            sa.Column("score_breakdown_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint(
                "score_value >= 0 and score_value <= 1",
                name="ck_candidate_scores_score_value_between_0_and_1",
            ),
            sa.CheckConstraint(
                "length(score_type) > 0", name="ck_candidate_scores_score_type_non_empty"
            ),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "candidate_scores", "ix_candidate_scores_rule_id"):
        op.create_index("ix_candidate_scores_rule_id", "candidate_scores", ["rule_id"])
    if not _has_index(inspector, "candidate_scores", "ix_candidate_scores_run_id"):
        op.create_index("ix_candidate_scores_run_id", "candidate_scores", ["run_id"])

    if not _has_table(inspector, "oracle_evaluation_results"):
        op.create_table(
            "oracle_evaluation_results",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("oracle_case_id", sa.String(length=80), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint(
                "score >= 0 and score <= 1",
                name="ck_oracle_evaluation_results_score_between_0_and_1",
            ),
            sa.CheckConstraint(
                "length(oracle_case_id) > 0",
                name="ck_oracle_evaluation_results_oracle_case_id_non_empty",
            ),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "oracle_evaluation_results", "ix_oracle_evaluation_results_rule_id"):
        op.create_index(
            "ix_oracle_evaluation_results_rule_id", "oracle_evaluation_results", ["rule_id"]
        )
    if not _has_index(inspector, "oracle_evaluation_results", "ix_oracle_evaluation_results_run_id"):
        op.create_index(
            "ix_oracle_evaluation_results_run_id", "oracle_evaluation_results", ["run_id"]
        )

    if not _has_table(inspector, "regression_runs"):
        op.create_table(
            "regression_runs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown"),
            sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint(
                "status in ('passed', 'failed', 'unknown')",
                name="ck_regression_runs_status_allowed",
            ),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "regression_runs", "ix_regression_runs_rule_id"):
        op.create_index("ix_regression_runs_rule_id", "regression_runs", ["rule_id"])
    if not _has_index(inspector, "regression_runs", "ix_regression_runs_run_id"):
        op.create_index("ix_regression_runs_run_id", "regression_runs", ["run_id"])

    if not _has_table(inspector, "quality_snapshots"):
        op.create_table(
            "quality_snapshots",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("snapshot_type", sa.String(length=64), nullable=False),
            sa.Column("metrics_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint(
                "length(snapshot_type) > 0",
                name="ck_quality_snapshots_snapshot_type_non_empty",
            ),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "quality_snapshots", "ix_quality_snapshots_run_id"):
        op.create_index("ix_quality_snapshots_run_id", "quality_snapshots", ["run_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "quality_snapshots", "ix_quality_snapshots_run_id"):
        op.drop_index("ix_quality_snapshots_run_id", table_name="quality_snapshots")
    if _has_table(inspector, "quality_snapshots"):
        op.drop_table("quality_snapshots")

    inspector = sa.inspect(bind)
    if _has_index(inspector, "regression_runs", "ix_regression_runs_run_id"):
        op.drop_index("ix_regression_runs_run_id", table_name="regression_runs")
    if _has_index(inspector, "regression_runs", "ix_regression_runs_rule_id"):
        op.drop_index("ix_regression_runs_rule_id", table_name="regression_runs")
    if _has_table(inspector, "regression_runs"):
        op.drop_table("regression_runs")

    inspector = sa.inspect(bind)
    if _has_index(inspector, "oracle_evaluation_results", "ix_oracle_evaluation_results_run_id"):
        op.drop_index("ix_oracle_evaluation_results_run_id", table_name="oracle_evaluation_results")
    if _has_index(inspector, "oracle_evaluation_results", "ix_oracle_evaluation_results_rule_id"):
        op.drop_index("ix_oracle_evaluation_results_rule_id", table_name="oracle_evaluation_results")
    if _has_table(inspector, "oracle_evaluation_results"):
        op.drop_table("oracle_evaluation_results")

    inspector = sa.inspect(bind)
    if _has_index(inspector, "candidate_scores", "ix_candidate_scores_run_id"):
        op.drop_index("ix_candidate_scores_run_id", table_name="candidate_scores")
    if _has_index(inspector, "candidate_scores", "ix_candidate_scores_rule_id"):
        op.drop_index("ix_candidate_scores_rule_id", table_name="candidate_scores")
    if _has_table(inspector, "candidate_scores"):
        op.drop_table("candidate_scores")

    inspector = sa.inspect(bind)
    if _has_index(inspector, "proof_obligations", "ix_proof_obligations_run_id"):
        op.drop_index("ix_proof_obligations_run_id", table_name="proof_obligations")
    if _has_index(inspector, "proof_obligations", "ix_proof_obligations_rule_candidate_id"):
        op.drop_index("ix_proof_obligations_rule_candidate_id", table_name="proof_obligations")
    if _has_table(inspector, "proof_obligations"):
        op.drop_table("proof_obligations")

    inspector = sa.inspect(bind)
    if _has_index(inspector, "pipeline_runs", "ix_pipeline_runs_detection_spec_id"):
        op.drop_index("ix_pipeline_runs_detection_spec_id", table_name="pipeline_runs")
    if _has_index(inspector, "pipeline_runs", "ix_pipeline_runs_report_id"):
        op.drop_index("ix_pipeline_runs_report_id", table_name="pipeline_runs")
    if _has_index(inspector, "pipeline_runs", "ix_pipeline_runs_run_id"):
        op.drop_index("ix_pipeline_runs_run_id", table_name="pipeline_runs")
    if _has_table(inspector, "pipeline_runs"):
        op.drop_table("pipeline_runs")

    inspector = sa.inspect(bind)
    with op.batch_alter_table("generated_rules") as batch_op:
        if _has_column(inspector, "generated_rules", "rule_content"):
            batch_op.drop_column("rule_content")

    inspector = sa.inspect(bind)
    with op.batch_alter_table("detection_specs") as batch_op:
        if _has_column(inspector, "detection_specs", "is_validated"):
            batch_op.drop_column("is_validated")
        if _has_column(inspector, "detection_specs", "spec_payload"):
            batch_op.drop_column("spec_payload")
        if _has_column(inspector, "detection_specs", "abstain_human_message"):
            batch_op.drop_column("abstain_human_message")
        if _has_column(inspector, "detection_specs", "abstain_context"):
            batch_op.drop_column("abstain_context")
        if _has_column(inspector, "detection_specs", "abstain_code"):
            batch_op.drop_column("abstain_code")
```

- [ ] **Step 2: Run targeted migration parity tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py::test_migrated_detection_spec_and_generated_rule_columns_match_models tests/integration/db/test_migrations_contract.py::test_migrated_breadth_tables_match_current_models tests/integration/db/test_migrations_contract.py::test_migrated_breadth_tables_have_required_indexes_fks_and_checks -q
```

Expected: PASS.

- [ ] **Step 3: Run all DB migration tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit migration implementation**

```bash
git add alembic/versions/20260524_01_schema_contract_parity_hardening.py tests/integration/db/test_migrations_contract.py
git commit -m "fix(db): align Alembic schema with persistence models"
```

---

### Task 3: Verify review/export works on Alembic-created DB

**Files:**
- Modify: `tests/integration/db/test_migrations_contract.py`
- Test: `tests/integration/db/test_migrations_contract.py`

- [ ] **Step 1: Write failing integration test using migrated schema and ReviewService**

Add imports near the top of `tests/integration/db/test_migrations_contract.py`:

```python
from sqlalchemy.orm import Session, sessionmaker

from de_forge.services.review import ReviewService
```

Append this test:

```python
def test_review_export_gate_works_on_alembic_created_schema(migrated_engine) -> None:
    maker = sessionmaker(bind=migrated_engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()
    try:
        db.execute(
            text(
                """
                INSERT INTO reports (
                    id, source_type, source_uri, title, raw_text, content_hash,
                    metadata_json, status, created_at, updated_at
                )
                VALUES (
                    'report_migrated_review', 'txt', 'report.txt', 'Report',
                    'encoded powershell behavior', 'hash_migrated_review', '{}',
                    'ingested', '2026-05-24T00:00:00+00:00', '2026-05-24T00:00:00+00:00'
                )
                """
            )
        )
        db.execute(
            text(
                """
                INSERT INTO detection_specs (
                    id, report_id, spec_payload, is_validated
                )
                VALUES (
                    'spec_migrated_review', 'report_migrated_review', '{}', 1
                )
                """
            )
        )
        db.execute(
            text(
                """
                INSERT INTO generated_rules (
                    id, detection_spec_id, query_candidate_id, rule_content
                )
                VALUES (
                    'rule_migrated_review', 'spec_migrated_review', NULL,
                    'title: migrated review rule'
                )
                """
            )
        )
        db.execute(
            text(
                """
                INSERT INTO proof_obligations (
                    id, run_id, rule_candidate_id, claim_type, claim_text,
                    required_artifact_types, status, justification
                )
                VALUES
                    (
                        'po_migrated_review_1', 'run_migrated_review',
                        'rule_migrated_review', 'detects_report_behavior',
                        'Rule detects report behavior.', '["evidence_quote"]',
                        'proven', NULL
                    ),
                    (
                        'po_migrated_review_2', 'run_migrated_review',
                        'rule_migrated_review', 'not_overbroad',
                        'Rule is not overbroad.', '["false_positive_analysis"]',
                        'proven', NULL
                    )
                """
            )
        )
        db.commit()

        service = ReviewService(db)
        decision_id = service.record_decision(
            rule_id="rule_migrated_review",
            decision="approved",
            reviewer="analyst@example.com",
            run_id="run_migrated_review",
            comments="Approved on Alembic-created schema.",
        )

        assert decision_id
        service.assert_can_export(
            rule_id="rule_migrated_review",
            rule_status="awaiting_review",
        )
    finally:
        db.close()
```

- [ ] **Step 2: Run the new review/export migration test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py::test_review_export_gate_works_on_alembic_created_schema -q
```

Expected: PASS after Task 2 migration; if this fails before Task 2 in an implementation session, the failure should be due to missing Alembic columns/tables.

- [ ] **Step 3: Run affected review/export tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit review/export Alembic verification**

```bash
git add tests/integration/db/test_migrations_contract.py
git commit -m "test(review): verify export gate on migrated schema"
```

---

### Task 4: Run phase-level verification

**Files:**
- No code changes unless verification reveals a current-task defect.
- Test: DB migration and review/export suites.

- [ ] **Step 1: Run DB and review gate verification**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

- [ ] **Step 2: Run docs preflight because migration/docs governance must remain clean**

Run:

```bash
python scripts/docs_preflight.py
```

Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 3: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 4: Inspect git status for unrelated files**

Run:

```bash
git status --short
```

Expected: only files intentionally changed by this phase are modified/untracked. Do not stage `de_forge.db`, `.claude/settings.local.json`, caches, or worktree artifacts.

- [ ] **Step 5: Commit any verification-only fixes if needed**

If Task 4 revealed a current-task issue that required a small correction, commit only the related migration/test files:

```bash
git add alembic/versions/20260524_01_schema_contract_parity_hardening.py tests/integration/db/test_migrations_contract.py
git commit -m "fix(db): complete schema parity verification"
```

If no changes remain, do not create an empty commit.

---

## Self-Review

- Spec coverage: This plan covers Phase 1 only: Alembic parity, migration/model parity tests, and review/export verification on Alembic-created DB. It intentionally does not implement ingestion, evidence, retrieval, pipeline orchestration, validation-depth, proof artifact links, CORS, metrics, or health fixes.
- Placeholder scan: No TBD/TODO/fill-in placeholders remain; every task includes concrete file paths, code, commands, and expected outcomes.
- Type consistency: Tests use the existing `migrated_engine` fixture, `sqlalchemy.inspect`, `sqlalchemy.text`, `Session`, `sessionmaker`, and `ReviewService` APIs already present in the repo.

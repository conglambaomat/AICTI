"""Integration tests for database schema contract."""

from sqlalchemy import create_engine, inspect

import de_forge.models  # noqa: F401
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


def test_memory_tables_exist_with_expected_columns() -> None:
    """Ensure memory_events and memory_views tables expose required columns."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    memory_event_columns = {column["name"] for column in inspector.get_columns("memory_events")}
    memory_view_columns = {column["name"] for column in inspector.get_columns("memory_views")}

    assert {"id", "scope", "key", "value", "created_at"}.issubset(memory_event_columns)
    assert {"id", "scope", "key", "value", "updated_at"}.issubset(memory_view_columns)


def test_persistence_lineage_columns_exist_for_section20_domains() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    validation_columns = {column["name"] for column in inspector.get_columns("validation_results")}
    test_run_columns = {column["name"] for column in inspector.get_columns("test_runs")}
    review_columns = {column["name"] for column in inspector.get_columns("review_decisions")}
    refinement_columns = {
        column["name"] for column in inspector.get_columns("refinement_iterations")
    }

    assert {"id", "rule_id", "run_id", "status", "details_json", "created_at"}.issubset(
        validation_columns
    )
    assert {"id", "rule_id", "run_id", "status", "result_json", "created_at"}.issubset(
        test_run_columns
    )
    assert {
        "id",
        "rule_id",
        "run_id",
        "decision",
        "reviewer",
        "comments",
        "created_at",
    }.issubset(review_columns)
    assert {
        "id",
        "detection_spec_id",
        "rule_id",
        "run_id",
        "feedback_ref",
        "regression_ref",
        "created_at",
    }.issubset(refinement_columns)


def test_persistence_lineage_foreign_keys_exist_for_section20_domains() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    validation_fks = inspector.get_foreign_keys("validation_results")
    test_run_fks = inspector.get_foreign_keys("test_runs")
    review_fks = inspector.get_foreign_keys("review_decisions")
    refinement_fks = inspector.get_foreign_keys("refinement_iterations")

    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in validation_fks
    )
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in test_run_fks
    )
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in review_fks
    )
    assert any(
        fk["referred_table"] == "detection_specs"
        and fk["constrained_columns"] == ["detection_spec_id"]
        for fk in refinement_fks
    )
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in refinement_fks
    )


def test_lineage_indexes_exist_for_section20_domains() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    validation_indexes = {idx["name"] for idx in inspector.get_indexes("validation_results")}
    test_run_indexes = {idx["name"] for idx in inspector.get_indexes("test_runs")}
    review_indexes = {idx["name"] for idx in inspector.get_indexes("review_decisions")}
    refinement_indexes = {idx["name"] for idx in inspector.get_indexes("refinement_iterations")}

    assert "ix_validation_results_rule_id" in validation_indexes
    assert "ix_validation_results_run_id" in validation_indexes
    assert "ix_test_runs_rule_id" in test_run_indexes
    assert "ix_test_runs_run_id" in test_run_indexes
    assert "ix_review_decisions_rule_id" in review_indexes
    assert "ix_review_decisions_run_id" in review_indexes
    assert "ix_refinement_iterations_detection_spec_id" in refinement_indexes
    assert "ix_refinement_iterations_rule_id" in refinement_indexes
    assert "ix_refinement_iterations_run_id" in refinement_indexes


def test_refinement_iteration_has_feedback_regression_traceability_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    refinement_columns = {
        column["name"] for column in inspector.get_columns("refinement_iterations")
    }

    assert "feedback_ref" in refinement_columns
    assert "regression_ref" in refinement_columns
    assert "run_id" in refinement_columns
    assert "created_at" in refinement_columns


def test_review_decision_has_audit_payload_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    review_columns = {column["name"] for column in inspector.get_columns("review_decisions")}

    assert "run_id" in review_columns
    assert "comments" in review_columns
    assert "created_at" in review_columns


def test_validation_and_test_runs_have_status_payload_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    validation_columns = {column["name"] for column in inspector.get_columns("validation_results")}
    test_run_columns = {column["name"] for column in inspector.get_columns("test_runs")}

    assert "run_id" in validation_columns
    assert "status" in validation_columns
    assert "details_json" in validation_columns
    assert "created_at" in validation_columns

    assert "run_id" in test_run_columns
    assert "status" in test_run_columns
    assert "result_json" in test_run_columns
    assert "created_at" in test_run_columns

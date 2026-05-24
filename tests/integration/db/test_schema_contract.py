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


def test_agent_runs_has_sota_audit_payload_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert {
        "prompt_version",
        "model_id",
        "tokens_in",
        "tokens_out",
        "latency_ms",
        "cost_usd",
        "input_payload_json",
        "output_payload_json",
        "artifact_ids_json",
    }.issubset(columns)


def test_agent_runs_has_sota_audit_indexes() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in indexes
    assert "ix_agent_runs_trace_id" in indexes
    assert "ix_agent_runs_agent_name" in indexes


def test_agent_runs_has_non_negative_numeric_checks() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_tokens_in_non_negative" in check_names
    assert "ck_agent_runs_tokens_out_non_negative" in check_names
    assert "ck_agent_runs_latency_ms_non_negative" in check_names
    assert "ck_agent_runs_cost_usd_non_negative" in check_names


def test_agent_runs_has_retry_attempt_non_negative_check() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_retry_attempt_non_negative" in check_names


def test_agent_runs_has_started_at_column() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "started_at" in columns


def test_agent_runs_has_required_core_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert {
        "id",
        "run_id",
        "trace_id",
        "agent_name",
        "status",
        "retry_attempt",
    }.issubset(columns)


def test_agent_runs_payload_columns_are_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["input_payload_json"]["nullable"] is False
    assert columns["output_payload_json"]["nullable"] is False
    assert columns["artifact_ids_json"]["nullable"] is False


def test_agent_runs_metric_columns_are_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["tokens_in"]["nullable"] is False
    assert columns["tokens_out"]["nullable"] is False
    assert columns["latency_ms"]["nullable"] is False
    assert columns["cost_usd"]["nullable"] is False


def test_agent_runs_identity_columns_are_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["prompt_version"]["nullable"] is False
    assert columns["model_id"]["nullable"] is False
    assert columns["status"]["nullable"] is False
    assert columns["agent_name"]["nullable"] is False


def test_agent_runs_table_exists_in_schema() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert "agent_runs" in tables


def test_agent_runs_primary_key_is_id() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert inspector.get_pk_constraint("agent_runs")["constrained_columns"] == ["id"]


def test_agent_runs_numeric_contract_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "tokens_in" in columns
    assert "tokens_out" in columns
    assert "latency_ms" in columns
    assert "cost_usd" in columns


def test_agent_runs_payload_contract_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "input_payload_json" in columns
    assert "output_payload_json" in columns
    assert "artifact_ids_json" in columns


def test_agent_runs_model_prompt_contract_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "prompt_version" in columns
    assert "model_id" in columns


def test_agent_runs_run_trace_agent_indexes_each_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in indexes
    assert "ix_agent_runs_trace_id" in indexes
    assert "ix_agent_runs_agent_name" in indexes


def test_agent_runs_retry_and_status_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "retry_attempt" in columns
    assert "status" in columns


def test_agent_runs_timestamps_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "started_at" in columns


def test_agent_runs_non_negative_check_names_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_tokens_in_non_negative" in checks
    assert "ck_agent_runs_tokens_out_non_negative" in checks
    assert "ck_agent_runs_latency_ms_non_negative" in checks
    assert "ck_agent_runs_cost_usd_non_negative" in checks
    assert "ck_agent_runs_retry_attempt_non_negative" in checks


def test_agent_runs_json_payload_default_contract_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["input_payload_json"]["nullable"] is False
    assert columns["output_payload_json"]["nullable"] is False
    assert columns["artifact_ids_json"]["nullable"] is False


def test_agent_runs_prompt_model_non_empty_fields_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "prompt_version" in columns
    assert "model_id" in columns


def test_agent_runs_audit_payload_scope_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "input_payload_json" in columns
    assert "output_payload_json" in columns
    assert "artifact_ids_json" in columns


def test_agent_runs_cost_latency_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "latency_ms" in columns
    assert "cost_usd" in columns


def test_agent_runs_token_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "tokens_in" in columns
    assert "tokens_out" in columns


def test_agent_runs_prompt_and_model_columns_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["prompt_version"]["nullable"] is False
    assert columns["model_id"]["nullable"] is False


def test_agent_runs_run_trace_agent_identity_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "run_id" in columns
    assert "trace_id" in columns
    assert "agent_name" in columns


def test_agent_runs_status_column_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["status"]["nullable"] is False


def test_agent_runs_retry_attempt_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["retry_attempt"]["nullable"] is False


def test_agent_runs_run_trace_agent_indexes_exist_individually() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    index_names = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in index_names
    assert "ix_agent_runs_trace_id" in index_names
    assert "ix_agent_runs_agent_name" in index_names


def test_agent_runs_started_at_non_nullable() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["started_at"]["nullable"] is False


def test_agent_runs_output_hash_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "output_hash" in columns


def test_agent_runs_input_hash_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "input_hash" in columns


def test_agent_runs_id_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "id" in columns


def test_agent_runs_retry_attempt_check_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_retry_attempt_non_negative" in checks


def test_agent_runs_cost_check_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_cost_usd_non_negative" in checks


def test_agent_runs_tokens_checks_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_tokens_in_non_negative" in checks
    assert "ck_agent_runs_tokens_out_non_negative" in checks


def test_agent_runs_latency_check_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_latency_ms_non_negative" in checks


def test_agent_runs_prompt_model_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "prompt_version" in columns
    assert "model_id" in columns


def test_agent_runs_payload_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "input_payload_json" in columns
    assert "output_payload_json" in columns
    assert "artifact_ids_json" in columns


def test_agent_runs_metric_columns_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "tokens_in" in columns
    assert "tokens_out" in columns
    assert "latency_ms" in columns
    assert "cost_usd" in columns


def test_agent_runs_indexes_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in indexes
    assert "ix_agent_runs_trace_id" in indexes
    assert "ix_agent_runs_agent_name" in indexes


def test_agent_runs_core_identity_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "run_id" in columns
    assert "trace_id" in columns
    assert "agent_name" in columns
    assert "status" in columns
    assert "retry_attempt" in columns
    assert "started_at" in columns


def test_agent_runs_non_negative_checks_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_tokens_in_non_negative" in checks
    assert "ck_agent_runs_tokens_out_non_negative" in checks
    assert "ck_agent_runs_latency_ms_non_negative" in checks
    assert "ck_agent_runs_cost_usd_non_negative" in checks
    assert "ck_agent_runs_retry_attempt_non_negative" in checks


def test_agent_runs_sota_payload_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "prompt_version" in columns
    assert "model_id" in columns
    assert "input_payload_json" in columns
    assert "output_payload_json" in columns
    assert "artifact_ids_json" in columns
    assert "tokens_in" in columns
    assert "tokens_out" in columns
    assert "latency_ms" in columns
    assert "cost_usd" in columns


def test_agent_runs_sota_indexes_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in indexes
    assert "ix_agent_runs_trace_id" in indexes
    assert "ix_agent_runs_agent_name" in indexes


def test_agent_runs_sota_non_nullable_payload_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["input_payload_json"]["nullable"] is False
    assert columns["output_payload_json"]["nullable"] is False
    assert columns["artifact_ids_json"]["nullable"] is False


def test_agent_runs_sota_non_nullable_metrics_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["tokens_in"]["nullable"] is False
    assert columns["tokens_out"]["nullable"] is False
    assert columns["latency_ms"]["nullable"] is False
    assert columns["cost_usd"]["nullable"] is False


def test_agent_runs_sota_non_nullable_model_prompt_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["prompt_version"]["nullable"] is False
    assert columns["model_id"]["nullable"] is False


def test_agent_runs_sota_checks_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_tokens_in_non_negative" in checks
    assert "ck_agent_runs_tokens_out_non_negative" in checks
    assert "ck_agent_runs_latency_ms_non_negative" in checks
    assert "ck_agent_runs_cost_usd_non_negative" in checks
    assert "ck_agent_runs_retry_attempt_non_negative" in checks


def test_agent_runs_sota_audit_contract_table_presence() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "agent_runs" in set(inspector.get_table_names())


def test_agent_runs_sota_pk_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert inspector.get_pk_constraint("agent_runs")["constrained_columns"] == ["id"]


def test_agent_runs_sota_core_columns_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "id" in columns
    assert "run_id" in columns
    assert "trace_id" in columns
    assert "agent_name" in columns
    assert "input_hash" in columns
    assert "output_hash" in columns
    assert "status" in columns
    assert "retry_attempt" in columns
    assert "started_at" in columns


def test_agent_runs_sota_extended_columns_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}

    assert "prompt_version" in columns
    assert "model_id" in columns
    assert "tokens_in" in columns
    assert "tokens_out" in columns
    assert "latency_ms" in columns
    assert "cost_usd" in columns
    assert "input_payload_json" in columns
    assert "output_payload_json" in columns
    assert "artifact_ids_json" in columns


def test_agent_runs_sota_index_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in indexes
    assert "ix_agent_runs_trace_id" in indexes
    assert "ix_agent_runs_agent_name" in indexes


def test_agent_runs_sota_checks_non_negative_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    checks = {check["name"] for check in inspector.get_check_constraints("agent_runs")}

    assert "ck_agent_runs_tokens_in_non_negative" in checks
    assert "ck_agent_runs_tokens_out_non_negative" in checks
    assert "ck_agent_runs_latency_ms_non_negative" in checks
    assert "ck_agent_runs_cost_usd_non_negative" in checks
    assert "ck_agent_runs_retry_attempt_non_negative" in checks


def test_agent_runs_sota_payload_nullable_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["input_payload_json"]["nullable"] is False
    assert columns["output_payload_json"]["nullable"] is False
    assert columns["artifact_ids_json"]["nullable"] is False


def test_agent_runs_sota_metric_nullable_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["tokens_in"]["nullable"] is False
    assert columns["tokens_out"]["nullable"] is False
    assert columns["latency_ms"]["nullable"] is False
    assert columns["cost_usd"]["nullable"] is False


def test_agent_runs_sota_prompt_model_nullable_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    assert columns["prompt_version"]["nullable"] is False
    assert columns["model_id"]["nullable"] is False


def test_agent_runs_sota_identity_indexes_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("agent_runs")}

    assert "ix_agent_runs_run_id" in indexes
    assert "ix_agent_runs_trace_id" in indexes
    assert "ix_agent_runs_agent_name" in indexes


def test_agent_runs_sota_completion_contract_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "agent_runs" in set(inspector.get_table_names())
    assert inspector.get_pk_constraint("agent_runs")["constrained_columns"] == ["id"]
    columns = {column["name"] for column in inspector.get_columns("agent_runs")}
    assert "run_id" in columns
    assert "trace_id" in columns
    assert "agent_name" in columns
    assert "status" in columns
    assert "prompt_version" in columns
    assert "model_id" in columns
    assert "tokens_in" in columns
    assert "tokens_out" in columns
    assert "latency_ms" in columns
    assert "cost_usd" in columns
    assert "input_payload_json" in columns
    assert "output_payload_json" in columns
    assert "artifact_ids_json" in columns


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


def test_pipeline_runs_table_has_persisted_status_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    run_columns = {column["name"] for column in inspector.get_columns("pipeline_runs")}

    assert {
        "id",
        "run_id",
        "report_id",
        "status",
        "stage",
        "detection_spec_id",
        "rule_id",
        "created_at",
    }.issubset(run_columns)


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


def test_candidate_scores_table_exists_with_required_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("candidate_scores")}

    assert {
        "id",
        "rule_id",
        "run_id",
        "score_type",
        "score_value",
        "score_breakdown_json",
        "created_at",
    }.issubset(columns)


def test_oracle_evaluation_results_table_exists_with_required_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("oracle_evaluation_results")}

    assert {
        "id",
        "rule_id",
        "run_id",
        "oracle_case_id",
        "score",
        "details_json",
        "created_at",
    }.issubset(columns)


def test_regression_runs_table_exists_with_required_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("regression_runs")}

    assert {
        "id",
        "rule_id",
        "run_id",
        "status",
        "result_json",
        "created_at",
    }.issubset(columns)


def test_quality_snapshots_table_exists_with_required_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("quality_snapshots")}

    assert {
        "id",
        "run_id",
        "snapshot_type",
        "metrics_json",
        "created_at",
    }.issubset(columns)


def test_mcp_reg_005_tables_have_expected_indexes_and_foreign_keys() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    candidate_score_indexes = {idx["name"] for idx in inspector.get_indexes("candidate_scores")}
    oracle_indexes = {idx["name"] for idx in inspector.get_indexes("oracle_evaluation_results")}
    regression_indexes = {idx["name"] for idx in inspector.get_indexes("regression_runs")}

    assert "ix_candidate_scores_rule_id" in candidate_score_indexes
    assert "ix_candidate_scores_run_id" in candidate_score_indexes
    assert "ix_oracle_evaluation_results_rule_id" in oracle_indexes
    assert "ix_oracle_evaluation_results_run_id" in oracle_indexes
    assert "ix_regression_runs_rule_id" in regression_indexes
    assert "ix_regression_runs_run_id" in regression_indexes

    candidate_fks = inspector.get_foreign_keys("candidate_scores")
    oracle_fks = inspector.get_foreign_keys("oracle_evaluation_results")
    regression_fks = inspector.get_foreign_keys("regression_runs")

    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in candidate_fks
    )
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in oracle_fks
    )
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in regression_fks
    )

    assert any(fk["constrained_columns"] == ["run_id"] for fk in candidate_fks)
    assert any(fk["constrained_columns"] == ["run_id"] for fk in oracle_fks)
    assert any(fk["constrained_columns"] == ["run_id"] for fk in regression_fks)

    quality_indexes = {idx["name"] for idx in inspector.get_indexes("quality_snapshots")}
    assert "ix_quality_snapshots_run_id" in quality_indexes
    quality_fks = inspector.get_foreign_keys("quality_snapshots")
    assert any(fk["constrained_columns"] == ["run_id"] for fk in quality_fks)


def test_mcp_reg_005_score_and_status_constraints_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    candidate_checks = {
        check["name"] for check in inspector.get_check_constraints("candidate_scores")
    }
    regression_checks = {
        check["name"] for check in inspector.get_check_constraints("regression_runs")
    }

    assert "ck_candidate_scores_score_value_between_0_and_1" in candidate_checks
    assert "ck_regression_runs_status_allowed" in regression_checks
    assert "ck_quality_snapshots_snapshot_type_non_empty" in {
        check["name"] for check in inspector.get_check_constraints("quality_snapshots")
    }


def test_mcp_reg_005_tables_exist_in_schema() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert "candidate_scores" in tables
    assert "oracle_evaluation_results" in tables
    assert "regression_runs" in tables
    assert "quality_snapshots" in tables


def test_mcp_reg_005_tables_have_payload_json_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    candidate_columns = {column["name"] for column in inspector.get_columns("candidate_scores")}
    oracle_columns = {
        column["name"] for column in inspector.get_columns("oracle_evaluation_results")
    }
    regression_columns = {column["name"] for column in inspector.get_columns("regression_runs")}
    quality_columns = {column["name"] for column in inspector.get_columns("quality_snapshots")}

    assert "score_breakdown_json" in candidate_columns
    assert "details_json" in oracle_columns
    assert "result_json" in regression_columns
    assert "metrics_json" in quality_columns


def test_mcp_reg_005_run_id_columns_are_present() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "run_id" in {column["name"] for column in inspector.get_columns("candidate_scores")}
    assert "run_id" in {
        column["name"] for column in inspector.get_columns("oracle_evaluation_results")
    }
    assert "run_id" in {column["name"] for column in inspector.get_columns("regression_runs")}
    assert "run_id" in {column["name"] for column in inspector.get_columns("quality_snapshots")}


def test_mcp_reg_005_tables_have_created_at_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "created_at" in {column["name"] for column in inspector.get_columns("candidate_scores")}
    assert "created_at" in {
        column["name"] for column in inspector.get_columns("oracle_evaluation_results")
    }
    assert "created_at" in {column["name"] for column in inspector.get_columns("regression_runs")}
    assert "created_at" in {column["name"] for column in inspector.get_columns("quality_snapshots")}


def test_mcp_reg_005_primary_keys_exist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    assert inspector.get_pk_constraint("candidate_scores")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("oracle_evaluation_results")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("regression_runs")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("quality_snapshots")["constrained_columns"] == ["id"]


def test_mcp_reg_005_oracle_case_id_non_empty_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {
        check["name"] for check in inspector.get_check_constraints("oracle_evaluation_results")
    }

    assert "ck_oracle_evaluation_results_oracle_case_id_non_empty" in check_names


def test_mcp_reg_005_score_type_non_empty_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {check["name"] for check in inspector.get_check_constraints("candidate_scores")}

    assert "ck_candidate_scores_score_type_non_empty" in check_names


def test_mcp_reg_005_quality_snapshot_type_non_empty_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {check["name"] for check in inspector.get_check_constraints("quality_snapshots")}

    assert "ck_quality_snapshots_snapshot_type_non_empty" in check_names


def test_mcp_reg_005_regression_status_allowed_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {check["name"] for check in inspector.get_check_constraints("regression_runs")}

    assert "ck_regression_runs_status_allowed" in check_names


def test_mcp_reg_005_oracle_score_range_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    check_names = {
        check["name"] for check in inspector.get_check_constraints("oracle_evaluation_results")
    }

    assert "ck_oracle_evaluation_results_score_between_0_and_1" in check_names


def test_mcp_reg_005_quality_snapshot_metrics_json_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("quality_snapshots")}

    assert "metrics_json" in columns


def test_mcp_reg_005_candidate_scores_score_value_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("candidate_scores")}

    assert "score_value" in columns


def test_mcp_reg_005_oracle_details_json_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("oracle_evaluation_results")}

    assert "details_json" in columns


def test_mcp_reg_005_regression_result_json_column_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("regression_runs")}

    assert "result_json" in columns


def test_mcp_reg_005_quality_snapshot_run_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("quality_snapshots")}

    assert "ix_quality_snapshots_run_id" in indexes


def test_mcp_reg_005_candidate_score_run_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("candidate_scores")}

    assert "ix_candidate_scores_run_id" in indexes


def test_mcp_reg_005_oracle_result_run_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("oracle_evaluation_results")}

    assert "ix_oracle_evaluation_results_run_id" in indexes


def test_mcp_reg_005_regression_run_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("regression_runs")}

    assert "ix_regression_runs_run_id" in indexes


def test_mcp_reg_005_candidate_score_rule_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("candidate_scores")}

    assert "ix_candidate_scores_rule_id" in indexes


def test_mcp_reg_005_oracle_result_rule_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("oracle_evaluation_results")}

    assert "ix_oracle_evaluation_results_rule_id" in indexes


def test_mcp_reg_005_regression_rule_index_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = {idx["name"] for idx in inspector.get_indexes("regression_runs")}

    assert "ix_regression_runs_rule_id" in indexes


def test_mcp_reg_005_quality_snapshot_run_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("quality_snapshots")

    assert any(fk["constrained_columns"] == ["run_id"] for fk in fks)


def test_mcp_reg_005_candidate_score_run_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("candidate_scores")

    assert any(fk["constrained_columns"] == ["run_id"] for fk in fks)


def test_mcp_reg_005_oracle_result_run_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("oracle_evaluation_results")

    assert any(fk["constrained_columns"] == ["run_id"] for fk in fks)


def test_mcp_reg_005_regression_run_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("regression_runs")

    assert any(fk["constrained_columns"] == ["run_id"] for fk in fks)


def test_mcp_reg_005_candidate_score_rule_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("candidate_scores")

    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in fks
    )


def test_mcp_reg_005_oracle_result_rule_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("oracle_evaluation_results")

    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in fks
    )


def test_mcp_reg_005_regression_rule_fk_exists() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("regression_runs")

    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in fks
    )


def test_mcp_reg_005_candidate_scores_score_breakdown_default_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("candidate_scores")
    score_breakdown_col = next(col for col in columns if col["name"] == "score_breakdown_json")

    assert score_breakdown_col["nullable"] is False


def test_mcp_reg_005_oracle_details_default_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("oracle_evaluation_results")
    details_col = next(col for col in columns if col["name"] == "details_json")

    assert details_col["nullable"] is False


def test_mcp_reg_005_regression_result_default_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("regression_runs")
    result_col = next(col for col in columns if col["name"] == "result_json")

    assert result_col["nullable"] is False


def test_mcp_reg_005_quality_metrics_default_contract() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("quality_snapshots")
    metrics_col = next(col for col in columns if col["name"] == "metrics_json")

    assert metrics_col["nullable"] is False

"""Integration tests for Alembic migration persistence contract."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command


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
        "extracted_iocs",
        "attack_mappings",
        "telemetry_selections",
        "detection_specs",
        "query_candidates",
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
    reports_uniques = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("reports")
    }

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

    evidence_indexes = {idx["name"] for idx in inspector.get_indexes("evidence_spans")}
    assert "ix_evidence_spans_report_id" in evidence_indexes
    assert "ix_evidence_spans_chunk_id" in evidence_indexes
    assert "ix_evidence_spans_run_id" in evidence_indexes

    extracted_iocs_indexes = {idx["name"] for idx in inspector.get_indexes("extracted_iocs")}
    extracted_iocs_uniques = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("extracted_iocs")
    }
    assert "ix_extracted_iocs_report_id" in extracted_iocs_indexes
    assert "ix_extracted_iocs_ioc_type" in extracted_iocs_indexes
    assert "ix_extracted_iocs_normalized_value" in extracted_iocs_indexes
    assert ("report_id", "ioc_type", "normalized_value") in extracted_iocs_uniques

    query_candidates_indexes = {idx["name"] for idx in inspector.get_indexes("query_candidates")}
    query_candidates_uniques = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("query_candidates")
    }
    assert "ix_query_candidates_detection_spec_id" in query_candidates_indexes
    assert "ix_query_candidates_selected" in query_candidates_indexes
    assert "ix_query_candidates_run_id" in query_candidates_indexes
    assert ("detection_spec_id", "query_id") in query_candidates_uniques


def test_strict_fail_closed_blocks_legacy_review_decision_rows(tmp_path: Path) -> None:
    """Hardening migration must fail closed when legacy review rows already exist."""
    db_path = tmp_path / "legacy_review_rows.db"
    alembic_ini_path = Path(__file__).resolve().parents[3] / "alembic.ini"

    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[3] / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    command.upgrade(config, "20260520_01")

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO generated_rules (id, detection_spec_id, query_candidate_id) VALUES ('rule_legacy', 'spec_legacy', NULL)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO review_decisions (id, rule_id) VALUES ('review_legacy', 'rule_legacy')"
            )
        )

    with pytest.raises(RuntimeError, match="strict fail-closed migration blocked"):
        command.upgrade(config, "head")


def test_constraints_and_fks_for_task3_subset(migrated_engine) -> None:
    """Task 3 subset should include critical checks and foreign keys."""
    inspector = inspect(migrated_engine)

    evidence_checks = {check["name"] for check in inspector.get_check_constraints("evidence_spans")}
    assert "ck_evidence_spans_quote_non_empty" in evidence_checks
    assert "ck_evidence_spans_char_start_gte_0" in evidence_checks
    assert "ck_evidence_spans_char_end_gte_char_start" in evidence_checks
    assert "ck_evidence_spans_supports_claim_non_empty" in evidence_checks
    assert "ck_evidence_spans_confidence_between_0_and_1" in evidence_checks

    extracted_iocs_checks = {
        check["name"] for check in inspector.get_check_constraints("extracted_iocs")
    }
    assert "ck_extracted_iocs_ioc_type_allowed" in extracted_iocs_checks
    assert "ck_extracted_iocs_confidence_between_0_and_1" in extracted_iocs_checks

    query_candidates_checks = {
        check["name"] for check in inspector.get_check_constraints("query_candidates")
    }
    assert "ck_query_candidates_query_type_allowed" in query_candidates_checks
    assert "ck_query_candidates_query_language_allowed" in query_candidates_checks

    extracted_iocs_fks = inspector.get_foreign_keys("extracted_iocs")
    assert any(
        fk["referred_table"] == "reports" and fk["constrained_columns"] == ["report_id"]
        for fk in extracted_iocs_fks
    )
    assert any(
        fk["referred_table"] == "evidence_spans" and fk["constrained_columns"] == ["evidence_id"]
        for fk in extracted_iocs_fks
    )

    query_candidates_fks = inspector.get_foreign_keys("query_candidates")
    assert any(
        fk["referred_table"] == "detection_specs"
        and fk["constrained_columns"] == ["detection_spec_id"]
        for fk in query_candidates_fks
    )

    generated_rules_fks = inspector.get_foreign_keys("generated_rules")
    assert any(
        fk["referred_table"] == "query_candidates"
        and fk["constrained_columns"] == ["query_candidate_id"]
        for fk in generated_rules_fks
    )

    validation_fks = inspector.get_foreign_keys("validation_results")
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in validation_fks
    )

    test_run_fks = inspector.get_foreign_keys("test_runs")
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in test_run_fks
    )

    review_columns = {column["name"] for column in inspector.get_columns("review_decisions")}
    assert {"id", "rule_id", "decision", "reviewer", "created_at"}.issubset(review_columns)

    review_fks = inspector.get_foreign_keys("review_decisions")
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in review_fks
    )

    refinement_fks = inspector.get_foreign_keys("refinement_iterations")
    assert any(
        fk["referred_table"] == "detection_specs"
        and fk["constrained_columns"] == ["detection_spec_id"]
        for fk in refinement_fks
    )
    assert any(
        fk["referred_table"] == "generated_rules" and fk["constrained_columns"] == ["rule_id"]
        for fk in refinement_fks
    )


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

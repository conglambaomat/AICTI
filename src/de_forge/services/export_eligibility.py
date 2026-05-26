"""Centralized export eligibility gate."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec, GeneratedRule, PipelineRunRecord, ProofObligationRecord
from de_forge.services.compiler_provenance import (
    CompilerProvenanceError,
    CompilerProvenanceService,
)
from de_forge.services.evidence_graph import EvidenceGraphError, EvidenceGraphService
from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService
from de_forge.services.review import ReviewService


class ExportBlockedReason(ValueError):  # noqa: N818
    """Raised with the stable reason code for a blocked export."""


class ExportEligibilityRepository(Protocol):
    """Read boundary for export eligibility checks."""

    def get_run(self, run_id: str) -> object | None:
        """Return the pipeline run for run_id, if present."""

    def get_rule(self, rule_id: str) -> object | None:
        """Return the generated rule for rule_id, if present."""

    def get_detection_spec(self, spec_id: str) -> object | None:
        """Return the detection spec for spec_id, if present."""

    def get_proof_rows(self, run_id: str, rule_id: str) -> object:
        """Return persisted proof obligation rows for the run and rule."""

    def latest_review_decision(self, run_id: str, rule_id: str) -> object | None:
        """Return the latest human review decision for the run and rule."""

    def assert_evidence_graph_complete(self, run_id: str, rule_id: str) -> None:
        """Assert the persisted evidence graph export path is complete."""


class SqlAlchemyExportEligibilityRepository:
    """SQLAlchemy-backed repository for export eligibility checks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_run(self, run_id: str) -> PipelineRunRecord | None:
        return (
            self.db.query(PipelineRunRecord)
            .filter(PipelineRunRecord.run_id == run_id)
            .first()
        )

    def get_rule(self, rule_id: str) -> GeneratedRule | None:
        return self.db.get(GeneratedRule, rule_id)

    def get_detection_spec(self, spec_id: str | None) -> DetectionSpec | None:
        if spec_id is None:
            return None
        return self.db.get(DetectionSpec, spec_id)

    def get_proof_rows(self, run_id: str, rule_id: str) -> list[dict[str, object]]:
        rows = (
            self.db.query(ProofObligationRecord)
            .filter(
                ProofObligationRecord.run_id == run_id,
                ProofObligationRecord.rule_candidate_id == rule_id,
            )
            .all()
        )
        return [
            {
                "run_id": row.run_id,
                "rule_candidate_id": row.rule_candidate_id,
                "claim_type": row.claim_type,
                "status": row.status,
                "justification": row.justification,
            }
            for row in rows
        ]

    def latest_review_decision(self, run_id: str, rule_id: str) -> object | None:
        return ReviewService(self.db)._get_latest_decision(rule_id, run_id=run_id)

    def assert_evidence_graph_complete(self, run_id: str, rule_id: str) -> None:
        EvidenceGraphService(self.db).assert_export_path_complete(run_id=run_id, rule_id=rule_id)


class ExportEligibilityService:
    """Fail-closed export eligibility checks for generated rules."""

    def __init__(self, repository: ExportEligibilityRepository) -> None:
        self.repository = repository
        self.compiler_provenance = CompilerProvenanceService()
        self.proof_coverage = ProofCoverageService()

    def assert_exportable(self, run_id: str, rule_id: str) -> None:
        run = self.repository.get_run(run_id)
        if run is None:
            raise ExportBlockedReason("PIPELINE_RUN_MISSING")

        if getattr(run, "rule_id", None) != rule_id:
            raise ExportBlockedReason("RULE_MAPPING_MISMATCH")

        rule = self.repository.get_rule(rule_id)
        if rule is None or not getattr(rule, "rule_content", None):
            raise ExportBlockedReason("GENERATED_RULE_MISSING")

        spec_id = getattr(run, "detection_spec_id", None)
        spec = self.repository.get_detection_spec(spec_id)
        if spec is None or not getattr(spec, "is_validated", False):
            raise ExportBlockedReason("DETECTION_SPEC_MISSING")

        try:
            self.compiler_provenance.assert_rule_has_compiler_provenance(rule)
        except CompilerProvenanceError as exc:
            raise ExportBlockedReason("COMPILER_PROVENANCE_MISSING") from exc

        latest_decision = self.repository.latest_review_decision(run_id, rule_id)
        if getattr(latest_decision, "decision", None) != "approved":
            raise ExportBlockedReason("HUMAN_APPROVAL_REQUIRED")

        try:
            self.proof_coverage.assert_coverage_satisfied(
                run_id=run_id,
                rule_id=rule_id,
                proof_rows=self.repository.get_proof_rows(run_id, rule_id),
            )
        except ProofCoverageError as exc:
            raise ExportBlockedReason("PROOF_COVERAGE_MISSING") from exc

        try:
            self.repository.assert_evidence_graph_complete(run_id, rule_id)
        except EvidenceGraphError as exc:
            raise ExportBlockedReason("EVIDENCE_GRAPH_INCOMPLETE") from exc

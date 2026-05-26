"""Centralized export eligibility gate."""

from __future__ import annotations

from typing import Protocol

from de_forge.services.compiler_provenance import (
    CompilerProvenanceError,
    CompilerProvenanceService,
)
from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService


class ExportBlockedReason(ValueError):
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

        try:
            self.proof_coverage.assert_coverage_satisfied(
                run_id=run_id,
                rule_id=rule_id,
                proof_rows=self.repository.get_proof_rows(run_id, rule_id),
            )
        except ProofCoverageError as exc:
            raise ExportBlockedReason("PROOF_COVERAGE_MISSING") from exc

        latest_decision = self.repository.latest_review_decision(run_id, rule_id)
        if getattr(latest_decision, "decision", None) != "approved":
            raise ExportBlockedReason("HUMAN_APPROVAL_REQUIRED")

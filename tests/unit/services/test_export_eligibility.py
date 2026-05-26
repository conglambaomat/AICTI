from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from de_forge.services.artifact_lineage import ArtifactLineageError
from de_forge.services.evidence_graph import EvidenceGraphError
from de_forge.services.export_eligibility import (
    ExportBlockedReason,
    ExportEligibilityService,
)
from de_forge.services.proof_coverage import ProofCoverageService


@dataclass
class FakeRepository:
    run: object | None = None
    rule: object | None = None
    spec: object | None = None
    proof_rows: list[dict[str, object]] | None = None
    review_decision: object | None = None
    evidence_graph_error: bool = False
    artifact_lineage_error: bool = False

    def get_run(self, run_id: str) -> object | None:
        return self.run

    def get_rule(self, rule_id: str) -> object | None:
        return self.rule

    def get_detection_spec(self, spec_id: str) -> object | None:
        return self.spec

    def get_proof_rows(self, run_id: str, rule_id: str) -> list[dict[str, object]]:
        return self.proof_rows or []

    def latest_review_decision(self, run_id: str, rule_id: str) -> object | None:
        return self.review_decision

    def assert_evidence_graph_complete(self, run_id: str, rule_id: str) -> None:
        if self.evidence_graph_error:
            raise EvidenceGraphError("evidence graph path incomplete")

    def assert_artifact_lineage_complete(self, run_id: str, rule_id: str) -> None:
        if self.artifact_lineage_error:
            raise ArtifactLineageError("artifact lineage incomplete")


def valid_proof_rows(run_id: str = "run-1", rule_id: str = "rule-1") -> list[dict[str, object]]:
    return [
        {
            "run_id": run_id,
            "rule_candidate_id": rule_id,
            "claim_type": claim_type,
            "status": "proven",
            "justification": "verified",
        }
        for claim_type in ProofCoverageService().required_claim_types()
    ]


def valid_repo() -> FakeRepository:
    return FakeRepository(
        run=SimpleNamespace(id="run-1", rule_id="rule-1", detection_spec_id="spec-1"),
        rule=SimpleNamespace(
            id="rule-1",
            rule_content="title: compiled rule",
            generation_source="compiler",
            detection_ast_id="ast-1",
            compiled_sigma_id="sigma-1",
        ),
        spec=SimpleNamespace(id="spec-1", is_validated=True),
        proof_rows=valid_proof_rows(),
        review_decision=SimpleNamespace(decision="approved"),
    )


def assert_blocks(repo: FakeRepository, reason: str) -> None:
    service = ExportEligibilityService(repo)
    with pytest.raises(ExportBlockedReason) as exc_info:
        service.assert_exportable("run-1", "rule-1")
    assert str(exc_info.value) == reason


def test_missing_run_blocks_export() -> None:
    repo = valid_repo()
    repo.run = None

    assert_blocks(repo, "PIPELINE_RUN_MISSING")


def test_rule_mapping_mismatch_blocks_export() -> None:
    repo = valid_repo()
    repo.run = SimpleNamespace(id="run-1", rule_id="other-rule", detection_spec_id="spec-1")

    assert_blocks(repo, "RULE_MAPPING_MISMATCH")


def test_missing_generated_rule_blocks_export() -> None:
    repo = valid_repo()
    repo.rule = SimpleNamespace(
        id="rule-1",
        rule_content="",
        generation_source="compiler",
        detection_ast_id="ast-1",
        compiled_sigma_id="sigma-1",
    )

    assert_blocks(repo, "GENERATED_RULE_MISSING")


def test_invalid_spec_blocks_export() -> None:
    repo = valid_repo()
    repo.spec = SimpleNamespace(id="spec-1", is_validated=False)

    assert_blocks(repo, "DETECTION_SPEC_MISSING")


def test_missing_compiler_provenance_blocks_export() -> None:
    repo = valid_repo()
    repo.rule = SimpleNamespace(
        id="rule-1",
        rule_content="title: manually generated rule",
        generation_source="agent",
        detection_ast_id="ast-1",
        compiled_sigma_id="sigma-1",
    )

    assert_blocks(repo, "COMPILER_PROVENANCE_MISSING")


def test_missing_proof_coverage_blocks_export() -> None:
    repo = valid_repo()
    repo.proof_rows = []

    assert_blocks(repo, "PROOF_COVERAGE_MISSING")


def test_latest_rejected_review_blocks_export() -> None:
    repo = valid_repo()
    repo.review_decision = SimpleNamespace(decision="rejected")

    assert_blocks(repo, "HUMAN_APPROVAL_REQUIRED")


def test_incomplete_evidence_graph_blocks_export_before_success() -> None:
    repo = valid_repo()
    repo.evidence_graph_error = True

    assert_blocks(repo, "EVIDENCE_GRAPH_INCOMPLETE")


def test_incomplete_artifact_lineage_blocks_export_before_success() -> None:
    repo = valid_repo()
    repo.artifact_lineage_error = True

    assert_blocks(repo, "ARTIFACT_LINEAGE_INCOMPLETE")


def test_full_valid_fake_repo_passes() -> None:
    ExportEligibilityService(valid_repo()).assert_exportable("run-1", "rule-1")

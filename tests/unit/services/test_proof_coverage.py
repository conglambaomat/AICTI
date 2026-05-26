import pytest

from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService


def test_missing_required_proof_blocks_selection() -> None:
    service = ProofCoverageService()

    with pytest.raises(ProofCoverageError, match="missing required proof obligations"):
        service.assert_coverage_satisfied(
            run_id="run-1",
            rule_id="rule-1",
            proof_rows=[
                {
                    "run_id": "run-1",
                    "rule_candidate_id": "rule-1",
                    "claim_type": "citation_faithful",
                    "status": "proven",
                    "justification": "exact quote verified",
                },
            ],
        )


def test_all_required_proofs_proven_passes() -> None:
    service = ProofCoverageService()
    rows = [
        {
            "run_id": "run-1",
            "rule_candidate_id": "rule-1",
            "claim_type": claim_type,
            "status": "proven",
            "justification": "verified",
        }
        for claim_type in service.required_claim_types()
    ]

    service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def _complete_rows(status: str = "proven", justification: str = "verified") -> list[dict[str, str]]:
    service = ProofCoverageService()
    return [
        {
            "run_id": "run-1",
            "rule_candidate_id": "rule-1",
            "claim_type": claim_type,
            "status": status,
            "justification": justification,
        }
        for claim_type in service.required_claim_types()
    ]


def test_wrong_scope_proofs_do_not_count() -> None:
    service = ProofCoverageService()
    rows = [{**row, "run_id": "other-run"} for row in _complete_rows()]

    with pytest.raises(ProofCoverageError, match="missing required proof obligations"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_failed_or_unknown_proof_blocks_selection() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    rows[0]["status"] = "failed"

    with pytest.raises(ProofCoverageError, match="proof obligation"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)

    rows = _complete_rows()
    rows[0]["status"] = "unknown"

    with pytest.raises(ProofCoverageError, match="proof obligation"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_unjustified_not_applicable_blocks_selection() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    for row in rows:
        if row["claim_type"] == "oracle_expectations_satisfied":
            row["status"] = "not_applicable"
            row["justification"] = ""

    with pytest.raises(ProofCoverageError, match="oracle_expectations_satisfied"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_allowed_justified_not_applicable_passes_for_conditional_claim() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    for row in rows:
        if row["claim_type"] == "oracle_expectations_satisfied":
            row["status"] = "not_applicable"
            row["justification"] = "no oracle case is available for this report"

    service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_duplicate_proof_claim_type_blocks_selection() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    rows.append(dict(rows[0]))

    with pytest.raises(ProofCoverageError, match="duplicate current proof obligation"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)

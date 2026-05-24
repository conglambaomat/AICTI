import pytest
from pydantic import ValidationError

from de_forge.schemas.artifact import ArtifactCreate, ArtifactKind


def test_artifact_create_requires_lineage_hashes() -> None:
    artifact = ArtifactCreate(
        run_id="run_1",
        kind=ArtifactKind.REPORT,
        stage="ingestion",
        payload={"name": "report.txt"},
        input_hash="in_hash",
        output_hash="out_hash",
        parent_artifact_ids=[],
        created_by="system",
    )

    assert artifact.kind == ArtifactKind.REPORT
    assert artifact.parent_artifact_ids == []


def test_artifact_create_rejects_empty_stage() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(
            run_id="run_1",
            kind=ArtifactKind.REPORT,
            stage="",
            payload={},
            input_hash="in_hash",
            output_hash="out_hash",
            parent_artifact_ids=[],
            created_by="system",
        )

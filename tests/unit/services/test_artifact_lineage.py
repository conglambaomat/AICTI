import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models.artifact import Artifact, ArtifactLink
from de_forge.services.artifact_lineage import ArtifactLineageError, ArtifactLineageService


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    local = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return local()


def _artifact(artifact_id: str, *, run_id: str = "run-1", kind: str = "report") -> Artifact:
    return Artifact(
        id=artifact_id,
        run_id=run_id,
        kind=kind,
        stage=kind,
        payload={"rule_id": artifact_id if kind == "generated_rule" else ""},
        input_hash=f"input-{artifact_id}",
        output_hash=f"output-{artifact_id}",
        parent_artifact_ids="[]",
        created_by="test",
    )


def _add_complete_lineage(db: Session, *, run_id: str = "run-1", rule_id: str = "rule-1") -> None:
    db.add_all(
        [
            _artifact("artifact-report", run_id=run_id, kind="report"),
            _artifact("artifact-spec", run_id=run_id, kind="detection_spec"),
            _artifact(
                "artifact-rule",
                run_id=run_id,
                kind="generated_rule",
            ),
        ]
    )
    db.flush()
    db.get(Artifact, "artifact-rule").payload = {"rule_id": rule_id}
    db.add_all(
        [
            ArtifactLink(
                id="link-report-spec",
                parent_artifact_id="artifact-report",
                child_artifact_id="artifact-spec",
                link_type="derived_from",
            ),
            ArtifactLink(
                id="link-spec-rule",
                parent_artifact_id="artifact-spec",
                child_artifact_id="artifact-rule",
                link_type="derived_from",
            ),
        ]
    )
    db.commit()


def test_missing_rule_lineage_blocks_export() -> None:
    service = ArtifactLineageService(db=None)

    with pytest.raises(ArtifactLineageError, match="artifact lineage incomplete"):
        service.assert_rule_lineage_complete(run_id="run-1", rule_id="rule-1")


def test_complete_rule_lineage_passes() -> None:
    db = _session()
    _add_complete_lineage(db)

    ArtifactLineageService(db).assert_rule_lineage_complete(run_id="run-1", rule_id="rule-1")


def test_missing_rule_artifact_blocks_export() -> None:
    db = _session()
    db.add(_artifact("artifact-report", kind="report"))
    db.commit()

    with pytest.raises(ArtifactLineageError, match="artifact lineage incomplete"):
        ArtifactLineageService(db).assert_rule_lineage_complete(run_id="run-1", rule_id="rule-1")


def test_missing_upstream_report_link_blocks_export() -> None:
    db = _session()
    _add_complete_lineage(db)
    db.delete(db.get(ArtifactLink, "link-report-spec"))
    db.commit()

    with pytest.raises(ArtifactLineageError, match="artifact lineage incomplete"):
        ArtifactLineageService(db).assert_rule_lineage_complete(run_id="run-1", rule_id="rule-1")


def test_cross_run_artifacts_do_not_satisfy_lineage() -> None:
    db = _session()
    _add_complete_lineage(db, run_id="other-run")

    with pytest.raises(ArtifactLineageError, match="artifact lineage incomplete"):
        ArtifactLineageService(db).assert_rule_lineage_complete(run_id="run-1", rule_id="rule-1")

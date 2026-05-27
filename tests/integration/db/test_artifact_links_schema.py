from typing import Any

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import Protocol

import de_forge.models  # noqa: F401
from de_forge.db.base import Base
from de_forge.models.artifact import Artifact, ArtifactLink


class _SQLiteConnection(Protocol):
    def execute(self, statement: str, parameters: Any = ...) -> Any: ...


def create_sqlite_engine_with_foreign_keys() -> Engine:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: _SQLiteConnection, _connection_record: object) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine


def _artifact(artifact_id: str) -> Artifact:
    return Artifact(
        id=artifact_id,
        run_id="run-1",
        kind="report",
        stage="ingestion",
        payload={"id": artifact_id},
        input_hash=f"input-{artifact_id}",
        output_hash=f"output-{artifact_id}",
        parent_artifact_ids="[]",
        created_by="test",
    )


def test_artifact_links_table_exists_with_required_constraints() -> None:
    engine = create_sqlite_engine_with_foreign_keys()
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "artifact_links" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("artifact_links")}
    assert {"id", "parent_artifact_id", "child_artifact_id", "link_type", "created_at"}.issubset(
        columns
    )

    foreign_keys = {
        foreign_key["name"]: (
            tuple(foreign_key["constrained_columns"]),
            foreign_key["referred_table"],
            tuple(foreign_key["referred_columns"]),
        )
        for foreign_key in inspector.get_foreign_keys("artifact_links")
    }
    assert foreign_keys["fk_artifact_links_parent_artifact_id_artifacts"] == (
        ("parent_artifact_id",),
        "artifacts",
        ("id",),
    )
    assert foreign_keys["fk_artifact_links_child_artifact_id_artifacts"] == (
        ("child_artifact_id",),
        "artifacts",
        ("id",),
    )

    unique_constraints = {
        constraint["name"]: tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("artifact_links")
    }
    assert unique_constraints["uq_artifact_links_parent_child_type"] == (
        "parent_artifact_id",
        "child_artifact_id",
        "link_type",
    )

    check_constraints = {
        constraint["name"]: constraint["sqltext"]
        for constraint in inspector.get_check_constraints("artifact_links")
    }
    assert check_constraints["ck_artifact_links_no_self_link"] == (
        "parent_artifact_id != child_artifact_id"
    )


def test_self_artifact_link_is_rejected() -> None:
    engine = create_sqlite_engine_with_foreign_keys()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        artifact = _artifact("artifact-1")
        session.add(artifact)
        session.flush()
        session.add(
            ArtifactLink(
                id="link-self",
                parent_artifact_id=artifact.id,
                child_artifact_id=artifact.id,
                link_type="derived_from",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_artifact_link_to_missing_parent_is_rejected() -> None:
    engine = create_sqlite_engine_with_foreign_keys()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        child = _artifact("artifact-child")
        session.add(child)
        session.flush()
        session.add(
            ArtifactLink(
                id="link-missing-parent",
                parent_artifact_id="missing-parent",
                child_artifact_id=child.id,
                link_type="derived_from",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_duplicate_artifact_link_is_rejected() -> None:
    engine = create_sqlite_engine_with_foreign_keys()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        parent = _artifact("artifact-parent")
        child = _artifact("artifact-child")
        session.add_all([parent, child])
        session.flush()
        session.add_all(
            [
                ArtifactLink(
                    id="link-1",
                    parent_artifact_id=parent.id,
                    child_artifact_id=child.id,
                    link_type="derived_from",
                ),
                ArtifactLink(
                    id="link-2",
                    parent_artifact_id=parent.id,
                    child_artifact_id=child.id,
                    link_type="derived_from",
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            session.commit()

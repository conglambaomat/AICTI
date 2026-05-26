from __future__ import annotations

from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models.artifact import Artifact, ArtifactLink


class ArtifactLineageError(ValueError):
    pass


class ArtifactLineageService:
    def __init__(self, db: Session | None) -> None:
        self.db = db

    def assert_rule_lineage_complete(self, *, run_id: str, rule_id: str) -> None:
        db = self._require_db()
        artifacts = db.execute(select(Artifact).where(Artifact.run_id == run_id)).scalars().all()
        artifact_ids = {artifact.id for artifact in artifacts}
        rule_artifacts = [
            artifact
            for artifact in artifacts
            if artifact.kind == "generated_rule" and artifact.payload.get("rule_id") == rule_id
        ]
        if not rule_artifacts:
            raise ArtifactLineageError("artifact lineage incomplete")

        links = (
            db.execute(
                select(ArtifactLink).where(
                    ArtifactLink.parent_artifact_id.in_(artifact_ids),
                    ArtifactLink.child_artifact_id.in_(artifact_ids),
                    ArtifactLink.link_type == "derived_from",
                )
            )
            .scalars()
            .all()
        )
        parents_by_child: dict[str, list[str]] = defaultdict(list)
        for link in links:
            parents_by_child[link.child_artifact_id].append(link.parent_artifact_id)

        if not any(
            self._has_report_ancestor(rule_artifact.id, artifacts, parents_by_child)
            for rule_artifact in rule_artifacts
        ):
            raise ArtifactLineageError("artifact lineage incomplete")

    def _require_db(self) -> Session:
        if self.db is None:
            raise ArtifactLineageError("artifact lineage incomplete")
        return self.db

    def _has_report_ancestor(
        self,
        artifact_id: str,
        artifacts: list[Artifact],
        parents_by_child: dict[str, list[str]],
    ) -> bool:
        artifacts_by_id = {artifact.id: artifact for artifact in artifacts}
        queue: deque[str] = deque([artifact_id])
        visited: set[str] = {artifact_id}
        while queue:
            current_id = queue.popleft()
            for parent_id in parents_by_child.get(current_id, []):
                if parent_id in visited:
                    continue
                parent = artifacts_by_id.get(parent_id)
                if parent is None:
                    continue
                if parent.kind == "report":
                    return True
                visited.add(parent_id)
                queue.append(parent_id)
        return False

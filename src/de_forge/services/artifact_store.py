from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from de_forge.models.artifact import Artifact


class ArtifactStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_artifact(
        self,
        *,
        run_id: str,
        kind: str,
        stage: str,
        payload: dict[str, Any],
        input_hash: str,
        output_hash: str,
        parent_artifact_ids: list[str],
        created_by: str,
    ) -> str:
        artifact_id = f"artifact_{uuid4().hex[:12]}"
        row = Artifact(
            id=artifact_id,
            run_id=run_id,
            kind=kind,
            stage=stage,
            payload=payload,
            input_hash=input_hash,
            output_hash=output_hash,
            parent_artifact_ids=json.dumps(parent_artifact_ids),
            created_by=created_by,
        )
        self.db.add(row)
        self.db.commit()
        return artifact_id

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        return self.db.get(Artifact, artifact_id)

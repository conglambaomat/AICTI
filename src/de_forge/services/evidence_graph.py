from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from de_forge.models.evidence_graph import EvidenceEdge, EvidenceNode


class EvidenceGraphStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_node(self, *, run_id: str, node_type: str, payload: dict[str, Any]) -> str:
        node_id = f"node_{uuid4().hex[:12]}"
        row = EvidenceNode(id=node_id, run_id=run_id, node_type=node_type, payload=payload)
        self.db.add(row)
        self.db.commit()
        return node_id

    def add_edge(
        self, *, run_id: str, source_node_id: str, target_node_id: str, edge_type: str
    ) -> str:
        edge_id = f"edge_{uuid4().hex[:12]}"
        row = EvidenceEdge(
            id=edge_id,
            run_id=run_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
        )
        self.db.add(row)
        self.db.commit()
        return edge_id

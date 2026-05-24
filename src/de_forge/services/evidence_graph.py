from __future__ import annotations

from collections import defaultdict, deque
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models.evidence_graph import EvidenceEdge, EvidenceNode


class EvidenceGraphStore:
    _ALLOWED_NODE_TYPES = {
        "evidence_quote",
        "detection_strategy",
        "analytic",
        "data_component",
        "telemetry_source",
        "reviewed_rule_candidate",
    }
    _ALLOWED_EDGE_TYPES = {"supports", "derives", "maps_to", "implements"}
    _REQUIRED_LINEAGE_PATH = [
        "evidence_quote",
        "detection_strategy",
        "analytic",
        "data_component",
        "telemetry_source",
        "reviewed_rule_candidate",
    ]

    def __init__(self, db: Session) -> None:
        self.db = db

    def add_node(self, *, run_id: str, node_type: str, payload: dict[str, Any]) -> str:
        if node_type not in self._ALLOWED_NODE_TYPES:
            raise ValueError("unsupported node_type")

        node_id = f"node_{uuid4().hex[:12]}"
        row = EvidenceNode(id=node_id, run_id=run_id, node_type=node_type, payload=payload)
        self.db.add(row)
        self.db.commit()
        return node_id

    def add_edge(
        self, *, run_id: str, source_node_id: str, target_node_id: str, edge_type: str
    ) -> str:
        if edge_type not in self._ALLOWED_EDGE_TYPES:
            raise ValueError("unsupported edge_type")

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

    def has_required_lineage_path(
        self, *, run_id: str, from_node_type: str, to_node_type: str
    ) -> bool:
        if (
            from_node_type != self._REQUIRED_LINEAGE_PATH[0]
            or to_node_type != self._REQUIRED_LINEAGE_PATH[-1]
        ):
            return False

        nodes = (
            self.db.execute(select(EvidenceNode).where(EvidenceNode.run_id == run_id))
            .scalars()
            .all()
        )
        edges = (
            self.db.execute(select(EvidenceEdge).where(EvidenceEdge.run_id == run_id))
            .scalars()
            .all()
        )

        node_type_by_id = {node.id: node.node_type for node in nodes}
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            adjacency[edge.source_node_id].append(edge.target_node_id)

        start_nodes = [node.id for node in nodes if node.node_type == from_node_type]
        for start_node in start_nodes:
            queue: deque[tuple[str, int]] = deque([(start_node, 0)])
            visited: set[tuple[str, int]] = {(start_node, 0)}

            while queue:
                node_id, step = queue.popleft()
                if step == len(self._REQUIRED_LINEAGE_PATH) - 1:
                    return True

                next_step = step + 1
                required_type = self._REQUIRED_LINEAGE_PATH[next_step]
                for target_id in adjacency.get(node_id, []):
                    if node_type_by_id.get(target_id) != required_type:
                        continue
                    state = (target_id, next_step)
                    if state in visited:
                        continue
                    visited.add(state)
                    queue.append(state)

        return False

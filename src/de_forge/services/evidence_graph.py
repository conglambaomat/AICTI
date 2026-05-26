from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models.contract import GraphEdge, GraphNode
from de_forge.models.evidence_graph import EvidenceEdge, EvidenceNode


class EvidenceGraphError(ValueError):
    pass


class EvidenceGraphService:
    def __init__(self, db: Session | None) -> None:
        self.db = db

    def upsert_node(
        self,
        *,
        run_id: str,
        node_type: str,
        ref_table: str,
        ref_id: str,
        payload: dict[str, object] | None = None,
    ) -> str:
        db = self._require_db()
        row = db.execute(
            select(GraphNode).where(
                GraphNode.run_id == run_id,
                GraphNode.node_type == node_type,
                GraphNode.ref_table == ref_table,
                GraphNode.ref_id == ref_id,
            )
        ).scalar_one_or_none()
        payload_json = json.dumps(payload or {}, sort_keys=True)
        if row is not None:
            row.payload_json = payload_json
            return row.id

        node_id = str(uuid4())
        db.add(
            GraphNode(
                id=node_id,
                run_id=run_id,
                node_type=node_type,
                ref_table=ref_table,
                ref_id=ref_id,
                payload_json=payload_json,
                created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            )
        )
        return node_id

    def add_edge(
        self,
        *,
        run_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_type: str,
        payload: dict[str, object] | None = None,
    ) -> str:
        db = self._require_db()
        row = db.execute(
            select(GraphEdge).where(
                GraphEdge.run_id == run_id,
                GraphEdge.source_node_id == source_node_id,
                GraphEdge.target_node_id == target_node_id,
                GraphEdge.edge_type == edge_type,
            )
        ).scalar_one_or_none()
        payload_json = json.dumps(payload or {}, sort_keys=True)
        if row is not None:
            row.payload_json = payload_json
            return row.id

        edge_id = str(uuid4())
        db.add(
            GraphEdge(
                id=edge_id,
                run_id=run_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                edge_type=edge_type,
                payload_json=payload_json,
                created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            )
        )
        return edge_id

    def assert_export_path_complete(self, *, run_id: str, rule_id: str) -> None:
        db = self._require_db()
        nodes = db.execute(select(GraphNode).where(GraphNode.run_id == run_id)).scalars().all()
        edges = db.execute(select(GraphEdge).where(GraphEdge.run_id == run_id)).scalars().all()
        nodes_by_id = {node.id: node for node in nodes}
        adjacency: dict[str, list[GraphNode]] = defaultdict(list)
        for edge in edges:
            target = nodes_by_id.get(edge.target_node_id)
            if target is not None:
                adjacency[edge.source_node_id].append(target)

        rule_node = next(
            (
                node
                for node in nodes
                if node.node_type == "generated_rule"
                and node.ref_table == "generated_rules"
                and node.ref_id == rule_id
            ),
            None,
        )
        if rule_node is None:
            raise EvidenceGraphError("evidence graph path incomplete")

        if not any(node.node_type == "review_decision" for node in adjacency[rule_node.id]):
            raise EvidenceGraphError("evidence graph path incomplete")
        if not any(node.node_type == "validation_result" for node in adjacency[rule_node.id]):
            raise EvidenceGraphError("evidence graph path incomplete")

        validation_nodes = [node for node in adjacency[rule_node.id] if node.node_type == "validation_result"]
        if not any(
            target.node_type == "proof_obligation"
            for validation_node in validation_nodes
            for target in adjacency[validation_node.id]
        ):
            raise EvidenceGraphError("evidence graph path incomplete")

        if not self._has_upstream_detection_spec(rule_node_id=rule_node.id, nodes_by_id=nodes_by_id, edges=edges):
            raise EvidenceGraphError("evidence graph path incomplete")

    def _require_db(self) -> Session:
        if self.db is None:
            raise EvidenceGraphError("evidence graph path incomplete")
        return self.db

    def _has_upstream_detection_spec(
        self,
        *,
        rule_node_id: str,
        nodes_by_id: dict[str, GraphNode],
        edges: list[GraphEdge],
    ) -> bool:
        reverse_adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            reverse_adjacency[edge.target_node_id].append(edge.source_node_id)

        queue: deque[str] = deque([rule_node_id])
        visited: set[str] = {rule_node_id}
        while queue:
            node_id = queue.popleft()
            for source_id in reverse_adjacency.get(node_id, []):
                if source_id in visited:
                    continue
                source = nodes_by_id.get(source_id)
                if source is None:
                    continue
                if source.node_type == "detection_spec":
                    return True
                visited.add(source_id)
                queue.append(source_id)
        return False


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

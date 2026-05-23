from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models.artifact import Artifact
from de_forge.models.evidence_graph import EvidenceEdge, EvidenceNode
from de_forge.services.artifact_store import ArtifactStore
from de_forge.services.evidence_graph import EvidenceGraphStore


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    local = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return local()


def test_artifact_store_persists_lineage_artifact() -> None:
    db = _session()
    store = ArtifactStore(db)

    artifact_id = store.create_artifact(
        run_id="run_1",
        kind="report",
        stage="ingestion",
        payload={"text": "hello"},
        input_hash="in_hash",
        output_hash="out_hash",
        parent_artifact_ids=[],
        created_by="system",
    )

    row = db.get(Artifact, artifact_id)
    assert row is not None
    assert row.run_id == "run_1"
    assert row.kind == "report"


def test_artifact_store_reads_artifact_by_id() -> None:
    db = _session()
    store = ArtifactStore(db)

    artifact_id = store.create_artifact(
        run_id="run_1",
        kind="chunk",
        stage="chunking",
        payload={"chunk": "abc"},
        input_hash="in_hash",
        output_hash="out_hash",
        parent_artifact_ids=[],
        created_by="system",
    )

    fetched = store.get_artifact(artifact_id)
    assert fetched is not None
    assert fetched.id == artifact_id
    assert fetched.payload["chunk"] == "abc"


def test_evidence_graph_store_persists_nodes_and_edges() -> None:
    db = _session()
    graph = EvidenceGraphStore(db)

    n1 = graph.add_node(run_id="run_1", node_type="report_chunk", payload={"chunk_id": "c1"})
    n2 = graph.add_node(run_id="run_1", node_type="behavior", payload={"behavior_id": "b1"})
    e1 = graph.add_edge(run_id="run_1", source_node_id=n1, target_node_id=n2, edge_type="supports")

    assert db.get(EvidenceNode, n1) is not None
    edge = db.get(EvidenceEdge, e1)
    assert edge is not None
    assert edge.source_node_id == n1

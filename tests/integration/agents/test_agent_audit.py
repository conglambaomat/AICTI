from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.models.agent_run import AgentRun
from de_forge.schemas.agent_io import AgentMetadata, AgentOutputEnvelope
from de_forge.services.agent_audit import AgentAuditService


def test_agent_audit_persists_input_output_hashes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    envelope = AgentOutputEnvelope(
        run_id="run_1",
        agent_name="evidence_agent",
        input_artifact_ids=["artifact_1"],
        output={"evidence_quotes": []},
        confidence=0.9,
        citations=[],
        abstain=False,
        metadata=AgentMetadata(
            model="cx/gpt-5.5",
            prompt_version="evidence_agent:v1",
            tokens_in=10,
            tokens_out=5,
            latency_ms=100,
        ),
    )

    with Session(engine) as session:
        record = AgentAuditService(session).persist(
            input_payload={"chunks": []}, output_envelope=envelope
        )
        session.commit()
        loaded = session.scalar(select(AgentRun).where(AgentRun.id == record.id))

    assert loaded is not None
    assert loaded.agent_name == "evidence_agent"
    assert loaded.input_hash
    assert loaded.output_hash

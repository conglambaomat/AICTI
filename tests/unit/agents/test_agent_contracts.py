import pytest
from pydantic import ValidationError

from de_forge.agents.attack_mapping_agent import AttackMappingAgent
from de_forge.agents.base import BaseAgent
from de_forge.agents.critic_agent import CriticAgent
from de_forge.agents.detection_spec_agent import DetectionSpecAgent
from de_forge.agents.evidence_agent import EvidenceAgent
from de_forge.schemas.agent_io import AgentMetadata, AgentOutputEnvelope, Citation
from de_forge.services.llm_client import LLMClient, LlmRequest, LlmResponse
from de_forge.services.prompt_registry import PromptRegistry


def test_agent_output_envelope_tracks_metadata_and_artifacts() -> None:
    output = AgentOutputEnvelope(
        run_id="run_1",
        agent_name="evidence_agent",
        input_artifact_ids=["artifact_1"],
        output={"evidence_quotes": []},
        confidence=0.9,
        citations=[],
        abstain=False,
        abstain_reason=None,
        metadata=AgentMetadata(
            model="cx/gpt-5.5",
            prompt_version="evidence:v1",
            tokens_in=100,
            tokens_out=50,
            latency_ms=1000,
        ),
    )

    assert output.agent_name == "evidence_agent"
    assert output.metadata.model == "cx/gpt-5.5"


def test_agent_output_confidence_must_be_bounded() -> None:
    with pytest.raises(ValidationError):
        AgentOutputEnvelope(
            run_id="run_1",
            agent_name="bad_agent",
            input_artifact_ids=[],
            output={},
            confidence=1.5,
            citations=[],
            abstain=False,
            metadata=AgentMetadata(
                model="m", prompt_version="p", tokens_in=0, tokens_out=0, latency_ms=0
            ),
        )


def test_citation_schema_tracks_exact_span() -> None:
    citation = Citation(chunk_id="chunk_1", quote="encoded command", start_offset=10, end_offset=25)

    assert citation.chunk_id == "chunk_1"
    assert citation.start_offset == 10


def test_prompt_registry_returns_versioned_prompt() -> None:
    registry = PromptRegistry.default()

    prompt = registry.get("evidence_agent", "v1")

    assert prompt.prompt_id == "evidence_agent:v1"
    assert "Extract only explicitly supported behavioral evidence" in prompt.system_prompt


def test_llm_request_and_response_contracts() -> None:
    request = LlmRequest(
        system_prompt="system", user_prompt="user", response_schema_name="EvidenceOutput"
    )
    response = LlmResponse(content={"ok": True}, tokens_in=10, tokens_out=5, latency_ms=20)

    assert request.response_schema_name == "EvidenceOutput"
    assert response.content == {"ok": True}


class FakeClient(LLMClient):
    def __init__(self) -> None:
        pass

    def complete_json(self, request: LlmRequest) -> LlmResponse:
        return LlmResponse(content={"answer": "ok"}, tokens_in=1, tokens_out=1, latency_ms=1)


class TestAgent(BaseAgent):
    __test__ = False
    agent_name = "test_agent"
    prompt_version = "v1"
    response_schema_name = "TestOutput"

    def build_user_prompt(self, input_payload: dict[str, object]) -> str:
        return "test"


def test_base_agent_wraps_llm_response_in_envelope() -> None:
    agent = TestAgent(llm_client=FakeClient(), system_prompt="system")

    envelope = agent.run(run_id="run_1", input_artifact_ids=["artifact_1"], input_payload={"x": 1})

    assert envelope.agent_name == "test_agent"
    assert envelope.output == {"answer": "ok"}
    assert envelope.metadata.prompt_version == "test_agent:v1"


class EvidenceFakeClient(LLMClient):
    def __init__(self) -> None:
        pass

    def complete_json(self, request: LlmRequest) -> LlmResponse:
        return LlmResponse(
            content={
                "confidence": 0.95,
                "evidence_quotes": [
                    {
                        "quote": "PowerShell executed an encoded command",
                        "chunk_id": "chunk_1",
                        "start_offset": 0,
                        "end_offset": 38,
                        "behavior_label": "encoded PowerShell execution",
                    }
                ],
                "abstain": False,
            },
            tokens_in=20,
            tokens_out=10,
            latency_ms=50,
        )


def test_evidence_agent_returns_citations_from_evidence_quotes() -> None:
    agent = EvidenceAgent(llm_client=EvidenceFakeClient())

    envelope = agent.run(
        run_id="run_1",
        input_artifact_ids=["chunk_artifact_1"],
        input_payload={
            "chunks": [{"id": "chunk_1", "text": "PowerShell executed an encoded command"}]
        },
    )

    assert envelope.agent_name == "evidence_agent"
    assert envelope.citations[0].chunk_id == "chunk_1"
    assert envelope.citations[0].quote == "PowerShell executed an encoded command"


def test_attack_mapping_agent_prompt_mentions_evidence_only() -> None:
    agent = AttackMappingAgent(llm_client=FakeClient())

    prompt = agent.build_user_prompt({"behaviors": [{"id": "behavior_1"}], "evidence": []})

    assert "using only supplied evidence" in prompt


def test_detection_spec_agent_prompt_mentions_verified_spec_contract() -> None:
    agent = DetectionSpecAgent(llm_client=FakeClient())

    prompt = agent.build_user_prompt({"graph_paths": []})

    assert "DetectionSpec" in prompt
    assert "telemetry" in prompt


def test_critic_agent_prompt_asks_for_false_positive_and_bypass_risks() -> None:
    agent = CriticAgent(llm_client=FakeClient())

    prompt = agent.build_user_prompt({"candidate": {"id": "candidate_1"}})

    assert "false positive" in prompt
    assert "bypass" in prompt


class TestBadAgentName:
    pass


__all__ = ["TestAgent", "FakeClient", "TestBadAgentName"]

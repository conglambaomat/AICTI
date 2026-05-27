from __future__ import annotations

import pytest

from de_forge.agents.base import AgentOutputValidationError, BaseAgent
from de_forge.agents.evidence_agent import EvidenceAgent


class FakeLlm:
    def complete_json(self, request):
        return type(
            "Response",
            (),
            {
                "content": {"confidence": 0.9},
                "tokens_in": 1,
                "tokens_out": 1,
                "latency_ms": 1,
                "cost_usd": 0.0,
            },
        )()


class CitationRequiredAgent(BaseAgent):
    agent_name = "evidence"
    prompt_version = "v1"
    response_schema_name = "evidence"
    requires_citations = True

    def build_user_prompt(self, input_payload):
        return "extract evidence"


def test_citation_required_agent_rejects_empty_citations() -> None:
    agent = CitationRequiredAgent(FakeLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="citations required"):
        agent.run("run-1", ["artifact-1"], {"text": "PowerShell"})


def test_citation_required_agent_allows_valid_citations() -> None:
    class CitationLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.9,
                        "citations": [
                            {
                                "chunk_id": "chunk-1",
                                "quote": "PowerShell",
                                "start_offset": 0,
                                "end_offset": 10,
                            }
                        ],
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(CitationLlm(), "system")

    envelope = agent.run("run-1", ["artifact-1"], {"text": "PowerShell"})

    assert envelope.citations[0].chunk_id == "chunk-1"
    assert envelope.citations[0].quote == "PowerShell"


def test_citation_required_agent_rejects_malformed_citations() -> None:
    class MalformedCitationLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.9,
                        "citations": [
                            {
                                "chunk_id": "chunk-1",
                                "start_offset": 0,
                                "end_offset": 10,
                            }
                        ],
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(MalformedCitationLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="citations malformed"):
        agent.run("run-1", ["artifact-1"], {"text": "PowerShell"})


def test_citation_required_agent_rejects_non_list_citations() -> None:
    class NonListCitationLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.9,
                        "citations": {
                            "chunk_id": "chunk-1",
                            "quote": "PowerShell",
                            "start_offset": 0,
                            "end_offset": 10,
                        },
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(NonListCitationLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="citations must be a list"):
        agent.run("run-1", ["artifact-1"], {"text": "PowerShell"})


def test_citation_required_agent_rejects_falsy_non_list_citations() -> None:
    class FalsyNonListCitationLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {"confidence": 0.9, "citations": ""},
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(FalsyNonListCitationLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="citations must be a list"):
        agent.run("run-1", ["artifact-1"], {"text": "PowerShell"})


def test_citation_required_agent_rejects_abstain_without_reason() -> None:
    class AbstainWithoutReasonLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {"confidence": 0.1, "abstain": True},
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(AbstainWithoutReasonLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="abstain_reason required"):
        agent.run("run-1", ["artifact-1"], {"text": ""})


def test_citation_required_agent_rejects_blank_abstain_reason() -> None:
    class BlankAbstainReasonLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.1,
                        "abstain": True,
                        "abstain_reason": "   ",
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(BlankAbstainReasonLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="abstain_reason required"):
        agent.run("run-1", ["artifact-1"], {"text": ""})


def test_citation_required_agent_allows_abstain_with_reason() -> None:
    class AbstainLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.1,
                        "abstain": True,
                        "abstain_reason": "no evidence",
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = CitationRequiredAgent(AbstainLlm(), "system")

    envelope = agent.run("run-1", ["artifact-1"], {"text": ""})

    assert envelope.abstain is True
    assert envelope.abstain_reason == "no evidence"


def test_evidence_agent_enforces_evidence_quote_citations() -> None:
    class EmptyEvidenceLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {"confidence": 0.9, "evidence_quotes": []},
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = EvidenceAgent(EmptyEvidenceLlm())

    with pytest.raises(AgentOutputValidationError, match="citations required"):
        agent.run("run-1", ["artifact-1"], {"chunks": []})


def test_evidence_agent_rejects_malformed_evidence_quote_citations() -> None:
    class MalformedEvidenceQuoteLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.9,
                        "evidence_quotes": [
                            {
                                "chunk_id": "chunk-1",
                                "start_offset": 0,
                                "end_offset": 10,
                            }
                        ],
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = EvidenceAgent(MalformedEvidenceQuoteLlm())

    with pytest.raises(AgentOutputValidationError, match="citations malformed"):
        agent.run("run-1", ["artifact-1"], {"chunks": []})


def test_evidence_agent_rejects_non_list_evidence_quote_citations() -> None:
    class NonListEvidenceQuoteLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.9,
                        "evidence_quotes": {
                            "chunk_id": "chunk-1",
                            "quote": "PowerShell",
                            "start_offset": 0,
                            "end_offset": 10,
                        },
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = EvidenceAgent(NonListEvidenceQuoteLlm())

    with pytest.raises(AgentOutputValidationError, match="citations must be a list"):
        agent.run("run-1", ["artifact-1"], {"chunks": []})


def test_evidence_agent_rejects_falsy_non_list_evidence_quote_citations() -> None:
    class FalsyNonListEvidenceQuoteLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {"confidence": 0.9, "evidence_quotes": ""},
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = EvidenceAgent(FalsyNonListEvidenceQuoteLlm())

    with pytest.raises(AgentOutputValidationError, match="citations must be a list"):
        agent.run("run-1", ["artifact-1"], {"chunks": []})


def test_evidence_agent_accepts_evidence_quote_citations() -> None:
    class EvidenceQuoteLlm:
        def complete_json(self, request):
            return type(
                "Response",
                (),
                {
                    "content": {
                        "confidence": 0.9,
                        "evidence_quotes": [
                            {
                                "chunk_id": "chunk-1",
                                "quote": "PowerShell",
                                "start_offset": 0,
                                "end_offset": 10,
                            }
                        ],
                    },
                    "tokens_in": 1,
                    "tokens_out": 1,
                    "latency_ms": 1,
                    "cost_usd": 0.0,
                },
            )()

    agent = EvidenceAgent(EvidenceQuoteLlm())

    envelope = agent.run("run-1", ["artifact-1"], {"chunks": []})

    assert envelope.citations[0].chunk_id == "chunk-1"
    assert envelope.citations[0].quote == "PowerShell"

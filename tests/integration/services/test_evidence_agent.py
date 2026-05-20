from __future__ import annotations

from de_forge.services.evidence import EvidenceAgentService


class StubRetrievalService:
    def __init__(self, chunks: list[dict[str, object]]) -> None:
        self.chunks = chunks
        self.last_query: str | None = None

    def retrieve(self, query: str, report_id: str) -> list[dict[str, object]]:
        self.last_query = query
        return self.chunks


class StubLlmClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.last_payload: dict[str, object] | None = None

    def generate_structured(self, *, schema_name: str, payload: dict[str, object]) -> dict[str, object]:
        self.last_payload = {"schema_name": schema_name, "payload": payload}
        return self.response


def test_extract_evidence_returns_grounded_quotes_with_offsets() -> None:
    chunks = [
        {
            "chunk_id": "c1",
            "text": "The attacker used powershell.exe -enc aGVsbG8= to execute payload.",
        }
    ]
    llm_response = {
        "evidence": [
            {
                "chunk_id": "c1",
                "quote": "powershell.exe -enc",
                "start_offset": 18,
                "end_offset": 37,
                "claim": "Encoded PowerShell execution",
            }
        ]
    }

    retrieval = StubRetrievalService(chunks)
    llm = StubLlmClient(llm_response)
    service = EvidenceAgentService(retrieval_service=retrieval, llm_client=llm)

    result = service.extract(report_id="r1", report_text="PowerShell execution observed.")

    assert result["status"] == "ok"
    assert result["query_plan"]["query"] == "PowerShell execution observed."
    assert result["evidence"][0]["chunk_id"] == "c1"
    assert retrieval.last_query == "PowerShell execution observed."
    assert llm.last_payload is not None
    assert llm.last_payload["schema_name"] == "evidence_output"


def test_extract_evidence_abstains_when_evidence_is_weak() -> None:
    chunks = [{"chunk_id": "c1", "text": "Report mentions CVE-2024-0001 only."}]
    llm_response = {"evidence": []}

    retrieval = StubRetrievalService(chunks)
    llm = StubLlmClient(llm_response)
    service = EvidenceAgentService(retrieval_service=retrieval, llm_client=llm)

    result = service.extract(report_id="r2", report_text="CVE mention with no behavior.")

    assert result["status"] == "abstain"
    assert result["abstain_code"] == "NO_EVIDENCE_BACKED_BEHAVIOR"

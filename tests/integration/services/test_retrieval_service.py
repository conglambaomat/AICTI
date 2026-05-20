from de_forge.services.retrieval import RetrievalService


def test_index_chunks_produces_deterministic_chunk_ids() -> None:
    service = RetrievalService()
    report_id = "report-1"
    report_text = "Alpha bravo charlie " * 400

    first_index = service.index_chunks(report_id=report_id, report_text=report_text)
    second_index = service.index_chunks(report_id=report_id, report_text=report_text)

    first_ids = [chunk.chunk_id for chunk in first_index.chunks]
    second_ids = [chunk.chunk_id for chunk in second_index.chunks]

    assert first_ids == second_ids
    assert len(first_ids) > 0


def test_retrieve_returns_rrf_fused_ordering() -> None:
    service = RetrievalService()
    report_id = "report-2"
    report_text = (
        "powershell download cradle execution command observed. "
        "benign office process launch noted. "
        "network transfer via certutil detected. "
    ) * 100

    service.index_chunks(report_id=report_id, report_text=report_text)
    results = service.retrieve(query="powershell download", report_id=report_id, k=5)

    assert len(results) > 0
    fused_scores = [result.score_fused for result in results]
    assert fused_scores == sorted(fused_scores, reverse=True)


def test_retrieve_is_deterministic_for_same_input() -> None:
    service = RetrievalService()
    report_id = "report-3"
    report_text = "cmd.exe /c whoami executed by suspicious parent process. " * 200

    service.index_chunks(report_id=report_id, report_text=report_text)

    first = service.retrieve(query="cmd whoami", report_id=report_id, k=5)
    second = service.retrieve(query="cmd whoami", report_id=report_id, k=5)

    first_ids = [result.chunk_id for result in first]
    second_ids = [result.chunk_id for result in second]

    assert first_ids == second_ids

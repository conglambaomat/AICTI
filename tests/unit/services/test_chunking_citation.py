import pytest

from de_forge.services.chunking import chunk_text
from de_forge.services.citation_verifier import verify_citation


def test_chunk_text_splits_deterministically() -> None:
    text = "a b c d e f g h"
    chunks = chunk_text(text, chunk_size=5)
    assert len(chunks) >= 2
    assert chunks[0]["start"] == 0


def test_verify_citation_accepts_exact_quote_and_offsets() -> None:
    text = "PowerShell encoded command observed"
    quote = "encoded command"
    start = text.index(quote)
    end = start + len(quote)
    assert verify_citation(text, quote, start, end) is True


def test_verify_citation_rejects_mismatch() -> None:
    text = "PowerShell encoded command observed"
    assert verify_citation(text, "wrong", 0, 5) is False


def test_verify_citation_rejects_out_of_bounds() -> None:
    text = "short"
    with pytest.raises(ValueError):
        verify_citation(text, "x", -1, 1)

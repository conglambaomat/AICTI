from pathlib import Path

import pytest

from de_forge.services.pdf_text_extraction import (
    PdfExtractionError,
    PdfTextExtractionService,
)


def test_empty_pdf_bytes_fail_closed() -> None:
    service = PdfTextExtractionService()

    with pytest.raises(PdfExtractionError, match="PDF text extraction failed"):
        service.extract_text(b"")


def test_text_based_pdf_extracts_text_with_page_offsets() -> None:
    content = Path("tests/fixtures/text_report.pdf").read_bytes()

    result = PdfTextExtractionService().extract_text(content)

    assert "PowerShell" in result.text
    assert result.pages[0].page_number == 1
    assert result.pages[0].global_char_start == 0
    assert result.pages[0].global_char_end > 0
    assert (
        result.text[result.pages[0].global_char_start : result.pages[0].global_char_end]
        == result.pages[0].text
    )
    assert (
        "PowerShell"
        in result.text[result.pages[0].global_char_start : result.pages[0].global_char_end]
    )
    assert result.metadata["page_count"] == 1
    assert result.metadata["extractor"] == "pypdf"

import pytest

from de_forge.services.pdf_text_extraction import (
    PdfExtractionError,
    PdfTextExtractionService,
)


def test_empty_pdf_bytes_fail_closed() -> None:
    service = PdfTextExtractionService()

    with pytest.raises(PdfExtractionError, match="PDF text extraction failed"):
        service.extract_text(b"")

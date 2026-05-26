from __future__ import annotations

from dataclasses import dataclass


class PdfExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class PdfPageText:
    page_number: int
    text: str
    global_char_start: int
    global_char_end: int


@dataclass(frozen=True)
class PdfExtractionResult:
    text: str
    pages: list[PdfPageText]
    metadata: dict[str, object]


class PdfTextExtractionService:
    def extract_text(self, content: bytes) -> PdfExtractionResult:
        if not content:
            raise PdfExtractionError("PDF text extraction failed")
        raise PdfExtractionError("PDF text extraction failed")

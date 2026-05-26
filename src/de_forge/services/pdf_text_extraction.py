from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


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
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise PdfExtractionError("PDF text extraction failed: encrypted PDF")

            pages: list[PdfPageText] = []
            parts: list[str] = []
            cursor = 0
            for index, page in enumerate(reader.pages, start=1):
                page_text = (page.extract_text() or "").strip()
                if not page_text:
                    continue
                if parts:
                    parts.append("\n")
                    cursor += 1
                start = cursor
                parts.append(page_text)
                cursor += len(page_text)
                pages.append(PdfPageText(index, page_text, start, cursor))

            text = "".join(parts)
            if not text:
                raise PdfExtractionError("PDF text extraction failed: no extractable text")
            return PdfExtractionResult(
                text=text,
                pages=pages,
                metadata={"page_count": len(reader.pages), "extractor": "pypdf"},
            )
        except PdfExtractionError:
            raise
        except Exception as exc:
            raise PdfExtractionError("PDF text extraction failed") from exc

from __future__ import annotations

from fastapi import HTTPException

MAX_REPORT_BYTES = 10 * 1024 * 1024
PDF_MAGIC = b"%PDF"
_ALLOWED_TEXT_EXTENSIONS = {".txt"}


def assert_report_size(content_bytes: bytes) -> None:
    if len(content_bytes) > MAX_REPORT_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")


def classify_report_upload(filename: str, content_bytes: bytes) -> str:
    lowered = filename.lower()
    is_pdf = content_bytes.startswith(PDF_MAGIC)
    if lowered.endswith(".pdf"):
        if not is_pdf:
            raise HTTPException(status_code=400, detail="PDF upload must start with a PDF header")
        return "pdf"
    if any(lowered.endswith(extension) for extension in _ALLOWED_TEXT_EXTENSIONS):
        if is_pdf:
            raise HTTPException(status_code=400, detail="PDF upload must use a PDF extension")
        return "txt"
    raise HTTPException(status_code=400, detail="Unsupported report file type")

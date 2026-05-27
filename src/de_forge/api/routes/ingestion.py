"""Ingestion API routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from de_forge.api.routes.ingestion_boundary import assert_report_size, classify_report_upload
from de_forge.db.session import get_db
from de_forge.services.ingestion import IngestionService
from de_forge.services.pdf_text_extraction import PdfExtractionError, PdfTextExtractionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("")
async def ingest_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    """Ingest a threat report file.

    Args:
        file: Uploaded file (TXT or PDF).
        db: Database session.

    Returns:
        Dictionary with report_id and chunk_count.

    Raises:
        HTTPException: If file exceeds 10MB or contains invalid UTF-8.
    """
    filename = file.filename or "unknown.txt"

    content_bytes = await file.read()
    assert_report_size(content_bytes)

    source_type = classify_report_upload(filename, content_bytes)
    metadata: dict[str, object] | None = None
    if source_type == "pdf":
        try:
            extraction = PdfTextExtractionService().extract_text(content_bytes)
        except PdfExtractionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        source_type = "pdf"
        content_bytes = extraction.text.encode("utf-8")
        metadata = {"pdf_extraction": extraction.metadata}

    service = IngestionService(db)
    try:
        result = service.ingest(
            source_type=source_type,
            filename=filename,
            content_bytes=content_bytes,
            metadata=metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "report_id": result.report_id,
        "chunk_count": len(result.chunks),
    }

"""Ingestion API routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from de_forge.db.session import get_db
from de_forge.services.ingestion import IngestionService

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
    max_file_size = 10 * 1024 * 1024  # 10MB
    filename = file.filename or "unknown"
    if filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="PDF ingestion is not supported")

    content_bytes = await file.read()
    if len(content_bytes) > max_file_size:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
    source_type = "txt"

    service = IngestionService(db)
    try:
        result = service.ingest(
            source_type=source_type,
            filename=filename,
            content_bytes=content_bytes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "report_id": result.report_id,
        "chunk_count": len(result.chunks),
    }

"""Ingestion API routes."""

from fastapi import APIRouter, Depends, File, UploadFile
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
    """
    content_bytes = await file.read()
    filename = file.filename or "unknown"

    # Determine source type from filename extension
    source_type = "txt"
    if filename.lower().endswith(".pdf"):
        source_type = "pdf"

    service = IngestionService(db)
    result = service.ingest(
        source_type=source_type,
        filename=filename,
        content_bytes=content_bytes,
    )

    return {
        "report_id": result.report_id,
        "chunk_count": len(result.chunks),
    }

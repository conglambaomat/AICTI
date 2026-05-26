from collections.abc import Generator
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.routes.ingestion import router as ingestion_router
from de_forge.db.base import Base
from de_forge.db.session import get_db
from de_forge.models import Report, ReportChunk


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    test_app = FastAPI()
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.include_router(ingestion_router)
    return TestClient(test_app), db


def test_pdf_upload_ingests_text_report() -> None:
    client, db = _build_client()
    content = Path("tests/fixtures/text_report.pdf").read_bytes()

    response = client.post(
        "/ingest",
        files={"file": ("text_report.pdf", content, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report_id"]
    assert body["chunk_count"] >= 1

    report = db.get(Report, body["report_id"])
    assert report is not None
    assert report.source_type == "pdf"
    assert "PowerShell" in report.raw_text
    assert "pdf_extraction" in report.metadata_json

    chunks = db.query(ReportChunk).filter_by(report_id=report.id).all()
    assert chunks
    assert "PowerShell" in chunks[0].chunk_text

"""arq handler: ingest one document by id."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from atlas_common.config import get_settings
from atlas_common.logging import get_logger
from atlas_ingestion.pipeline import (
    EmptyExtractError,
    cleanup_document_artifacts,
    run_ingest_pipeline,
)
from atlas_persistence.postgres.engine import get_session_factory, init_engine
from atlas_persistence.postgres.repositories.documents import DocumentRepository
from atlas_persistence.postgres.repositories.jobs import JobRepository

logger = get_logger(__name__)


async def ingest_document(ctx: dict[str, Any], document_id: str) -> dict[str, Any]:
    """Worker entry for arq job ``ingest_document``."""
    settings = get_settings()
    init_engine(settings)
    doc_uuid = UUID(document_id)
    factory = get_session_factory(settings)

    async with factory() as session:
        docs = DocumentRepository(session)
        jobs = JobRepository(session)
        document = await docs.get(doc_uuid)
        if document is None:
            logger.error("ingest missing document_id=%s", document_id)
            return {"ok": False, "error": "document not found"}
        job = await jobs.latest_for_document(doc_uuid)
        await docs.mark_status(document, "processing")
        if job is not None and job.status in {"queued", "running"}:
            await jobs.mark_status(job, "running")
        await session.commit()

    try:
        async with factory() as session:
            result = await run_ingest_pipeline(session, doc_uuid, settings=settings)
            docs = DocumentRepository(session)
            jobs = JobRepository(session)
            document = await docs.get(doc_uuid)
            job = await jobs.latest_for_document(doc_uuid)
            if document is not None:
                await docs.mark_status(document, "ready", error_message=None)
            payload = {
                "document_id": str(result.document_id),
                "chunk_count": result.chunk_count,
            }
            if job is not None:
                await jobs.mark_status(job, "succeeded", result=payload, error_message=None)
            await session.commit()
            return payload
    except Exception as exc:
        logger.exception("ingest failed document_id=%s", document_id)
        async with factory() as session:
            await cleanup_document_artifacts(session, doc_uuid, settings=settings)
            docs = DocumentRepository(session)
            jobs = JobRepository(session)
            document = await docs.get(doc_uuid)
            job = await jobs.latest_for_document(doc_uuid)
            message = str(exc)
            if isinstance(exc, EmptyExtractError):
                message = str(exc)
            if document is not None:
                await docs.mark_status(document, "failed", error_message=message)
            if job is not None:
                await jobs.mark_status(job, "failed", error_message=message)
            await session.commit()
        return {"ok": False, "error": message}

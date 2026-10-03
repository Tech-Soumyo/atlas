"""Document upload use case for the API."""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from atlas_common.config import Settings
from atlas_ingestion.validate import PdfValidationError, validate_pdf_upload
from atlas_persistence.object_store.local import write_document_bytes
from atlas_persistence.postgres.models import Document, Job
from atlas_persistence.postgres.repositories.chunks import ChunkRepository
from atlas_persistence.postgres.repositories.documents import DocumentRepository
from atlas_persistence.postgres.repositories.jobs import JobRepository
from atlas_persistence.redis.queue import enqueue_ingest_document
from atlas_persistence.vector.store import delete_points_by_document_id
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def upload_document(
    *,
    session: AsyncSession,
    settings: Settings,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> tuple[int, dict[str, object]]:
    try:
        # Offload CPU + sync I/O (pymupdf, sha256) so the event loop stays free.
        validated = await asyncio.to_thread(
            validate_pdf_upload,
            filename=filename,
            content_type=content_type,
            data=data,
            settings=settings,
        )
    except PdfValidationError as exc:
        raise DocumentServiceError(400, str(exc)) from exc

    docs = DocumentRepository(session)
    jobs = JobRepository(session)
    existing = await docs.get_by_sha256(validated.sha256)
    if existing is not None:
        if existing.status == "ready":
            return 200, docs.to_dict(existing)
        if existing.status in {"queued", "processing"}:
            latest = await jobs.latest_for_document(existing.id)
            if latest is None:
                raise DocumentServiceError(500, "in flight document missing job")
            return 202, {
                "job_id": str(latest.id),
                "document_id": str(existing.id),
                "status": existing.status,
            }
        if existing.status == "failed":
            await ChunkRepository(session).delete_by_document_id(existing.id)
            # Sync vector client — must not block the event loop.
            await asyncio.to_thread(delete_points_by_document_id, existing.id, settings=settings)
            await docs.reset_for_requeue(existing)
            job = await jobs.add(
                Job(type="ingest_document", status="queued", document_id=existing.id)
            )
            # Service owns commit for enqueue ordering (AC-1: Document+Job before
            # enqueue). get_db_session may also commit on exit as a no-op safety net.
            await session.commit()
            try:
                await enqueue_ingest_document(existing.id, settings=settings, job_id=job.id)
            except Exception as exc:
                await jobs.mark_status(job, "failed", error_message=f"enqueue failed: {exc}")
                await docs.mark_status(existing, "failed", error_message=f"enqueue failed: {exc}")
                await session.commit()
            return 202, {
                "job_id": str(job.id),
                "document_id": str(existing.id),
                "status": "queued",
            }

    active = await docs.count_active()
    if active >= settings.atlas_max_documents:
        raise DocumentServiceError(
            400,
            f"document cap reached ({settings.atlas_max_documents})",
        )

    document_id = uuid4()
    # Sync filesystem write — offload to a worker thread.
    storage_path = await asyncio.to_thread(
        write_document_bytes, document_id, data, settings=settings
    )
    document = await docs.add(
        Document(
            id=document_id,
            filename=filename,
            content_type=content_type or "application/pdf",
            byte_size=len(data),
            page_count=validated.page_count,
            sha256=validated.sha256,
            storage_path=str(storage_path),
            status="queued",
        )
    )
    job = await jobs.add(Job(type="ingest_document", status="queued", document_id=document.id))
    # Service owns commit for enqueue ordering (AC-1: Document+Job before
    # enqueue). get_db_session may also commit on exit as a no-op safety net.
    await session.commit()
    try:
        await enqueue_ingest_document(document.id, settings=settings, job_id=job.id)
    except Exception as exc:
        await jobs.mark_status(job, "failed", error_message=f"enqueue failed: {exc}")
        await docs.mark_status(document, "failed", error_message=f"enqueue failed: {exc}")
        await session.commit()
    return 202, {
        "job_id": str(job.id),
        "document_id": str(document.id),
        "status": "queued",
    }


async def get_document(session: AsyncSession, document_id: UUID) -> dict[str, object] | None:
    document = await DocumentRepository(session).get(document_id)
    if document is None:
        return None
    return DocumentRepository(session).to_dict(document)


async def list_documents(
    session: AsyncSession, *, limit: int, offset: int
) -> tuple[list[dict[str, object]], int]:
    rows, total = await DocumentRepository(session).list_documents(limit=limit, offset=offset)
    repo = DocumentRepository(session)
    return [repo.to_dict(row) for row in rows], total

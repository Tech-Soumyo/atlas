"""Stale processing / running job reconcile on worker startup."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from atlas_common.config import Settings, get_settings
from atlas_common.logging import get_logger
from atlas_ingestion.pipeline import cleanup_document_artifacts
from atlas_persistence.postgres.engine import get_session_factory, init_engine
from atlas_persistence.postgres.repositories.documents import DocumentRepository
from atlas_persistence.postgres.repositories.jobs import JobRepository

logger = get_logger(__name__)


async def reconcile_stale_jobs(settings: Settings | None = None) -> int:
    """Fail Document/Job pairs stuck past ATLAS_INGEST_STALE_SECONDS."""
    cfg = settings or get_settings()
    init_engine(cfg)
    cutoff = datetime.now(UTC) - timedelta(seconds=cfg.atlas_ingest_stale_seconds)
    factory = get_session_factory(cfg)
    count = 0
    async with factory() as session:
        docs = DocumentRepository(session)
        jobs = JobRepository(session)
        stale_docs = await docs.list_stale_processing(cutoff)
        stale_jobs = await jobs.list_stale_running(cutoff)
        seen_doc_ids = set()
        for document in stale_docs:
            await cleanup_document_artifacts(session, document.id, settings=cfg)
            await docs.mark_status(
                document,
                "failed",
                error_message="stale processing reconciled on worker startup",
            )
            job = await jobs.latest_for_document(document.id)
            if job is not None and job.status in {"queued", "running"}:
                await jobs.mark_status(
                    job,
                    "failed",
                    error_message="stale processing reconciled on worker startup",
                )
            seen_doc_ids.add(document.id)
            count += 1
        for job in stale_jobs:
            if job.document_id in seen_doc_ids:
                continue
            await cleanup_document_artifacts(session, job.document_id, settings=cfg)
            stale_document = await docs.get(job.document_id)
            if stale_document is not None and stale_document.status in {
                "queued",
                "processing",
            }:
                await docs.mark_status(
                    stale_document,
                    "failed",
                    error_message="stale running job reconciled on worker startup",
                )
            await jobs.mark_status(
                job,
                "failed",
                error_message="stale running job reconciled on worker startup",
            )
            count += 1
        await session.commit()
    if count:
        logger.warning("reconciled stale ingest items count=%s", count)
    return count

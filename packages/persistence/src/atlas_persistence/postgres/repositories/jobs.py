"""Job repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_persistence.postgres.models import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, job_id: UUID) -> Job | None:
        return await self._session.get(Job, job_id)

    async def add(self, job: Job) -> Job:
        self._session.add(job)
        await self._session.flush()
        return job

    async def latest_for_document(self, document_id: UUID) -> Job | None:
        result = await self._session.execute(
            select(Job)
            .where(Job.document_id == document_id)
            .order_by(Job.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_status(
        self,
        job: Job,
        status: str,
        *,
        error_message: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> Job:
        job.status = status
        if status == "succeeded":
            job.error_message = None
        elif error_message is not None or status == "failed":
            job.error_message = error_message
        if result is not None:
            job.result = result
        job.updated_at = datetime.now(UTC)
        await self._session.flush()
        return job

    async def list_stale_running(self, older_than: datetime) -> list[Job]:
        result = await self._session.execute(
            select(Job).where(
                Job.status == "running",
                Job.updated_at < older_than,
            )
        )
        return list(result.scalars().all())

    def to_dict(self, job: Job) -> dict[str, Any]:
        return {
            "id": str(job.id),
            "type": job.type,
            "status": job.status,
            "document_id": str(job.document_id),
            "error_message": job.error_message,
            "result": job.result or {},
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }

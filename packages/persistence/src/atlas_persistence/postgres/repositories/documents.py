"""Document repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_persistence.postgres.models import Document

ACTIVE_STATUSES = ("queued", "processing", "ready")


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, document_id: UUID) -> Document | None:
        return await self._session.get(Document, document_id)

    async def get_by_sha256(self, sha256: str) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.sha256 == sha256)
        )
        return result.scalar_one_or_none()

    async def count_active(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Document).where(Document.status.in_(ACTIVE_STATUSES))
        )
        return int(result.scalar_one())

    async def list_documents(
        self, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[Document], int]:
        total_result = await self._session.execute(select(func.count()).select_from(Document))
        total = int(total_result.scalar_one())
        result = await self._session.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def add(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_ready_ids(self, document_ids: list[UUID]) -> list[UUID]:
        if not document_ids:
            return []
        result = await self._session.execute(
            select(Document.id).where(
                Document.id.in_(document_ids),
                Document.status == "ready",
            )
        )
        return list(result.scalars().all())

    async def mark_status(
        self,
        document: Document,
        status: str,
        *,
        error_message: str | None = None,
    ) -> Document:
        document.status = status
        document.error_message = error_message
        document.updated_at = datetime.now(UTC)
        await self._session.flush()
        return document

    async def reset_for_requeue(self, document: Document) -> Document:
        document.status = "queued"
        document.error_message = None
        document.updated_at = datetime.now(UTC)
        await self._session.flush()
        return document

    async def list_stale_processing(self, older_than: datetime) -> list[Document]:
        result = await self._session.execute(
            select(Document).where(
                Document.status == "processing",
                Document.updated_at < older_than,
            )
        )
        return list(result.scalars().all())

    def to_dict(self, document: Document) -> dict[str, Any]:
        return {
            "id": str(document.id),
            "filename": document.filename,
            "content_type": document.content_type,
            "byte_size": document.byte_size,
            "page_count": document.page_count,
            "sha256": document.sha256,
            "storage_path": document.storage_path,
            "status": document.status,
            "error_message": document.error_message,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
        }

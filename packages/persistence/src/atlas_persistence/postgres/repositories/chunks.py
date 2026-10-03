"""Chunk repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_persistence.postgres.models import Chunk


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def delete_by_document_id(self, document_id: UUID) -> int:
        result = await self._session.execute(
            delete(Chunk).where(Chunk.document_id == document_id)
        )
        await self._session.flush()
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0)

    async def add_many(self, chunks: list[Chunk]) -> list[Chunk]:
        self._session.add_all(chunks)
        await self._session.flush()
        return chunks

    async def get_by_ids(self, chunk_ids: list[UUID]) -> list[Chunk]:
        if not chunk_ids:
            return []
        result = await self._session.execute(select(Chunk).where(Chunk.id.in_(chunk_ids)))
        by_id = {row.id: row for row in result.scalars().all()}
        return [by_id[cid] for cid in chunk_ids if cid in by_id]

    def to_dict(self, chunk: Chunk) -> dict[str, Any]:
        return {
            "id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "ordinal": chunk.ordinal,
            "text": chunk.text,
            "token_count": chunk.token_count,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "embedding_model": chunk.embedding_model,
        }

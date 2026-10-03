"""Ask repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from atlas_persistence.postgres.models import Ask, AskDocument


class AskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, ask_id: UUID) -> Ask | None:
        return await self._session.get(Ask, ask_id)

    async def create(
        self,
        *,
        question: str,
        answer: str,
        abstained: bool,
        citations: list[dict[str, Any]],
        retrieved_chunk_ids: list[UUID],
        model_name: str,
        latency_ms: int,
        document_ids: list[UUID],
    ) -> Ask:
        ask = Ask(
            question=question,
            answer=answer,
            abstained=abstained,
            citations=citations,
            retrieved_chunk_ids=retrieved_chunk_ids,
            model_name=model_name,
            latency_ms=latency_ms,
        )
        self._session.add(ask)
        await self._session.flush()
        for document_id in document_ids:
            self._session.add(AskDocument(ask_id=ask.id, document_id=document_id))
        await self._session.flush()
        return ask

    def to_dict(self, ask: Ask) -> dict[str, Any]:
        return {
            "id": str(ask.id),
            "question": ask.question,
            "answer": ask.answer,
            "abstained": ask.abstained,
            "citations": ask.citations or [],
            "retrieved_chunk_ids": [str(cid) for cid in (ask.retrieved_chunk_ids or [])],
            "model_name": ask.model_name,
            "latency_ms": ask.latency_ms,
            "created_at": ask.created_at.isoformat() if ask.created_at else None,
            "document_ids": [str(link.document_id) for link in ask.ask_documents],
        }

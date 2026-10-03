"""Ask use case façade with Ask persistence."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from atlas_common.config import Settings, get_settings
from atlas_persistence.postgres.engine import get_session_factory
from atlas_persistence.postgres.models import Ask
from atlas_persistence.postgres.repositories.asks import AskRepository
from sqlalchemy.orm import selectinload

from atlas_orchestration.graphs.ask_graph import get_ask_graph


@dataclass(frozen=True)
class AskResult:
    ask_id: UUID
    answer: str
    abstained: bool
    citations: list[dict[str, Any]]
    retrieved_chunk_ids: list[UUID]
    model_name: str
    latency_ms: int


async def run_ask(
    *,
    question: str,
    document_ids: list[UUID],
    top_k: int | None = None,
    temperature: float | None = None,
    model: str | None = None,
    settings: Settings | None = None,
) -> AskResult:
    cfg = settings or get_settings()
    started = time.perf_counter()
    graph = get_ask_graph()
    final_state = await graph.ainvoke(
        {
            "question": question,
            "document_ids": document_ids,
            "top_k": top_k,
            "temperature": temperature,
            "model": model,
        }
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    citations = list(final_state.get("citations") or [])
    retrieved = list(final_state.get("retrieved_chunk_ids") or [])
    answer = str(final_state.get("answer") or "")
    abstained = bool(final_state.get("abstained"))
    model_name = str(final_state.get("model_name") or cfg.llm_model)

    factory = get_session_factory(cfg)
    async with factory() as session:
        ask = await AskRepository(session).create(
            question=question,
            answer=answer,
            abstained=abstained,
            citations=citations,
            retrieved_chunk_ids=retrieved,
            model_name=model_name,
            latency_ms=latency_ms,
            document_ids=document_ids,
        )
        await session.commit()
        ask_id = ask.id

    return AskResult(
        ask_id=ask_id,
        answer=answer,
        abstained=abstained,
        citations=citations,
        retrieved_chunk_ids=retrieved,
        model_name=model_name,
        latency_ms=latency_ms,
    )


async def get_ask_record(ask_id: UUID, *, settings: Settings | None = None) -> dict[str, Any] | None:
    cfg = settings or get_settings()
    factory = get_session_factory(cfg)
    async with factory() as session:
        ask = await session.get(
            Ask,
            ask_id,
            options=(selectinload(Ask.ask_documents),),
        )
        if ask is None:
            return None
        return AskRepository(session).to_dict(ask)

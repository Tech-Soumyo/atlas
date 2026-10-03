"""Retrieve node for the linear ask graph."""

from __future__ import annotations

from typing import Any

from atlas_common.config import get_settings
from atlas_persistence.postgres.engine import get_session_factory
from atlas_persistence.postgres.repositories.chunks import ChunkRepository
from atlas_retrieval.service import retrieve_dense

from atlas_orchestration.state import AskState


async def retrieve_node(state: AskState) -> dict[str, Any]:
    settings = get_settings()
    document_ids = list(state.get("document_ids") or [])
    hits = retrieve_dense(
        state["question"],
        document_ids,
        top_k=state.get("top_k"),
        settings=settings,
    )
    chunk_ids = [hit.chunk_id for hit in hits]
    factory = get_session_factory(settings)
    async with factory() as session:
        chunks = await ChunkRepository(session).get_by_ids(chunk_ids)
    by_id = {chunk.id: chunk for chunk in chunks}
    contexts: list[str] = []
    citations: list[dict[str, Any]] = []
    for hit in hits:
        chunk = by_id.get(hit.chunk_id)
        if chunk is None:
            continue
        snippet = chunk.text[:500]
        contexts.append(chunk.text)
        citations.append(
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "snippet": snippet,
                "score": hit.score,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
            }
        )
    best = hits[0].score if hits else None
    return {
        "hits": [
            {
                "chunk_id": str(hit.chunk_id),
                "document_id": str(hit.document_id),
                "score": hit.score,
                "ordinal": hit.ordinal,
            }
            for hit in hits
        ],
        "contexts": contexts,
        "citations": citations,
        "retrieved_chunk_ids": chunk_ids,
        "best_similarity": best,
    }

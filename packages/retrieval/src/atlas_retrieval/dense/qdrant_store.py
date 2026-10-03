"""Dense ANN search via the persistence vector store façade."""

from __future__ import annotations

from uuid import UUID

from atlas_common.config import Settings, get_settings
from atlas_persistence.vector.store import search_by_document_ids as store_search

from atlas_retrieval.models import RetrievedHit


def search_by_document_ids(
    query_vector: list[float],
    document_ids: list[UUID],
    *,
    top_k: int,
    settings: Settings | None = None,
) -> list[RetrievedHit]:
    if not document_ids:
        return []
    cfg = settings or get_settings()
    rows = store_search(
        query_vector,
        document_ids,
        top_k=top_k,
        settings=cfg,
    )
    return [
        RetrievedHit(
            chunk_id=UUID(str(row["chunk_id"])),
            document_id=UUID(str(row["document_id"])),
            score=float(row["score"]),
            ordinal=int(row["ordinal"]),
        )
        for row in rows
    ]

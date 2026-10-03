"""Data-plane vector store façade: Upstash Vector (cloud) or Qdrant (local)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from atlas_common.config import Settings, get_settings


def ensure_chunks_collection(settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    if cfg.is_upstash_plane:
        from atlas_persistence.vector.upstash_client import (
            ensure_chunks_collection as ensure_upstash,
        )

        ensure_upstash(cfg)
        return
    from atlas_persistence.qdrant.client import (
        ensure_chunks_collection as ensure_qdrant,
    )

    ensure_qdrant(cfg)


def delete_points_by_document_id(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
) -> None:
    cfg = settings or get_settings()
    if cfg.is_upstash_plane:
        from atlas_persistence.vector.upstash_client import (
            delete_points_by_document_id as delete_upstash,
        )

        delete_upstash(document_id, settings=cfg)
        return
    from atlas_persistence.qdrant.client import (
        delete_points_by_document_id as delete_qdrant,
    )

    delete_qdrant(document_id, settings=cfg)


def upsert_chunk_points(
    points: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
) -> None:
    cfg = settings or get_settings()
    if cfg.is_upstash_plane:
        from atlas_persistence.vector.upstash_client import (
            upsert_chunk_points as upsert_upstash,
        )

        upsert_upstash(points, settings=cfg)
        return
    from atlas_persistence.qdrant.client import (
        upsert_chunk_points as upsert_qdrant,
    )

    upsert_qdrant(points, settings=cfg)


def search_by_document_ids(
    query_vector: list[float],
    document_ids: list[UUID],
    *,
    top_k: int,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    """Route dense search; returns chunk_id/document_id/score/ordinal dicts."""
    cfg = settings or get_settings()
    if cfg.is_upstash_plane:
        from atlas_persistence.vector.upstash_client import (
            search_by_document_ids as search_upstash,
        )

        return search_upstash(
            query_vector,
            document_ids,
            top_k=top_k,
            settings=cfg,
        )
    return _search_qdrant(
        query_vector,
        document_ids,
        top_k=top_k,
        settings=cfg,
    )


def _search_qdrant(
    query_vector: list[float],
    document_ids: list[UUID],
    *,
    top_k: int,
    settings: Settings,
) -> list[dict[str, Any]]:
    from qdrant_client.http import models as qm

    from atlas_persistence.qdrant.client import get_qdrant_client

    if not document_ids:
        return []
    client = get_qdrant_client(settings)
    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=qm.Filter(
            must=[
                qm.FieldCondition(
                    key="document_id",
                    match=qm.MatchAny(any=[str(doc_id) for doc_id in document_ids]),
                )
            ]
        ),
    )
    hits: list[dict[str, Any]] = []
    for point in response.points:
        payload = point.payload or {}
        hits.append(
            {
                "chunk_id": str(payload.get("chunk_id", point.id)),
                "document_id": str(payload["document_id"]),
                "score": float(point.score or 0.0),
                "ordinal": int(payload.get("ordinal", 0)),
            }
        )
    return hits

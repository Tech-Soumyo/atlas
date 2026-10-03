"""Qdrant collection helpers for atlas_chunks (Cosine)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from atlas_common.config import Settings, get_settings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm


def get_qdrant_client(settings: Settings | None = None) -> QdrantClient:
    cfg = settings or get_settings()
    return QdrantClient(
        url=cfg.qdrant_url,
        api_key=cfg.qdrant_api_key,
        prefer_grpc=False,
        check_compatibility=False,
    )


def ensure_chunks_collection(settings: Settings | None = None) -> None:
    """Create Cosine collection ``atlas_chunks`` if missing."""
    cfg = settings or get_settings()
    client = get_qdrant_client(cfg)
    name = cfg.qdrant_collection
    if client.collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(
            size=cfg.embedding_dims,
            distance=qm.Distance.COSINE,
        ),
    )


def delete_points_by_document_id(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
) -> None:
    cfg = settings or get_settings()
    client = get_qdrant_client(cfg)
    client.delete(
        collection_name=cfg.qdrant_collection,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="document_id",
                        match=qm.MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
    )


def upsert_chunk_points(
    points: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
) -> None:
    """Upsert points. Each item: chunk_id, document_id, ordinal, vector."""
    if not points:
        return
    cfg = settings or get_settings()
    client = get_qdrant_client(cfg)
    client.upsert(
        collection_name=cfg.qdrant_collection,
        points=[
            qm.PointStruct(
                id=str(item["chunk_id"]),
                vector=list(item["vector"]),
                payload={
                    "document_id": str(item["document_id"]),
                    "chunk_id": str(item["chunk_id"]),
                    "ordinal": int(item["ordinal"]),
                },
            )
            for item in points
        ],
    )

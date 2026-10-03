"""Dense ANN search against Qdrant."""

from __future__ import annotations

from uuid import UUID

from atlas_common.config import Settings, get_settings
from atlas_persistence.qdrant.client import get_qdrant_client
from qdrant_client.http import models as qm

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
    client = get_qdrant_client(cfg)
    response = client.query_points(
        collection_name=cfg.qdrant_collection,
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
    hits: list[RetrievedHit] = []
    for point in response.points:
        payload = point.payload or {}
        hits.append(
            RetrievedHit(
                chunk_id=UUID(str(payload.get("chunk_id", point.id))),
                document_id=UUID(str(payload["document_id"])),
                score=float(point.score or 0.0),
                ordinal=int(payload.get("ordinal", 0)),
            )
        )
    return hits

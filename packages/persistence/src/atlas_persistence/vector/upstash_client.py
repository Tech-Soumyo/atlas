"""Upstash Vector adapter for atlas chunk embeddings (COSINE, 384-d)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from atlas_common.config import Settings, get_settings
from upstash_vector import Index

_index: Index | None = None
_index_key: tuple[str, str] | None = None


def _quote_filter_value(value: str) -> str:
    """Escape a string for Upstash SQL-like metadata filters."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def document_id_equals_filter(document_id: UUID | str) -> str:
    return f"document_id = {_quote_filter_value(str(document_id))}"


def document_ids_in_filter(document_ids: list[UUID | str]) -> str:
    joined = ", ".join(_quote_filter_value(str(doc_id)) for doc_id in document_ids)
    return f"document_id IN ({joined})"


def get_upstash_index(settings: Settings | None = None) -> Index:
    """Return a process-wide Upstash Vector Index (URL/token from settings)."""
    global _index, _index_key
    cfg = settings or get_settings()
    url = (cfg.upstash_vector_rest_url or "").strip()
    token = (cfg.upstash_vector_rest_token or "").strip()
    if not url or not token:
        msg = (
            "Upstash Vector requires UPSTASH_VECTOR_REST_URL and "
            "UPSTASH_VECTOR_REST_TOKEN when ATLAS_DATA_PLANE=upstash"
        )
        raise RuntimeError(msg)
    key = (url, token)
    if _index is not None and _index_key == key:
        return _index
    _index = Index(url=url, token=token)
    _index_key = key
    return _index


def ensure_chunks_collection(settings: Settings | None = None) -> None:
    """Validate the remote index is 384-d COSINE (indexes are created in console)."""
    cfg = settings or get_settings()
    index = get_upstash_index(cfg)
    info = index.info()
    expected_dims = int(cfg.embedding_dims)
    actual_dims = int(info.dimension)
    similarity = str(info.similarity_function or "").upper()
    if actual_dims != expected_dims:
        msg = (
            f"Upstash Vector dimension mismatch: index={actual_dims}, "
            f"expected={expected_dims}"
        )
        raise RuntimeError(msg)
    if similarity != "COSINE":
        msg = (
            f"Upstash Vector similarity mismatch: index={info.similarity_function}, "
            "expected=COSINE"
        )
        raise RuntimeError(msg)


def delete_points_by_document_id(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
) -> None:
    cfg = settings or get_settings()
    index = get_upstash_index(cfg)
    index.delete(filter=document_id_equals_filter(document_id))


def upsert_chunk_points(
    points: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
) -> None:
    """Upsert points. Each item: chunk_id, document_id, ordinal, vector."""
    if not points:
        return
    cfg = settings or get_settings()
    index = get_upstash_index(cfg)
    vectors = [
        {
            "id": str(item["chunk_id"]),
            "vector": list(item["vector"]),
            "metadata": {
                "document_id": str(item["document_id"]),
                "chunk_id": str(item["chunk_id"]),
                "ordinal": int(item["ordinal"]),
            },
        }
        for item in points
    ]
    index.upsert(vectors=vectors)


def search_by_document_ids(
    query_vector: list[float],
    document_ids: list[UUID],
    *,
    top_k: int,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    """Dense ANN with ``document_id IN (...)`` metadata filter.

    Returns dicts: chunk_id, document_id, score, ordinal (string UUIDs).
    """
    if not document_ids:
        return []
    cfg = settings or get_settings()
    index = get_upstash_index(cfg)
    results = index.query(
        vector=list(query_vector),
        top_k=top_k,
        include_metadata=True,
        include_vectors=False,
        filter=document_ids_in_filter(list(document_ids)),
    )
    hits: list[dict[str, Any]] = []
    for result in results:
        metadata = result.metadata or {}
        hits.append(
            {
                "chunk_id": str(metadata.get("chunk_id", result.id)),
                "document_id": str(metadata["document_id"]),
                "score": float(result.score or 0.0),
                "ordinal": int(metadata.get("ordinal", 0)),
            }
        )
    return hits

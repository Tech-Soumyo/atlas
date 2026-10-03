"""Public retrieval façade for the ask graph."""

from __future__ import annotations

from uuid import UUID

from atlas_common.config import Settings, get_settings, get_yaml_config

from atlas_retrieval.dense.embedder import Embedder
from atlas_retrieval.dense.qdrant_store import search_by_document_ids
from atlas_retrieval.models import RetrievedHit

__all__ = ["RetrievedHit", "retrieve_dense"]


def retrieve_dense(
    question: str,
    document_ids: list[UUID],
    *,
    top_k: int | None = None,
    settings: Settings | None = None,
    embedder: Embedder | None = None,
) -> list[RetrievedHit]:
    cfg = settings or get_settings()
    retrieval_cfg = get_yaml_config("retrieval", settings=cfg)
    resolved_top_k = top_k if top_k is not None else int(retrieval_cfg.get("top_k", 8))
    resolved_top_k = max(1, min(20, resolved_top_k))
    model = embedder or Embedder(settings=cfg)
    vector = model.embed_query(question)
    return search_by_document_ids(
        vector,
        document_ids,
        top_k=resolved_top_k,
        settings=cfg,
    )

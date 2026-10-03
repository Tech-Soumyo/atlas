"""Ask graph state."""

from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID


class AskState(TypedDict, total=False):
    question: str
    document_ids: list[UUID]
    top_k: int | None
    temperature: float | None
    model: str | None
    hits: list[dict[str, Any]]
    contexts: list[str]
    best_similarity: float | None
    answer: str
    abstained: bool
    citations: list[dict[str, Any]]
    retrieved_chunk_ids: list[UUID]
    model_name: str

"""Ask request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str
    # Length caps are enforced in the route as HTTP 400 (AC-6), not Pydantic 422.
    document_ids: list[str]
    top_k: int | None = Field(default=None, ge=1, le=20)
    temperature: float | None = None
    model: str | None = None


class CitationOut(BaseModel):
    chunk_id: str
    document_id: str
    snippet: str
    score: float
    page_start: int | None = None
    page_end: int | None = None


class AskResponse(BaseModel):
    ask_id: str
    answer: str
    abstained: bool
    citations: list[CitationOut]


class AskRecordOut(BaseModel):
    id: str
    question: str
    answer: str
    abstained: bool
    citations: list[dict[str, Any]]
    retrieved_chunk_ids: list[str]
    model_name: str
    latency_ms: int
    created_at: str | None = None
    document_ids: list[str] = Field(default_factory=list)

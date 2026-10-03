"""Retrieval DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetrievedHit:
    chunk_id: UUID
    document_id: UUID
    score: float
    ordinal: int

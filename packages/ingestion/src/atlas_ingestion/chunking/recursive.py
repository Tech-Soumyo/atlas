"""Recursive character splitter for M1 naive ingest."""

from __future__ import annotations

from dataclasses import dataclass

from atlas_common.config import get_settings, get_yaml_config
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(frozen=True)
class TextChunk:
    ordinal: int
    text: str
    token_count: int
    page_start: int | None
    page_end: int | None


def split_text(text: str, *, page_start: int | None = None, page_end: int | None = None) -> list[TextChunk]:
    settings = get_settings()
    cfg = get_yaml_config("chunking", settings=settings)
    chunk_size = int(cfg.get("chunk_size", 1000))
    chunk_overlap = int(cfg.get("chunk_overlap", 200))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    parts = splitter.split_text(text)
    return [
        TextChunk(
            ordinal=index,
            text=part,
            token_count=len(part.split()),
            page_start=page_start,
            page_end=page_end,
        )
        for index, part in enumerate(parts)
        if part.strip()
    ]

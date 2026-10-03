"""Worker ingest pipeline: parse, split, embed, persist, upsert."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from atlas_common.config import Settings, get_settings
from atlas_common.logging import get_logger
from atlas_persistence.object_store.local import document_storage_path
from atlas_persistence.postgres.models import Chunk
from atlas_persistence.postgres.repositories.chunks import ChunkRepository
from atlas_persistence.qdrant.client import (
    delete_points_by_document_id,
    ensure_chunks_collection,
    upsert_chunk_points,
)
from atlas_retrieval.dense.embedder import Embedder
from sqlalchemy.ext.asyncio import AsyncSession

from atlas_ingestion.chunking.recursive import split_text
from atlas_ingestion.parsers.pdf import extract_pdf_pages, join_extractable_text

logger = get_logger(__name__)


@dataclass(frozen=True)
class IngestResult:
    document_id: UUID
    chunk_count: int


class EmptyExtractError(RuntimeError):
    """PDF had no extractable text."""


async def cleanup_document_artifacts(
    session: AsyncSession,
    document_id: UUID,
    *,
    settings: Settings | None = None,
) -> None:
    """Delete Postgres chunks and Qdrant points for a document."""
    chunks = ChunkRepository(session)
    await chunks.delete_by_document_id(document_id)
    delete_points_by_document_id(document_id, settings=settings)


async def run_ingest_pipeline(
    session: AsyncSession,
    document_id: UUID,
    *,
    settings: Settings | None = None,
    embedder: Embedder | None = None,
) -> IngestResult:
    """Full worker ingest for one document id."""
    cfg = settings or get_settings()
    path = document_storage_path(document_id, settings=cfg)
    pages = extract_pdf_pages(str(path))
    text = join_extractable_text(pages)
    if not text:
        await cleanup_document_artifacts(session, document_id, settings=cfg)
        raise EmptyExtractError("no extractable text in PDF")

    page_start = pages[0].page_number if pages else None
    page_end = pages[-1].page_number if pages else None
    text_chunks = split_text(text, page_start=page_start, page_end=page_end)
    if not text_chunks:
        await cleanup_document_artifacts(session, document_id, settings=cfg)
        raise EmptyExtractError("no chunks produced from PDF text")

    await cleanup_document_artifacts(session, document_id, settings=cfg)
    ensure_chunks_collection(cfg)
    model = embedder or Embedder(settings=cfg)
    vectors = model.embed_texts([chunk.text for chunk in text_chunks])

    rows: list[Chunk] = []
    points: list[dict[str, object]] = []
    for chunk, _vector in zip(text_chunks, vectors, strict=True):
        row = Chunk(
            document_id=document_id,
            ordinal=chunk.ordinal,
            text=chunk.text,
            token_count=chunk.token_count,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            embedding_model=cfg.embedding_model,
        )
        rows.append(row)
    chunk_repo = ChunkRepository(session)
    await chunk_repo.add_many(rows)

    for row, vector in zip(rows, vectors, strict=True):
        points.append(
            {
                "chunk_id": row.id,
                "document_id": document_id,
                "ordinal": row.ordinal,
                "vector": vector,
            }
        )
    upsert_chunk_points(points, settings=cfg)
    logger.info(
        "ingest complete document_id=%s chunk_count=%s",
        document_id,
        len(rows),
    )
    return IngestResult(document_id=document_id, chunk_count=len(rows))

"""arq enqueue helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from atlas_common.config import Settings, get_settings

_pool: ArqRedis | None = None


async def get_arq_pool(settings: Settings | None = None) -> ArqRedis:
    global _pool
    if _pool is not None:
        return _pool
    cfg = settings or get_settings()
    _pool = await create_pool(RedisSettings.from_dsn(cfg.redis_url))
    return _pool


async def close_arq_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def enqueue_ingest_document(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
    job_id: UUID | str | None = None,
) -> Any:
    """Enqueue ``ingest_document`` with payload ``{document_id}`` only."""
    pool = await get_arq_pool(settings)
    kwargs: dict[str, Any] = {}
    if job_id is not None:
        kwargs["_job_id"] = str(job_id)
    return await pool.enqueue_job("ingest_document", str(document_id), **kwargs)

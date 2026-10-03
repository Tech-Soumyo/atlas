"""Job enqueue helpers — arq (local) or QStash (upstash).

Upstash mode must not open a TCP Redis connection for jobs. Local mode keeps
the existing arq pool against ``REDIS_URL``.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from atlas_common.config import Settings, get_settings
from atlas_common.logging import get_logger

logger = get_logger(__name__)

_pool: Any | None = None
_qstash: Any | None = None

INGEST_PATH = "/internal/jobs/ingest"
INGEST_FAILED_PATH = "/internal/jobs/ingest-failed"


def _worker_base_url(settings: Settings) -> str:
    base = (settings.atlas_worker_public_url or "").rstrip("/")
    if not base:
        msg = (
            "ATLAS_WORKER_PUBLIC_URL is required when ATLAS_DATA_PLANE=upstash "
            "(public HTTPS base QStash can reach, e.g. a Cloudflare Tunnel)."
        )
        raise RuntimeError(msg)
    return base


def _deduplication_id(document_id: str, job_id: str | None) -> str:
    """Idempotent publish key.

    Prefer ``document_id`` (acceptance). When ``job_id`` is present, append it so
    a failed-document requeue (new job row) is not dropped by the 90-day QStash
    dedupe window.
    """
    if job_id:
        return f"ingest:{document_id}:{job_id}"
    return f"ingest:{document_id}"


async def get_arq_pool(settings: Settings | None = None) -> Any:
    """Return a shared arq Redis pool (local data plane only)."""
    global _pool
    cfg = settings or get_settings()
    if cfg.is_upstash_plane:
        msg = (
            "arq pool is unavailable when ATLAS_DATA_PLANE=upstash; "
            "jobs are published via QStash (no TCP Redis queue)."
        )
        raise RuntimeError(msg)
    if _pool is not None:
        return _pool
    from arq import create_pool
    from arq.connections import RedisSettings

    _pool = await create_pool(RedisSettings.from_dsn(cfg.redis_url))
    return _pool


async def close_arq_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def get_qstash_client(settings: Settings | None = None) -> Any:
    """Return a shared ``AsyncQStash`` client (upstash data plane)."""
    global _qstash
    if _qstash is not None:
        return _qstash
    cfg = settings or get_settings()
    if not cfg.qstash_token:
        msg = "QSTASH_TOKEN is required when ATLAS_DATA_PLANE=upstash"
        raise RuntimeError(msg)
    from qstash import AsyncQStash

    kwargs: dict[str, Any] = {"token": cfg.qstash_token}
    if cfg.qstash_url:
        kwargs["base_url"] = cfg.qstash_url
    _qstash = AsyncQStash(**kwargs)
    return _qstash


async def close_qstash_client() -> None:
    """Drop the cached QStash client (HTTP client has no explicit close)."""
    global _qstash
    _qstash = None


async def _enqueue_via_qstash(
    document_id: str,
    *,
    settings: Settings,
    job_id: str | None,
) -> Any:
    client = get_qstash_client(settings)
    base = _worker_base_url(settings)
    url = f"{base}{INGEST_PATH}"
    failure_callback = f"{base}{INGEST_FAILED_PATH}"
    body: dict[str, str] = {"document_id": document_id}
    if job_id is not None:
        body["job_id"] = job_id
    result = await client.message.publish_json(
        url=url,
        body=body,
        retries=settings.worker_max_retries,
        failure_callback=failure_callback,
        deduplication_id=_deduplication_id(document_id, job_id),
        label="atlas-ingest-document",
    )
    logger.info(
        "qstash published ingest document_id=%s job_id=%s message_id=%s deduplicated=%s",
        document_id,
        job_id,
        getattr(result, "message_id", None),
        getattr(result, "deduplicated", None),
    )
    return result


async def _enqueue_via_arq(
    document_id: str,
    *,
    settings: Settings,
    job_id: str | None,
) -> Any:
    pool = await get_arq_pool(settings)
    kwargs: dict[str, Any] = {}
    if job_id is not None:
        kwargs["_job_id"] = job_id
    return await pool.enqueue_job("ingest_document", document_id, **kwargs)


async def enqueue_ingest_document(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
    job_id: UUID | str | None = None,
) -> Any:
    """Enqueue ``ingest_document`` with payload ``document_id`` (+ optional ``job_id``).

    * ``ATLAS_DATA_PLANE=upstash`` — QStash ``publish_json`` to the worker HTTP
      ingest endpoint (retries + failure callback). No TCP Redis.
    * ``ATLAS_DATA_PLANE=local`` — arq job on ``REDIS_URL``.
    """
    cfg = settings or get_settings()
    doc = str(document_id)
    jid = str(job_id) if job_id is not None else None
    if cfg.is_upstash_plane:
        return await _enqueue_via_qstash(doc, settings=cfg, job_id=jid)
    return await _enqueue_via_arq(doc, settings=cfg, job_id=jid)

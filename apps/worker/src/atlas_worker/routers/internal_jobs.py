"""Internal job endpoints invoked by QStash (signature required)."""

from __future__ import annotations

import base64
import json
from typing import Any
from uuid import UUID

from atlas_common.config import get_settings
from atlas_common.logging import get_logger
from atlas_persistence.postgres.engine import get_session_factory, init_engine
from atlas_persistence.postgres.repositories.documents import DocumentRepository
from atlas_persistence.postgres.repositories.jobs import JobRepository
from fastapi import APIRouter, Request, Response, status

from atlas_worker.handlers.ingest_document import ingest_document
from atlas_worker.qstash_verify import QStashSignatureError, verify_qstash_request

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/jobs", tags=["internal-jobs"])


def _signature_from_headers(request: Request) -> str | None:
    return request.headers.get("upstash-signature") or request.headers.get(
        "Upstash-Signature"
    )


async def _read_and_verify(request: Request) -> str:
    raw = await request.body()
    body = raw.decode("utf-8")
    settings = get_settings()
    verify_url = None
    if settings.atlas_worker_public_url:
        verify_url = settings.atlas_worker_public_url.rstrip("/") + str(request.url.path)
    try:
        verify_qstash_request(
            signature=_signature_from_headers(request),
            body=body,
            settings=settings,
            url=verify_url,
        )
    except QStashSignatureError as exc:
        logger.warning("qstash signature rejected path=%s err=%s", request.url.path, exc)
        raise
    return body


@router.post("/ingest")
async def ingest_job(request: Request, response: Response) -> dict[str, Any]:
    """QStash delivery target: run ``ingest_document`` after signature verify."""
    try:
        body = await _read_and_verify(request)
    except QStashSignatureError:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"ok": False, "error": "invalid signature"}
    except RuntimeError as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ok": False, "error": str(exc)}

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"ok": False, "error": "invalid json body"}

    document_id = payload.get("document_id")
    if not document_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"ok": False, "error": "document_id required"}

    settings = get_settings()
    ctx: dict[str, Any] = {"settings": settings}
    result = await ingest_document(ctx, str(document_id))
    if isinstance(result, dict) and result.get("ok") is False:
        # Non-2xx so QStash retries until exhausted, then failure_callback.
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return result
    return {"ok": True, "result": result}


def _decode_source_body(callback: dict[str, Any]) -> dict[str, Any]:
    source = callback.get("sourceBody") or callback.get("source_body")
    if not source or not isinstance(source, str):
        return {}
    try:
        decoded = base64.b64decode(source).decode("utf-8")
        parsed = json.loads(decoded)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, json.JSONDecodeError):
        return {}


@router.post("/ingest-failed")
async def ingest_failed(request: Request, response: Response) -> dict[str, Any]:
    """QStash failure callback / DLQ-ish: mark Job (+ Document) failed."""
    try:
        body = await _read_and_verify(request)
    except QStashSignatureError:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"ok": False, "error": "invalid signature"}
    except RuntimeError as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ok": False, "error": str(exc)}

    try:
        callback = json.loads(body) if body else {}
    except json.JSONDecodeError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"ok": False, "error": "invalid json body"}

    source = _decode_source_body(callback if isinstance(callback, dict) else {})
    document_id_raw = source.get("document_id")
    job_id_raw = source.get("job_id")
    if not document_id_raw:
        logger.error("ingest-failed missing document_id in sourceBody callback=%s", callback)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"ok": False, "error": "document_id missing in sourceBody"}

    dlq_id = callback.get("dlqId") or callback.get("dlq_id")
    status_code = callback.get("status")
    message = (
        f"qstash delivery exhausted (status={status_code}, dlq_id={dlq_id})"
    )

    settings = get_settings()
    init_engine(settings)
    factory = get_session_factory(settings)
    doc_uuid = UUID(str(document_id_raw))
    job_uuid = UUID(str(job_id_raw)) if job_id_raw else None

    async with factory() as session:
        docs = DocumentRepository(session)
        jobs = JobRepository(session)
        document = await docs.get(doc_uuid)
        job = None
        if job_uuid is not None:
            job = await jobs.get(job_uuid)
        if job is None:
            job = await jobs.latest_for_document(doc_uuid)
        if document is not None and document.status not in {"ready", "failed"}:
            await docs.mark_status(document, "failed", error_message=message)
        if job is not None and job.status not in {"succeeded", "failed"}:
            await jobs.mark_status(job, "failed", error_message=message)
        await session.commit()

    logger.error(
        "ingest failure callback document_id=%s job_id=%s dlq_id=%s",
        document_id_raw,
        job_id_raw,
        dlq_id,
    )
    return {"ok": True, "document_id": str(document_id_raw), "marked_failed": True}

"""Ask and Ask history routes."""

from __future__ import annotations

import asyncio
from uuid import UUID

from atlas_generation.llm_client import LlmError
from atlas_orchestration.service import get_ask_record, run_ask
from atlas_persistence.postgres.repositories.documents import DocumentRepository
from fastapi import APIRouter, HTTPException, Request

from atlas_api.dependencies import (
    ApiKeyDep,
    SessionDep,
    SettingsDep,
    client_ip,
    enforce_rate_limit,
)
from atlas_api.schemas.ask import AskRecordOut, AskRequest, AskResponse, CitationOut

router = APIRouter(prefix="/v1", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def post_ask(
    body: AskRequest,
    request: Request,
    settings: SettingsDep,
    session: SessionDep,
    _: ApiKeyDep,
) -> AskResponse:
    await enforce_rate_limit(
        kind="ask",
        client_ip=client_ip(request),
        limit=settings.atlas_rate_limit_ask_per_min,
        settings=settings,
    )

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")
    if not body.document_ids:
        raise HTTPException(status_code=400, detail="document_ids must not be empty")
    if len(body.document_ids) > 20:
        raise HTTPException(status_code=400, detail="document_ids max is 20")

    try:
        requested = [UUID(value) for value in body.document_ids]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid document_ids") from exc

    ready_ids = await DocumentRepository(session).get_ready_ids(requested)
    if not ready_ids:
        raise HTTPException(
            status_code=400,
            detail="no ready documents in document_ids",
        )

    try:
        result = await asyncio.wait_for(
            run_ask(
                question=question,
                document_ids=ready_ids,
                top_k=body.top_k,
                temperature=body.temperature,
                model=body.model,
                settings=settings,
            ),
            timeout=settings.llm_timeout_seconds,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="generation timed out") from exc
    except LlmError as exc:
        raise HTTPException(status_code=502, detail=f"generation provider error: {exc}") from exc

    return AskResponse(
        ask_id=str(result.ask_id),
        answer=result.answer,
        abstained=result.abstained,
        citations=[CitationOut.model_validate(item) for item in result.citations],
    )


@router.get("/asks/{ask_id}", response_model=AskRecordOut)
async def get_ask(ask_id: UUID, _: ApiKeyDep, settings: SettingsDep) -> AskRecordOut:
    record = await get_ask_record(ask_id, settings=settings)
    if record is None:
        raise HTTPException(status_code=404, detail="ask not found")
    return AskRecordOut.model_validate(record)

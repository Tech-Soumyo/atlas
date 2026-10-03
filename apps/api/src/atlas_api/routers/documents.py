"""Document upload and list/get routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, Request, Response, UploadFile

from atlas_api.dependencies import (
    ApiKeyDep,
    SessionDep,
    SettingsDep,
    client_ip,
    enforce_rate_limit,
)
from atlas_api.schemas.documents import DocumentListOut, DocumentOut, UploadAccepted
from atlas_api.services.documents import (
    DocumentServiceError,
    get_document,
    list_documents,
    upload_document,
)

router = APIRouter(prefix="/v1/documents", tags=["documents"])

UploadFileDep = Annotated[UploadFile, File()]


@router.post("")
async def post_document(
    request: Request,
    response: Response,
    settings: SettingsDep,
    session: SessionDep,
    _: ApiKeyDep,
    file: UploadFileDep,
) -> UploadAccepted | DocumentOut:
    await enforce_rate_limit(
        kind="upload",
        client_ip=client_ip(request),
        limit=settings.atlas_rate_limit_upload_per_min,
        settings=settings,
    )

    data: bytes = await file.read()
    try:
        code, payload = await upload_document(
            session=session,
            settings=settings,
            filename=file.filename or "upload.pdf",
            content_type=file.content_type,
            data=data,
        )
    except DocumentServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    response.status_code = code
    if code == 200:
        return DocumentOut.model_validate(payload)
    return UploadAccepted.model_validate(payload)


@router.get("", response_model=DocumentListOut)
async def get_documents(
    session: SessionDep,
    _: ApiKeyDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentListOut:
    items, total = await list_documents(session, limit=limit, offset=offset)
    return DocumentListOut(
        items=[DocumentOut.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document_by_id(
    document_id: UUID,
    session: SessionDep,
    _: ApiKeyDep,
) -> DocumentOut:
    payload = await get_document(session, document_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="document not found")
    return DocumentOut.model_validate(payload)

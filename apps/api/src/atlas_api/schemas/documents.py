"""Document and job response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    byte_size: int
    page_count: int
    sha256: str
    storage_path: str
    status: str
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class UploadAccepted(BaseModel):
    job_id: str
    document_id: str
    status: str = "queued"


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int


class JobOut(BaseModel):
    id: str
    type: str
    status: str
    document_id: str
    error_message: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None

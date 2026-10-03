"""Local filesystem object store for PDF bytes."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from atlas_common.config import Settings, get_settings


def document_storage_path(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
) -> Path:
    cfg = settings or get_settings()
    root = Path(cfg.object_store_path)
    return root / "documents" / f"{document_id}.pdf"


def write_document_bytes(
    document_id: UUID | str,
    data: bytes,
    *,
    settings: Settings | None = None,
) -> Path:
    path = document_storage_path(document_id, settings=settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def read_document_bytes(
    document_id: UUID | str,
    *,
    settings: Settings | None = None,
) -> bytes:
    path = document_storage_path(document_id, settings=settings)
    return path.read_bytes()

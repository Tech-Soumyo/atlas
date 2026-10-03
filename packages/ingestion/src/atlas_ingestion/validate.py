"""Cheap PDF validation for the API upload path."""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf
from atlas_common.config import Settings, get_settings


class PdfValidationError(ValueError):
    """Raised when an upload fails API side PDF checks."""


@dataclass(frozen=True)
class PdfValidationResult:
    page_count: int
    sha256: str


def looks_like_pdf(*, filename: str, content_type: str | None, data: bytes) -> bool:
    name = filename.lower()
    ctype = (content_type or "").lower()
    extension_ok = name.endswith(".pdf")
    type_ok = "pdf" in ctype or ctype in {"", "application/octet-stream"}
    magic_ok = data[:4] == b"%PDF"
    return magic_ok and (extension_ok or type_ok)


def validate_pdf_upload(
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
    settings: Settings | None = None,
) -> PdfValidationResult:
    """Validate PDF type, size, and page cap via a cheap pymupdf open."""
    import hashlib

    cfg = settings or get_settings()
    if not looks_like_pdf(filename=filename, content_type=content_type, data=data):
        raise PdfValidationError("file must be a PDF (%PDF magic and pdf type/extension)")
    if len(data) > cfg.atlas_max_upload_bytes:
        raise PdfValidationError(
            f"file exceeds max upload bytes ({cfg.atlas_max_upload_bytes})"
        )
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PdfValidationError(f"unable to open PDF: {exc}") from exc
    try:
        page_count = doc.page_count
    finally:
        doc.close()
    if page_count > cfg.atlas_max_pdf_pages:
        raise PdfValidationError(
            f"PDF exceeds max pages ({cfg.atlas_max_pdf_pages})"
        )
    digest = hashlib.sha256(data).hexdigest()
    return PdfValidationResult(page_count=page_count, sha256=digest)

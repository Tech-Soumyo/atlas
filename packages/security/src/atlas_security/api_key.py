"""Shared X-API-Key verification."""

from __future__ import annotations

import hmac

from atlas_common.config import Settings, get_settings


class ApiKeyError(PermissionError):
    """Missing or invalid API key."""


def require_api_key_configured(settings: Settings | None = None) -> None:
    """Refuse process start outside test when ATLAS_API_KEY is empty."""
    cfg = settings or get_settings()
    if cfg.is_test:
        return
    if not cfg.atlas_api_key:
        raise RuntimeError("ATLAS_API_KEY must be set when ATLAS_ENV is not test")


def verify_api_key(provided: str | None, settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    if cfg.is_test:
        return
    expected = cfg.atlas_api_key or ""
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise ApiKeyError("invalid or missing API key")

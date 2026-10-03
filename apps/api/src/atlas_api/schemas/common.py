"""Shared API response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "atlas-api"
    version: str


class DependencyCheck(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: list[DependencyCheck] = Field(default_factory=list)

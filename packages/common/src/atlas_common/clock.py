"""Clock helpers (injectable in tests later)."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC time as an aware datetime."""
    return datetime.now(UTC)

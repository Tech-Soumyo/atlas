"""QStash signature verification for worker HTTP endpoints."""

from __future__ import annotations

from atlas_common.config import Settings, get_settings
from qstash import Receiver


class QStashSignatureError(Exception):
    """Incoming request failed QStash signature verification."""


def get_qstash_receiver(settings: Settings | None = None) -> Receiver:
    cfg = settings or get_settings()
    current = cfg.qstash_current_signing_key
    next_key = cfg.qstash_next_signing_key
    if not current or not next_key:
        msg = (
            "QSTASH_CURRENT_SIGNING_KEY and QSTASH_NEXT_SIGNING_KEY are required "
            "to verify QStash deliveries"
        )
        raise RuntimeError(msg)
    return Receiver(
        current_signing_key=current,
        next_signing_key=next_key,
    )


def verify_qstash_request(
    *,
    signature: str | None,
    body: str,
    settings: Settings | None = None,
    url: str | None = None,
) -> None:
    """Verify ``Upstash-Signature`` against current + next signing keys.

    Raises ``QStashSignatureError`` when the signature is missing or invalid.
    """
    if not signature:
        raise QStashSignatureError("missing Upstash-Signature header")
    receiver = get_qstash_receiver(settings)
    try:
        kwargs: dict[str, object] = {"signature": signature, "body": body}
        if url:
            kwargs["url"] = url
        receiver.verify(**kwargs)  # type: ignore[arg-type]
    except QStashSignatureError:
        raise
    except Exception as exc:
        raise QStashSignatureError(str(exc)) from exc

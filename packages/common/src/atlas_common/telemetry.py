"""OpenTelemetry helpers (noop wiring for M0; real export in M7)."""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)


def setup_telemetry(*, service_name: str, otlp_endpoint: str | None = None) -> None:
    """Configure tracing when an OTLP endpoint is set; otherwise no-op."""
    if not otlp_endpoint:
        _logger.debug("OTel skipped (no OTEL_EXPORTER_OTLP_ENDPOINT) service=%s", service_name)
        return
    _logger.info(
        "OTel endpoint configured for %s (full SDK wiring lands in M7)",
        service_name,
    )

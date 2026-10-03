# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.6.14-python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package atlas-worker

FROM python:3.12-slim-bookworm AS runtime

RUN useradd --create-home --uid 1000 atlas \
    && mkdir -p /app/configs /app/data/raw \
    && chown -R atlas:atlas /app

WORKDIR /app

COPY --from=builder --chown=atlas:atlas /app/.venv /app/.venv
COPY --chown=atlas:atlas configs /app/configs

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ATLAS_CONFIGS_DIR=/app/configs

USER atlas

CMD ["atlas-worker"]

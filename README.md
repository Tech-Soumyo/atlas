# Atlas

Production-oriented multi-tenant hybrid RAG platform (Phase 1: RAG + thin Next.js).

| Doc | Purpose |
|-----|---------|
| [`PRD.md`](PRD.md) | Product requirements & milestones |
| [`TASKLIST.md`](TASKLIST.md) | High-level end-to-end task checklist |
| [`TECH_STACK.md`](TECH_STACK.md) | Stack, libs, package inventory |
| [`STRUCTURE.md`](STRUCTURE.md) | File/folder layout & boundaries |
| [`docs/zero_cost_showcase.md`](docs/zero_cost_showcase.md) | ₹0 showcase (Groq/Gemini + local infra) |
| [`docs/upstash_integration.md`](docs/upstash_integration.md) | Default cloud data plane (Neon + Upstash Redis / Vector / QStash) |
| [`docs/code_explain_loop.md`](docs/code_explain_loop.md) | Code → interview explain ritual |
| [`docs/skills_usage_guide.md`](docs/skills_usage_guide.md) | When to use which installed agent skill |
| [`../topics.md`](../topics.md) | 120 RAG topics |
| [`../Questions_RAG_120.md`](../Questions_RAG_120.md) | 120 interview questions |

## Layout (short)

```text
apps/api       FastAPI edge
apps/worker    Async ingest
apps/web       Next.js E2E UI
packages/*     Domain logic (independently testable)
configs/       Non-secret tunables
tests/         Unit / integration / security
evals/         Golden data + reports
deploy/docker  Containerfiles
```

See [`STRUCTURE.md`](STRUCTURE.md) for the full tree and dependency rules.

## Quick start (M0)

```bash
# 1) Env (never commit .env)
cp .env.example .env
# Default host plane is Neon + Upstash (ATLAS_DATA_PLANE=upstash).
# For Compose offline stack, either leave .env as-is (Compose overrides to local)
# or set ATLAS_DATA_PLANE=local for host runs against Docker Redis/Qdrant.
cp apps/web/.env.example apps/web/.env.local

# 2) Python + web tooling
make install
make install-web
make pre-commit-install

# 3) Compose stack (postgres, qdrant, redis, api, worker, web) — local plane
make up
# equivalent: docker compose up --build

# 4) Smoke checks
curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready
# Web shell: http://localhost:3000  (server-side fetch uses ATLAS_API_INTERNAL_URL)

# 5) Unit tests (no Compose required)
make test-unit
```

Compose forces `ATLAS_DATA_PLANE=local` and service DNS URLs for postgres/redis/qdrant even if your host `.env` points at cloud services. Secrets stay in `.env` (gitignored). Host cloud runs keep using Neon/Upstash from `.env` without Compose.

Stop the stack with `make down`.

### Host run against Neon + Upstash (cloud plane)

```bash
# Fill .env: DATABASE_URL(+_POOLED), UPSTASH_*, QSTASH_*, ATLAS_WORKER_PUBLIC_URL, ATLAS_API_KEY
# ATLAS_DATA_PLANE=upstash (default)

# Public HTTPS tunnel to the worker HTTP app (QStash delivery target)
# Example: cloudflared tunnel --url http://localhost:8001
# Set ATLAS_WORKER_PUBLIC_URL to that https://….trycloudflare.com URL

uv run uvicorn atlas_api.main:app --host 0.0.0.0 --port 8000
uv run uvicorn atlas_worker.http_app:app --host 0.0.0.0 --port 8001

curl -s http://localhost:8000/ready   # postgres + upstash_redis + upstash_vector + qstash
```

Upload still calls `enqueue_ingest_document` → QStash → `POST {ATLAS_WORKER_PUBLIC_URL}/internal/jobs/ingest` (signature verified). See [`docs/upstash_integration.md`](docs/upstash_integration.md).

## Tooling

```bash
make lint
make format
make typecheck
make test
make ci
```

## Status

**M0 foundations:** Compose stack, `packages/common` config, FastAPI `/health` + `/ready`, worker heartbeat, Next.js health shell, pytest smoke.

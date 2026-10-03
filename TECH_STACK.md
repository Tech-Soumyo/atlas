# Atlas — Tech Stack, Libraries & Packages Tracker

> Living inventory for Phase 1 (RAG + thin Next.js E2E) and Phase 2 upgrades.  
> Rule: **keep the core RAG pipeline independently testable**; add libraries only when a concrete milestone requires them.  
> Companions: [`PRD.md`](PRD.md) · [`STRUCTURE.md`](STRUCTURE.md) · [`docs/zero_cost_showcase.md`](docs/zero_cost_showcase.md) · [`docs/upstash_integration.md`](docs/upstash_integration.md) · [`docs/code_explain_loop.md`](docs/code_explain_loop.md)

| Field | Value |
|-------|-------|
| **Last updated** | 2026-10-03 |
| **Phase** | 1 — RAG + Next.js E2E |
| **Status** | M0 foundations in progress |

---

## 1. Stack at a glance

```text
[Next.js Web] ──HTTP/SSE──► [FastAPI API] ──► [LangGraph ask]
       │                         │
       │                         ├── Postgres (ACL, BM25, jobs)
       │                         ├── Qdrant (dense vectors)
       │                         ├── Redis (queue + cache)
       │                         └── Workers (ingest)
       │
       └── Auth token (tenant/user) same JWT/API-key model as API
```

| Layer | Choice | Phase 1 role |
|-------|--------|--------------|
| Language (backend) | Python 3.12+ | All RAG services |
| API | FastAPI + Pydantic + Uvicorn | Ingest, ask, jobs, admin |
| Web UI | **Next.js (App Router) + TypeScript** | Ask chat, upload, job status, citations |
| Orchestration | LangGraph | Ask / later agentic graphs |
| OLTP + sparse search | PostgreSQL | Metadata, ACL, FTS/BM25, jobs |
| Vector DB | Qdrant | Dense ANN + payload filters |
| Queue / cache | Redis **or Upstash Redis + QStash** | Local Compose default; Upstash optional — [`docs/upstash_integration.md`](docs/upstash_integration.md) |
| Vector (alt) | Qdrant **or Upstash Vector** | Upstash supports hybrid + RRF/DBSF + metadata filters |
| Embeddings / rerank | Sentence Transformers | Local encode + cross-encoder (₹0) |
| LLM (default showcase) | **Groq free tier** (backup: **Gemini free**; offline: Ollama) | OpenAI-compatible adapter — see [`docs/zero_cost_showcase.md`](docs/zero_cost_showcase.md) |
| Evals | Custom metrics + Ragas | Golden + CI gates |
| Telemetry | OpenTelemetry | Traces/metrics across API + worker |
| Packaging / run | Docker Compose | Local prod-like E2E |
| Tests (backend) | pytest | Unit + integration + ACL + evals |
| Tests (web) | Playwright (smoke) or manual | Thin; don’t block RAG |

---

## 2. Applications

| App | Path (planned) | Runtime | Responsibility |
|-----|----------------|---------|----------------|
| `api` | `apps/api` | Python / FastAPI | REST + SSE; auth; wire packages |
| `worker` | `apps/worker` | Python | Async ingest: parse→chunk→embed→index |
| `web` | `apps/web` | **Next.js** | End-to-end UI for ask + ingest + citations |

### Next.js Phase 1 scope (thin, not a product redesign)

| Page / feature | Priority | Calls |
|----------------|----------|-------|
| Sign-in / set API token + tenant | P0 | local session → `Authorization` header |
| Upload document + ACL fields | P0 | `POST /v1/documents` |
| Job status | P0 | `GET /v1/jobs/{id}` |
| Ask chat (sync + optional stream) | P0 | `POST /v1/ask` (+ `/stream`) |
| Show answer + citations + abstain | P0 | render API payload |
| Trace id / diagnostics drawer | P1 | from ask `diagnostics` |
| Thumbs up/down feedback | P1 | small feedback endpoint (optional) |

**Out of Next.js Phase 1:** design system sprawl, multi-channel, billing UI, heavy admin RBAC console, SSR-heavy SEO.

---

## 3. Backend packages (Python modules in-repo)

Keep these **importable and pytest-able without Next.js or Docker UI**.

| Package | Path | Status | Milestone | Notes |
|---------|------|--------|-----------|-------|
| `common` | `packages/common` | Planned | M0 | config, logging, OTel helpers |
| `security` | `packages/security` | Planned | M7 | ACL, injection, audit |
| `ingestion` | `packages/ingestion` | Planned | M2 | parse, clean, chunk, versioning |
| `retrieval` | `packages/retrieval` | Planned | M3–M4 | dense, sparse, hybrid, RRF, rerank |
| `generation` | `packages/generation` | Planned | M5 | prompts, budget, cite, abstain, LLM client |
| `orchestration` | `packages/orchestration` | Planned | M1 / M8 | LangGraph ask / agentic graphs |
| `persistence` | `packages/persistence` | Planned | M0–M2 | Postgres / Redis / object store adapters |
| `evals` | `packages/evals` | Planned | M6 | nDCG/MRR + Ragas wrappers |

---

## 4. Libraries & packages inventory

### 4.1 Python — core (Phase 1, always install)

| Package | Role | Introduce at |
|---------|------|--------------|
| `fastapi` | HTTP API | M0 |
| `uvicorn[standard]` | ASGI server | M0 |
| `pydantic` / `pydantic-settings` | Schemas + settings | M0 |
| `httpx` | Async HTTP (internal + some clients) | M1 |
| `openai` | Groq / Gemini / Ollama via OpenAI-compatible API | M1 |
| `sqlalchemy` | ORM / DB access | M0–M2 |
| `psycopg[binary]` | Postgres driver | M0–M2 |
| `alembic` | Migrations | M0–M2 |
| `redis` | Local queue + cache | M0 / M7 |
| `qdrant-client` | Dense vectors (local Compose mode) | M3 |
| `sentence-transformers` | Embeddings + cross-encoder rerank | M3–M4 |
| `torch` | Brought by Sentence Transformers (CPU OK) | M3 |
| `langgraph` | Ask orchestration | M1 / M4 |
| `langchain-core` | Light deps LangGraph often needs (not full LangChain app) | M1 |
| `ragas` | Generation-side evals | M6 |
| `opentelemetry-api` | Tracing | M0–M7 |
| `opentelemetry-sdk` | Tracing | M0–M7 |
| `opentelemetry-exporter-otlp` | Export traces | M0–M7 |
| `opentelemetry-instrumentation-fastapi` | Optional auto-instrument | M7 |
| `pytest` | Tests | M0 |
| `pytest-asyncio` | Async tests | M0 |
| `python-multipart` | File uploads in FastAPI | M0–M2 |
| `pyyaml` | Load `configs/*.yaml` | M0 |
| `PyJWT` | JWT auth (or `python-jose` — pick one) | M0 |
| `numpy` | Retrieval / eval math | M3–M6 |
| `tiktoken` | Context token budgeting | M5 |

**Mental model — always:**

```text
fastapi uvicorn[standard] pydantic-settings httpx openai
sqlalchemy psycopg[binary] alembic
redis qdrant-client
sentence-transformers langgraph langchain-core
ragas
opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
pytest pytest-asyncio python-multipart pyyaml PyJWT numpy tiktoken
```

### 4.2 Python — milestone-triggered

| Package | Role | Introduce at | Gate |
|---------|------|--------------|------|
| `pymupdf` | Fast PDF text | M2 | PDF ingest |
| `docling` | Layout / tables (heavier) | M2 | Table-heavy corpus |
| `python-docx` | DOCX parsing | M2 | DOCX support |
| `beautifulsoup4` / `lxml` | HTML parsing | M2 | HTML support |
| `xgboost` | Learned rerank | M4 | After cross-encoder baseline |
| `scikit-learn` | Features / metrics helpers | M4–M6 | Rerank / eval helpers |
| `deepeval` | Extra evaluators | M6 | Only if Ragas + custom insufficient |
| `minio` or `boto3` | S3-compatible blobs | M2+ | Only if not using local `./data` |
| `passlib` / `bcrypt` | Hash secrets | optional | Only if hashing API keys at rest |

**When you hit the milestone:**

```text
pymupdf docling python-docx beautifulsoup4 lxml   # M2 as needed
xgboost scikit-learn                              # M4+
deepeval                                          # M6 optional
```

### 4.3 Python — optional Upstash mode

Install as extras, e.g. `pip install -e ".[upstash]"`. See [`docs/upstash_integration.md`](docs/upstash_integration.md).

| Package | Role | When |
|---------|------|------|
| `upstash-redis` | Serverless Redis cache | `ATLAS_DATA_PLANE=upstash` |
| `upstash-vector` | Vectors / hybrid RRF (can replace Qdrant) | Upstash mode M3–M4 |
| `qstash` | Ingest jobs + retries (needs public worker URL) | Upstash mode M2 |

```text
upstash-redis upstash-vector qstash
```

### 4.4 Python — dev / quality (recommended)

| Package | Role |
|---------|------|
| `ruff` | Lint / format |
| `mypy` | Static types (optional) |
| `pre-commit` | Git hooks (optional) |
| `testcontainers` | Integration tests vs real deps (optional) |

### 4.5 Node / web (not Python — for E2E UI)

| Package | Role | Introduce at |
|---------|------|--------------|
| `next` | Web app (App Router) | M0 |
| `react` / `react-dom` | UI | M0 |
| `typescript` | Types | M0 |
| `@playwright/test` | Web E2E smoke | M5+ optional |
| `zod` | Client validation (optional; can mirror Pydantic) | M0–M1 optional |

### 4.6 Explicitly deferred / do not add by default

| Package / idea | Why deferred |
|----------------|--------------|
| Full `langchain` / LangChain Expression Language app | Harder to test/explain; own packages own the pipeline |
| `llama-index` as primary orchestrator | Same reason; optional later comparison ADR |
| OpenSearch / Elasticsearch clients | Postgres FTS covers Phase 1 sparse |
| `langfuse` / `langsmith` | OTel first; add if trace UX needs it |
| SPLADE / GraphRAG / RAPTOR libs | ★ topics / Phase 2 spikes |
| Auth0 / Cognito SDKs | JWT/API-key enough for Phase 1 |
| Heavy UI component systems | Thin Next.js pages only |

---

## 5. Docker Compose services (planned)

| Service | Image / build | Ports (dev) | Depends on |
|---------|---------------|-------------|------------|
| `api` | `apps/api` Dockerfile | 8000 | postgres, qdrant, redis |
| `worker` | `apps/worker` Dockerfile | — | postgres, qdrant, redis |
| `web` | `apps/web` Dockerfile | 3000 | api |
| `postgres` | `postgres:16` | 5432 | — |
| `qdrant` | `qdrant/qdrant` | 6333 | — |
| `redis` | `redis:7` | 6379 | — |
| `otel-collector` (optional) | otel collector | — | — |

---

## 6. Testing matrix (incl. Next.js)

| Layer | Scope | Tool | Needs UI? |
|-------|-------|------|-----------|
| Unit | chunking, RRF, ACL filters, budgeter | pytest | No |
| API integration | ingest/ask/jobs against Compose | pytest + httpx | No |
| Retrieval/eval | golden nDCG/MRR/Ragas | `packages/evals` | No |
| Security | cross-tenant leakage | pytest | No |
| Web smoke | upload → ready → ask → citations visible | Playwright or manual | Yes |
| Manual E2E | interviewer demo path | browser @ `:3000` | Yes |

**Priority:** backend pytest + evals are the quality gate. Next.js smoke is demo confidence, not a substitute for retrieval metrics.

---

## 7. Version pins (fill during M0)

Record exact versions when scaffolding so interviews can cite a reproducible stack. Prefer a root `pyproject.toml` with optional extras: `[upstash]`, `[ingest]`, `[rerank]`, `[dev]`.

| Package | Version | Pinned in | Date |
|---------|---------|-----------|------|
| Python | 3.12 | `.python-version` / Docker | 2026-10-03 |
| `fastapi` | 0.142.2 | `uv.lock` / `apps/api` | 2026-10-03 |
| `uvicorn` | 0.54.0 | `uv.lock` | 2026-10-03 |
| `pydantic` / `pydantic-settings` | 2.13.5 / 2.15.0 | `uv.lock` | 2026-10-03 |
| `psycopg` | 3.3.6 | `uv.lock` | 2026-10-03 |
| `sqlalchemy` / `alembic` | _TBD_ | M1–M2 | |
| `langgraph` | _TBD_ | M1 | |
| `openai` | _TBD_ | M1 | |
| `qdrant-client` | _TBD_ | M3 | |
| `redis` | 8.1.0 | `uv.lock` | 2026-10-03 |
| `httpx` | 0.28.1 | `uv.lock` | 2026-10-03 |
| `sentence-transformers` | _TBD_ | M1–M3 | |
| `ragas` | _TBD_ | M6 | |
| `upstash-redis` / `upstash-vector` / `qstash` | _TBD_ | optional `[upstash]` | |
| `next` | 16.3.8 | `apps/web/package.json` | 2026-10-03 |
| `react` / `react-dom` | 19.2.8 | `apps/web/package.json` | 2026-10-03 |
| Node | 22 (Docker web image) | `deploy/docker/web.Dockerfile` | 2026-10-03 |
| PostgreSQL | 16 | Compose | 2026-10-03 |
| Redis | 7 | Compose | 2026-10-03 |
| Qdrant | v1.13.2 | Compose | 2026-10-03 |

---

## 8. Environment variables (high level)

| Variable | Used by | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | api, worker | Postgres |
| `QDRANT_URL` | api, worker | Vectors |
| `REDIS_URL` | api, worker | Queue/cache |
| `OPENAI_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | api, worker | Chat (Groq/Gemini/Ollama) |
| `LLM_PROVIDER` | api, worker | `groq` \| `gemini` \| `ollama` |
| `EMBEDDING_MODEL` | worker, api | ST model id |
| `ATLAS_DATA_PLANE` | api, worker | `local` \| `upstash` |
| `UPSTASH_*` / `QSTASH_*` | api, worker | Upstash mode only |
| `ATLAS_JWT_SECRET` / API keys | api, web | Auth |
| `NEXT_PUBLIC_ATLAS_API_URL` | web | Browser → API base URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | api, worker | Traces |

Never commit secrets; use `.env.example` only.

---

## 9. Change log (stack decisions)

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-03 | Core: FastAPI, Postgres, Qdrant, Redis, ST, LangGraph, Ragas, OTel, Docker | Independently testable RAG core |
| 2026-10-03 | **Add Next.js in Phase 1** | End-to-end demo: upload → ask → citations in browser |
| 2026-10-03 | Next.js stays thin (ask + ingest + citations) | Don’t let UI steal RAG milestone time |
| 2026-10-03 | XGBoost / Docling / MinIO = milestone-gated | Add only when M2/M4 need them |
| 2026-10-03 | Default LLM = Groq free tier; Gemini backup; Ollama offline | See `docs/zero_cost_showcase.md`; embeddings stay local |
| 2026-10-03 | Optional Upstash Redis / Vector / QStash / Search / Workflow | Adapter-based; local Compose remains default — `docs/upstash_integration.md` |
| 2026-10-03 | Expanded §4 Python inventory (core / milestone / upstash / dev / deferred) | Single checklist for pip + extras |

---

## 10. How to update this file

When you add a dependency:

1. Put it in §4.1 (core), §4.2 (milestone), §4.3 (Upstash), or §4.4 (dev) with justification  
2. Pin version in §7  
3. Note decision in §9  
4. If it affects architecture, add a one-line ADR under `docs/adr/`  

If you cannot justify a package against a PRD requirement or milestone DoD — **don’t add it**.

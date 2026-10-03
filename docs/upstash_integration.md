# Atlas — Upstash Integration Option (Redis · Vector · QStash · Search · Workflow)

> Optional **serverless / free-tier** data plane using [Upstash](https://upstash.com/docs).  
> Local Docker (Postgres + Qdrant + Redis) remains the default offline path.  
> Docs checked via Context7: Upstash Vector, Redis, QStash, platform overview.  
> Companions: [`zero_cost_showcase.md`](zero_cost_showcase.md) · [`../TECH_STACK.md`](../TECH_STACK.md) · [`../STRUCTURE.md`](../STRUCTURE.md)

| Field | Value |
|-------|-------|
| **Mode name** | `ATLAS_DATA_PLANE=upstash` (optional) |
| **Default mode** | `local` Compose (Qdrant + Redis container) |
| **Goal** | ₹0–ish serverless showcase + interview story for managed RAG infra |

---

## 1. Why Upstash fits Atlas

| Atlas need | Upstash product | Fit |
|------------|-----------------|-----|
| Cache embeddings / retrieval / responses | **Upstash Redis** | REST Redis; `upstash-redis` Python SDK |
| Async ingest + retries / failure path | **QStash** | HTTP publish → worker URL; retries; failure callback ≈ DLQ |
| Dense (+ optional hybrid) vectors | **Upstash Vector** | Metadata filters; **hybrid dense+sparse**; **RRF / DBSF** fusion |
| Extra keyword / search | **Upstash Search** | Optional complement to Postgres FTS |
| Durable multi-step ingest | **Upstash Workflow** | Phase 2 / advanced orchestration |

Official SDKs (from Upstash docs):

- Redis: `from upstash_redis import Redis` — `Redis.from_env()`
- Vector: `from upstash_vector import Index, Vector` — hybrid + `FusionAlgorithm.RRF`
- QStash: `from qstash import QStash` — `publish_json(..., retries=3, failure_callback=...)`

---

## 2. Recommended Atlas mapping

### Keep always (even with Upstash)

| Component | Why |
|-----------|-----|
| **PostgreSQL** | Source of truth: documents, chunks text, ACL, jobs, audit (relational) |
| **FastAPI + worker endpoints** | QStash delivers HTTP to your worker URL |
| **Sentence Transformers** | Local embeddings (don’t burn LLM quota); vectors pushed to Upstash Vector |
| **Groq / Gemini** | Chat generation (unchanged) |

### Swap / add with Upstash mode

| Local Compose | Upstash mode |
|---------------|--------------|
| Redis container | **Upstash Redis** (cache) |
| Redis lists as queue | **QStash** → `POST /internal/jobs/ingest` |
| Qdrant | **Upstash Vector** (dense or hybrid index) |
| Postgres FTS only | Postgres FTS **and/or** Upstash Vector hybrid sparse + RRF |
| — | Optional **Upstash Search** later |
| — | Optional **Workflow** for multi-step ingest (Phase 2) |

```text
Next.js → FastAPI
            ├─ cache ──────────────► Upstash Redis
            ├─ enqueue ingest ─────► QStash ──HTTP──► Worker
            ├─ dense/hybrid query ─► Upstash Vector  (metadata filter = ACL)
            └─ metadata / BM25 ────► PostgreSQL
```

---

## 3. Product deep-dive (from Upstash docs)

### 3.1 Upstash Redis — cache

- HTTP/REST Redis client designed for serverless and serverful apps.
- Python: sync + async clients; reuse client outside handlers.
- Atlas uses: embedding cache, retrieval cache, optional response cache, rate-limit counters.

```python
from upstash_redis import Redis

redis = Redis.from_env()  # UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN
redis.set("retrieval:tenant:hash", cached_json)
redis.get("retrieval:tenant:hash")
```

### 3.2 Upstash Vector — retrieval

Supports:

- Dense query + **metadata filters** (critical for ACL):  
  `filter='tenant_id = "t1" AND "role_hr" IN allowed_roles'`
- **Hybrid indexes**: dense + sparse vectors in one query  
- Fusion: **`FusionAlgorithm.RRF`** or `DBSF` — aligns with Atlas M4 hybrid story

```python
from upstash_vector import Index, Vector
from upstash_vector.types import SparseVector, FusionAlgorithm

index = Index(url="...", token="...")

index.upsert(vectors=[
    Vector(
        id="chunk_123",
        vector=dense_embedding,
        sparse_vector=SparseVector(indices, values),  # if hybrid index
        metadata={
            "tenant_id": "t_hr",
            "document_id": "doc_1",
            "allowed_roles": ["hr", "admin"],
        },
    )
])

hits = index.query(
    vector=query_dense,
    sparse_vector=SparseVector(...),  # optional hybrid
    top_k=20,
    filter='tenant_id = "t_hr"',
    fusion_algorithm=FusionAlgorithm.RRF,
    include_metadata=True,
)
```

**Interview angle:** “We can run hybrid RRF inside Upstash Vector, or fuse Upstash dense with Postgres BM25 in our `packages/retrieval` layer — same interface either way.”

### 3.3 QStash — ingest jobs

- Serverless messaging: publish JSON to a **public HTTPS worker URL** (or tunnel in dev).
- **Retries** with backoff; after exhaustion → **failure_callback** (DLQ-like).
- Atlas: `POST` ingest accepted → QStash publish → worker runs parse/chunk/embed/upsert.

```python
from qstash import QStash

client = QStash("<QSTASH_TOKEN>")
client.message.publish_json(
    url="https://your-api.example/internal/worker/ingest",
    body={"jobId": "...", "documentId": "..."},
    retries=3,
    failure_callback="https://your-api.example/internal/worker/ingest-failed",
)
```

**Dev note:** Localhost URLs need a tunnel (e.g. Cloudflare Tunnel / ngrok) for QStash to reach the worker, **or** keep Redis queue for pure-local mode.

### 3.4 Upstash Search (optional)

- Separate product for search use cases.
- Use if you want managed keyword/search without owning OpenSearch.
- Phase 1 can stay on **Postgres FTS**; add Search when justifying another index.

### 3.5 Upstash Workflow (optional / Phase 2)

- Durable steps for long ingest pipelines (parse → chunk → embed → index → invalidate).
- Prefer after QStash single-job path works.

---

## 4. Two showcase profiles

| Profile | When | Data plane |
|---------|------|------------|
| **A. Local Compose (default)** | Offline laptop, no tunnels | Postgres + Qdrant + Redis containers |
| **B. Upstash free-tier** | Serverless story, less Docker RAM | Postgres local (or free PG) + Upstash Redis + Vector + QStash |

You can implement **adapters** so both work:

```text
packages/persistence/redis/     → LocalRedis | UpstashRedis
packages/retrieval/dense/       → QdrantStore | UpstashVectorStore
apps/worker queue               → RedisQueue | QStashPublisher
```

---

## 5. Env vars (Upstash mode)

```bash
ATLAS_DATA_PLANE=upstash

# Redis
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=

# Vector
UPSTASH_VECTOR_REST_URL=
UPSTASH_VECTOR_REST_TOKEN=

# QStash
QSTASH_TOKEN=
QSTASH_CURRENT_SIGNING_KEY=    # verify incoming worker requests
QSTASH_NEXT_SIGNING_KEY=
ATLAS_WORKER_PUBLIC_URL=https://xxxx.trycloudflare.com  # must be reachable by QStash

# Still required
DATABASE_URL=postgresql+psycopg://...
```

Never commit tokens. Use free-tier DBs from [Upstash console](https://console.upstash.com).

---

## 6. Packages to add (milestone-gated)

| Package | When | Purpose |
|---------|------|---------|
| `upstash-redis` | Upstash mode / M7 cache | Cache client |
| `upstash-vector` | Upstash mode / M3–M4 | Vector + hybrid RRF |
| `qstash` | Upstash mode / M2 ingest | Job publish + retries |

Do **not** hard-depend these in local-only installs — optional extras in `pyproject.toml`:

```toml
[project.optional-dependencies]
upstash = ["upstash-redis", "upstash-vector", "qstash"]
```

---

## 7. Security notes

1. **ACL filters** must be applied in Vector `filter` (and Postgres) — never trust client-supplied tenant alone.  
2. **Verify QStash signatures** on worker routes (`QSTASH_*_SIGNING_KEY`) so random internet traffic can’t trigger ingest.  
3. Cache keys must include `tenant_id` + ACL scope.  
4. Rotate REST tokens if leaked; keep in `.env` only.

---

## 8. ₹0 / free-tier cautions

- Upstash free tiers have **command / storage / message limits** — fine for showcase, not load tests.  
- QStash needs a **public URL** (tunnel) in local dev.  
- Prefer **local embeddings** + Upstash only for store/query to control cost/quota.  
- For interviews: say “free-tier serverless data plane” and know the local Compose fallback.

---

## 9. Milestone suggestion

| Step | Work |
|------|------|
| M0 | Feature flag `ATLAS_DATA_PLANE=local\|upstash`; interfaces only |
| M3 | `UpstashVectorStore` behind dense interface (+ metadata filter) |
| M2/M7 | QStash publish path **or** keep Redis queue locally |
| M4 | Optional Upstash **hybrid index + RRF**; compare to Postgres BM25 + app-side RRF |
| M7 | Upstash Redis cache + invalidation |
| Phase 2 | Workflow / Search if needed |

---

## 10. Interview one-liner

> “Atlas abstracts the data plane: local Compose for offline demos, or Upstash Redis + Vector + QStash on free tier for a serverless story. Retrieval still enforces tenant metadata filters; hybrid can use Upstash’s native RRF or our Postgres BM25 + dense fusion.”

---

## 11. Decision log

| Date | Decision |
|------|----------|
| 2026-10-03 | Document Upstash as **optional** data plane (not required to replace Postgres) |
| 2026-10-03 | Prefer adapters: Qdrant↔Upstash Vector, Redis↔Upstash Redis, Redis queue↔QStash |
| 2026-10-03 | Use Upstash Vector hybrid+RRF as a strong M4 alternative path |
| 2026-10-03 | Default remain local Compose for zero-tunnel demos |

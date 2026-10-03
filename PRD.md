# PRD: Atlas — Production Multi-Tenant Hybrid RAG Platform

| Field | Value |
|-------|-------|
| **Product** | Atlas |
| **Version** | 1.1 |
| **Status** | Ready for implementation (Phase 1) |
| **Owner** | Soumyo (AI Engineering Interview Prep) |
| **Last updated** | 2026-10-03 |
| **Companion** | [`TASKLIST.md`](TASKLIST.md) · [`TECH_STACK.md`](TECH_STACK.md) · [`STRUCTURE.md`](STRUCTURE.md) · [`../topics.md`](../topics.md) · [`../Questions_RAG_120.md`](../Questions_RAG_120.md) |
| **Primary goal** | Phase 1: learn RAG via a production Atlas system **with thin Next.js E2E UI**. Phase 2: upgrade the same repo layer-by-layer toward the full agentic architecture. |

---

## 1. Executive summary

**Atlas** is a multi-tenant, permission-aware enterprise document Q&A platform.

Users upload company documents; Atlas asynchronously ingests, indexes (sparse + dense), retrieves via hybrid search + reranking, and generates **grounded, citation-backed answers**. The system is secured per document ACL, observable end-to-end, eval-gated in CI, and optimized for latency and cost.

Atlas is both:
1. A **portfolio / interview-defense project** (design, debug, trade-offs)
2. A **learning vehicle** for the 120-topic RAG checklist, then full production layers

**One-sentence pitch:**  
*Upload docs → hybrid retrieve → rerank → cite → answer — with tenant isolation, evals, and production ops.*

**Delivery strategy:** RAG-first in Phase 1, then thicken each architecture layer in Phase 2 on the **same codebase** (additive upgrades, not a rewrite). See [§5a](#5a-phased-delivery-strategy).

---

## 2. Problem statement

### 2.1 User / business problem
Enterprise knowledge is trapped in PDFs, Confluence/HTML exports, DOCX, Markdown, and email. Employees ask questions; search returns links or wrong snippets; chatbots hallucinate or leak cross-team data.

### 2.2 Learning problem
Interview prep lists 120 RAG topics, but reading alone does not produce interview-ready depth. A single production system is needed where each topic shows up as a design decision, failure mode, metric, or code path.

### 2.3 Why now
AI Engineer interviews emphasize hybrid RAG, reranking, nDCG/MRR, ACL-aware retrieval, FastAPI services, LangGraph workflows, and production failure recovery — exactly what Atlas implements.

---

## 3. Goals and non-goals

### 3.1 Goals (must achieve)

| ID | Goal | Measurable outcome |
|----|------|--------------------|
| G1 | End-to-end hybrid RAG | Dense (Qdrant) + sparse (Postgres BM25) + RRF + rerank path live |
| G2 | Grounded answers | Every answer includes chunk-level citations or explicit abstention |
| G3 | Multi-tenant + ACL | Zero cross-tenant leakage in automated security tests |
| G4 | Freshness | Doc update/delete reflected in answers within ingest SLA |
| G5 | Evaluated quality | Golden set + Recall@K / MRR / nDCG@K + faithfulness gates in CI |
| G6 | Production ops | Async ingest, retries/DLQ, Redis cache+invalidation, tracing, cost attribution |
| G7 | Interview readiness | 10-min architecture talk + 3 debug stories backed by real traces/metrics |
| G8 | Topic coverage | All ★★★ and ★★ topics from `topics.md` exercised in code or design docs |

### 3.2 Non-goals (explicitly out of v1)

| ID | Non-goal | Rationale |
|----|----------|-----------|
| NG1 | Train foundation models from scratch | AI Eng scope = apply/serve models |
| NG2 | Full GraphRAG / RAPTOR production | ★ topics only — optional M8 spike |
| NG3 | Audio/video RAG | Out of scope for v1 |
| NG4 | SPLADE as primary sparse path | Optional experiment; BM25 is required |
| NG5 | Multi-cloud SaaS billing | Demo tenancy only |
| NG6 | Pixel-perfect / design-system-heavy UI | **Next.js is in Phase 1** for E2E demo, but stays thin (ask + upload + citations) — see [`TECH_STACK.md`](TECH_STACK.md) |
| NG7 | Real enterprise IdP federation | JWT/API-key tenancy sufficient for Phase 1 |
| NG8 | Full 12-layer agentic platform in Phase 1 | Phase 2 upgrades; Phase 1 keeps thin shells only |

---

## 4. Personas and use cases

### 4.1 Personas

| Persona | Needs |
|---------|-------|
| **Employee (Asker)** | Fast, cited answers from docs they are allowed to see |
| **Knowledge Admin** | Upload/version/delete docs; see ingest status; manage ACLs |
| **Platform Engineer** | SLOs, traces, cost, capacity, safe deploys |
| **Eval Owner (you)** | Golden sets, ablations, regression gates |
| **Interviewer (consumer)** | Clear architecture, trade-offs, failure recovery |

### 4.2 Primary use cases

1. **UC-Ask:** Authenticated user asks a question → receives streamed or sync answer with citations (or abstains).
2. **UC-Ingest:** Admin uploads documents → async pipeline parses, chunks, embeds, indexes → ready for ask.
3. **UC-Update:** Admin replaces or deletes a document → indexes and caches invalidate → answers stay fresh.
4. **UC-Permission:** User without ACL on a doc never sees that doc’s chunks in retrieval or context.
5. **UC-Eval:** Offline suite scores retrieval + generation; CI blocks regressions.
6. **UC-Debug:** Engineer opens a request trace and attributes failure to retrieve vs generate.
7. **UC-Agent (v1.1):** Multi-hop / tool-based retrieval when single-shot hybrid fails.

---

## 5. Product scope by milestone

Milestones are the delivery plan. Each maps to `topics.md` sections.

| Milestone | Name | Topics | Deliverable |
|-----------|------|--------|-------------|
| **M0** | Foundations | 101–102, 110 | Repo, Docker Compose, config, health checks |
| **M1** | Naive RAG | 1–10 | Single-tenant PDF → embed → top-K → answer |
| **M2** | Ingestion & chunking | 11–20, 108 | Multi-format parse, metadata, parent-child chunks, versioning |
| **M3** | Indexes | 21–30, 105, 107 | Qdrant dense + Postgres BM25 + filtered ANN |
| **M4** | Hybrid + rerank | 31–50, 106 | Query rewrite, RRF/MMR, cross-encoder + XGBoost rerank |
| **M5** | Context & generation | 51–60 | Budgeting, citations, abstention, streaming |
| **M6** | Evaluation | 71–80, 109 | Golden set, metrics, RAGAS/custom, CI gate |
| **M7** | Security & prod | 81–100 | ACL, injection tests, queues, cache, SLO, obs |
| **M8** | Advanced + design | 61–70 (selective), 103–104, 111–120 | Agentic RAG, SQL RAG optional; interview writeups |

**MVP for “portfolio ready”:** M0–M7 complete (end of Phase 1).  
**Interview max (Phase 1):** M8 selective + talk track.  
**Phase 2:** layer upgrades L1–L12 (see §5a–§5c).

---

## 5a. Phased delivery strategy

```text
Phase 1 — RAG excellence (M0–M7, optional M8 spikes)
  Learn topics.md ★★★ / ★★ through a working hybrid RAG product.
  Keep orchestration, gateway, infra as thin but real shells.

Phase 2 — Architecture layer upgrades (same repo)
  Evolve Atlas toward agentic_ai_architecture_full.jpg, one layer at a time.
  Additive packages/services — do not rewrite the RAG core.
```

| Phase | Focus | Done when |
|-------|-------|-----------|
| **Phase 1** | 120 RAG topics via Atlas M0–M7 | Hybrid+rerank beats dense-only; ACL tests green; eval CI gate; talk track ready |
| **Phase 2** | Full architecture layers around that core | Each target layer has a deeper implementation + ADR + demo path |

### Learning loop (every milestone)

1. Read 3–5 interview questions for the slice ([`docs/code_explain_loop.md`](docs/code_explain_loop.md))  
2. Implement the milestone feature  
3. Answer those questions out loud using Atlas (interview card: definition → why → how Atlas → trade-off → failure)  
4. Write a short ADR or note if a topic is design-only  
5. Tick the matching rows in [`../topics.md`](../topics.md)  
6. Add/adjust one eval or test that locks the behavior  
7. Only then start the next milestone  

---

## 5b. Architecture layers — Phase 1 thin vs Phase 2 deep

North Star: `docs/agentic_ai_architecture_full.jpg` (12 layers).

| # | Layer | Phase 1 (thin / required) | Phase 2 (upgrade) |
|---|-------|---------------------------|-------------------|
| 1 | Users & Channels | **Next.js** ask + upload + job status + citations; curl/eval still supported | Slack/Teams; richer admin; multi-channel |
| 2 | Orchestration (Agent Runtime) | Linear ask graph (rewrite→retrieve→rerank→generate); LangGraph state | Planner, sub-agents, memory manager, tool executor, HITL checkpoints |
| 3 | Tools & Integrations | Vector DB + Postgres + object store as tools behind retrieval | Broader tool registry (search, CRM stubs, code exec sandbox) |
| 4 | Context & Memory (RAG) | **Full Phase 1 core** — ingest, hybrid, rerank, context, citations | Advanced memory, GraphRAG/RAPTOR spikes if still needed |
| 5 | Guardrails | Input injection checks + output citation/schema checks | Full in/out rails, toxicity, PII masking, policy engine |
| 6 | LLM Gateway | Single OpenAI-compatible adapter: timeouts, retries, basic cache, cost log | Routing, failover, load balance, semantic/embedding/API cache tiers, multi-provider |
| 7 | Model Layer | Env-swappable chat + embedding + rerank models; RAG vs FT documented | Model selection matrix, optional PEFT/FT experiment, serving notes |
| 8 | Observability & Evaluation | OTel traces, golden metrics, CI regression gate | Full online evals, richer graders, feedback→eval automation |
| 9 | Security & Governance | Tenant/ACL, audit log, secrets via env, adversarial tests | Zero-trust hardening, richer compliance/retention controls |
| 10 | Infrastructure | Docker Compose (API, worker, Postgres, Qdrant, Redis) | K8s-lite / cloud deploy, autoscaling story |
| 11 | DevOps & Delivery | pytest + eval gate locally/CI | Progressive delivery, scan stage, prod feedback cycle automation |
| 12 | Human-in-the-Loop | Optional thumbs feedback stored for analysis | Expert review queue, RLHF/RLAIF-style improvement loop (lightweight) |

**Rule:** Phase 1 must not block on Phase 2 depth. If a layer is only a shell in Phase 1, document the upgrade path in `docs/adr/`.

---

## 5c. Milestone definition of done (Phase 1)

| Milestone | Definition of done (all must pass) |
|-----------|-------------------------------------|
| **M0** | Compose stack healthy (api, worker, web, postgres, qdrant, redis); `/health` + `/ready`; Next.js loads and can hit API health; config via `.env` + YAML; empty packages importable; README runbook |
| **M1** | Upload one PDF → naive retrieve → answer via API **and Next.js**; can explain naive vs advanced RAG; topics 1–10 notes started |
| **M2** | Multi-format ingest via UI/API; parent-child chunks persisted; version/delete path works; topics 11–20 ticked for implemented items |
| **M3** | Dense (Qdrant) + sparse (Postgres) queries return filtered results; embedding version stored; topics 21–30 covered |
| **M4** | Hybrid RRF path live; rerank (cross-encoder and/or XGBoost); ablation script compares dense vs hybrid; topics 31–50 covered |
| **M5** | Cited or abstained answers only; context budgeter; streaming optional; Next.js renders citations/abstain; topics 51–60 covered |
| **M6** | Golden set runs; Recall@K/MRR/nDCG + faithfulness reported; CI fails on regression threshold; topics 71–80 covered |
| **M7** | Cross-tenant tests pass; cache invalidation demo; traces+cost logs; DLQ/retry path; topics 81–100 covered |
| **M8** | ≤2 advanced spikes (prefer agentic RAG); `interview_talk_track.md` answers 111–120 using Atlas |

**Phase 1 exit checklist**

- [ ] M0–M7 DoD met  
- [ ] Hybrid+rerank > dense-only on golden nDCG@10 / MRR (numbers in README)  
- [ ] `topics.md` ★★★ / ★★ mostly ticked (code or ADR)  
- [ ] Interview talk track rehearsed once  
- [ ] Phase 2 backlog ordered (first upgrade layer chosen)

**Suggested Phase 2 order** (adjust by interview needs):  
`L6 Gateway → L2 Orchestration → L5 Guardrails → L8 Obs/Evals → L11 DevOps → L9 Security → L10 Infra → L12 HITL → L1 Channels → L7 Model/FT`

---

## 6. Functional requirements

### 6.1 Authentication, tenancy, authorization

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-A1 | Every request carries `tenant_id` + `user_id` (JWT or API key) | P0 |
| FR-A2 | Documents and chunks store ACL attributes (`allowed_roles`, `allowed_user_ids`, `sensitivity`) | P0 |
| FR-A3 | Retrieval applies ACL filters in **both** sparse and dense paths (never post-filter-only as sole control) | P0 |
| FR-A4 | Cross-tenant queries impossible by construction (collection/index namespaced or mandatory filter) | P0 |
| FR-A5 | Audit log: who asked/ingested what, doc ids touched, allow/deny | P1 |

### 6.2 Document ingestion

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-I1 | Support PDF, HTML, DOCX, Markdown; email (.eml) best-effort | P0 / P1 |
| FR-I2 | Async ingest via queue; API returns `job_id` immediately | P0 |
| FR-I3 | Pipeline: load → parse → clean/normalize → dedupe → metadata → chunk → embed → index | P0 |
| FR-I4 | Layout-aware parsing + table extraction for PDFs (Docling/PyMuPDF) | P1 |
| FR-I5 | OCR path for scanned PDFs | P1 |
| FR-I6 | Chunk strategies: fixed, recursive, semantic; configurable size/overlap | P0 |
| FR-I7 | Parent-child chunking with small-to-big retrieval | P0 |
| FR-I8 | Document versioning; incremental reindex; hard/soft delete with index consistency | P0 |
| FR-I9 | Idempotent jobs (same content hash → no duplicate chunks) | P0 |
| FR-I10 | Retries with backoff; dead-letter queue for poison messages | P0 |

### 6.3 Indexing & retrieval

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-R1 | Dense embeddings via Sentence Transformers (configurable model + dims) | P0 |
| FR-R2 | Vector store: Qdrant with HNSW; metadata payload filters | P0 |
| FR-R3 | Sparse: Postgres full-text BM25 (field-weighted title/body where useful) | P0 |
| FR-R4 | Hybrid: dense + sparse candidate pools → RRF (and optional weighted fusion) | P0 |
| FR-R5 | Optional MMR for diversity | P1 |
| FR-R6 | Query rewriting + optional multi-query retrieval | P0 |
| FR-R7 | Rerank: bi-encoder retrieve → cross-encoder and/or XGBoost feature rerank | P0 |
| FR-R8 | Top-K and score thresholds configurable per tenant/env | P0 |
| FR-R9 | Exact-identifier / keyword boost for ticket IDs, RFC numbers, etc. | P1 |
| FR-R10 | Fallback strategy when hybrid returns weak scores (rewrite → broaden → abstain) | P0 |
| FR-R11 | Re-embedding job when embedding model version changes | P1 |
| FR-R12 | Intent router (optional): FAQ vs deep-doc vs SQL tool | P1 |

### 6.4 Context construction & generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-G1 | Context window budgeter (token-aware packing) | P0 |
| FR-G2 | Ordering strategy that mitigates lost-in-the-middle | P0 |
| FR-G3 | Prompt templates enforce “answer only from context” + citation format | P0 |
| FR-G4 | Citation attribution: answer spans map to `doc_id` + `chunk_id` (+ page if available) | P0 |
| FR-G5 | Abstain when evidence insufficient (configurable confidence/retrieval thresholds) | P0 |
| FR-G6 | Handle conflicting/stale sources (prefer newest version; surface conflict note) | P1 |
| FR-G7 | Streaming responses (SSE) with late citation validation | P1 |
| FR-G8 | Optional contextual compression before generation | P1 |

### 6.5 Evaluation & experimentation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-E1 | Golden dataset: questions, relevance judgments (chunk ids), optional reference answers | P0 |
| FR-E2 | Retrieval metrics: Recall@K, Precision@K, Hit Rate, MRR, nDCG@K | P0 |
| FR-E3 | Generation metrics: faithfulness, answer relevance, context relevance, citation accuracy | P0 |
| FR-E4 | Support RAGAS / DeepEval + custom deterministic graders | P1 |
| FR-E5 | LLM-as-judge with calibration notes and known limitations documented | P1 |
| FR-E6 | Ablation harness: dense-only vs hybrid vs hybrid+rerank | P0 |
| FR-E7 | CI regression gate on main (fail if metric drops beyond threshold) | P0 |
| FR-E8 | Error attribution report: retrieval miss vs generation failure | P0 |

### 6.6 Security & governance

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-S1 | Input guardrails: prompt injection detection on user query | P0 |
| FR-S2 | Treat retrieved content as untrusted; resist indirect injection | P0 |
| FR-S3 | PII detection/redaction hooks on ingest and optional on logs | P1 |
| FR-S4 | Adversarial eval suite (injection, filter bypass attempts) | P1 |
| FR-S5 | Retention/deletion APIs keep Postgres + Qdrant + cache consistent | P0 |

### 6.7 Production platform

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-P1 | Redis cache: embeddings, retrieval results, optional response/semantic cache | P0 |
| FR-P2 | Cache invalidation on document change/delete | P0 |
| FR-P3 | OpenTelemetry traces spanning ask + ingest stages | P0 |
| FR-P4 | Metrics: latency (p50/p95), token cost/request, retrieval scores, error rates | P0 |
| FR-P5 | Timeouts + circuit breakers around LLM and embedding providers | P0 |
| FR-P6 | Graceful degradation: e.g. skip rerank / return retrieval-only on LLM outage | P1 |
| FR-P7 | Config via env + versioned YAML (no secrets in git) | P0 |
| FR-P8 | Docker Compose local prod-like stack | P0 |

### 6.8 Advanced (v1.1 / M8)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-X1 | LangGraph agentic RAG: iterative retrieve / tools / HITL checkpoint | P1 |
| FR-X2 | Multi-hop QA for questions needing 2+ evidence hops | P1 |
| FR-X3 | Structured SQL RAG for one demo relational dataset | P2 |
| FR-X4 | Spike only: CRAG or Self-RAG or GraphRAG lite | P2 |

---

## 7. Non-functional requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Latency | p95 ask (excluding cold model load) target **≤ 8s** local/demo with streaming first token **≤ 2s** when LLM streams |
| NFR-2 | Ingest SLA | Small doc (≤20 pages) searchable within **≤ 60s** of upload under nominal load |
| NFR-3 | Availability | Local Compose: documented restart behavior; API health + readiness probes |
| NFR-4 | Scale (design) | Architecture doc explains path to **millions of chunks** (sharding, HNSW params, async workers) even if demo corpus is small |
| NFR-5 | Security | Automated tests prove no cross-tenant retrieval |
| NFR-6 | Cost | Per-request token + embedding cost logged and attributable by tenant |
| NFR-7 | Quality | Hybrid+rerank beats dense-only on golden nDCG@10 / MRR (document delta in README) |
| NFR-8 | Maintainability | Typed Python, Pydantic schemas, pytest coverage on critical paths |
| NFR-9 | Observability | One trace id per ask; spans: rewrite, dense, sparse, fusion, rerank, generate |

---

## 8. System architecture

### 8.1 Logical architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│ Clients: Next.js (web) / curl / eval runner                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ JWT / API key
┌─────────────────────────────▼───────────────────────────────────┐
│ Atlas API (FastAPI)                                             │
│  auth · rate limit · validation · SSE                           │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
     ┌──────────▼──────────┐       ┌──────────▼──────────┐
     │ Ask Orchestrator    │       │ Ingest API          │
     │ (LangGraph)         │       │ enqueue job         │
     │ rewrite → retrieve  │       └──────────┬──────────┘
     │ → fuse → rerank     │                  │
     │ → budget → generate │       ┌──────────▼──────────┐
     │ → cite / abstain    │       │ Workers             │
     └──────────┬──────────┘       │ parse→chunk→embed   │
                │                  │ → index → invalidate│
                │                  └──────────┬──────────┘
     ┌──────────▼─────────────────────────────▼──────────┐
     │ Data plane                                         │
     │ Postgres (docs, chunks, BM25, jobs, ACL, audits)   │
     │ Qdrant (dense vectors + payload filters)           │
     │ Redis (queue, cache)                               │
     │ Object store (local MinIO/S3) for raw files        │
     └───────────────────────┬────────────────────────────┘
                             │
     ┌───────────────────────▼────────────────────────────┐
     │ Cross-cutting: Guardrails · OTel · Evals · Config  │
     └────────────────────────────────────────────────────┘
```

### 8.2 Ask path (online)

1. Authenticate → resolve tenant/user/ACL context  
2. Input guardrails  
3. Query rewrite (and optional multi-query)  
4. Parallel: dense ANN (filtered) + BM25 (filtered)  
5. Fuse (RRF) → optional MMR → rerank  
6. Build context (budget, order, compress)  
7. Generate with citation schema  
8. Output checks → stream/return  
9. Log metrics/feedback; cache safe results  

### 8.3 Ingest path (offline / async)

1. Accept upload → store blob → enqueue idempotent job  
2. Parse (layout/OCR as needed) → clean → dedupe  
3. Extract metadata + ACL  
4. Chunk (parent-child)  
5. Embed → upsert Qdrant + Postgres FTS  
6. Bump document version; invalidate caches  
7. Emit ingest complete event / status  

### 8.4 Modular RAG framing (interview language)

| Module | Atlas component |
|--------|-----------------|
| Indexing | Workers + Postgres + Qdrant |
| Retrieval | Hybrid + rerank package |
| Augmentation / context | Context budgeter |
| Generation | LLM adapter + prompts |
| Orchestration | LangGraph |
| Evaluation | `packages/evals` + CI |
| Governance | ACL + guardrails + audit |

---

## 9. Data model (logical)

### 9.1 Core entities

**Tenant**  
`id`, `name`, `plan_limits`, `created_at`

**User**  
`id`, `tenant_id`, `roles[]`, `api_subjects`

**Document**  
`id`, `tenant_id`, `title`, `source_uri`, `content_hash`, `version`, `status` (`pending|processing|ready|failed|deleted`), `acl`, `mime_type`, `created_at`, `updated_at`

**Chunk**  
`id`, `document_id`, `tenant_id`, `parent_chunk_id?`, `text`, `token_count`, `ordinal`, `page?`, `metadata` (JSON), `acl` (denormalized), `embedding_model_version`, `content_hash`

**IngestJob**  
`id`, `tenant_id`, `document_id`, `idempotency_key`, `state`, `attempts`, `last_error`, `created_at`, `finished_at`

**AskRequest (log)**  
`id`, `tenant_id`, `user_id`, `query`, `trace_id`, `latency_ms`, `token_cost`, `retrieval_stats`, `abstained`, `citation_ids[]`

**GoldenExample**  
`id`, `query`, `relevant_chunk_ids[]`, `reference_answer?`, `tags[]`

### 9.2 Index records
- **Postgres FTS:** `chunk_id`, `tenant_id`, `title_tsv`, `body_tsv`, `acl` columns for filters  
- **Qdrant point:** vector + payload `{tenant_id, document_id, chunk_id, acl fields, version}`

---

## 10. API contracts (v1 sketch)

### 10.1 Ingest

```http
POST /v1/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data

file, title?, acl_json, metadata_json?
→ 202 { "documentId", "jobId", "status": "pending" }
```

```http
GET /v1/jobs/{jobId}
→ 200 { "jobId", "documentId", "status", "error?" }
```

```http
DELETE /v1/documents/{documentId}
→ 202 { "jobId" }  # async delete + index cleanup
```

### 10.2 Ask

```http
POST /v1/ask
{
  "query": "What is our PTO policy for contractors?",
  "topK": 8,
  "stream": false,
  "filters": { "collection": "hr" }
}
→ 200 {
  "answer": "...",
  "citations": [
    { "documentId": "...", "chunkId": "...", "title": "...", "snippet": "...", "score": 0.81 }
  ],
  "abstained": false,
  "traceId": "...",
  "diagnostics": { "rewrite": "...", "denseHits": 20, "sparseHits": 20, "fused": 30, "reranked": 8 }
}
```

```http
POST /v1/ask/stream  # SSE: tokens + final citations event
```

### 10.3 Eval (internal / admin)

```http
POST /v1/admin/evals/run
{ "suite": "golden_v1", "experiment": "hybrid_rrf_xgb" }
→ 202 { "runId" }
```

---

## 11. Tech stack

Canonical inventory (versions, gates, deferred libs): **[`TECH_STACK.md`](TECH_STACK.md)**.

| Layer | Choice | Why |
|-------|--------|-----|
| Web UI | **Next.js (App Router) + TypeScript** | Phase 1 E2E: upload, ask, citations in browser |
| API | FastAPI + Pydantic + asyncio | RAG services; UI talks only to API |
| Orchestration | LangGraph | Stateful retrieval / agentic RAG |
| Optional libs | LangChain primitives as needed | Don’t over-abstract; core stays testable |
| Dense index | Qdrant **or Upstash Vector** | Filtered ANN; Upstash also offers hybrid+RRF — [`docs/upstash_integration.md`](docs/upstash_integration.md) |
| Sparse index | PostgreSQL FTS (and/or Upstash hybrid sparse) | Hybrid + relational metadata/ACL |
| Embeddings / rerank | Sentence Transformers | Local, controllable |
| Learned rerank | XGBoost on retrieval features | M4+ when justified |
| Parsing | PyMuPDF + Docling | M2 when justified |
| Queue / cache | Redis | Jobs + caching |
| Object storage | Local volume first; MinIO optional | Raw docs |
| LLM | OpenAI-compatible (**Groq** free / **Gemini** free / Ollama) | Env-swappable; see `docs/zero_cost_showcase.md` |
| Obs | OpenTelemetry | Traces |
| Evals | Custom metrics + Ragas | CI gates |
| Tests | pytest (+ optional Playwright smoke) | Backend is quality gate; UI is demo |
| Deploy | Docker Compose (`api`, `worker`, `web`, data plane) | Reproducible local E2E |

**Principle:** Core RAG packages stay independently testable without Next.js. Next.js is a client of FastAPI only.

---

## 12. Repository structure

**Source of truth:** [`STRUCTURE.md`](STRUCTURE.md) (full production tree, boundaries, security/scale rules).

Summary:

```text
atlas/
  apps/api|worker|web     # edges (HTTP, jobs, Next.js)
  packages/*              # domain logic (testable without UI)
  configs/                # non-secret tunables
  migrations/             # Postgres schema
  tests/ + evals/         # quality gates
  deploy/docker|k8s       # images; k8s = Phase 2
  docs/adr                # decisions
```

Dependency rule: `apps → packages`; `packages ↛ apps`; `web → API only`.

---

## 13. Configuration & versioning

All runtime knobs are config-driven (no hard-coded magic numbers in business logic):

- Chunk size / overlap / strategy  
- Embedding model name + version + dims  
- Dense `top_k`, sparse `top_k`, fused `k`, rerank `k`  
- RRF `k` constant; MMR λ  
- Abstention thresholds  
- Cache TTLs  
- Timeouts / retry budgets  
- Feature flags: `enable_query_rewrite`, `enable_xgb_rerank`, `enable_agentic`

**Model/index compatibility:** store `embedding_model_version` on chunks; block ask or trigger re-embed if mismatch.

---

## 14. Evaluation plan

### 14.1 Corpus (demo)
- 200–500 documents across **3 tenants** (e.g. HR, Eng, Finance)  
- Mix: policies, runbooks, product docs, PDFs with tables  
- Artificial ACL boundaries for security tests  

### 14.2 Golden set
- 80–150 questions  
- Graded relevant `chunk_id`s  
- Tags: factual, multi-hop, identifier lookup, adversarial, unanswerable  

### 14.3 Required experiments (document results in README)
1. Dense-only  
2. Sparse-only  
3. Hybrid RRF  
4. Hybrid + cross-encoder  
5. Hybrid + cross-encoder + XGBoost  

### 14.4 CI gate (example thresholds — tune after baseline)
- nDCG@10 drop > 3% vs baseline → fail  
- Cross-tenant leakage tests must pass (hard fail)  
- Unit tests for ACL filter construction must pass  

---

## 15. Security requirements (detail)

1. **Defense in depth:** authn → authz filters at retrieve → context ACL re-check → output filtering  
2. **Never trust retrieved text** for tool execution without policy  
3. **No secrets in prompts or traces**; redact PII in logs where feasible  
4. **Adversarial cases** in golden/adversarial suite:  
   - “Ignore previous instructions…” in user query  
   - Poisoned doc instructing model to exfiltrate other tenants  
   - Metadata filter bypass attempts  

---

## 16. Observability & SLOs

| Signal | Use |
|--------|-----|
| Trace spans | rewrite, dense, sparse, rrf, rerank, budget, llm |
| Latency histograms | p50/p95 ask; ingest job duration |
| Quality proxies | retrieval score distributions; abstain rate; thumbs feedback (optional) |
| Cost | input/output tokens, embedding calls, $/request |
| Errors | LLM 5xx, timeouts, DLQ depth |

**Demo SLOs (local):**  
- Ask availability (process up) ≥ 99% during demo window  
- Ingest success rate ≥ 95% for supported formats  
- DLQ investigated within same study session when non-empty  

---

## 17. Success metrics (product + learning)

### 17.1 Product
- [ ] Hybrid+rerank wins on nDCG@10 and MRR vs dense-only  
- [ ] 0 cross-tenant leaks in test suite  
- [ ] Update/delete freshness demonstrated  
- [ ] p95 latency profiled with bottlenecks named  
- [ ] CI eval gate green on main  

### 17.2 Learning (topics.md)
- [ ] All ★★★ topics have a code path **or** ADR explaining the decision  
- [ ] All ★★ topics have a short note in `docs/` or inline design comment  
- [ ] ★ topics: 2–3 spikes max (agentic + one other)  
- [ ] Interview talk track answers scenarios 111–120 using Atlas as the system  

---

## 18. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope explosion (all 120 equally deep) | Never finishes | Depth ratings; M8 selective |
| LLM API cost | Budget burn | Caching, small models for rewrite/judge, local embeddings |
| Parsing quality variance | Bad chunks → bad RAG | Start PDF+MD; add OCR later; measure retrieval misses |
| Hybrid tuning rabbit hole | Time sink | Freeze configs after ablation doc |
| LangChain abstraction soup | Hard to explain | Prefer thin LangGraph + own retrieval package |
| Fake “multi-tenant” | Interview fail | Enforce filters in both indexes + tests |

---

## 19. Timeline

### Phase 1 — suggested 4 weeks (RAG)

| Week | Focus | Exit criteria |
|------|-------|---------------|
| 1 | M0–M3 | Naive RAG + real ingest + dual indexes |
| 2 | M4–M5 | Hybrid+rerank+citations+abstain |
| 3 | M6–M7 | Evals in CI + ACL + async prod hardening |
| 4 | M8 + polish | Selective advanced + interview docs + latency pass |

Priority stays **M1→M7 before advanced spikes**.

### Phase 2 — after Phase 1 exit (layer upgrades)

| Wave | Layers | Exit criteria |
|------|--------|---------------|
| W1 | L6 Gateway, L2 Orchestration | Multi-provider/failover story; real agent runtime path |
| W2 | L5 Guardrails, L8 Obs/Evals | Stronger rails; online eval + feedback→eval loop |
| W3 | L11 DevOps, L9 Security, L10 Infra | CI/CD + hardened security + deploy story |
| W4 | L12 HITL, L1 Channels, L7 Model | Feedback ops, extra channels, FT-vs-RAG demo note |

---

## 20. Interview talk track (required artifact)

Deliverable: `docs/interview_talk_track.md` covering:

1. End-to-end architecture (2 min)  
2. Why hybrid + RRF + rerank (2 min)  
3. ACL enforcement design (1 min)  
4. Eval metrics and one ablation result (2 min)  
5. Debug story: high recall, bad answers (1.5 min)  
6. Debug story: missing relevant docs (1.5 min)  
7. Latency/cost knobs (1 min)  
8. Trade-offs vs fine-tuning / long-context (1 min)  

This maps directly to topics **111–120**.

---

## 21. Open questions

| # | Question | Default for v1 |
|---|----------|----------------|
| OQ1 | Which LLM for ₹0 showcase? | **Decided:** Groq free tier primary, Gemini free backup, Ollama offline — see [`docs/zero_cost_showcase.md`](docs/zero_cost_showcase.md) |
| OQ2 | OpenSearch vs Postgres FTS for BM25? | Postgres FTS first (simpler Compose) |
| OQ3 | Cross-encoder model choice? | Small ST cross-encoder; document in `models.yaml` |
| OQ4 | UI scope? | **Decided:** thin Next.js in Phase 1 (ask + upload + citations); see `TECH_STACK.md` |
| OQ5 | Real MinIO vs local filesystem? | Local FS first; S3 interface abstracted |

---

## 22. Acceptance checklist (PRD done → build)

- [x] Problem, goals, non-goals defined  
- [x] Personas and use cases defined  
- [x] Functional + non-functional requirements listed  
- [x] Architecture and data model sketched  
- [x] API contracts sketched  
- [x] Stack and repo layout chosen  
- [x] Milestones mapped to 120 topics  
- [x] Eval, security, and SLO plans defined  
- [x] Phase 1 vs Phase 2 strategy documented  
- [x] Layer thin/deep upgrade map documented  
- [x] Milestone definitions of done documented  
- [x] Learning loop (feature → topics.md → test) documented  
- [ ] M0 scaffold implemented (next engineering step)  

---

## 23. Appendix — Topic → milestone map

| Topics.md section | Milestone |
|-------------------|-----------|
| 1. Fundamentals 1–10 | M1 |
| 2. Ingestion 11–20 | M2 |
| 3. Embeddings & indexes 21–30 | M3 |
| 4. Retrieval 31–40 | M4 |
| 5. Hybrid 41–50 | M4 |
| 6. Context & generation 51–60 | M5 |
| 7. Advanced 61–70 | M8 (selective) |
| 8. Evaluation 71–80 | M6 |
| 9. Security 81–90 | M7 |
| 10. Production 91–100 | M7 |
| 11. Python tooling 101–110 | M0–M7 continuous |
| 12. System design 111–120 | M8 + talk track |

Phase 2 does **not** remap the 120 RAG topics; it deepens architecture layers around the Phase 1 RAG core. New ADRs live under `docs/adr/phase2_L{n}_*.md`.

---

## 24. Approval

| Role | Name | Decision |
|------|------|----------|
| Product / learner | Soumyo | ☐ Approve Phase 1 → implement M0 |
| Eng lead (self) | Soumyo | ☐ Freeze non-goals NG1–NG8 for Phase 1 |
| Phase 2 gate | Soumyo | ☐ Only start after Phase 1 exit checklist |

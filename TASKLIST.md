# Atlas — High-Level End-to-End Task List

> Master checklist for Phase 1 (RAG + Next.js) and Phase 2 (architecture layer upgrades).  
> Details: [`PRD.md`](PRD.md) · [`STRUCTURE.md`](STRUCTURE.md) · [`TECH_STACK.md`](TECH_STACK.md) · [`docs/skills_usage_guide.md`](docs/skills_usage_guide.md)

| Field | Value |
|-------|-------|
| **Status** | Not started (pre-M0) |
| **Portfolio ready** | End of **Phase 1** when M0–M7 ✅ |
| **Interview max** | M8 + talk track |
| **Every milestone** | Follow learning loop below before moving on |

---

## How to use this list

For **each** milestone slice:

1. Read 3–5 questions — [`../Questions_RAG_120.md`](../Questions_RAG_120.md) + [`docs/code_explain_loop.md`](docs/code_explain_loop.md)  
2. Pick skills — [`docs/skills_usage_guide.md`](docs/skills_usage_guide.md)  
3. Implement + test  
4. Explain out loud (Atlas-based interview card)  
5. Tick [`../topics.md`](../topics.md)  
6. Check milestone DoD in PRD §5c  
7. Only then advance  

**Rule:** Atlas docs win over generic skill defaults. Keep RAG logic in `packages/*`.

---

## Progress overview

| Phase | Block | Status |
|-------|-------|--------|
| 0 | Prep & scaffold | ☐ |
| 1 | M0 Foundations | ☐ |
| 1 | M1 Naive RAG | ☐ |
| 1 | M2 Ingestion & chunking | ☐ |
| 1 | M3 Indexes | ☐ |
| 1 | M4 Hybrid + rerank | ☐ |
| 1 | M5 Context & generation | ☐ |
| 1 | M6 Evaluation | ☐ |
| 1 | M7 Security & production | ☐ |
| 1 | M8 Advanced + interview | ☐ |
| 1 | Phase 1 exit gate | ☐ |
| 2 | Layer upgrades (L6→…→L7) | ☐ |

---

## Phase 0 — Prep (before coding)

- [ ] Read PRD §1–5c, STRUCTURE, TECH_STACK, zero_cost_showcase  
- [ ] Copy `.env.example` → `.env`; set Groq (or Gemini) key  
- [ ] Copy `apps/web/.env.example` → `apps/web/.env.local`  
- [ ] Confirm skills installed (`docs/skills_usage_guide.md`)  
- [ ] Run `bash scripts/scaffold_structure.sh` if tree incomplete  
- [ ] Decide data plane default: `ATLAS_DATA_PLANE=local` (recommended)

---

## Phase 1 — RAG product (M0–M8)

### M0 — Foundations
**Topics:** 101–102, 110 · **Skills:** `fastapi`, `fastapi-templates`, `multi-stage-dockerfile`, `tdd`

- [ ] Root `pyproject.toml` + package path installs (`atlas_*`)  
- [ ] `packages/common` config (env + YAML)  
- [ ] Docker Compose: postgres, qdrant, redis, api, worker, web  
- [ ] `deploy/docker/*` multi-stage Dockerfiles  
- [ ] FastAPI `/health` + `/ready`  
- [ ] Worker process starts and heartbeats / idle OK  
- [ ] Next.js shell loads; can call API health  
- [ ] `.env` wired; secrets not committed  
- [ ] README runbook: `make up` / compose up, test smoke  
- [ ] pytest smoke for health  
- [ ] **DoD:** Compose healthy; packages importable; web→API health  
- [ ] **Explain:** Q101–Q102, Q110  

---

### M1 — Naive RAG
**Topics:** 1–10 · **Skills:** `rag-implementation`, `langgraph-fundamentals`, `fastapi`

- [ ] Minimal ingest: one PDF → chunks → embed → store  
- [ ] Naive retrieve top-K → LLM answer (Groq/Gemini adapter)  
- [ ] LangGraph linear ask graph (v0)  
- [ ] API `POST /v1/documents` + `POST /v1/ask` (sync)  
- [ ] Next.js: upload + ask happy path  
- [ ] Document naive vs advanced limitations in ADR/note  
- [ ] **DoD:** PDF→answer via API and UI  
- [ ] **Explain:** Q1–Q10  

---

### M2 — Ingestion & chunking
**Topics:** 11–20, 108 · **Skills:** `fastapi`, `async-python-patterns`, `tdd`

- [ ] Async ingest job queue (Redis local)  
- [ ] Job status API + UI polling  
- [ ] Parsers: PDF (+ MD); HTML/DOCX as needed  
- [ ] Cleaning, dedupe, metadata schema  
- [ ] Chunk strategies: recursive + parent-child  
- [ ] Versioning + delete + reindex path  
- [ ] Idempotent jobs + basic retries  
- [ ] **DoD:** Multi-format ingest; parent-child persisted; version/delete works  
- [ ] **Explain:** Q11–Q20  

---

### M3 — Indexes (dense + sparse)
**Topics:** 21–30, 105, 107 · **Skills:** `qdrant-clients-sdk`, `rag-implementation`

- [ ] Qdrant collection + payload (tenant, ACL, version)  
- [ ] Dense embed + upsert + filtered ANN  
- [ ] Postgres FTS / BM25-style sparse search  
- [ ] Store `embedding_model_version` on chunks  
- [ ] Re-embed job stub / migration note  
- [ ] **DoD:** Dense + sparse filtered queries work  
- [ ] **Explain:** Q21–Q30  

---

### M4 — Hybrid retrieval + rerank
**Topics:** 31–50, 106 · **Skills:** `rag-implementation`, `langgraph-fundamentals`, `async-python-patterns`

- [ ] Parallel dense + sparse retrieve  
- [ ] RRF fusion (+ optional MMR)  
- [ ] Query rewrite (feature-flagged)  
- [ ] Cross-encoder rerank  
- [ ] Optional XGBoost rerank (after CE baseline)  
- [ ] Fallback when scores weak  
- [ ] Ablation script: dense vs sparse vs hybrid vs hybrid+rerank  
- [ ] **DoD:** Hybrid+rerank live; ablation numbers recorded  
- [ ] **Explain:** Q31–Q50  

---

### M5 — Context engineering & generation
**Topics:** 51–60 · **Skills:** `rag-implementation`, `langgraph-fundamentals`

- [ ] Context budgeter (tiktoken)  
- [ ] Ordering / lost-in-the-middle mitigation  
- [ ] Citation-required prompts + citation objects  
- [ ] Abstain when evidence insufficient  
- [ ] Conflict/stale source handling (prefer newest version)  
- [ ] Optional SSE streaming + Next.js render  
- [ ] Next.js shows citations / abstain clearly  
- [ ] **DoD:** Cited or abstained only; UI shows citations  
- [ ] **Explain:** Q51–Q60  

---

### M6 — Evaluation & CI
**Topics:** 71–80, 109 · **Skills:** `llm-evaluation`, `python-testing-patterns`, `tdd`

- [ ] Golden set + qrels (40–80 Qs, 3 tenants)  
- [ ] Retrieval metrics: Recall@K, Precision@K, Hit Rate, MRR, nDCG@K  
- [ ] Generation metrics: faithfulness / relevance (Ragas or custom; quota-aware)  
- [ ] Error attribution helper (retrieve vs generate)  
- [ ] Ablation report in README  
- [ ] CI workflow: unit + eval gate (fail on nDCG drop)  
- [ ] **DoD:** Suite runs; CI regression gate green  
- [ ] **Explain:** Q71–Q80  

---

### M7 — Security & production engineering
**Topics:** 81–100 · **Skills:** `async-python-patterns`, `python-testing-patterns`, `multi-stage-dockerfile`

- [ ] Multi-tenant + doc ACL on **both** dense and sparse paths  
- [ ] Cross-tenant leakage tests (hard fail)  
- [ ] Input + retrieved-text injection checks  
- [ ] Audit log for ask/ingest  
- [ ] Redis cache (embed/retrieval/response) + invalidation on doc change  
- [ ] Timeouts, retries, DLQ path for ingest  
- [ ] OpenTelemetry traces (rewrite→retrieve→rerank→llm)  
- [ ] Cost/token logging per request  
- [ ] Graceful degradation notes (skip rerank / abstain)  
- [ ] **DoD:** ACL tests pass; cache invalidation demo; traces+cost visible  
- [ ] **Explain:** Q81–Q100  

---

### M8 — Advanced spikes + interview polish
**Topics:** 61–70 (selective), 103–104, 111–120 · **Skills:** `langgraph-persistence`, `langgraph-fundamentals`, `rag-implementation`

- [ ] Agentic / multi-hop RAG spike (LangGraph) **or** one other advanced pattern  
- [ ] Optional: SQL structured RAG demo (small)  
- [ ] Skip GraphRAG/RAPTOR/audio unless needed (★ only)  
- [ ] Write `docs/interview_talk_track.md` (Q111–Q120)  
- [ ] Rehearse 10-min architecture + 3 debug stories  
- [ ] README: architecture diagram, ablation table, ₹0 stack note  
- [ ] **DoD:** ≤2 spikes; talk track complete; scenarios explainable  
- [ ] **Explain:** Q61–Q70 (chosen), Q111–Q120  

---

## Phase 1 exit gate (portfolio / interview ready)

- [ ] M0–M7 DoD all met  
- [ ] Hybrid+rerank > dense-only on golden nDCG@10 / MRR (numbers published)  
- [ ] `topics.md` ★★★ / ★★ mostly ticked (code or ADR)  
- [ ] Cross-tenant tests green  
- [ ] Interview talk track rehearsed once  
- [ ] Demo script: 5–10 questions (respect Groq/Gemini quotas)  
- [ ] Phase 2 first layer chosen  

---

## Phase 2 — Architecture layer upgrades (same repo)

Order (from PRD): **L6 → L2 → L5 → L8 → L11 → L9 → L10 → L12 → L1 → L7**

### W1
- [ ] **L6 LLM Gateway** — routing, failover, multi-cache, multi-provider  
- [ ] **L2 Orchestration** — planner, tools, memory, HITL checkpoints  

### W2
- [ ] **L5 Guardrails** — fuller in/out rails, PII, policy engine  
- [ ] **L8 Obs/Evals** — online evals, feedback→eval loop  

### W3
- [ ] **L11 DevOps** — progressive delivery, scans, stronger CI  
- [ ] **L9 Security** — zero-trust hardening, retention/compliance  
- [ ] **L10 Infra** — K8s-lite / cloud deploy story  

### W4
- [ ] **L12 HITL** — review queue / lightweight improvement loop  
- [ ] **L1 Channels** — Slack/Teams or richer admin  
- [ ] **L7 Model** — selection matrix; optional FT vs RAG demo note  

### Optional anytime in Phase 2
- [ ] Upstash mode adapters (`docs/upstash_integration.md`) if not done in Phase 1  
- [ ] ADR per layer upgrade under `docs/adr/phase2_L{n}_*.md`  

---

## Cross-cutting tasks (track continuously)

- [ ] Keep `.env.example` in sync with real env vars  
- [ ] Update TECH_STACK version pins when deps settle  
- [ ] One ADR per non-obvious trade-off  
- [ ] No secrets in git (`scripts/check_no_secrets.sh`)  
- [ ] Prefer local embeddings; protect LLM free-tier quotas  
- [ ] After each milestone: voice answers for question pack  

---

## Suggested calendar (flexible)

| Week | Focus |
|------|-------|
| 1 | Phase 0 + M0–M3 |
| 2 | M4–M5 |
| 3 | M6–M7 |
| 4 | M8 + Phase 1 exit + interview rehearsal |
| Later | Phase 2 waves |

---

## Definition of “project complete”

| Level | Criteria |
|-------|----------|
| **Showcase complete** | Phase 1 exit gate ✅ + working Next.js demo |
| **Interview complete** | Showcase + talk track + Q111–Q120 cold |
| **Architecture complete** | Phase 2 waves done (or consciously deferred with ADRs) |

---

## Related docs

| Doc | Role |
|-----|------|
| [`PRD.md`](PRD.md) | Requirements & DoD |
| [`TASKLIST.md`](TASKLIST.md) | This file — execution checklist |
| [`../topics.md`](../topics.md) | Learning coverage |
| [`../Questions_RAG_120.md`](../Questions_RAG_120.md) | Interview questions |
| [`docs/skills_usage_guide.md`](docs/skills_usage_guide.md) | Which skill when |
| [`docs/zero_cost_showcase.md`](docs/zero_cost_showcase.md) | ₹0 / Groq-Gemini path |
| [`docs/upstash_integration.md`](docs/upstash_integration.md) | Optional serverless data plane |

# Atlas — ₹0 (Zero-Cost) Showcase Guide

> Build and demo a production-**shaped** hybrid RAG system at **₹0** for portfolio and interviews.  
> Companions: [`../PRD.md`](../PRD.md) · [`../TECH_STACK.md`](../TECH_STACK.md) · [`../STRUCTURE.md`](../STRUCTURE.md)

| Field | Value |
|-------|-------|
| **Goal** | Full local E2E: upload → hybrid retrieve → cite/abstain → Next.js demo |
| **Budget** | ₹0 (free-tier LLM APIs + local infra) |
| **Default LLM** | **Groq free tier** (primary) · **Gemini free tier** (backup) |
| **Offline fallback** | Ollama (optional) |
| **Honest framing** | “Prod-shaped on Docker Compose + free-tier LLM,” not “unlimited multi-region SaaS” |

---

## 1. Can you do it for free?

**Yes.**

- **Infra** (Postgres, Qdrant, Redis, API, worker, Next.js, embeddings, rerank): local Docker / laptop — ₹0  
- **LLM generation**: [Groq](https://console.groq.com) and/or [Google AI Studio / Gemini](https://aistudio.google.com) **free tiers** — ₹0 within quotas  
- Keys live only in `.env` — never commit them  

Spend money only later if you want a public hosted demo or higher rate limits.

---

## 2. Free stack map

| Piece | ₹0 choice | Notes |
|-------|-----------|-------|
| Compute / Compose | Laptop + Docker | api, worker, web, postgres, qdrant, redis |
| Embeddings | Sentence Transformers (local) | Keep embeddings local — don’t burn LLM quota |
| Rerank | Local cross-encoder | Same reason |
| **LLM (default)** | **Groq free tier** | OpenAI-compatible; very fast |
| **LLM (backup)** | **Gemini free tier** | OpenAI-compatible endpoint; swap via env |
| LLM (offline) | Ollama | When no network / quota exhausted |
| Evals | Custom nDCG/MRR + light Ragas | Don’t run huge LLM-judge sweeps on free tier |
| Observability | OpenTelemetry → console | Skip paid LangSmith |
| Object storage | `./data/raw` | Local disk |
| Data plane (optional) | **Upstash** Redis + Vector + QStash free tier | Serverless alt to Docker Redis/Qdrant — see [`upstash_integration.md`](upstash_integration.md) |

---

## 3. Provider strategy

```text
Primary:  Groq free tier   → fast chat for /ask demos
Backup:   Gemini free tier → when Groq rate-limits or model unavailable
Fallback: Ollama local     → offline / demos without internet
```

Use one OpenAI-compatible client in `packages/generation`. Switching providers = change env vars only.

| Provider | Base URL | Env key | Docs |
|----------|----------|---------|------|
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` → map to `OPENAI_API_KEY` or dedicated | [OpenAI compatibility](https://console.groq.com/docs/openai) |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Google AI OpenAI-compatible API |
| Ollama | `http://localhost:11434/v1` | any placeholder | Local |

**Atlas convention:** set `LLM_BASE_URL` + `OPENAI_API_KEY` + `LLM_MODEL` (adapter reads these three).

---

## 4. Setup — Groq (primary)

1. Create account at [console.groq.com](https://console.groq.com) (free plan; no card required for basic free tier).  
2. Create an API key.  
3. Put it in local `.env` only.

```bash
LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_your_groq_key_here
# Pick a model currently listed on your Groq console / models page.
# Free-tier catalogs change — verify in console before demos.
LLM_MODEL=openai/gpt-oss-20b
```

**Quota hygiene (important for showcase):**

- Free tiers are limited (RPM / requests-per-day / tokens-per-day). Check [Groq rate limits](https://console.groq.com/docs/rate-limits) for your plan/model.  
- Cache retrieval + avoid re-generating the same demo questions.  
- Run evals with **small** golden sets; prefer non-LLM retrieval metrics for CI.  
- Don’t parallel-spam `/ask` during development.

---

## 5. Setup — Gemini (backup)

1. Get an API key from [Google AI Studio](https://aistudio.google.com).  
2. Switch env when Groq is throttling:

```bash
LLM_PROVIDER=gemini
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.0-flash
```

Confirm the exact free-tier model id in AI Studio if names change (`gemini-2.0-flash`, `gemini-1.5-flash`, etc.).

---

## 6. Full `.env` example (Groq default)

See also [`../.env.example`](../.env.example).

```bash
ATLAS_ENV=development
ATLAS_JWT_SECRET=change-me-in-local-only
DATABASE_URL=postgresql+psycopg://atlas:atlas@localhost:5432/atlas
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
OBJECT_STORE_PATH=./data/raw

LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_your_groq_key_here
LLM_MODEL=openai/gpt-oss-20b

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
NEXT_PUBLIC_ATLAS_API_URL=http://localhost:8000
```

**Gemini switch** (comment Groq block, uncomment):

```bash
# LLM_PROVIDER=gemini
# LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
# OPENAI_API_KEY=your_gemini_api_key_here
# LLM_MODEL=gemini-2.0-flash
```

**Ollama offline fallback:**

```bash
# LLM_PROVIDER=ollama
# LLM_BASE_URL=http://localhost:11434/v1
# OPENAI_API_KEY=ollama
# LLM_MODEL=llama3.2:3b
```

---

## 7. Cost traps → free substitutes

| Cost trap | Do this instead |
|-----------|-----------------|
| OpenAI paid Chat API | Groq / Gemini free tier |
| OpenAI Embeddings API | Sentence Transformers **local** (save quota) |
| Cloud Postgres / Qdrant / Redis | Docker Compose |
| LangSmith / paid obs | OTel → console |
| Huge LLM-as-judge eval sweeps | Retrieval metrics first; tiny judge sample |
| GPU cloud | Not needed if LLM is remote free tier |

---

## 8. Optional: Upstash instead of local Redis/Qdrant

If you want less Docker and a serverless interview story, use **Upstash free-tier** products:

| Replace | With |
|---------|------|
| Redis container | Upstash Redis (cache) |
| Qdrant | Upstash Vector (dense or hybrid + RRF) |
| Redis job queue | QStash → worker HTTP (needs public URL/tunnel) |

Keep **Postgres** local for documents/ACL. Full design: [`upstash_integration.md`](upstash_integration.md).

---

## 9. Hardware reality check

With Groq/Gemini for chat, laptop mainly runs Compose + embeddings/rerank:

| RAM | Practical choice |
|-----|------------------|
| 8 GB | MiniLM embeddings, small corpus, careful Docker limits |
| 16 GB | Comfortable Compose + ST embed/rerank + ~200–500 docs |
| 32 GB+ | Easy headroom for evals |

You no longer need large local LLM VRAM unless using Ollama fallback.

---

## 10. Showcase corpus (keep it small)

- **3 fake tenants** (HR / Eng / Finance)  
- **~50–200 documents**  
- **40–80 golden questions**  

Small corpus = fewer LLM calls during demos and evals → stay inside free quotas.

---

## 11. What “done for showcase” means (₹0 bar)

- [ ] Compose stack up (api, worker, web, postgres, qdrant, redis)  
- [ ] Groq (or Gemini) key in `.env`; `/ask` returns cited or abstained answer  
- [ ] Can switch Groq ↔ Gemini by env only (document in README)  
- [ ] Embeddings/rerank stay local (no paid embed API)  
- [ ] Hybrid (+ rerank) beats dense-only on a small golden set  
- [ ] Cross-tenant test passes  
- [ ] Interview talk includes free-tier limits + caching/fallback story  

---

## 12. Free-tier operating rules (don’t get burned mid-demo)

1. **Cache** retrieval results and repeated demo Q&A when safe.  
2. **Script the demo** — 5–10 known questions, not open-ended load tests.  
3. **Backoff** on 429; surface a friendly “rate limited, try Gemini/Ollama” path.  
4. **Never** commit keys; rotate if leaked.  
5. **Re-check model ids** before interviews — free catalogs change (e.g. Groq model list).  
6. Keep **CI evals** mostly non-LLM (nDCG/MRR); optional 5-question LLM smoke only.

---

## 13. How to talk about it in interviews

**Good:**

> “Infra is local Compose — Postgres BM25, Qdrant, Sentence Transformers. Generation uses an OpenAI-compatible adapter pointed at Groq’s free tier, with Gemini as backup and Ollama offline. I design for rate limits, caching, and provider swap without rewriting the RAG core.”

**Avoid:**

> Claiming unlimited production traffic on free tier, or implying you fine-tune Groq/Gemini models.

---

## 14. Phase 2 / later (optional spend)

| Spend | Why |
|-------|-----|
| Paid Groq/Gemini / OpenAI credits | Higher RPM for public demo |
| Cheap VPS | Hosted link for recruiters |
| Domain | Nicer URL |

Not required if local + GitHub + metrics README are solid.

---

## 15. Decision log

| Date | Decision |
|------|----------|
| 2026-10-03 | Initial default = Ollama local |
| 2026-10-03 | **Updated default = Groq free tier primary, Gemini free tier backup; Ollama offline fallback** |
| 2026-10-03 | Embeddings/rerank stay local to protect free-tier quotas |
| 2026-10-03 | Adapter stays OpenAI-compatible (`LLM_BASE_URL` + `OPENAI_API_KEY` + `LLM_MODEL`) |
| 2026-10-03 | Optional Upstash Redis / Vector / QStash data plane documented |

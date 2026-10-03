# Code → Explain Loop (Interview Prep While Building Atlas)

Use this every coding session. Goal: **ship a feature and be able to teach it in an interview the same day.**

Sources:
- Topics: [`../../topics.md`](../../topics.md)
- **Primary questions (full RAG):** [`../../Questions_RAG_120.md`](../../Questions_RAG_120.md) — Q# = topic #
- Stack / libs tracker: [`../TECH_STACK.md`](../TECH_STACK.md) (includes Next.js Phase 1)
- Broader AI Eng (optional): [`../../../Questions_Set_1.md`](../../../Questions_Set_1.md)
- Talk track (later): `interview_talk_track.md`

---

## Daily ritual (60–90 min code + 15–20 min explain)

```text
1. Pick ONE milestone slice (e.g. M2 parent-child chunking)
2. Read 3–5 related interview questions BEFORE coding
3. Implement the slice in Atlas
4. Out loud (or voice note): answer those questions using YOUR code paths
5. Write a 5–8 line "Interview card" in the section below / in a note
6. Tick topics.md rows you can now explain
7. Commit / stop — don’t stack unexplained features
```

**Rule:** If you can’t explain it in 60–90 seconds with a concrete Atlas example, you’re not done with that slice.

---

## Answer template (use every time)

For each question, fill this mentally or in notes:

1. **Definition** (1 sentence)  
2. **Why it matters in production** (1 sentence)  
3. **How Atlas does it** (file/module + flow)  
4. **Trade-off** (what you didn’t choose and why)  
5. **Failure mode + how you’d detect it** (metric/trace)

Example (chunking):

> Chunking splits docs into retrieval units. Too large → noisy context; too small → broken meaning. Atlas uses recursive + parent-child so we retrieve small children then expand parents. We rejected pure fixed-size for policies with headings. Failure: answer cites wrong section → check chunk boundaries + nDCG drop.

---

## Milestone → interview questions map

Question IDs refer to **[`Questions_RAG_120.md`](../../Questions_RAG_120.md)** (same numbers as `topics.md`).

| Milestone | Before coding (read) | After coding (must explain cold) | Topics |
|-----------|----------------------|----------------------------------|--------|
| **M0** Foundations | Q101–Q102, Q110 | Compose, FastAPI contracts, secrets/config | 101–102, 110 |
| **M1** Naive RAG | Q1–Q10 | Lifecycle, naive vs advanced, RAG vs FT | 1–10 |
| **M2** Ingest & chunk | Q11–Q20 | Parse, chunking, parent-child, versioning | 11–20 |
| **M3** Indexes | Q21–Q30 | Embeddings, ANN/HNSW, filters, Postgres FTS | 21–30 |
| **M4** Hybrid + rerank | Q31–Q50 | BM25, RRF, rerank, hybrid tuning, fallbacks | 31–50 |
| **M5** Context & gen | Q51–Q60 | Budget, lost-in-middle, citations, abstain | 51–60 |
| **M6** Evals | Q71–Q80 | nDCG/MRR, faithfulness, ablations, attribution | 71–80 |
| **M7** Security & prod | Q81–Q100 | ACL, injection, cache, traces, SLOs | 81–100 |
| **M8** Design polish | Q61–Q70 (selective), Q111–Q120 | Agentic spike + design/debug scenarios | 61–70, 111–120 |

---

## Per-session checklist (copy into your notes)

```md
### Session: M? — <feature>
Date:

Questions read:
- Q?
- Q?
- Q?

What I built:
- 

Interview cards (60–90s each):
1. Q?: ...
2. Q?: ...
3. Q?: ...

Atlas pointers (path / function):
- 

topics.md ticked:
- 

Blind spot / follow-up:
-
```

---

## Weekly interview drills (separate from feature work)

| Day | Drill | Time |
|-----|-------|------|
| End of each milestone | 5 questions closed-book, voice answers | 25 min |
| Once / week | Whiteboard Atlas ask + ingest paths | 20 min |
| Once / week | Debug prompt: “high recall, bad answers” *or* “relevant docs missing” | 15 min |
| Phase 1 exit | Full Q91 walkthrough + ablation numbers | 15 min |

Record yourself once per week. If you say “basically…” without a metric or component name, rewrite the card.

---

## What *not* to do

- Don’t binge all 120 topics before coding  
- Don’t only read Answers_Set_*.md without tying to Atlas  
- Don’t implement M4 hybrid before you can explain M1–M3 flows  
- Don’t skip abstention/evals — interviewers probe failure modes hard  

---

## Minimal “always ready” set (memorize with Atlas examples)

Even mid-project, keep these sharp (`Questions_RAG_120.md`):

1. Q3 — RAG vs fine-tuning vs long-context  
2. Q1 / Q10 — lifecycle  
3. Q41–Q43 — hybrid + RRF  
4. Q36 — bi-encoder vs cross-encoder rerank  
5. Q17–Q19 — chunking + parent-child  
6. Q73–Q74 — Recall@K / MRR / nDCG  
7. Q54 / Q57 — citation + abstain  
8. Q82–Q84 — ACL on both indexes  
9. Q94–Q95 — cache + invalidation  
10. Q80 / Q116 — error attribution / debug

---

## Link back to PRD learning loop

This file is the interview half of PRD §5a:

`implement → explain (this file) → tick topics.md → add test/eval → next slice`

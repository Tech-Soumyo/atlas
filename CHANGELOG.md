# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Naive PDF to answer API loop: upload PDFs, poll ingest jobs, ask over explicit `document_ids` with citations or abstain (see spec 0001)
- Async ingest on the `arq` worker with recursive character chunking, MiniLM embeddings, and Qdrant Cosine collection `atlas_chunks`
- Postgres persistence for documents, chunks, jobs, asks, and ask document links (Alembic migration `20261003_0001`)
- Shared `X-API-Key` auth and per IP rate limits on upload and ask POSTs
- ADR `docs/adr/0001_naive_vs_advanced_rag.md` and M1 interview card stub for naive versus advanced limits
- Unit and integration tests for upload branches, ask validation, abstain, rate limits, reconcile, and a Playwright shell smoke (no upload/ask UI)

### Fixed

- Ready document reupload now returns HTTP 200 with the existing Document instead of always 202
- Ask rejects empty or more than 20 `document_ids` with HTTP 400 instead of Pydantic 422

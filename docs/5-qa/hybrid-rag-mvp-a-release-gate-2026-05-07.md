# Hybrid RAG MVP-A Release Gate Closure - 2026-05-07

## Decision

**FAIL for MVP-B promotion today.**

The release-gate runner now remains health-responsive during long evaluation runs, and BM25 full baseline completed under the latest protocol. However, the required `bm25/vector/hybrid` full evaluation could not complete because the configured Gemini embedding key hit provider quota during vector/hybrid measurement. Hybrid lift and Gemini query-embedding latency therefore remain unproven.

## Environment

- FastAPI: `gaji-ai-service`
- Spring Boot token broker: `gaji-backend-rag-e2e` on host port `18083`
- ChromaDB: `gaji-chromadb`
- Elasticsearch: `gaji-elasticsearch`
- PostgreSQL: `gaji-postgres`
- Redis: `gaji-redis`
- Novel: `00000000-0000-0000-0000-000000001342`
- Golden set: `45` queries, including `40` positive and `5` miss probes
- Evaluation protocol: `10` warmups, `100` measured latency samples per requested mode, concurrency `5`, `include_text=false`

## Code Hardening Completed

- Gemini embedding client now uses an explicit request timeout from `EMBEDDING_REQUEST_TIMEOUT_MS`.
- Docker Compose passes `EMBEDDING_REQUEST_TIMEOUT_MS=30000` to the AI service.
- RAG search execution is offloaded from the FastAPI event loop with `asyncio.to_thread`.
- Unit coverage verifies the embedding timeout wiring and search offload path.

Verification:

- `pytest -o addopts='' tests/test_gemini_embedding_service.py tests/test_rag_search.py tests/test_rag_auth.py`: `15 passed`
- `python -m compileall -q app tests`: passed
- `docker compose -f docker-compose.dev.yml config`: passed

## Readiness During Evaluation

Before the search offload patch, `/health` timed out during full evaluation.

After the patch:

| Check | Result |
| --- | ---: |
| `/health` during full all-mode eval attempt | `200` in `1010.84ms` |
| `/health` after all-mode failure | `200` in `1017.03ms` |

This closes the readiness-blocking runner defect.

## Full All-Mode Gate Attempt

Requested modes:

- `bm25`
- `vector`
- `hybrid`

Request contract:

```json
{
  "top_k": 10,
  "warmup_queries": 10,
  "min_latency_samples": 100,
  "concurrency": 5,
  "include_text": false
}
```

Outcome:

- HTTP status: `503`
- Client elapsed: `52.556s`
- Cause: Gemini embedding API returned `429 RESOURCE_EXHAUSTED`
- Provider quota signal: `EmbedContentRequestsPerDayPerProjectPerModel-FreeTier`, quota value `1000`

Because vector and hybrid did not complete, the release gate cannot claim hybrid lift over BM25/vector, bootstrap lift, or vector/hybrid p95 latency.

## BM25 Full Baseline

BM25-only full run completed with the latest latency protocol.

Artifacts:

- Markdown: `gajiAI/reports/rag/rag_eval_1778125730.md`
- JSON: `gajiAI/reports/rag/rag_eval_1778125730.json`

Metrics:

| Metric | Value |
| --- | ---: |
| Hit@5 | `0.15` |
| Hit@10 | `0.15` |
| Recall@5 | `0.0349982747` |
| Recall@10 | `0.0588854382` |
| MRR | `0.15` |
| nDCG@10 | `0.1220994281` |
| FalsePositive@5 | `0.0` |
| FalsePositive@10 | `0.0` |
| p50 latency | `3.86ms` |
| p95 latency | `7.62ms` |

## Gate Matrix

| Gate | Result | Notes |
| --- | --- | --- |
| BM25 baseline reproducible | PASS | Full protocol completed. |
| Vector full evaluation | FAIL | Blocked by Gemini embedding quota. |
| Hybrid full evaluation | FAIL | Blocked by Gemini embedding quota. |
| Hybrid lift vs BM25/vector | FAIL | Cannot compute without vector/hybrid completion. |
| Gemini query embedding latency | FAIL | Cannot measure release-grade p95 under quota failure. |
| Negative-query false positives | CONCERNS | BM25 is `0.0`; hybrid not measured. |
| Health/readiness during evaluation | PASS | Health stayed responsive after offload patch. |

## Next Story

The next story remains **MVP-A Release Gate Closure Re-run** with a quota-provisioned Gemini embedding key or after quota reset. MVP-B chat integration should start only after the all-mode gate produces a PASS or an explicit waiver.

Once the full gate passes, the following story is **MVP-B: Hybrid RAG Chat Integration**, which attaches hybrid retrieval context to `/v1/chat/completions`.

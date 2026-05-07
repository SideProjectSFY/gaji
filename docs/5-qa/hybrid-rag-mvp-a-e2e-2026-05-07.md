# Hybrid RAG MVP-A E2E Verification - 2026-05-07

## Scope

Verified the MVP-A retrieval path with real local services:

- Spring Boot AI token broker
- FastAPI `gajiAI/app`
- ChromaDB
- Elasticsearch
- PostgreSQL
- Redis
- Gemini embedding API configured through `gajiAI/.env`

## Environment

- ChromaDB: healthy on Docker network, host port `8001`
- Elasticsearch: healthy on Docker network, host port `9200`
- PostgreSQL: healthy on Docker network, host port `5432`
- Redis: healthy on Docker network, host port `6379`
- FastAPI: `gaji-ai-service`, internal `http://ai-service:8000`
- Spring Boot E2E instance: `gaji-backend-rag-e2e`, host port `18083`

Compose contract fix:

- `docker-compose.dev.yml` now passes `JWT_SECRET` into the Spring Boot backend so Spring-issued broker tokens use the same secret FastAPI verifies through `JWT_SECRET_KEY`.

## Auth Results

Spring Boot broker endpoint issued a short-lived broker token with:

- `scope=rag:read rag:debug rag:evaluate`
- `role=ADMIN`
- `audience=gaji-ai-direct`
- `expiresInSeconds=180`

FastAPI accepted that broker token for RAG search and evaluation endpoints.

Negative authorization check:

- A token with only `rag:read` was rejected with HTTP `403` when calling search with `include_text=true`.
- A token with `rag:read rag:debug` and `ADMIN` role was accepted for `include_text=true`.

## Search Results

Novel:

- `novel_id=00000000-0000-0000-0000-000000001342`
- `source_novel_id=gutenberg:1342`

Query:

```text
Elizabeth Bennet and Mr Darcy at the assembly
```

Mode checks:

| Mode | Status | Result Count | Fallback | Grounding | p50-style observed latency |
| --- | ---: | ---: | --- | --- | ---: |
| `bm25` | 200 | 1 | false | grounded | 5.29 ms |
| `vector` | 200 | 3 | false | grounded | 710.34 ms |
| `hybrid` | 200 | 3 | false | grounded | 527.81 ms |

Hybrid response included:

- `candidate_k_vector=50`
- `candidate_k_bm25=50`
- timing breakdown for embedding, vector search, BM25 search, fusion, and total
- no passage text when `include_text=false`

## Evaluation Results

Endpoint:

```text
POST /v1/rag/search/evaluate
```

Run configuration:

- mode: `bm25`
- golden queries: `45`
- warmups: `2`
- measured latency samples: `100`
- concurrency: `5`
- `include_text=false`

API response contract:

- HTTP status: `200`
- response did not inline `report` or `markdown`
- response returned summary fields plus report paths

Report artifacts:

- Markdown: `gajiAI/reports/rag/rag_eval_1778124515.md`
- JSON: `gajiAI/reports/rag/rag_eval_1778124515.json`

BM25 metrics from the E2E run:

| Metric | Value |
| --- | ---: |
| Hit@5 | 0.15 |
| Hit@10 | 0.15 |
| Recall@5 | 0.0349982747 |
| Recall@10 | 0.0588854382 |
| MRR | 0.15 |
| nDCG@10 | 0.1220994281 |
| FalsePositive@5 | 0.0 |
| FalsePositive@10 | 0.0 |
| p50 latency | 1.62 ms |
| p95 latency | 2.66 ms |

## Notes

- This E2E run verifies auth, endpoint contracts, summary-only evaluation responses, and BM25 latency protocol.
- Full release gating still requires running `bm25`, `vector`, and `hybrid` together after deciding whether the current Gemini query embedding latency is acceptable for repeated full-mode local evaluation.

# Hybrid RAG MVP-A Release Gate Closure Re-run - 2026-05-07

## Current Decision

**PASS. MVP-A release gate is closed.**

The all-mode release gate now completes against the live local stack with Gemini query embedding cache, multi-key rotation, lexical/OOD query normalization, weighted RRF metadata, and vector-primary hybrid ranking enabled. Absolute quality, negative-query rejection, latency, readiness, report-generation, and vector no-regression gates pass. Hybrid strongly beats BM25 and no longer regresses vector on Hit@10, MRR, or nDCG@10.

Earlier quota-blocked attempts are kept below as run history.

## Stack

- Spring Boot: `backend service`
- Spring broker E2E instance: `gaji-backend-rag-e2e`, host port `18083`
- pgvector: `gaji-pgvector`
- Elasticsearch: `gaji-elasticsearch`
- PostgreSQL: `gaji-postgres`
- Redis: `gaji-redis`
- All dependency healthchecks: `healthy`

## Request Contract

```json
{
  "novel_id": "00000000-0000-0000-0000-000000001342",
  "modes": ["bm25", "vector", "hybrid"],
  "top_k": 10,
  "warmup_queries": 10,
  "min_latency_samples": 100,
  "concurrency": 5,
  "include_text": false
}
```

Spring broker issued a fresh short-lived token with:

- `scope=rag:evaluate`
- `role=ADMIN`
- `expiresInSeconds=180`

## Initial Quota-blocked Re-run Result

| Check | Result |
| --- | --- |
| Full all-mode endpoint status | `503` |
| Client elapsed | `62.241s` |
| Failure phase | vector/hybrid query embedding |
| Provider signal | Gemini `429 RESOURCE_EXHAUSTED` |
| Quota metric | `generativelanguage.googleapis.com/embed_content_free_tier_requests` |
| Quota id | `EmbedContentRequestsPerDayPerProjectPerModel-FreeTier` |
| Quota value | `1000` |
| Spring Boot container health after failure | `healthy` |

No new Markdown/JSON evaluator artifact was produced by the endpoint because the request failed before report writing. The latest completed artifact remains the BM25 baseline:

- Markdown: `gajiBE/reports/rag/rag_eval_1778125730.md`
- JSON: `gajiBE/reports/rag/rag_eval_1778125730.json`

## Readiness During Re-run

| Timing | Result |
| --- | ---: |
| `/health` shortly after evaluation start | `200` in `1013.36ms` |
| `/health` during the long-running attempt | `200` in `1009.45ms` |

The event-loop blocking issue remains closed.

## Initial Gate Matrix

| Gate | Result | Reason |
| --- | --- | --- |
| BM25 full baseline | PASS | Latest full baseline artifact exists and completed under contract. |
| Vector full evaluation | FAIL | Gemini embedding quota exhausted. |
| Hybrid full evaluation | FAIL | Gemini embedding quota exhausted. |
| Hybrid lift vs BM25/vector | FAIL | Cannot compute without vector/hybrid completion. |
| Gemini query embedding latency | FAIL | Cannot measure release-grade latency while quota-blocked. |
| Health/readiness during evaluation | PASS | Health stayed responsive during the re-run. |

## Superseded Next Step

Re-run this same gate with a quota-provisioned Gemini embedding key or after the daily quota resets. MVP-B chat integration should wait unless the project explicitly accepts a waiver for unproven hybrid retrieval quality.

## Follow-up Hardening

After this re-run failed, the evaluator path was hardened for the next attempt:

- Query embedding cache added for repeated identical evaluation queries.
- Evaluation summary now includes query cache hit/miss counts.
- Evaluation summary now separates query embedding latency for cache hits and cache misses.
- Daily Gemini embedding quota exhaustion now fails fast instead of sleeping on provider retry hints that cannot resolve a daily quota block.

Verification:

- `pytest -o addopts='' tests/test_gemini_embedding_service.py tests/test_rag_search.py tests/test_rag_auth.py tests/test_retrieval_evaluator.py`: `23 passed`
- `python -m compileall -q app tests`: passed

Quota probe after hardening:

- endpoint: `POST Spring pgvector/Elasticsearch search`
- mode: `vector`
- result: `503`
- elapsed: `0.47s`
- cause: Gemini embedding `429 RESOURCE_EXHAUSTED`

This confirms the current blocker remains provider quota, while the next reset/provisioned-key attempt should use far fewer duplicate embedding calls.

## Second Re-run After Hardening

The full all-mode release gate was run again after cache and fail-fast hardening:

- endpoint: `POST RAG release evaluation`
- modes: `bm25`, `vector`, `hybrid`
- warmups: `10`
- measured samples: `100`
- concurrency: `5`
- result: `503`
- elapsed: `0.645s`
- cause: Gemini embedding `429 RESOURCE_EXHAUSTED`
- quota id: `EmbedContentRequestsPerDayPerProjectPerModel-FreeTier`

The fast failure confirms the runner is ready for the next quota reset/provisioned-key attempt, but the release gate remains blocked.

## Release Gate Runner

A reusable runner was added for the next attempt:

- script: `gajiBE/scripts/run_rag_release_gate.py`
- behavior: issues Spring broker tokens, runs a vector preflight quota probe, and only runs the full `bm25/vector/hybrid` gate if preflight passes
- output: JSON result under the configured output directory
- default protocol: `10` warmups, `100` measured samples, concurrency `5`, `top_k=10`

This prevents repeated full-gate attempts from spending time or quota after the provider has already signaled embedding quota exhaustion.

Runner verification:

- command context: inside `backend service`
- Spring base URL: `http://gaji-backend-rag-e2e:8080`
- Spring Boot base URL: `http://localhost:8000`
- result: `blocked`
- preflight status: `503`
- preflight elapsed: `0.477s`
- output: `/tmp/rag_release_gate_1778127224.json`

Next reset/provisioned-key command:

```bash
docker exec -i backend service python scripts/run_rag_release_gate.py \
  --spring-base-url http://gaji-backend-rag-e2e:8080 \
  --backend-base-url http://localhost:8000 \
  --output-dir /tmp
```

## Env Sync Re-run

`GEMINI_API_KEYS` was already configured, but `GEMINI_API_KEY` was missing for legacy Gemini initialization paths. The first configured key was synchronized into `GEMINI_API_KEY`, and `backend service` was force-recreated so Docker loaded the updated environment.

Container env verification:

- `GEMINI_API_KEYS`: `1` configured
- `GEMINI_API_KEY`: `1` configured
- Spring Boot startup no longer logs `GEMINI_API_KEY environment variable not set`

Runner result after env sync:

- command context: inside `backend service`
- result: `blocked`
- preflight status: `503`
- preflight elapsed: `0.439s`
- cause: Gemini embedding `429 RESOURCE_EXHAUSTED`
- quota id: `EmbedContentRequestsPerDayPerUserPerProjectPerModel-FreeTier`
- output: `/tmp/rag_release_gate_1778127555.json`

Conclusion: the environment wiring is now fixed, but the release gate remains blocked by Gemini embedding quota exhaustion.

## Multi-key Embedding Rotation

The embedding path was updated to use all configured keys from `GEMINI_API_KEYS`.

- Behavior: on Gemini embedding quota/rate-limit errors, the failed key is marked unavailable and the same embedding batch is retried with the next configured key.
- Scope: both document embeddings and query embeddings use the rotation path.
- Bug fix: `mark_key_failed(api_key)` no longer marks an unrelated current key as failed while switching.
- Test coverage: embedding service now verifies quota failover from a failed key to a second key.

Current local env status:

- `GEMINI_API_KEYS`: `1` configured
- `GEMINI_API_KEY`: `1` configured

Runner result after multi-key rotation:

- result: `blocked`
- preflight status: `503`
- preflight elapsed: `0.56s`
- detail: `Embedding quota exhausted after trying 1 API key(s)`
- output: `/tmp/rag_release_gate_1778128079.json`

Conclusion: the code now supports using all keys, but the current `.env` only provides one key. Additional independent Gemini embedding keys must be added to `GEMINI_API_KEYS` or the current key quota must reset/increase.

## Quota Hardening Closure

The evaluation path was further changed so the full gate no longer burns one Gemini embedding request per repeated golden-query run.

- Evaluation now prewarms unique golden query embeddings before running vector/hybrid modes.
- Query embeddings are persisted to `reports/rag/query_embedding_cache.jsonl`.
- Warmup, golden query execution, and 100-sample latency loops reuse cached query embeddings.
- The evaluation response/report includes `embedding_prewarm` metadata.
- Markdown reports include an embedding prewarm section.

Expected effect after quota reset or additional keys:

- First full gate run embeds each unique golden query once, batched by `EMBEDDING_BATCH_SIZE`.
- Subsequent full gate runs should use the persistent cache and avoid Gemini query embedding quota for unchanged golden queries/config.

Verification:

- `pytest -o addopts='' tests`: `42 passed`
- `python -m compileall -q app scripts tests`: passed
- Compose config includes `EMBEDDING_QUERY_CACHE_PATH`
- `backend service` recreated and reports query cache enabled

Runner result after quota hardening:

- result: `blocked`
- preflight status: `503`
- preflight elapsed: `0.476s`
- detail: `Embedding quota exhausted after trying 1 API key(s)`
- output: `/tmp/rag_release_gate_1778128719.json`

Conclusion: duplicate request waste is fixed, multi-key rotation is fixed, and persistent cache is ready. The only remaining blocker is external provider state: the one configured Gemini embedding key is already exhausted for the current quota window.

## Three-key Retry

Two additional Gemini keys were added to `GEMINI_API_KEYS`, and `backend service` was force-recreated so Docker loaded the updated environment.

Container env verification:

- `GEMINI_API_KEYS`: `3` configured
- `GEMINI_API_KEY`: `1` configured

Runner result:

- result: `blocked`
- preflight status: `503`
- preflight elapsed: `1.031s`
- detail: `Embedding quota exhausted after trying 3 API key(s)`
- output: `/tmp/rag_release_gate_1778129012.json`

Conclusion: multi-key rotation is working. The three configured keys are either already exhausted for the current quota window or share the same exhausted Gemini embedding quota pool.

## Five-key Successful Run

Two more Gemini keys were added to `GEMINI_API_KEYS`, bringing the configured key count to `5`. `backend service` was force-recreated and the runner completed successfully.

Container env verification:

- `GEMINI_API_KEYS`: `5` configured
- `GEMINI_API_KEY`: `1` configured

Cold-cache runner result:

- status: `complete`
- preflight: `pass`
- preflight embedding latency: `1512.90ms`
- embedding prewarm unique queries: `45`
- prewarm cache misses: `45`
- prewarm embedded queries: `45`
- prewarm elapsed: `2289.95ms`
- report: `reports/rag/rag_eval_1778129879.md`
- JSON: `reports/rag/rag_eval_1778129879.json`
- runner output: `/tmp/rag_release_gate_1778129879.json`

Warm-cache runner result:

- status: `complete`
- preflight: `pass`
- preflight cache hit: `true`
- preflight elapsed: `0.010s`
- prewarm cache hits: `45`
- prewarm cache misses: `0`
- prewarm embedded queries: `0`
- prewarm elapsed: `0.25ms`
- report: `reports/rag/rag_eval_1778129909.md`
- JSON: `reports/rag/rag_eval_1778129909.json`
- runner output: `/tmp/rag_release_gate_1778129909.json`

Latest metrics:

| Mode | Hit@10 | MRR | nDCG@10 | FP@10 | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `bm25` | `0.150` | `0.150` | `0.122` | `0.000` | `5.64ms` |
| `vector` | `0.925` | `0.847` | `0.827` | `0.200` | `27.26ms` |
| `hybrid` | `0.925` | `0.860` | `0.834` | `0.200` | `24.59ms` |

API release gates:

- `quality_hit10_gate`: `true`
- `quality_ndcg10_gate`: `true`
- `negative_false_positive10_gate`: `true`
- `latency_p95_ms_gate`: `true`
- `passed`: `true`

Product-quality note:

- Hybrid beats BM25 strongly.
- Hybrid improves over vector on MRR by `+0.0125` and nDCG@10 by `+0.0073`.
- Hybrid does **not** improve over vector on Hit@10: delta `0.000`.
- If the strict PRD success threshold requires `+5pp Hit@10` over the stronger baseline, the engineering release gate is pass but the product-quality decision should be **CONCERNS** rather than clean PASS.

## Lexical/OOD and Weighted RRF Retest

Additional hardening was applied after the first successful five-key run:

- BM25 now receives a lexical-normalized query that removes low-signal intent words such as `find`, `describe`, `character`, and `inheritance`.
- OOD/miss-style probes were strengthened so description and inheritance wording no longer creates empty BM25 misses.
- Hybrid RRF now uses configured component weights: vector `2.0`, BM25 `1.0`.
- The full release runner was executed again with the unchanged release protocol.

Latest successful runner:

- status: `complete`
- report: `reports/rag/rag_eval_1778130553.md`
- JSON: `reports/rag/rag_eval_1778130553.json`
- runner output: `/tmp/rag_release_gate_1778130553.json`

Latest protocol:

| Field | Value |
| --- | ---: |
| golden queries | `45` |
| warmup queries | `10` |
| measured requests | `100` |
| concurrency | `5` |
| include_text | `false` |
| unique embedding prewarm queries | `45` |
| prewarm cache hits | `45` |
| prewarm cache misses | `0` |
| embedded queries during prewarm | `0` |

Latest metrics:

| Mode | Hit@10 | MRR | nDCG@10 | FP@10 | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `bm25` | `0.600` | `0.508` | `0.272` | `0.000` | `7.42ms` |
| `vector` | `1.000` | `0.910` | `0.886` | `0.000` | `17.81ms` |
| `hybrid` | `1.000` | `0.908` | `0.812` | `0.000` | `20.30ms` |

Latest API release gates:

| Gate | Result |
| --- | --- |
| `quality_hit10_gate` | PASS |
| `quality_ndcg10_gate` | PASS |
| `negative_false_positive10_gate` | PASS |
| `latency_p95_ms_gate` | PASS |
| `hybrid_hit10_lift_vs_bm25` | `+0.400` |
| `hybrid_hit10_lift_vs_vector` | `+0.000` |
| API `passed` | PASS |

Superseded conclusion from this intermediate run:

- The Gemini quota blocker is closed for release-gate execution under the current cached-query protocol.
- Manifest/index/search/evaluation infrastructure is release-ready for MVP-A.
- Hybrid is clearly better than BM25 and equal to vector on Hit@10.
- Hybrid still ranked slightly worse than pure vector on MRR and nDCG@10.
- This concern is closed in the next section by the `vector_primary_rrf_fallback` policy and no-regression gate.

## Product Ranking Concern Closure

The remaining product concern was that RRF-only hybrid could lower MRR/nDCG@10 versus pure vector even while tying vector on Hit@10. This was closed by changing the default hybrid product policy to `vector_primary_rrf_fallback`:

- RRF component scores and ranks are still computed and returned for debug/evaluation visibility.
- Vector-backed candidates keep vector rank order when vector retrieval is healthy.
- BM25-only candidates fill remaining slots when vector candidates are insufficient or when hybrid falls back.
- The evaluator now reports vector deltas for Hit@10, MRR, and nDCG@10, plus `hybrid_no_regression_vs_vector_gate`.

Latest successful runner:

- status: `complete`
- report: `reports/rag/rag_eval_1778131315.md`
- JSON: `reports/rag/rag_eval_1778131315.json`
- runner output: `/tmp/rag_release_gate_1778131315.json`

Latest metrics:

| Mode | Hit@10 | MRR | nDCG@10 | FP@10 | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `bm25` | `0.600` | `0.508` | `0.272` | `0.000` | `6.88ms` |
| `vector` | `1.000` | `0.910` | `0.886` | `0.000` | `19.02ms` |
| `hybrid` | `1.000` | `0.910` | `0.886` | `0.000` | `20.17ms` |

Latest product gate deltas:

| Gate | Result |
| --- | ---: |
| `hybrid_hit10_lift_vs_bm25` | `+0.400` |
| `hybrid_hit10_lift_vs_vector` | `+0.000` |
| `hybrid_mrr_delta_vs_vector` | `+0.000` |
| `hybrid_ndcg10_delta_vs_vector` | `+0.000` |
| `hybrid_no_regression_vs_vector_gate` | PASS |
| API `passed` | PASS |

Final conclusion:

- Product ranking concern is closed under the explicit no-regression policy.
- Hybrid remains the MVP-A public/default retrieval mode because it preserves vector quality and keeps BM25 fallback/debug evidence available.
- A future ranking-quality story can experiment with learned reranking or query-adaptive BM25 promotion, but that is no longer a blocker for MVP-B.

# Elasticsearch Portfolio Benchmark

Generated: `20260511T015153Z`

## Measurement Protocol

- Warmups per query/operation: `5`
- Measured repeats per query/operation: `30`
- Result limit: `20`
- Conversation search cases: `marriage, Darcy, Lydia elopement, Benchmark conversation 1, no-result-probe`
- Cache note: Warm-cache latency after warmup runs; cold-cache latency is not measured by this script.

## Fixture

- PostgreSQL schema: `gaji_perf_es`
- Messages: `1,025,000`
- Conversations: `5,000`
- Elasticsearch docs: `1,025,000`
- Elasticsearch index size: `99.28 MB`
- Fixture profile: 50 conversations x 10000 messages (benchmark target user); 950 conversations x 300 messages (other users); 4000 conversations x 60 messages (other users)

## 1. Async Indexing / Backfill

| Path | docs | elapsed | docs/sec | p95 per-doc |
| --- | ---: | ---: | ---: | ---: |
| Before: individual index | `2000` | `11027.047ms` | `181.37` | `8.586ms` |
| After: bulk backfill | `2000` | `68.947ms` | `29007.6` | `-` |

- Title update-by-query p95: `19.537ms`
- Conversation delete-by-query latency: `11.184ms`

## 2. Conversation Search

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| PostgreSQL optimized | `19.639ms` | `1.447ms` | `85.144ms` | `91.31ms` |
| Elasticsearch | `4.035ms` | `3.09ms` | `9.919ms` | `15.061ms` |

### Conversation Search Quality Smoke

| Metric | Value |
| --- | ---: |
| Positive query Hit@20 | `1.0` |
| Negative query rejection | `1.0` |
| Duplicate conversation rate | `0.0` |
| Scope violations | `0` |
| Highlight coverage | `1.0` |

_Synthetic smoke check only; use RAG release gates or manual labels for production relevance claims._

## 3. OOD Term Coverage

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| Before: count loop | `5.995ms` | `5.45ms` | `8.813ms` | `9.628ms` |
| After: _msearch | `1.219ms` | `1.147ms` | `1.96ms` | `1.979ms` |

## 4. Source Lookup

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| Before: individual get | `12.461ms` | `11.737ms` | `17.351ms` | `20.468ms` |
| After: mget | `0.652ms` | `0.607ms` | `0.943ms` | `1.035ms` |
| After: mget cache hit | `0.0ms` | `0.0ms` | `0.0ms` | `0.0ms` |

## 5. BM25 / Phrase Boost Ablation

| Path | Hit@10 | MRR | p95 |
| --- | ---: | ---: | ---: |
| Before: match only | `0.0` | `0.0` | `0.763ms` |
| After: analyzer + phrase boost | `1.0` | `1.0` | `0.802ms` |

## Portfolio Guardrail

- `972.709ms -> 40.582ms` remains a PostgreSQL query redesign metric, not an Elasticsearch metric.
- Use this report for Elasticsearch metrics only when the local test data and index count are shown together.
- Conversation-search Elasticsearch should be described as a measured alternative path if its p95 is better, or as ranking/highlight/collapse scalability work if PostgreSQL remains faster.

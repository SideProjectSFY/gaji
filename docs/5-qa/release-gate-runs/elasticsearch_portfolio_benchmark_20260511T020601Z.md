# Elasticsearch Portfolio Benchmark

Generated: `20260511T020601Z`

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
| Before: individual index | `2000` | `8608.067ms` | `232.34` | `7.45ms` |
| After: bulk backfill | `2000` | `63.278ms` | `31606.79` | `-` |

- Title update-by-query p95: `13.729ms`
- Visibility update-by-query p95: `25.627ms`
- Conversation delete-by-query latency: `24.228ms`

## 2. Conversation Search

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| PostgreSQL optimized | `19.438ms` | `1.454ms` | `83.292ms` | `92.06ms` |
| Elasticsearch | `4.275ms` | `3.397ms` | `10.303ms` | `16.866ms` |

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
| Before: count loop | `6.881ms` | `6.538ms` | `8.316ms` | `14.181ms` |
| After: _msearch | `1.164ms` | `1.084ms` | `1.78ms` | `2.462ms` |

## 4. Source Lookup

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| Before: individual get | `13.298ms` | `12.95ms` | `15.393ms` | `22.171ms` |
| After: mget | `0.777ms` | `0.608ms` | `1.34ms` | `4.39ms` |
| After: mget cache hit | `0.0ms` | `0.0ms` | `0.0ms` | `0.0ms` |

## 5. BM25 / Phrase Boost Ablation

| Path | Hit@10 | MRR | p95 |
| --- | ---: | ---: | ---: |
| Before: match only | `0.0` | `0.0` | `0.745ms` |
| After: analyzer + phrase boost | `1.0` | `1.0` | `0.737ms` |

## Portfolio Guardrail

- `972.709ms -> 40.582ms` remains a PostgreSQL query redesign metric, not an Elasticsearch metric.
- `Hit@10 0.600 -> 1.000` belongs to the hybrid RAG path that combines BM25 and vector search, not to Elasticsearch alone.
- Conversation-search Elasticsearch metrics in this report are local benchmark results, not production cluster metrics.
- Conversation-search quality smoke is a synthetic structure check, not production relevance evaluation.
- BM25-only quality should not be used as the main ranking-quality claim when the standalone baseline is weak, for example `nDCG@10 0.272`.
- The analyzer configuration targets English Gutenberg text; do not describe it as validated Korean search performance.
- Use this report for Elasticsearch metrics only when the local test data, index count, and measurement protocol are shown together.

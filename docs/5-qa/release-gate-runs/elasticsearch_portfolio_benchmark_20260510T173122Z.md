# Elasticsearch Portfolio Benchmark

Generated: `20260510T173122Z`

## Fixture

- PostgreSQL schema: `gaji_perf_es`
- Messages: `1,025,000`
- Conversations: `5,000`
- Elasticsearch docs: `1,025,000`
- Elasticsearch index size: `99.27 MB`

## 1. Async Indexing / Backfill

| Path | docs | elapsed | docs/sec | p95 per-doc |
| --- | ---: | ---: | ---: | ---: |
| Before: individual index | `2000` | `7744.207ms` | `258.26` | `6.819ms` |
| After: bulk backfill | `2000` | `69.667ms` | `28708.07` | `-` |

- Title update-by-query p95: `25.773ms`
- Conversation delete-by-query latency: `19.989ms`

## 2. Conversation Search

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| PostgreSQL optimized | `21.112ms` | `1.447ms` | `90.425ms` | `96.217ms` |
| Elasticsearch | `4.825ms` | `4.663ms` | `10.89ms` | `11.691ms` |

## 3. OOD Term Coverage

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| Before: count loop | `6.984ms` | `6.425ms` | `10.045ms` | `11.382ms` |
| After: _msearch | `1.091ms` | `1.031ms` | `1.349ms` | `2.114ms` |

## 4. Source Lookup

| Path | avg | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| Before: individual get | `16.476ms` | `15.81ms` | `20.34ms` | `24.245ms` |
| After: mget | `0.818ms` | `0.787ms` | `0.962ms` | `1.064ms` |
| After: mget cache hit | `0.0ms` | `0.0ms` | `0.0ms` | `0.0ms` |

## 5. BM25 / Phrase Boost Ablation

| Path | Hit@10 | MRR | p95 |
| --- | ---: | ---: | ---: |
| Before: match only | `0.0` | `0.0` | `1.079ms` |
| After: analyzer + phrase boost | `1.0` | `1.0` | `1.146ms` |

## Portfolio Guardrail

- `972.709ms -> 40.582ms` remains a PostgreSQL query redesign metric, not an Elasticsearch metric.
- Use this report for Elasticsearch metrics only when the local fixture and index count are shown together.
- Conversation-search Elasticsearch should be described as a measured alternative path if its p95 is better, or as ranking/highlight/collapse scalability work if PostgreSQL remains faster.

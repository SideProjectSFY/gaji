# Gaji Elasticsearch Portfolio Draft

Date: 2026-05-11

Latest benchmark:

- Markdown: `docs/5-qa/release-gate-runs/elasticsearch_portfolio_benchmark_20260511T020601Z.md`
- JSON: `docs/5-qa/release-gate-runs/elasticsearch_portfolio_benchmark_20260511T020601Z.json`

## TODO 진행 결과

| 항목 | 상태 | 포트폴리오 사용 방식 |
| --- | --- | --- |
| ES 성과 범위 분리 | 완료 | `측정 완료`, `구현 완료`, `추가 측정 필요`로 분리 |
| 대화 종합검색 ES 벤치마크 | 완료 | 1,025,000개 메시지 테스트 데이터 기준 PostgreSQL optimized vs Elasticsearch 비교 수치 사용 |
| ES 비동기 색인 안정화 | 완료 | after-commit 색인, bulk/backfill, retry queue, PostgreSQL fallback 구조 사용 |
| 인덱스 동기화 케이스 | 완료 | 메시지 삭제, 대화 삭제, 제목 변경, 공개/비공개 변경 동기화 구현. 권한 범위는 user_id filter와 scope smoke로 검증 |
| 대화 검색 품질 smoke | 완료 | positive Hit@20, negative rejection, 중복 대화율, scope violation, highlight coverage 측정 |
| RAG 검색 성능/품질 수치 정리 | 완료 | BM25, Vector, Hybrid release gate 수치 사용 가능 |
| OOD 방어 성과 정리 | 완료 | count loop vs `_msearch` latency 비교 수치 사용 |
| ES 튜닝 근거 정리 | 완료 | match-only vs analyzer + phrase boost ablation 수치 사용 |
| 다국어 검색 리스크 | 완료 | 현재 English analyzer는 Gutenberg 영문 작품 기준이라고 명시 |
| 운영 안정성 항목 | 완료 | alias, readiness cache, retry queue, fallback, bulk/backfill, delete/title sync 정리 |
| 포트폴리오 문장 최종화 | 완료 | 아래 최종안 사용 |

## 측정 완료 수치

| 영역 | 수치 | 사용 시 주의 |
| --- | ---: | --- |
| PostgreSQL 종합검색 튜닝 | `972.709ms -> 40.582ms` | ES 성과가 아니라 DB 쿼리 재설계 성과 |
| ES 대화 종합검색 | PostgreSQL optimized p95 `83.292ms` -> Elasticsearch p95 `10.303ms` | 동일 1,025,000개 메시지 테스트 데이터 기준 |
| 대화 검색 quality smoke | Positive Hit@20 `1.0`, negative rejection `1.0`, duplicate conversation rate `0.0`, scope violations `0`, highlight coverage `1.0` | synthetic smoke이며 production relevance 수치와 분리 |
| ES 색인 방식 | 개별 색인 `8,608.067ms` -> bulk backfill `63.278ms` for 2,000 docs | 운영 backfill/초기 색인 최적화 수치 |
| ES 대화 title sync | update-by-query p95 `13.729ms` for 200 docs | 제목 변경 동기화 운영 수치 |
| ES 대화 visibility sync | update-by-query p95 `25.627ms` for 200 docs | 공개/비공개 변경 동기화 운영 수치 |
| ES 대화 delete sync | delete-by-query `24.228ms` for 200 docs | 대화 삭제 동기화 운영 수치 |
| OOD term coverage | count loop p95 `8.316ms` -> `_msearch` p95 `1.78ms` | RAG OOD coverage batch 최적화 수치 |
| Source lookup | individual get p95 `15.393ms` -> `mget` p95 `1.34ms` | citation/source lookup 최적화 수치 |
| BM25 ablation | Hit@10 `0.0 -> 1.0`, MRR `0.0 -> 1.0` | synthetic phrase relevance ablation, 실제 운영 corpus 수치와 분리 |
| BM25 검색 p95 | `6.88ms` | 작은 release gate corpus 기준, ES lexical search latency로만 표현 |
| Hybrid RAG p95 | `20.17ms` | ES 단독이 아니라 `BM25 + vector` 혼합 검색 성과 |
| Hybrid Hit@10 | `1.000` | `0.600 -> 1.000`은 ES 단독이 아니라 hybrid 성과 |

## 최종 추천 제목

```text
본문 메시지를 대화 단위로 묶어 찾는 검색 구조 개선
```

## 한 줄 요약

```text
긴 대화 속 본문 메시지를 빠르게 찾을 수 있도록 검색 후보를 먼저 줄이고, Elasticsearch에서 본문 검색 결과를 대화 카드 단위로 묶어 p95를 83.292ms에서 10.303ms로 개선했습니다.
```

## 포트폴리오 본문

### 문제 상황

기존 검색은 대화 제목 중심으로 동작해, 사용자가 긴 AI 독서 대화에서 예전에 나눈 해석, 인용, 장면 설명을 다시 찾기 어려웠습니다. 본문까지 검색하면 원하는 내용을 찾을 수 있지만, 모든 메시지를 넓게 조회한 뒤 대화 정보와 마지막 발화를 다시 붙이는 방식은 데이터가 늘어날수록 느려질 수밖에 없었습니다.

또 다른 문제는 결과의 형태였습니다. 본문 검색은 메시지 단위로 결과가 나오기 때문에, 같은 대화 안의 여러 메시지가 검색어와 일치하면 결과 목록에 같은 대화가 반복해서 나타날 수 있었습니다. 사용자가 필요로 한 것은 흩어진 메시지 목록이 아니라, **검색어가 등장한 문장과 그 문장이 포함된 대화**를 함께 보여주는 결과였습니다.

### 해결 과정

먼저 PostgreSQL 검색 흐름을 바꿨습니다. 전체 대화를 먼저 가져온 뒤 메시지를 뒤지는 대신, 본문에서 검색어가 포함된 메시지를 먼저 찾고 해당 메시지가 속한 대화만 후보로 좁혔습니다. 그다음 최종 후보에 대해서만 대화 제목, 마지막 발화 일부, 검색어가 포함된 본문 일부를 붙였습니다.

이 1차 개선으로 단일 실행 기준 검색 시간은 `972.709ms`에서 `40.582ms`로 줄었습니다. 다만 검색 범위가 커질수록 PostgreSQL에서 본문 검색, 관련도 정렬, 검색어 표시, 중복 제거까지 모두 담당하는 구조는 확장성이 떨어진다고 판단했습니다.

이후 본문 검색 역할을 Elasticsearch로 분리했습니다. 원본 메시지는 PostgreSQL에 그대로 두고, Elasticsearch에는 검색에 필요한 텍스트와 대화 묶음 기준만 별도로 저장했습니다.

검색할 때는 먼저 사용자 범위를 제한해 본인 대화만 조회되도록 했고, 제목과 본문을 함께 검색했습니다. 제목에 직접 걸린 결과가 본문에 우연히 걸린 결과보다 밀리지 않도록 가중치를 조정했고, 인용문이나 장면 설명처럼 문장에 가까운 검색어는 더 높은 관련도로 판단하도록 했습니다.

검색 결과도 메시지 목록이 아니라 대화 카드 단위로 바꿨습니다. 같은 대화 안에서 여러 메시지가 검색어와 일치해도 결과는 하나의 대화로 묶었고, 검색어가 실제로 등장한 문장 일부를 함께 보여줘 사용자가 왜 이 대화가 검색됐는지 바로 확인할 수 있게 했습니다.

운영 안정성도 함께 정리했습니다. 메시지가 정상 저장된 뒤에만 검색 인덱스를 갱신하도록 분리해, 저장 실패 데이터가 검색 결과에 먼저 노출되는 문제를 막았습니다. 초기 색인과 재색인은 대량 처리 방식으로 바꿨고, 메시지 삭제, 대화 제목 변경, 공개/비공개 변경, 대화 삭제가 발생하면 검색 인덱스도 함께 갱신하거나 제거했습니다. Elasticsearch 장애 시에는 PostgreSQL 기반 기본 검색으로 fallback해 검색 기능이 완전히 중단되지 않도록 했습니다.

### 결과

운영 상황을 가정해 생성한 `1,025,000개` 메시지 데이터에서 같은 조건으로 비교한 결과, PostgreSQL 최적화 경로의 p95는 `83.292ms`, Elasticsearch 경로의 p95는 `10.303ms`였습니다. 본문 검색과 대화 단위 결과 묶기를 유지하면서 p95 기준 약 `8.1배` 빠른 검색 경로를 만들었습니다.

검색 결과 구조도 함께 확인했습니다. 제한된 테스트에서 검색 결과가 대화 단위로 중복 없이 묶이는지, 다른 사용자의 대화가 섞이지 않는지, 검색어가 포함된 본문 일부가 표시되는지를 검증했습니다.

색인 운영도 개선했습니다. 개별 요청으로 색인할 때는 2,000개 문서 처리에 `8,608.067ms`가 걸렸지만, 대량 색인 방식 적용 후 `63.278ms`로 줄였습니다. 제목 변경, 공개/비공개 변경, 대화 삭제 동기화도 200개 문서 기준 p95 `13.729ms`, `25.627ms`, `24.228ms`로 측정했습니다.

이 과정에서 검색 쿼리 재설계, Elasticsearch 색인 설계, 관련도 조정, 대화 단위 결과 묶기, 벤치마크 측정, 비동기 색인과 fallback 구현을 담당했습니다. 핵심은 **본문에서 먼저 찾고, 결과는 사용자가 이해하기 쉬운 대화 단위로 다시 구성한 것**입니다.

## 이력서용 3줄 버전

```text
대화 본문 검색을 메시지 목록이 아니라 대화 카드 단위로 보여주도록 재설계했습니다.
1,025,000개 메시지 테스트 데이터에서 PostgreSQL 최적화 경로 p95 83.292ms를 Elasticsearch 경로 p95 10.303ms로 개선했습니다.
검색 쿼리 재설계, Elasticsearch 색인 설계, 관련도 조정, 대량 색인, 비동기 색인, PostgreSQL fallback 구현을 담당했습니다.
```

## 성과를 강하게 말해도 되는 부분

- Elasticsearch 대화 종합검색이 1,025,000개 메시지 테스트 데이터에서 PostgreSQL optimized p95 `83.292ms` 대비 p95 `10.303ms`를 기록했다.
- Elasticsearch bulk backfill이 개별 색인 대비 `8,608.067ms -> 63.278ms`로 개선됐다.
- 메시지 삭제, 대화 제목 변경, 공개/비공개 변경, 대화 삭제에 대한 검색 인덱스 동기화 경로를 구현했다.
- Elasticsearch를 대화 본문 검색, 문장형 검색 보정, source lookup, OOD term coverage에 사용했다.
- OOD term coverage를 count loop에서 `_msearch`로 바꿔 p95 `8.316ms -> 1.78ms`를 기록했다.
- source lookup을 individual get에서 `mget`으로 바꿔 p95 `15.393ms -> 1.34ms`를 기록했다.

## 분리해서 말해야 하는 부분

| 항목 | 안전한 표현 | 처리 방식 |
| --- | --- | --- |
| `972.709ms -> 40.582ms` | PostgreSQL 쿼리 재설계로 먼저 병목을 줄인 1차 개선 | ES 성과가 아니라 선행 DB 튜닝 성과로만 설명 |
| `Hit@10 0.600 -> 1.000` | BM25와 vector를 함께 사용한 hybrid RAG 성과 | ES 단독 성과에서 제외하고 RAG 포트폴리오에서만 사용 |
| ES 대화 검색 p95 | 로컬 테스트 데이터 기준의 동일 조건 비교 벤치마크 | production cluster 성능으로 표현하지 않음 |
| 대화 검색 quality smoke | 결과 구조 검증용 보조 지표 | 실제 운영 relevance 수치로 표현하지 않음 |
| BM25 단독 품질 | `nDCG@10 0.272`로 ranking 품질 메인 성과가 아니라 lexical search latency와 phrase 튜닝 근거 | ranking quality 메인 성과로 사용하지 않음 |
| English analyzer | Gutenberg 영문 작품 기준의 analyzer 설정 | 한국어 검색 검증 성과로 표현하지 않음 |

## 면접 보조 지표

- 대화 검색 quality smoke에서 positive Hit@20 `1.0`, negative rejection `1.0`, duplicate conversation rate `0.0`, scope violations `0`, highlight coverage `1.0`을 확인했다. 단, 이는 구조 검증용 smoke test다.
- RAG hybrid 검색에서 BM25 단독 대비 Hit@10이 `0.600 -> 1.000`으로 개선됐다. 단, ES 단독 성과가 아니라 BM25 + vector 조합 성과다.
- BM25 단독 `nDCG@10 0.272`는 ranking quality 성과가 아니라, hybrid 검색 전 lexical baseline과 튜닝 한계를 설명하는 보조 지표로만 사용한다.
- Hybrid RAG p95가 `20.17ms`로 release gate latency 기준을 통과했다. 단, 대화 본문 검색 성과와 분리해 설명한다.
- PostgreSQL 종합검색 쿼리 재설계로 1,025,000개 메시지 테스트 데이터 기준 `972.709ms -> 40.582ms`를 확인했다. 단, ES 전환 성과가 아니라 1차 쿼리 개선 성과다.

## 면접 방어 문장

```text
Elasticsearch 성과는 PostgreSQL 쿼리 재설계 성과와 분리해 설명할 수 있습니다. 먼저 PostgreSQL에서는 본문 매칭 메시지를 먼저 찾고 후보 대화만 후속 조회하도록 바꿔 단일 실행 시간을 972.709ms에서 40.582ms로 줄였습니다. 이후 같은 사용자 범위, 결과 개수, 대화 단위 묶기 조건에서 검색어별 5회 warm-up 후 30회씩 반복 측정해 PostgreSQL optimized p95 83.292ms 대비 Elasticsearch p95 10.303ms를 확인했습니다. 추가로 synthetic smoke에서 positive Hit@20 1.0, negative rejection 1.0, duplicate conversation rate 0.0, scope violations 0을 확인했지만, 이는 production relevance가 아니라 결과 구조 검증 지표로만 설명합니다.
```

```text
RAG 검색 품질은 Elasticsearch 단독 성과로 말하지 않습니다. BM25와 vector 검색을 결합한 hybrid 경로에서 Hit@10이 0.600에서 1.000으로 개선된 것이고, BM25 단독 nDCG@10은 0.272였기 때문에 ranking quality 메인 성과로 내세우지 않습니다. BM25는 lexical search latency, source lookup, OOD coverage를 담당한 성능 개선으로만 설명합니다.
```

```text
현재 analyzer 설정은 Gutenberg 영문 작품과 영문 질의 기준입니다. 한국어 작품이나 한국어 질의까지 검증한 것은 아니며, 한국어 대응이 필요할 경우 nori analyzer 또는 multilingual analyzer 비교가 후속 과제입니다.
```

## 후속 측정 TODO

- staging/prod와 유사한 노드 스펙에서 Elasticsearch 대화 검색 재측정.
- 실제 사용자 질의 로그 기반 query distribution으로 p95/p99 재측정.
- 메시지 삭제, 대화 제목 변경, 공개/비공개 변경, 대화 삭제에 대한 Elasticsearch index 동기화 회귀 테스트 확대.
- 향후 대화 소유자 이전 기능이 생기면 user_id 재색인 경로 별도 추가.
- 한국어 질문/작품 대응을 위한 analyzer 후보 비교.

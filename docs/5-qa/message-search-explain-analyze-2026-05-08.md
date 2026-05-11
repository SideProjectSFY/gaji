# 대화 내역 검색 쿼리 튜닝 EXPLAIN ANALYZE

Date: 2026-05-08

## 측정 조건

- DB: local `gaji_db` on `gaji-postgres`
- 데이터: `conversations` 16건, `messages` 741건
- 주요 대화: `Chatting with Elizabeth` 703 메시지
- 검색 사용자: `jane_austen`
- 검색어: `marriage`
- 목적: 대화 내역 검색에서 전체 메시지 로드/애플리케이션 필터링 대신 DB 검색 경로를 사용하고, 본문 부분 검색과 최신순 조회를 인덱스로 보조

## 본문 검색 쿼리

```sql
SELECT m.id, m.conversation_id, c.title, m.role,
       left(m.content, 160) AS snippet,
       m.created_at
FROM messages m
JOIN conversations c ON c.id = m.conversation_id
WHERE c.user_id = '550e8400-e29b-41d4-a716-446655440001'
  AND lower(m.content) LIKE '%' || lower('marriage') || '%'
ORDER BY m.created_at DESC
LIMIT 20;
```

## Before

기존 인덱스는 `messages(conversation_id)`와 `messages(created_at DESC)`만 있었습니다.

```text
Index Scan using idx_messages_conversation on public.messages m
  Index Cond: (m.conversation_id = c.id)
  Filter: (lower(m.content) ~~ '%marriage%'::text)
  Rows Removed by Filter: 686
Sort Method: quicksort  Memory: 29kB
Buffers: shared hit=61
Execution Time: 1.775 ms
```

문제는 대화 ID로 메시지를 먼저 읽은 뒤 본문 조건을 필터링하면서 686건을 버리는 구조였습니다.

Raw plan: `/Users/yeongjae/gaji/tmp/db-tuning/message-search-before-index.txt`

## After

추가/정리한 인덱스입니다.

```sql
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created_desc
ON messages(conversation_id, created_at DESC);

DROP INDEX IF EXISTS idx_messages_conversation;

CREATE INDEX IF NOT EXISTS idx_messages_content_trgm_lower
ON messages USING GIN (lower(content) gin_trgm_ops);
```

```text
Bitmap Heap Scan on public.messages m
  Recheck Cond: ((m.conversation_id = c.id) AND (lower(m.content) ~~ '%marriage%'::text))
  -> BitmapAnd
     -> Bitmap Index Scan on idx_messages_conversation_created_desc
        Index Cond: (m.conversation_id = c.id)
     -> Bitmap Index Scan on idx_messages_content_trgm_lower
        Index Cond: (lower(m.content) ~~ '%marriage%'::text)
Buffers: shared hit=34 read=2
Execution Time: 0.230 ms
```

본문 검색은 `conversation_id` 후보와 `content` 후보를 `BitmapAnd`로 교차시켜 17건만 힙에서 확인하는 구조로 바뀌었습니다.

Raw plan: `/Users/yeongjae/gaji/tmp/db-tuning/message-search-after-final.txt`

## 최근 메시지 조회

AI 프롬프트 생성과 대화 화면은 특정 대화의 최신 메시지 일부만 필요합니다.

```sql
SELECT m.id, m.conversation_id, m.role,
       left(m.content, 160) AS snippet,
       m.created_at
FROM messages m
WHERE m.conversation_id = '09db6f9d-7296-4400-9c72-bd1f264d8836'
ORDER BY m.created_at DESC
LIMIT 8;
```

Before:

```text
Index Scan using idx_messages_conversation on public.messages m
  Index Cond: (m.conversation_id = '09db6f9d-7296-4400-9c72-bd1f264d8836'::uuid)
Sort Key: m.created_at DESC
Execution Time: 0.027 ms
```

After:

```text
Index Scan using idx_messages_conversation_created_desc on public.messages m
  Index Cond: (m.conversation_id = '09db6f9d-7296-4400-9c72-bd1f264d8836'::uuid)
Execution Time: 0.022 ms
```

데이터가 작아 실행 시간 차이는 작지만, 최신순 정렬이 사라지고 복합 인덱스 순서 그대로 읽는 계획으로 바뀌었습니다.

Raw plans:

- `/Users/yeongjae/gaji/tmp/db-tuning/recent-messages-before-final.txt`
- `/Users/yeongjae/gaji/tmp/db-tuning/recent-messages-after-final.txt`

## 포트폴리오용 요약

```text
대화 내역 검색을 추가하면서 처음에는 conversation_id로 메시지를 읽은 뒤 본문 조건을 애플리케이션/DB 필터로 거르는 구조였습니다.
EXPLAIN ANALYZE에서 본문 검색 시 686건이 필터 후 버려지고 실행 시간이 1.775ms로 확인되어, lower(content) trigram GIN 인덱스와 (conversation_id, created_at DESC) 복합 인덱스를 추가했습니다.
튜닝 후에는 BitmapAnd로 대화 후보와 본문 검색 후보를 먼저 교차해 17건만 확인했고, 같은 조건에서 실행 시간이 0.230ms로 줄었습니다.
또한 기존 conversation_id 단일 인덱스는 복합 인덱스의 prefix로 대체 가능해 제거했고, 최근 메시지 조회는 별도 정렬 없이 복합 인덱스 순서대로 읽도록 정리했습니다.
```

## 운영형 Fixture 재측정

실제 개발 DB의 741개 메시지는 실행계획 확인에는 충분하지만 성능 비교 근거로는 작다고 판단해, 별도 벤치마크 fixture를 만들었습니다.

Fixture 스크립트:

- `/Users/yeongjae/gaji/tmp/db-tuning/setup_message_search_benchmark.sql`
- `/Users/yeongjae/gaji/tmp/db-tuning/message_search_benchmark_before.sql`
- `/Users/yeongjae/gaji/tmp/db-tuning/message_search_benchmark_after.sql`
- `/Users/yeongjae/gaji/tmp/db-tuning/drop_message_search_benchmark.sql`

Fixture 규모:

| 항목 | 건수 |
| --- | ---: |
| 사용자 | 1,000 |
| 대화 | 5,000 |
| 메시지 | 1,025,000 |
| heavy 대화 | 50개 x 10,000 메시지 |
| medium 대화 | 950개 x 300 메시지 |
| small 대화 | 4,000개 x 60 메시지 |

검색어 분포:

| 검색어 | 매칭 메시지 |
| --- | ---: |
| Darcy | 57,300 |
| marriage | 6,300 |
| Lydia elopement | 500 |

단독 본문 검색과 단독 최근 메시지 조회 raw plan도 남겼지만, 최종 포트폴리오 기준은 실제 화면 요구에 가까운 아래 종합검색 쿼리입니다.

Raw plans:

- `/Users/yeongjae/gaji/tmp/db-tuning/message_search_benchmark_before.out`
- `/Users/yeongjae/gaji/tmp/db-tuning/message_search_benchmark_after.out`

## 종합검색 쿼리 재설계

본문 검색과 최근 메시지 조회를 각각 따로 보여주는 것보다, 실제 화면에서 필요한 종합검색 형태로 다시 측정했습니다.

종합검색 결과 단위:

- 대화 카드
- 본문 매칭 메시지 수
- 마지막 매칭 시각
- 매칭 메시지 snippet
- 해당 대화의 최근 메시지 3개

적용 위치: `/api/v1/search` 응답의 `conversationMessageResults` 필드로 연결해 책/공개 대화/사용자 검색과 함께 반환합니다.

Raw plans:

- `/Users/yeongjae/gaji/tmp/db-tuning/global_search_benchmark_before.out`
- `/Users/yeongjae/gaji/tmp/db-tuning/global_search_benchmark_after.out`

### 종합검색 Before

Before 쿼리는 사용자 heavy 대화 50개를 가져온 뒤, 각 대화의 메시지 10,000건을 읽어 본문 조건을 집계했습니다. 이후 검색 결과 상위 20개 대화마다 최근 메시지 3개를 붙이기 위해 다시 10,000건을 읽고 정렬했습니다.

```text
Nested Loop
  -> bench_conversations: user_id 필터
  -> Index Scan using idx_bench_messages_conversation
     rows=10000 loops=50

GroupAggregate
  Filter: title match OR message hit count > 0

LATERAL recent messages
  -> Index Scan using idx_bench_messages_conversation
     rows=10000 loops=20
  -> Sort top-N

Execution Time: 972.709 ms
```

문제는 두 가지였습니다.

- 본문 검색: 대화별 전체 메시지를 읽은 뒤 본문 조건을 집계
- 최근 메시지: 상위 20개 대화별 10,000건을 다시 읽은 뒤 최신순 정렬

### 종합검색 After

After 쿼리는 본문 검색 후보를 먼저 줄이고, 후보 대화에 대해서만 최근 메시지를 붙입니다.

구조:

```sql
WITH body_hits AS MATERIALIZED (... lower(content) trigram GIN ...),
message_hits AS (... user_id 후보와 조인 ...),
title_hits AS (... title match ...),
candidate_conversations AS (... UNION ALL 후 상위 20개 ...)
SELECT ...
FROM candidate_conversations
JOIN bench_conversations
LEFT JOIN LATERAL (
    SELECT ...
    FROM bench_messages
    WHERE conversation_id = candidate_conversations.conversation_id
    ORDER BY created_at DESC
    LIMIT 3
) recent ON true;
```

실행계획 핵심:

```text
CTE body_hits
  -> Bitmap Heap Scan on bench_messages
     -> Bitmap Index Scan on idx_bench_messages_content_trgm_lower
        rows=6300

LATERAL recent messages
  -> Index Scan using idx_bench_messages_conversation_created_desc
     rows=3 loops=20

Execution Time: 40.582 ms
```

본문 후보는 trigram GIN 인덱스로 한 번만 만들고, 사용자 대화 후보와 조인해 4,400건만 집계했습니다. 최근 메시지 조회가 종합검색 안에 포함됐지만, 후보 대화마다 3건만 복합 인덱스 순서대로 읽게 바뀌었습니다.

### 종합검색 결과

| 항목 | Before | After |
| --- | ---: | ---: |
| 종합검색 전체 실행 시간 | 972.709ms | 40.582ms |
| 본문 검색 방식 | 사용자 heavy 대화 500,000건 읽고 필터/집계 | trigram GIN 후보 6,300건 생성 후 사용자 후보와 조인 |
| 최근 메시지 조회 | 상위 20개 대화 x 10,000건 재조회 후 정렬 | 상위 20개 대화 x 3건 인덱스 순서 조회 |
| 최근 메시지 LATERAL | `rows=10000 loops=20` | `rows=3 loops=20` |

### 종합검색 포트폴리오 문장

```text
본문 검색과 최근 메시지 preview를 따로 호출하지 않고, 종합검색 결과의 대화 카드 안에 함께 포함되도록 쿼리를 재설계했습니다.
튜닝한 쿼리는 `/api/v1/search` 응답의 `conversationMessageResults`에 연결해 본문 매칭 수, 매칭 snippet, 최근 메시지 3개를 함께 반환하도록 적용했습니다.
초기 쿼리는 사용자 heavy 대화 50개에서 총 500,000건을 읽어 본문 조건을 집계하고, 최근 메시지 3개를 붙이기 위해 상위 20개 대화에서 다시 10,000건씩 읽어 정렬했습니다.
1,025,000메시지 벤치마크에서 EXPLAIN ANALYZE 기준 종합검색 전체 실행 시간은 972.709ms였습니다.
튜닝 후에는 lower(content) trigram GIN 인덱스로 본문 후보 6,300건을 먼저 만들고, 사용자 대화 후보와 조인한 뒤 후보 대화마다 최근 메시지 3건만 LATERAL로 조회했습니다.
그 결과 종합검색 전체 실행 시간은 40.582ms로 감소했고, 최근 메시지 조회는 rows=10000 loops=20에서 rows=3 loops=20으로 바뀌었습니다.
```

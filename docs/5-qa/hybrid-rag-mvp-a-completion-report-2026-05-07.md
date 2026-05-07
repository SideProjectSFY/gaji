# Hybrid RAG MVP-A 완료 보고서 - 2026-05-07

## 요약

MVP-A는 learner-facing chat에 RAG를 붙이기 전에 필요한 **검색 기반 RAG substrate**를 완성하고 검증한 단계다. `Pride and Prejudice`를 기준 소설로 삼아 ChromaDB vector search와 Elasticsearch BM25 search에 dual index했고, 인증된 검색/디버그/평가 API, passage manifest readiness persistence, 재현 가능한 release gate 리포트까지 구현했다.

최종 판정: **PASS**.

MVP-A를 통해 Gaji는 채팅 통합 전에 “소설 근거를 안정적으로 검색하고, 품질 수치로 검증할 수 있다”는 상태에 도달했다.

## 구현한 것

### Canonical AI Service 전환

- local Compose의 AI service를 `gajiAI/app` FastAPI 애플리케이션으로 전환했다.
- BM25 검색과 평가를 위해 Elasticsearch를 local development Compose에 추가했다.
- passage embedding 저장소로 ChromaDB를 유지했다.
- AI service 설정에 ChromaDB, Elasticsearch, Redis, Gemini embedding, AI broker JWT validation 값을 정리했다.

### Dual Retrieval Index

- `Pride and Prejudice` (`source_novel_id=gutenberg:1342`)를 두 검색 저장소에 색인했다.
  - ChromaDB collection: `novel_passages`
  - Elasticsearch alias: `gaji_novel_passages_current`
- ChromaDB와 Elasticsearch에서 동일한 canonical `passage_id`를 사용한다.
- passage ID는 novel/chunker/chapter/chunk/hash 구성으로 manifest-stable하게 생성된다.
- passage manifest metadata와 readiness 상태는 Spring internal API를 통해 PostgreSQL에 저장된다.

### RAG API

- `POST /v1/rag/index/novels/{novel_id}`: passage manifest 생성, embedding 생성, ChromaDB upsert, Elasticsearch bulk index, reconciliation 수행.
- `POST /v1/rag/search/passages`: `bm25`, `vector`, `hybrid` 검색 지원.
- `POST /v1/rag/search/evaluate`: release gate evaluation 실행 및 Markdown/JSON 리포트 생성.
- 검색 응답에는 final rank, vector/BM25 rank, RRF score, component scores, timing, fallback status, grounding status, manifest metadata, config metadata가 포함된다.

### 인증과 노출 제어

- 기존 chat broker scope인 `ai:chat:complete`는 유지했다.
- RAG endpoint에는 별도 scope를 추가했다.
  - `rag:read`
  - `rag:debug`
  - `rag:evaluate`
  - `rag:index`
- 일반 사용자의 RAG read에는 novel ownership claim을 검사한다.
- passage text/debug payload는 `rag:debug` 뒤에만 노출된다.
- RAG index/evaluate/debug 권한은 `ADMIN` 또는 `DEVELOPER`로 제한했다.

### Retrieval 품질과 Ranking

- BM25, vector, hybrid 검색을 구현했다.
- 동일 golden query 반복 평가에서 Gemini embedding quota를 낭비하지 않도록 query embedding cache를 추가했다.
- Gemini embedding quota 대응을 위해 multi-key rotation을 구현했다.
- BM25 품질을 높이기 위해 검색 의도어를 제거하는 lexical query normalization을 추가했다.
- corpus 밖 질의나 unsupported term에 대한 OOD/miss 처리를 추가했다.
- product ranking concern은 `vector_primary_rrf_fallback` 정책으로 닫았다.
  - vector retrieval이 정상일 때 vector rank order를 보존한다.
  - BM25-only 후보는 vector 후보가 부족하거나 fallback이 필요한 경우에 뒤를 채운다.
  - RRF component rank/score metadata는 debug/evaluation 관측성을 위해 계속 반환한다.

## 최종 Release Gate 수치

최신 산출물:

- Markdown: `gajiAI/reports/rag/rag_eval_1778131315.md`
- JSON: `gajiAI/reports/rag/rag_eval_1778131315.json`
- QA gate log: `docs/5-qa/hybrid-rag-mvp-a-release-gate-rerun-2026-05-07.md`

| Mode | Hit@10 | MRR | nDCG@10 | FalsePositive@10 | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | `0.600` | `0.508` | `0.272` | `0.000` | `6.88ms` |
| Vector | `1.000` | `0.910` | `0.886` | `0.000` | `19.02ms` |
| Hybrid | `1.000` | `0.910` | `0.886` | `0.000` | `20.17ms` |

최종 gate:

| Gate | Result |
| --- | --- |
| `quality_hit10_gate` | PASS |
| `quality_ndcg10_gate` | PASS |
| `negative_false_positive10_gate` | PASS |
| `latency_p95_ms_gate` | PASS |
| `hybrid_hit10_lift_vs_bm25` | `+0.400` |
| `hybrid_hit10_lift_vs_vector` | `+0.000` |
| `hybrid_mrr_delta_vs_vector` | `+0.000` |
| `hybrid_ndcg10_delta_vs_vector` | `+0.000` |
| `hybrid_no_regression_vs_vector_gate` | PASS |
| API `passed` | PASS |

## 설명 가능한 성과

다음과 같이 설명할 수 있다:

> MVP-A에서는 Gaji의 Hybrid RAG 검색 기반을 구현하고 검증했다. AI service는 canonical passage를 vector store와 lexical store에 dual index하고, BM25/vector/hybrid 검색을 제공하며, RAG 권한 경계와 passage manifest readiness를 관리한다. 또한 golden query 기반 release gate를 통해 hybrid retrieval이 BM25보다 우수하고 vector 대비 ranking regression이 없음을 수치로 확인했다.

아직 MVP-A만으로 설명하면 안 되는 것:

- learner-facing RAG chat 전체 완성
- conversation memory, character persona, scenario state까지 포함한 grounded response
- frontend citation UX

위 항목들은 MVP-B 이후 범위다.

## MVP-B 인계 사항

MVP-B는 MVP-A substrate를 `/v1/chat/completions`에 연결한다.

- 대상 endpoint: `/v1/chat/completions`
- 기본 retrieval mode: `hybrid`
- ranking policy: `vector_primary_rrf_fallback`
- chat token: 기존 `ai:chat:complete`
- retrieval authorization: novel ownership claim 또는 operator role
- 사용자 응답: answer plus citation metadata
- passage text는 내부 prompt context로만 사용하고, 응답에는 citation metadata만 반환한다.

## 현재 MVP-B 진행 상태

MVP-B의 learner chat integration 핵심 경로까지 진행했다. `/v1/chat/completions`는 이제 RAG context attachment 후 실제 Gemini direct generation service를 호출하고, Spring backend gateway와 learner conversation message flow에서도 동일 chat completion flow를 사용할 수 있다.

- 요청에서 `rag.enabled=true`와 `rag.novel_id`가 오면 내부적으로 hybrid retrieval을 실행한다.
- retrieval 결과의 passage text는 Gemini prompt context 구성에만 사용한다.
- retrieved passage text는 source-material block으로 감싸고, prompt-control 문구로 보이는 텍스트는 escape marker를 붙여 모델 지시문으로 해석되지 않게 한다.
- prompt context는 `[1]`, `[2]` 같은 passage 번호와 canonical `passage_id`를 함께 제공해 모델 citation 지시와 metadata citation을 맞춘다.
- composed grounded prompt를 Gemini generation call에 전달한다.
- Gemini generation은 multi-key quota rotation을 지원하는 별도 direct chat generation service를 통해 실행한다.
- direct chat 기본 `thinking_budget=0`으로 짧은 응답에서 hidden thinking이 출력 예산을 잠식하는 문제를 방지한다.
- provider generation failure는 endpoint에서 `503`으로 안전하게 매핑한다.
- retrieval failure fallback은 `grounding_status=fallback_ungrounded`, `fallback_used=true`, `fallback_reason=retrieval_exception` metadata를 반환한다.
- 응답에는 passage text를 노출하지 않고 citation metadata, grounding status, timing, manifest/config metadata만 반환한다.
- non-operator token은 `novel_ids` claim으로 novel ownership을 검사한다.
- 기존 RAG 없는 chat 요청과 legacy path는 호환을 유지한다.
- generation prompt와 retrieval query를 분리했다.
  - retrieval query는 사용자의 원문 질의를 짧게 정리한 `rag.query`로 전달한다.
  - generation prompt에는 conversation id, novel metadata, scenario what-if/change summary, character persona/speaking style, recent history, current user message를 포함한다.
  - FastAPI 응답 metadata에는 `query_source=rag.query` 또는 `prompt`가 기록된다.
- 테스트에서는 Gemini 호출을 fake service로 격리했고, Docker smoke에서는 실제 provider 응답을 확인했다.
- Spring `POST /api/v1/ai/chat/completions` 프록시를 추가했다.
  - Spring access token을 검증한 뒤 internal AI broker token을 발급한다.
  - RAG 요청이면 `rag.novelId`를 확인하고 broker token의 `novel_ids` claim에 포함한다.
  - generic direct RAG proxy는 conversation ownership context가 없으므로 `ADMIN`/`DEVELOPER`만 허용한다.
  - FastAPI `/v1/chat/completions`로 request/response를 전달한다.
  - null RAG optional field는 직렬화하지 않아 FastAPI strict schema validation과 맞춘다.
- Spring `POST /api/v1/conversations/{conversationId}/messages/chat-completion`을 추가했다.
  - user message 저장과 assistant message 저장은 짧은 DB transaction으로 분리한다.
  - canonical AI chat completion remote call은 DB transaction 밖에서 실행한다.
  - answer와 citation metadata를 같은 응답으로 반환한다.
  - 일반 사용자는 conversation owner만 호출할 수 있고, `ADMIN`/`DEVELOPER`는 operator smoke와 운영 확인을 위해 허용한다.
  - MVP seed data에서 P&P character id가 `_1342`로 끝나는 경우 canonical indexed novel id로 해석한다.
  - legacy conversation/message 저장 경로의 JPA UUID 수동 지정 충돌을 제거했다.
- Frontend conversation send path는 새 chat-completion endpoint를 우선 사용한다.
  - 응답의 RAG citation metadata를 assistant message에 붙인다.
  - chat bubble은 `grounding_status`, ranking policy, passage id citation pills를 보여준다.
  - passage text는 UI에 노출하지 않는다.
  - local 32s race timeout을 제거하고 API timeout 발생 시 conversation을 재동기화한다.
  - optional fork relationship API가 미구현/다른 shape를 반환해도 콘솔 에러 없이 graceful degrade한다.
- Gemini generation service는 quota rotation 외에 transient provider 5xx도 재시도한다.

## 검증

최신 검증:

- `pytest -o addopts='' tests`: `55 passed`
- `pytest -o addopts='' tests/test_direct_chat_generation_service.py tests/test_direct_chat.py`: `12 passed`
- `python -m compileall -q app scripts tests`: passed
- `./gradlew :apps:api-app:test --tests '*AiChatProxyServiceTest'`: passed
- `./gradlew :apps:api-app:test --tests 'com.gaji.ai.*'`: passed
- `./gradlew :apps:api-app:test`: passed
- `pnpm test:run src/components/chat/__tests__/ChatMessage.spec.ts src/stores/__tests__/conversation-fork.spec.ts`: `12 passed`
- `pnpm build`: passed
- `pnpm exec vue-tsc --noEmit`: failed on pre-existing project-wide type errors unrelated to this change.
- Docker health: FastAPI, ChromaDB, Elasticsearch, PostgreSQL, Redis 모두 healthy.
- Docker E2E smoke:
  - endpoint: `POST /v1/chat/completions`
  - request: `rag.enabled=true`, `mode=hybrid`
  - result: `200`
  - provider: `gemini`
  - `grounding_status=grounded`
  - `ranking_policy=vector_primary_rrf_fallback`
  - citation metadata returned
  - citation payload does not include passage text
- Spring gateway E2E smoke:
  - endpoint: `POST /api/v1/ai/chat/completions`
  - flow: Spring auth token -> AI broker token -> FastAPI chat completion -> hybrid RAG -> Gemini
  - result: `200`
  - provider: `gemini`
  - `grounding_status=grounded`
  - `ranking_policy=vector_primary_rrf_fallback`
  - citation count: `2`
  - citation payload does not include passage text
- Spring RAG authorization E2E smoke:
  - admin direct RAG proxy: `200`
  - non-operator direct RAG proxy: `403`
  - learner-owned conversation RAG: `200`
  - non-owner conversation RAG: `403`
- Learner conversation E2E smoke:
  - endpoint: `POST /api/v1/conversations/{conversationId}/messages/chat-completion`
  - flow: Spring auth token -> conversation message save -> AI broker token -> FastAPI chat completion -> hybrid RAG -> Gemini -> assistant message save
  - result: `200`
  - create conversation pre-step: `201`
  - provider: `gemini`
  - `grounding_status=grounded` for the canonical P&P assembly smoke query
  - `query_source=rag.query`
  - `ranking_policy=vector_primary_rrf_fallback`
  - citation count: `4`
  - citation payload keys: `passage_id`, `final_rank`, `vector_rank`, `bm25_rank`, `scores`, `metadata`
  - passage text is not returned
  - persisted DB turn check: latest roles are `system`, `user`, `assistant`
  - latest measured provider path latency: `2286.9ms`
- Browser UI smoke:
  - route: `/conversations/{conversationId}`
  - login -> send learner message -> grounded assistant response rendered
  - citation pills rendered: `4`
  - grounding label: `grounded`
  - raw passage text is not rendered
  - input re-enabled after response
  - unexpected console errors: `0`
  - screenshot: `/tmp/gaji-mvp-b-findings-ui-smoke.png`

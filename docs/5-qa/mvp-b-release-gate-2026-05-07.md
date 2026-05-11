# MVP-B Release Gate Closure

Date: 2026-05-07

Decision: PASS with non-blocking concerns

## Scope

MVP-B validates learner-facing hybrid RAG chat integration after MVP-A retrieval indexing/evaluation.

In scope:

- Spring learner endpoint: `POST /api/v1/conversations/{conversationId}/messages/chat-completion`
- Spring to canonical Spring RAG module proxy
- Spring Boot direct chat endpoint: `POST /api/v1/ai/chat/completions`
- Hybrid retrieval context insertion, citation metadata, prompt-injection guardrails
- Conversation owner authorization and persisted user/assistant turns

Out of scope:

- Streaming chat
- Multi-novel production rollout
- Full frontend browser regression across all pages
- Long-running load test beyond the live smoke sample below

## Fixes Applied During Gate

1. `gajiBE/app/routers/rag.py`
   - Added `fallback_reason` for degraded/partial retrieval responses.
   - Keeps clients and QA gates from seeing `fallback_used=true` with no reason.

2. `gajiBE/app/routers/direct_chat.py`
   - Propagates RAG `fallback_reason` into learner chat metadata.

3. `gajiBE/app/services/elasticsearch_passage_client.py`
   - Relaxed BM25 match operator from `and` to `or`.
   - Result: natural learner questions no longer degrade to vector-only retrieval when extra words are present.

4. `gajiBE/domains/chat-domain/src/main/java/com/gaji/chat/domain/model/Message.java`
   - Added `@PrePersist` timestamp fallback for `createdAt`.

5. `gajiBE/src/main/resources/db/migration/ddl/V58__backfill_message_created_at.sql`
   - Backfilled existing null `messages.created_at`.
   - Enforced `messages.created_at NOT NULL`.

## Environment Readiness

| Dependency | Result |
| --- | --- |
| Spring backend `localhost:18083` | `UP` |
| Spring RAG module | `healthy` |
| Gemini API | `connected` |
| pgvector | `connected` |
| Elasticsearch | `green` |
| Redis | `connected` |
| PostgreSQL | `UP` |

Flyway migration V58 applied successfully. DB check after final E2E:

- `messages.created_at IS NULL`: `0`
- total messages in test DB after gate: `64`

## Automated Gates

| Area | Command | Result |
| --- | --- | --- |
| Spring RAG module | `/tmp/gajiBE-test-venv/bin/python -m pytest -o addopts='' tests` | 55 passed |
| Spring API app | `./gradlew :apps:api-app:test` | BUILD SUCCESSFUL |
| Frontend typecheck | `pnpm exec vue-tsc --noEmit` | passed |
| Frontend unit tests | `pnpm test:run -- --reporter=dot` | 28 files, 267 tests passed |
| Frontend build | `pnpm build` | built successfully |

Non-blocking frontend warnings remain:

- Vite chunk size warning for the main bundle.
- Vite dynamic import warning for modules also imported statically.
- Test-console warnings from mocked router/3D/i18n paths, but no failed assertions.

## Live Spring Gateway E2E

Test conversation:

- Conversation: `770e8400-e29b-41d4-a716-446655440001`
- Owner: `jane.austen@gaji.com`
- Non-owner negative test: `test.user@gaji.com`
- Model: `gemini-2.5-flash`
- Retrieval: hybrid RAG over Pride and Prejudice

Authorization check:

| Case | Result |
| --- | --- |
| Non-owner sends to owner conversation | HTTP 403 |

Grounded chat sample:

| Query | HTTP | Grounding | Fallback | Citations | Text Leak | Latency |
| --- | --- | --- | --- | --- | --- | --- |
| Hunsford rejection evidence | 200 | grounded | false | 4 | false | 2789.0 ms |
| Prompt-injection red-team query | 200 | grounded | false | 4 | false | 5128.6 ms |
| Concise Hunsford answer | 200 | grounded | false | 4 | false | 3085.0 ms |

Latency summary:

- Count: 3 live provider requests
- Min: 2789.0 ms
- Median: 3085.0 ms
- Max: 5128.6 ms

Gate assertions:

- Owner requests return 200: PASS
- Non-owner access returns 403: PASS
- All live responses are grounded: PASS
- No retrieval fallback used: PASS
- Citations are present: PASS
- Citation metadata does not expose raw passage text: PASS
- Prompt-injection probe did not reveal system/context markers: PASS
- User and assistant `createdAt` returned from final E2E: PASS
- Persisted DB messages have non-null `created_at`: PASS

## Residual Concerns

1. Live provider sample is intentionally small.
   - This gate validates integration correctness, security shape, and real Gemini latency.
   - Before public release, run a larger concurrency gate, for example 5 concurrent users with 50-100 measured chat turns.

2. Frontend bundle size needs follow-up.
   - Build passes, but the main JS chunk is larger than Vite's default warning threshold.
   - Recommended next step: manual chunks for PrimeVue/Tres/Three and route-level lazy loading cleanup.

3. Test logs are noisy.
   - Vitest passes, but mocked 3D/router/i18n paths emit warnings.
   - Recommended next step: clean test setup mocks so warnings become meaningful again.

## Final Gate Result

MVP-B release gate is closed as PASS with non-blocking concerns.

The learner chat path now performs a real Spring-authenticated conversation turn, retrieves hybrid RAG context from the Spring RAG module, returns grounded citation metadata without passage text leakage, persists both user and assistant messages, blocks non-owner writes, and keeps fallback metadata contract-grade.

Recommended next story: MVP-C RAG Chat Hardening and Observability.

Suggested story goals:

- Add chat latency/concurrency release runner.
- Add structured RAG metadata persistence or analytics events for each assistant turn.
- Add frontend citation drawer/source inspection behind a safe debug/admin surface.
- Add streaming/SSE or async job mode if synchronous Gemini latency becomes UX friction.
- Reduce frontend bundle/test-warning debt before broader beta.

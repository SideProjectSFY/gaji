# MVP-C Citation Source Lookup

Date: 2026-05-07

Decision: PASS for implementation and source lookup smoke, CONCERNS remain for Gemini generation capacity

## Scope

This story makes persisted RAG chat citations inspectable from the learner chat UI without storing passage text in PostgreSQL.

Implemented:

- Spring source lookup endpoint for assistant-message RAG citations.
- Spring Boot exact passage source endpoint backed by Elasticsearch.
- Learner-bounded `rag:read` broker token path used only by Spring source lookup.
- Chat citation drawer in the frontend.
- Unit, type, build, and live source lookup smoke verification.

Deferred:

- Historical message hydration with RAG metadata on initial conversation load.
- Dedicated source analytics events.
- Larger generation-quality gate re-run after Gemini quota recovery.

## API

Spring:

- `GET /api/v1/conversations/{conversationId}/messages/{assistantMessageId}/rag-sources`

Spring Boot internal:

- `POST /api/v1/conversations/{id}/messages/{assistantMessageId}/rag-sources`

The Spring endpoint verifies the conversation owner or operator role, reads only persisted citation IDs/ranks from PostgreSQL, then asks Spring Boot for exact source text by passage ID. PostgreSQL still does not store passage text, prompts, or embeddings.

## Security

- Non-owners receive 403 from the Spring endpoint.
- Regular users still cannot request arbitrary public RAG scopes through `/api/v1/ai/chat/completions`.
- Source lookup uses a dedicated bounded broker path that issues only `rag:read` and only with the citation novel ID claim.
- Spring Boot re-checks `novel_ids` before returning exact passage sources.
- The frontend renders source text as text interpolation, not HTML.

## Frontend

Updated:

- `gajiFE/src/components/chat/ChatMessage.vue`
- `gajiFE/src/services/conversationApi.ts`
- `gajiFE/src/stores/conversation.ts`
- `gajiFE/src/views/ConversationChat.vue`

Behavior:

- Citation pills are now keyboard-focusable buttons.
- Opening a citation loads source passages for that assistant message.
- The drawer shows rank, chapter, passage ID, source text, loading state, error state, and unavailable-source state.

## Verification

Automated:

| Area | Command | Result |
| --- | --- | --- |
| Spring RAG module | `/tmp/gajiBE-test-venv/bin/python -m pytest -o addopts='' tests` | 63 passed |
| Spring API app | `./gradlew :apps:api-app:test` | BUILD SUCCESSFUL |
| Frontend tests | `pnpm vitest run` | 268 passed |
| Frontend type/build | `pnpm build:check` | PASS |

Live source lookup smoke:

| Check | Result |
| --- | --- |
| Owner source lookup | 200 |
| Citation count | 4 |
| Source available count | 4 |
| Missing passage IDs | 0 |
| First source text length | 1651 chars |
| Non-owner source lookup | 403 |

## Remaining Concern

The 10-warmup, 50-measured-request, 5-concurrency chat gate still fails because the configured Gemini generation keys exhaust daily free-tier quota. The app now falls back from `gemini-2.5-flash` to `gemini-2.5-flash-lite` before using the marked provider fallback, but release quality still requires a clean grounded run with a paid or otherwise sufficient generation quota.

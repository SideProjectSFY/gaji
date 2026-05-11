# RAG MVP Optimization Work Summary - 2026-05-07

## Context

This document summarizes the optimization work performed from the review basis:

- `docs/5-qa/rag-mvp-implementation-summary-and-performance-review-2026-05-07.md`

The work focused on MVP-A/B/C readiness items:

- P1 frontend bundle splitting
- P1 release gate automation
- P2 retrieval scaling preparation
- P2 source lookup cache
- P2 test warning noise cleanup

## Frontend Bundle Splitting

Changed files:

- `gajiFE/vite.config.ts`
- `gajiFE/src/router/index.ts`
- `gajiFE/src/services/api.ts`
- `gajiFE/src/components/chat/ConversationsSidebar.vue`

Implemented route-level lazy imports for Vue views so the initial application bundle no longer eagerly loads every route. Added Rollup manual chunks for large dependency groups:

- `vendor-three`
- `vendor-3d`
- `vendor-primevue`
- `vendor-motion`
- `vendor-utils`

Also removed a router dynamic import from the API interceptor by replacing it with a `gaji:navigate` browser event handled by the router. This eliminated Vite's mixed static/dynamic import warning. `ConversationsSidebar` now uses static service imports, removing another Vite chunking warning.

Build result after splitting:

- `index` bundle: about 159 kB minified, 57 kB gzip
- `vendor-primevue`: about 172 kB minified, 54 kB gzip
- `vendor-3d`: about 195 kB minified, 65 kB gzip
- `vendor-three`: about 719 kB minified, 187 kB gzip

The large Three.js payload remains large, but it is isolated away from the main application bundle.

## Release Gate Automation

Changed files:

- `gajiBE/scripts/run_rag_release_gate.py`
- `gajiBE/scripts/run_chat_release_gate.py`
- `gajiBE/tests/test_release_gate_runner.py`
- `gajiBE/tests/test_chat_release_gate_runner.py`

Added `--dry-run` support to the RAG and chat release gate runners. Dry runs validate configuration and write quota-safe reports without calling provider APIs.

Dry-run output includes:

- `status: dry-run-pass`
- `dry_run: true`
- provider readiness metadata
- quota-safe check metadata

This gives CI a safe default path while preserving provider-backed gates for manually approved runs with secrets.

## Retrieval Scaling Preparation

Changed files:

- `gajiBE/app/config/settings.py`
- `gajiBE/app/routers/rag.py`
- `gajiBE/app/services/elasticsearch_passage_client.py`
- `gajiBE/app/services/retrieval_evaluator.py`
- `gajiBE/tests/test_rag_search.py`

Added retrieval metadata needed to watch scaling pressure:

- `store_latency_ms.embedding`
- `store_latency_ms.vector`
- `store_latency_ms.bm25`
- `store_latency_ms.fusion`
- `store_latency_ms.total`
- `candidate_pool.top_k`
- `candidate_pool.vector_requested`
- `candidate_pool.bm25_requested`
- `candidate_pool.vector_returned`
- `candidate_pool.bm25_returned`
- `candidate_pool.fused_returned`
- saturation ratios for vector and BM25 candidate pools

Evaluation summaries and Markdown reports now aggregate candidate pool metrics, making it easier to notice when recall pressure or store latency starts growing before quality regresses.

Elasticsearch shard and replica counts are now configurable:

- `elasticsearch_number_of_shards`
- `elasticsearch_number_of_replicas`

Defaults remain development-friendly.

## Source Lookup Cache

Changed files:

- `gajiBE/app/config/settings.py`
- `gajiBE/app/routers/rag.py`
- `gajiBE/tests/test_rag_auth.py`
- `gajiFE/src/services/conversationApi.ts`

Added an in-memory short-lived LRU cache for `/api/v1/conversations/{id}/messages/{assistantMessageId}/rag-sources`. Authorization is still checked before cache lookup. Cache entries are keyed by novel ID and passage ID order, and responses are deep-copied before return.

Config knobs:

- `rag_source_lookup_cache_ttl_seconds`
- `rag_source_lookup_cache_max_entries`

The frontend now also caches RAG source lookups by conversation ID and assistant message ID. It caches in-flight promises as well as completed responses, so repeated citation drawer opens do not trigger duplicate backend requests.

## Direct Chat Streaming Support

Changed files:

- `gajiBE/app/routers/direct_chat.py`
- `gajiBE/app/services/direct_chat_generation_service.py`
- `gajiBE/tests/test_direct_chat.py`
- `gajiBE/tests/test_direct_chat_generation_service.py`
- `gajiBE/domains/ai-domain/src/main/java/com/gaji/ai/application/AiChatConcurrencyLimiter.java`
- `gajiBE/domains/ai-domain/src/main/java/com/gaji/ai/application/AiChatProxyService.java`
- `gajiBE/domains/chat-domain/src/main/java/com/gaji/chat/api/controller/MessageController.java`
- `gajiBE/domains/chat-domain/src/main/java/com/gaji/chat/application/MessageService.java`
- `gajiFE/src/views/ConversationChat.vue`
- `gajiFE/src/services/conversationApi.ts`

Added a streaming direct chat path that emits SSE events:

- `accepted`
- `context_ready`
- `delta`
- `completed`
- `error`

The frontend now attempts the streaming chat-completion endpoint and falls back to the previous polling path when the streaming endpoint is unavailable.

Spring Boot now has a streaming bridge from chat message submission to Spring Boot SSE:

- `AiChatProxyService.streamConversationChat(...)` forwards to `/api/v1/conversations/{id}/messages/chat-completion/stream`.
- `AiChatConcurrencyLimiter.executeFlux(...)` keeps concurrency permits held until the SSE stream terminates.
- `MessageController` now forwards intermediate stream events to the client instead of waiting for a single blocking completion result.
- `MessageService.submitMessageWithChatCompletionStream(...)` persists the user message first, forwards stream events, and saves the assistant turn when the completed event arrives.

## Test Warning Noise Cleanup

Changed files:

- `gajiFE/src/test-setup.ts`
- `gajiFE/src/components/CharCounter.vue`
- `gajiFE/src/components/__tests__/ScenarioCreationModal.spec.ts`
- `gajiFE/src/components/chat/__tests__/ForkNavigationWidget.spec.ts`
- `gajiFE/src/components/chat/__tests__/MemoEditor.spec.ts`
- `gajiFE/src/components/common/__tests__/LikeButton.spec.ts`
- `gajiFE/src/stores/__tests__/auth.spec.ts`
- `gajiFE/src/views/__tests__/LikedConversations.spec.ts`
- `gajiFE/src/components/chat/ConversationsSidebar.vue`
- `gajiFE/src/components/chat/MemoEditor.vue`
- `gajiFE/src/components/common/FollowButton.vue`
- `gajiFE/src/views/Profile.vue`

Reduced noisy test output by:

- Disabling Vue i18n missing/fallback warnings in test setup.
- Stubbing router and Tres components globally in tests.
- Allowing `CharCounter` to handle `null` and `undefined` text without prop warnings.
- Adding missing test routes for router-based component specs.
- Suppressing expected `console.error` calls inside negative-path tests.
- Mocking MemoEditor's conversation memo API dependency so tests do not leak real HTTP calls.
- Removing debug `console.log` and placeholder toast console output from components that were polluting test runs.

The previously observed `ECONNREFUSED localhost:3000` output was traced to MemoEditor mounting with an unmocked memo fetch path. The spec now mocks that API dependency.

## Verification

Frontend:

```bash
cd gajiFE
pnpm vitest run --reporter=verbose --sequence.concurrent false
pnpm test:run
pnpm build:check
```

Results:

- `28 passed (28)` test files
- `271 passed (271)` tests
- verbose run no longer prints the previous component debug logs or `ECONNREFUSED localhost:3000`
- production build completed without Vite chunk warnings

AI backend:

```bash
cd gajiBE
uv run --with-requirements requirements.txt pytest -q -o addopts='' \
  tests/test_release_gate_runner.py \
  tests/test_chat_release_gate_runner.py \
  tests/test_rag_search.py \
  tests/test_rag_auth.py \
  tests/test_elasticsearch_passage_client.py \
  tests/test_direct_chat.py \
  tests/test_direct_chat_generation_service.py
```

Result:

- `51 passed`

Release gate dry runs:

```bash
cd gajiBE
uv run --with-requirements requirements.txt python scripts/run_rag_release_gate.py --dry-run --output-dir /tmp/gaji-rag-gate
uv run --with-requirements requirements.txt python scripts/run_chat_release_gate.py --dry-run --output-dir /tmp/gaji-rag-gate
```

Result:

- RAG gate: `dry-run-pass`
- Chat gate: `dry-run-pass`

Backend:

```bash
cd gajiBE
./gradlew :apps:api-app:test --no-daemon
```

Result:

- `BUILD SUCCESSFUL`

## Remaining Notes

- Provider-backed release gates require real provider secrets and should be run intentionally, not on every PR.
- The source lookup cache is process-local. If the Spring RAG module is horizontally scaled, cache hit rates are per instance unless a shared cache is introduced.
- `vendor-three` remains the largest frontend artifact, but it is now split from the main route payload.
- Elasticsearch shard and replica defaults are conservative for development; staging and production should tune them based on corpus size and node count.

## Provider-Backed Gate Follow-Up

Additional review fixes were applied after the first provider-backed gate run:

- RAG negative/OOD abstention no longer bypasses abstention merely because BM25 returned a weak hit.
- A regression test now verifies that a weak BM25 match does not allow an unsupported hybrid query to return RAG hits.
- SSE chat streaming now marks the stream closed on completion, timeout, or error; failed `emitter.send()` calls stop the background stream consumer instead of continuing provider work after disconnect.

Rebuild/redeploy:

- Rebuilt `backend service` image: `74e3ad198209`
- Rebuilt `gaji-backend` image: `8404183a1f3b`
- Recreated `backend service`
- Recreated `gaji-backend-rag-e2e` on `http://localhost:18083`

Latest provider-backed results:

- RAG gate: `PASS`, `docs/5-qa/release-gate-runs/rag_release_gate_1778152342.json`
- Hybrid `FalsePositive@10`: `0.0`
- `negative_false_positive10_gate`: `true`
- Stream chat gate: `PASS`, `docs/5-qa/release-gate-runs/chat_release_gate_1778152361.json`
- Stream p95 latency: `3383.6 ms`
- Local staging smoke: `PASS`, `docs/5-qa/release-gate-runs/staging_smoke_1778152859.json`
- Smoke stream endpoint status: `200`

Latest focused verification:

- AI focused tests: `55 passed`
- Backend API app tests: `BUILD SUCCESSFUL`
- Release-gate runner CI subset: `10 passed`
- Release-gate workflow YAML parsed successfully

Automation follow-up:

- `.github/workflows/rag-mvp-release-gates.yml` now installs `gajiBE/requirements.txt` in both AI dry-run and provider-backed jobs before running tests or gate scripts.

## Second Review Follow-Up

The follow-up adversarial review found and closed three additional issues:

- RAG OOD coverage now fails closed when `query_term_coverage()` is unavailable for vector/hybrid queries.
- Frontend RAG source cache is now stored in `src/services/ragSourceCache.ts` and is cleared on auth save, refresh failure, logout start, and cookie/session teardown.
- API 404 routing no longer depends on a global `window` event listener. `src/services/navigation.ts` registers the Vue router when available and falls back to hard navigation only before router registration.

Latest verification after this round:

- AI focused tests: `56 passed`
- RAG auth/search focused tests: `24 passed`
- RAG provider-backed gate after fail-closed OOD fix: `PASS`, `docs/5-qa/release-gate-runs/rag_release_gate_1778159830.json`
- Frontend auth focused tests: `13 passed`
- Frontend unit tests: `28 passed`, `271 passed`
- Frontend build/typecheck: passed

## Performance Hardening Follow-Up

Additional performance items were applied after the MVP-A/B/C performance review:

- Spring chat prompt construction now loads only bounded recent history through `findRecentByConversationId(...)` instead of loading every message in the conversation. The default prior-message budget is controlled by `AI_CHAT_RECENT_HISTORY_MESSAGE_LIMIT`.
- Spring chat generation now uses a configurable answer budget through `AI_CHAT_MAX_OUTPUT_TOKENS`, defaulting to `768` to keep grounded answers tighter while preserving override room for experiments.
- Provider-backed RAG release automation now runs explicit `cold` and `warm` embedding-cache profiles. The cold profile clears query embedding cache before evaluation so cold-cache latency is measured separately from steady-state warm-cache latency.
- Provider-backed chat release automation now runs the `5,20,50` concurrency matrix by default and gates answer length with `chat_max_answer_chars_p95`.
- AI source lookup cache can now use Redis by setting `RAG_SOURCE_LOOKUP_CACHE_BACKEND=redis`; memory cache remains the default local mode, and Redis failures fall back to memory caching.

## Third Review Follow-Up

The final adversarial pass closed two additional edge cases:

- Frontend RAG source lookups now capture a cache generation and principal snapshot before the request starts. If auth teardown or auth principal changes while the request is in flight, the resolved response is discarded instead of being cached or rendered to the stale caller.
- RAG negative/OOD abstention now exposes `abstention_reason`. Elasticsearch coverage outages return `abstention_reason: ood_coverage_unavailable` and `errors.ood_coverage`, so monitoring and gate triage can distinguish retrieval health failures from ordinary `insufficient_context`.

Latest verification after this round:

- AI RAG search focused tests: `13 passed`
- AI focused tests: `57 passed`
- Frontend RAG source cache focused tests: `2 passed`
- Frontend unit tests: `273 passed`
- Frontend build/typecheck: passed

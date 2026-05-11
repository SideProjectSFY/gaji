# Provider-Backed Gate, Code Review, and Smoke Results - 2026-05-07

## Scope

Requested follow-up work:

- Run provider-backed release gates.
- Run code review.
- Run staging/local smoke checks.
- Fix review findings for RAG negative/OOD abstention and SSE disconnect handling.
- Rebuild/redeploy the AI and backend containers, then rerun the RAG and stream gates.

Provider inputs were used only as runtime environment for the gate execution path and were not written to repository files.

## Provider-Backed Release Gate Results

### RAG Release Gate

Latest command target:

- Spring Boot: `http://localhost:18083`
- Gaji AI Spring Boot: `http://192.168.156.7:8000`

Latest result file:

- `docs/5-qa/release-gate-runs/rag_release_gate_1778152342.json`

Outcome:

- Execution status: `complete`
- Release gate aggregate: `passed: true`

Key metrics:

- BM25 `Hit@10`: `0.9`
- Vector `Hit@10`: `1.0`
- Hybrid `Hit@10`: `1.0`
- Hybrid `nDCG@10`: `0.8858`
- Hybrid `FalsePositive@10`: `0.0`
- Hybrid latency p95: about `27.41 ms`
- Embedding query cache hit rate: `1.0`

Fixed gate:

- `negative_false_positive10_gate: true`

Interpretation:

The negative/OOD abstention fix removed the weak-BM25 bypass. Hybrid retrieval now keeps quality/latency gates green while returning no results for the negative golden queries.

### Chat Release Gate

Latest stream transport result file:

- `docs/5-qa/release-gate-runs/chat_release_gate_1778152361.json`

Outcome:

- `PASS`

Key stream metrics:

- Owner requests: all `200`
- Other user write probe: `403`
- Grounding: all `grounded`
- Fallback used: `false`
- Citations present: true
- Citation text leak: false
- Prompt marker revealed: false
- Stream events include `accepted`, `user_message`, `context_ready`, `delta`, and `completed`
- Delta events arrive before `completed`
- p95 latency: `3383.6 ms`, below the `8000 ms` gate
- Provider: `gemini`
- Model: `gemini-2.5-flash`

Earlier sync transport result file:

- `docs/5-qa/release-gate-runs/chat_release_gate_1778151452.json`

Outcome:

- `PASS`

Key sync metrics:

- Owner requests: all `200`
- Other user write probe: `403`
- Grounding: all `grounded`
- Fallback used: `false`
- Citations present: true
- Citation text leak: false
- Prompt marker revealed: false
- p95 latency: `3152.7 ms`, below the `8000 ms` gate
- Provider: `gemini`
- Model: `gemini-2.5-flash`

Interpretation:

The stream failure was deployment drift. Rebuilding and recreating `gaji-backend-rag-e2e` exposed the current `/chat-completion/stream` route and the stream gate now passes.

## Smoke Test Results

Latest result file:

- `docs/5-qa/release-gate-runs/staging_smoke_1778152859.json`

Checks:

- Owner login: `200`
- Conversation messages lookup: `200`
- Latest assistant source lookup: `200`
- Repeated source lookup: `200`
- Citation count: `4`
- Missing passage count: `0`
- Source text returned by explicit source lookup: `true`
- Stream endpoint status: `200`
- Stream event sequence: `accepted`, `user_message`, `context_ready`, `delta`, `completed`
- Delta before completed: `true`

Interpretation:

Core sync chat, explicit source lookup, and streaming route smoke checks are operational on the rebuilt backend container.

## Code Review Findings

### Fixed During Review - Streaming retry path could raise the wrong error before any chunks are emitted

File:

- `gajiBE/app/services/direct_chat_generation_service.py`
- `gajiBE/tests/test_direct_chat_generation_service.py`

Finding:

`stream_generate()` checks `emitted_any` in the exception path, but the variable is not initialized in the streaming loop before `client.models.generate_content_stream(...)` can fail. If Gemini raises before the first chunk, the handler can raise `UnboundLocalError` instead of marking quota errors, retrying transient failures, or falling back to the configured model.

Impact:

This can turn retryable provider failures into hard stream failures and will make stream behavior less reliable under quota, 5xx, or transport errors.

Fix applied:

Initialized `emitted_any = False` inside each streaming attempt before the `try` block, mirroring the sync generation path. Added a regression test where `generate_content_stream` raises before yielding and then succeeds on the next key.

### Fixed During Review - Source lookup cache could survive auth/session changes in the browser

File:

- `gajiFE/src/services/conversationApi.ts`

Finding:

The frontend RAG source cache is keyed only by `conversationId:assistantMessageId`. `clearRagSourceCache()` exists but is not called from logout or auth refresh failure paths.

Impact:

In a shared browser session, user B could receive cached source lookup data for a conversation/message opened by user A without a fresh authorization check. Server-side authorization remains correct, but the client cache bypasses the server once populated.

Fix applied:

The cache key now includes a principal component derived from the current user ID, or a hashed token fallback when user metadata is not available. This prevents cross-user reuse for the same conversation/message identifiers.

### Fixed - Streaming client disconnect does not stop provider work

File:

- `gajiBE/domains/chat-domain/src/main/java/com/gaji/chat/api/controller/MessageController.java`

Finding:

`sendSseEvent()` catches `IOException` and calls `completeWithError`, but it does not signal the background task or `MessageService` to stop consuming the provider stream. The background generation can continue and persist the assistant turn even after the client has gone away.

Impact:

Disconnected clients can still consume provider quota and write assistant messages that the client never received.

Fix applied:

The SSE controller now tracks stream liveness with an `AtomicBoolean`, flips it on completion/timeout/error, and treats failed `emitter.send()` as a stream cancellation. The event consumer throws a local cancellation exception so `MessageService.submitMessageWithChatCompletionStream(...)` exits instead of continuing provider consumption and assistant persistence after disconnect.

### Fixed - Negative/OOD abstention is bypassed when BM25 returns any result

File:

- `gajiBE/app/routers/rag.py`
- `gajiBE/tests/test_rag_search.py`

Finding:

`_should_abstain_for_unsupported_query()` returns `False` whenever `bm25_results` is non-empty. In the provider-backed RAG gate, this allowed negative queries to return results and caused `negative_false_positive10_gate` to fail.

Impact:

The system can look grounded for unsupported questions, raising hallucination risk and blocking the RAG release gate.

Fix applied:

Removed the early return that disabled abstention whenever BM25 returned any hit. Hybrid/vector searches now still evaluate query term coverage, so weak lexical overlap does not prevent abstention. Added a regression test where a negative/OOD query receives a weak BM25 hit but still abstains.

### Fixed In Second Review - OOD abstention failed open when coverage was unavailable

File:

- `gajiBE/app/routers/rag.py`
- `gajiBE/tests/test_rag_search.py`

Fix applied:

Coverage lookup failures now fail closed for OOD-capable modes. A regression test covers the degraded Elasticsearch coverage path.

### Fixed In Second Review - Source cache survived same-principal auth changes

File:

- `gajiFE/src/services/ragSourceCache.ts`
- `gajiFE/src/services/conversationApi.ts`
- `gajiFE/src/stores/auth.ts`
- `gajiFE/src/stores/__tests__/auth.spec.ts`

Fix applied:

RAG source cache storage was moved into a dedicated service and is cleared on auth save, refresh failure, logout start, and auth cookie/session teardown.

### Fixed In Second Review - 404 navigation depended on a global event listener

File:

- `gajiFE/src/services/navigation.ts`
- `gajiFE/src/services/api.ts`
- `gajiFE/src/router/index.ts`

Fix applied:

API 404 handling now calls a navigation service. The router registers itself at module initialization; before registration, the service falls back to direct browser navigation.

### Fixed In Third Review - In-flight source lookup could repopulate stale cache

File:

- `gajiFE/src/services/ragSourceCache.ts`
- `gajiFE/src/services/conversationApi.ts`
- `gajiFE/src/services/__tests__/ragSourceCache.spec.ts`
- `gajiFE/src/services/__tests__/conversationApi.spec.ts`

Fix applied:

RAG source cache writes now require the request-start cache generation to still be current. `getRagSources()` also captures the principal at request start and discards the resolved response if auth state changed while the lookup was in flight, preventing both stale cache repopulation and stale source rendering after logout.

### Fixed In Third Review - Coverage outage looked like ordinary insufficient context

File:

- `gajiBE/app/routers/rag.py`
- `gajiBE/tests/test_rag_search.py`

Fix applied:

OOD abstention now carries a structured `abstention_reason`. Coverage lookup failures still fail closed, but the response includes `abstention_reason: ood_coverage_unavailable` and `errors.ood_coverage`, so gates and monitoring can separate retrieval-health failures from normal insufficient-context abstention.

## Post-Fix Verification

After fixing the two direct code-review issues:

```bash
cd gajiBE
uv run --with-requirements requirements.txt pytest -q -o addopts='' \
  tests/test_release_gate_runner.py \
  tests/test_chat_release_gate_runner.py \
  tests/test_rag_search.py \
  tests/test_rag_auth.py \
  tests/test_elasticsearch_passage_client.py \
  tests/test_direct_chat_generation_service.py \
  tests/test_direct_chat.py

cd gajiFE
pnpm test:run
pnpm build:check
```

Results:

- AI focused tests: `56 passed`
- Frontend unit tests: `28 passed`, `271 passed`
- Frontend build/typecheck: passed
- Frontend auth focused tests: `13 passed`
- RAG provider-backed gate after second-review OOD fix: `PASS`, `docs/5-qa/release-gate-runs/rag_release_gate_1778159830.json`

Additional third-review verification:

- AI RAG search focused tests: `13 passed`
- AI focused tests: `57 passed`
- Frontend RAG source cache focused tests: `2 passed`
- Frontend unit tests: `273 passed`
- Frontend build/typecheck: passed

Backend:

```bash
cd gajiBE
./gradlew :apps:api-app:test --no-daemon
```

Result:

- `BUILD SUCCESSFUL`

Container rebuild/redeploy:

```bash
docker compose --env-file .env -f docker-compose.dev.yml build backend backend
docker compose --env-file .env -f docker-compose.dev.yml up -d --no-deps --force-recreate backend
```

Backend E2E container was recreated on host port `18083` from the rebuilt `gaji-backend` image.

Images:

- `gaji-backend`: `8404183a1f3b`
- `backend service`: `74e3ad198209`

## Release Recommendation

- RAG retrieval: releasable against the current provider-backed gate.
- Streaming chat path: releasable against the current provider-backed stream gate.
- Sync chat path: still releasable based on the earlier sync gate.
- Source lookup: operational; frontend cache isolation and AI-side lookup cache are both covered by the current implementation work.

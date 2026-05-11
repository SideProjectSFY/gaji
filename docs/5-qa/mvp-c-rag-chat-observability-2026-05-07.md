# MVP-C RAG Chat Hardening and Observability

Date: 2026-05-07

Decision: PASS for implementation, smoke gate, and provider load gate with the current preferred Gemini key

## Scope

This story starts MVP-C by closing the first observability loop for learner-facing RAG chat.

Implemented:

- Persist RAG chat turn metadata in PostgreSQL.
- Persist citation passage IDs and rank metadata without storing passage text.
- Return `ragMetadataId` and provider elapsed time in the learner chat response.
- Add a Spring learner chat latency/concurrency release runner.
- Harden Gemini generation retry behavior for transient provider errors.
- Return a marked fallback assistant response when retrieval succeeds but generation provider fails.
- Fall back from `gemini-2.5-flash` to `gemini-2.5-flash-lite` when the primary generation model hits quota/provider exhaustion.

Deferred:

- Frontend citation drawer/source inspection UI.
- Streaming/SSE or async job mode.

## Backend Persistence

New migrations:

- `gajiBE/src/main/resources/db/migration/ddl/V59__create_rag_chat_turn_observability.sql`
- `gajiBE/src/main/resources/db/migration/ddl/V60__add_rag_chat_turn_provider_latency.sql`

New tables:

- `rag_chat_turns`
- `rag_chat_turn_citations`

Stored fields include:

- `conversation_id`, `user_message_id`, `assistant_message_id`
- `novel_id`, `provider`, `model`
- `mode`, `grounding_status`, `fallback_used`, `fallback_reason`
- `ranking_policy`, `query_source`
- `passage_count`, `citation_count`, `token_usage`
- retrieval timing: `total_ms`, `embedding_ms`, `vector_search_ms`, `bm25_search_ms`, `fusion_ms`
- end-to-end provider call timing: `provider_elapsed_ms`
- citation metadata: `passage_id`, `final_rank`, `vector_rank`, `bm25_rank`, `manifest_id`, `chapter`

Explicitly not stored:

- passage text
- embeddings
- model prompt/context

## API Change

`POST /api/v1/conversations/{conversationId}/messages/chat-completion` now returns:

- existing `rag` metadata
- `ragMetadataId`
- `providerElapsedMs`

The frontend can ignore these fields safely, but QA and observability tools can use them immediately.

## Runner

New script:

- `gajiBE/scripts/run_chat_release_gate.py`

It validates:

- owner chat requests return 200
- non-owner write returns 403
- all measured turns are grounded
- no fallback is used
- citations are present
- citations do not contain raw passage text
- prompt-control markers are not leaked
- `createdAt`, `ragMetadataId`, and `providerElapsedMs` are returned
- p95 latency is within the configured gate

Example:

```bash
python scripts/run_chat_release_gate.py \
  --spring-base-url http://localhost:18083 \
  --warmups 1 \
  --measured-requests 5 \
  --concurrency 2 \
  --output-dir /tmp
```

## Generation Hardening

Updated:

- `gajiBE/app/services/direct_chat_generation_service.py`
- `gajiBE/app/routers/direct_chat.py`
- `gajiBE/app/services/api_key_manager.py`
- `gajiBE/app/config/settings.py`

Changes:

- transient Gemini 500/503 errors now back off before retrying
- retry attempts scale with configured key count
- final error now distinguishes quota exhaustion from retryable provider failure
- direct chat logs include a bounded error message for diagnosis
- if RAG retrieval succeeds but generation fails, Spring Boot returns a safe assistant fallback with:
  - `provider=fallback`
  - `grounding_status=fallback_ungrounded`
  - `fallback_used=true`
  - `fallback_reason=provider_generation_exception`
- if the primary generation model is quota-exhausted, generation retries configured fallback models before using the ungrounded provider fallback
- `GEMINI_PREFERRED_KEY_INDEXES` can restrict local testing to a known-good key index without exposing key material

## Verification

Automated tests:

| Area | Command | Result |
| --- | --- | --- |
| Spring RAG module | `/tmp/gajiBE-test-venv/bin/python -m pytest -o addopts='' tests` | 64 passed |
| Spring API app | `./gradlew :apps:api-app:test` | BUILD SUCCESSFUL |

Migration checks:

| Migration | Result |
| --- | --- |
| V59 create RAG chat observability tables | applied |
| V60 add provider latency column | applied |

Live DB checks after final smoke:

- `rag_chat_turns`: 2 rows
- `provider_elapsed_ms` populated: 1 row
- `rag_chat_turn_citations`: 8 rows
- Existing pre-V60 row keeps `provider_elapsed_ms` null as historical data.

Runtime provider checks after adding the current preferred Gemini key:

- Spring RAG module was recreated so `gajiBE/.env` env-file changes were loaded by Docker.
- Runtime key manager sees 6 configured Gemini keys and restricts the active local test pool to preferred key index 6.
- `VISION_PROVIDER_CODE=gemini` and `VISION_MODEL_NAME=gemini-2.5-flash` are visible inside `backend service`.
- Text generation probe against `gemini-2.5-flash`: PASS.
- Text generation fallback probe against `gemini-2.5-flash-lite`: PASS.
- Vision/multimodal probe with a 1x1 red PNG against `gemini-2.5-flash`: PASS, returned `Red` in 4468.0 ms.

## Live Runner Results

Initial stress probe:

```bash
python scripts/run_chat_release_gate.py \
  --spring-base-url http://localhost:18083 \
  --warmups 0 \
  --measured-requests 2 \
  --concurrency 1 \
  --output-dir /tmp
```

Output:

- JSON: `/tmp/chat_release_gate_1778140994.json`
- Decision: FAIL
- Cause: one request succeeded and persisted metadata; the next hit Gemini generation quota exhaustion.

Final smoke after retry/fallback hardening:

```bash
python scripts/run_chat_release_gate.py \
  --spring-base-url http://localhost:18083 \
  --warmups 0 \
  --measured-requests 1 \
  --concurrency 1 \
  --p95-latency-ms 30000 \
  --output-dir /tmp
```

Output:

- JSON: `/tmp/chat_release_gate_1778141323.json`
- Decision: PASS

Measured:

| Turn | HTTP | Grounding | Fallback | Citations | Text Leak | `ragMetadataId` | `providerElapsedMs` | Latency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 200 | grounded | false | 4 | false | present | 3141.8 ms | 3237.3 ms |

The smoke confirms the new persistence path, response fields, and gate runner work against the live stack.

## Decision

Implementation: PASS

Live smoke gate: PASS

Larger provider gate: PASS with the current preferred Gemini key

The code path is implemented, automated tests pass, the current provider key is usable for text and vision generation, and the learner-facing RAG chat release runner now passes the larger load gate without fallback.

## Larger Gate Re-Run

Command:

```bash
python scripts/run_chat_release_gate.py \
  --spring-base-url http://localhost:18083 \
  --warmups 10 \
  --measured-requests 50 \
  --concurrency 5 \
  --output-dir /tmp
```

Output:

- JSON: `/tmp/chat_release_gate_1778141749.json`
- Decision: FAIL
- HTTP/auth/metadata/citation/text-leak checks: PASS
- Latency p95: 4522.1 ms
- Failed assertions: `all_grounded`, `no_fallback_used`
- Cause: Gemini generation quota exhaustion caused provider fallback responses.

Follow-up key/model probe:

- `gemini-2.5-flash`: all configured keys returned daily free-tier generation quota exhaustion.
- `gemini-2.5-flash-lite`: individual requests could succeed on some keys, but repeated smoke/gate runs still exhausted available daily quota.

After model fallback hardening:

| Run | Output | Decision | Notes |
| --- | --- | --- | --- |
| 3 measured, 1 concurrency | `/tmp/chat_release_gate_1778143004.json` | PASS | `gemini-2.5-flash-lite`, all grounded, p95 7233.1 ms |
| 50 measured, 5 concurrency | `/tmp/chat_release_gate_1778143143.json` | FAIL | first 20+ measured grounded, later requests hit provider fallback as daily quota exhausted |
| preferred key smoke | `/tmp/chat_release_gate_1778143372.json` | FAIL | preferred key also produced fallback and p95 10031.3 ms |

Recommended next action:

1. Keep the current preferred Gemini key/project for release-gate verification, or move equivalent quota to the shared project before CI automation.
2. Add async retry/queue handling only if the marked provider fallback is not enough for learner UX.

## Preferred Key Gate Re-Run

The current preferred key was stored in `gajiBE/.env` without committing key material, then `backend service` was recreated so Docker reloaded the env-file.

Small smoke:

```bash
python scripts/run_chat_release_gate.py \
  --spring-base-url http://localhost:18083 \
  --warmups 0 \
  --measured-requests 3 \
  --concurrency 1 \
  --output-dir /tmp
```

Output:

- JSON: `/tmp/chat_release_gate_1778143762.json`
- Decision: PASS
- Model: `gemini-2.5-flash`
- Fallback used: false for all measured requests
- p95 latency: 2437.1 ms

Larger release gate:

```bash
python scripts/run_chat_release_gate.py \
  --spring-base-url http://localhost:18083 \
  --warmups 10 \
  --measured-requests 50 \
  --concurrency 5 \
  --output-dir /tmp
```

Output:

- JSON: `/tmp/chat_release_gate_1778143823.json`
- Decision: PASS
- Model: `gemini-2.5-flash`
- Owner requests: 50/50 HTTP 200
- Non-owner probe: HTTP 403
- Grounding: 50/50 grounded
- Fallback used: false for all measured requests
- Citations: present, 4 citations per response
- Citation text leak: false for all measured requests
- Prompt-control marker leak: false for all measured requests
- `ragMetadataId`, `createdAt`, and `providerElapsedMs`: present for all measured requests
- Latency: min 1611.8 ms, p50 2345.4 ms, p95 3427.8 ms, max 3865.4 ms

Conclusion:

- The previous larger-provider-load concern was quota-related, not a code-path failure.
- With the current preferred Gemini key, MVP-C RAG chat observability and generation fallback gates are release-ready.

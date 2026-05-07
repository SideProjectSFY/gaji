# MVP-C Streaming Chat Release Gate

Date: 2026-05-07

Decision: PASS

## Scope

This run validates the provider-backed learner chat path after the SSE/streaming work:

- Spring Boot chat endpoint: `/api/v1/conversations/{conversationId}/messages/chat-completion/stream`
- FastAPI generation endpoint: `/v1/chat/completions/stream`
- Retrieval-grounded Gemini response generation
- Citation metadata, RAG observability metadata, and source-text leak prevention
- Conversation ownership guard for another authenticated user

The test was run against the local Docker-backed E2E stack with PostgreSQL, Redis, ChromaDB, Elasticsearch, Spring Boot, FastAPI, and Gemini provider calls enabled.

## Preflight Fix

The first streaming smoke run found deployment drift and then a Spring boot failure after restarting the backend container. Root cause was `AiChatConcurrencyLimiter` having both the production constructor and a test constructor without an explicit injection marker. Spring attempted default construction and failed.

Fix applied:

- `AiChatConcurrencyLimiter` production constructor now has `@Autowired`.
- `gajiBE` test suite passed after the change.
- The backend E2E container restarted successfully and exposed the streaming endpoint.

## Protocol

Final run artifact:

- `docs/5-qa/release-gate-runs/chat_release_gate_1778152222.json`

Configuration:

| Item | Value |
| --- | --- |
| Transport | `stream` |
| Warmups | 10 |
| Measured requests | 100 |
| Concurrency | 5 |
| p95 latency gate | 8000 ms |
| Conversation | `770e8400-e29b-41d4-a716-446655440001` |
| Provider | Gemini |
| Model | `gemini-2.5-flash` |

## Gate Results

| Check | Result |
| --- | --- |
| Owner requests return 200 | PASS |
| Other authenticated user is forbidden | PASS, `403` |
| All measured responses are grounded | PASS |
| No fallback used | PASS |
| Citations present | PASS |
| Citation text not leaked in chat response | PASS |
| Prompt-control marker not revealed | PASS |
| User and assistant timestamps returned | PASS |
| `ragMetadataId` returned | PASS |
| `providerElapsedMs` returned | PASS |
| SSE `completed` event present | PASS |
| SSE `user_message` event present | PASS |
| SSE delta present | PASS |
| First delta emitted before completion | PASS |
| First delta latency recorded | PASS |
| p95 latency within gate | PASS |

Failed assertions: none.

## Performance

Measured request latency:

| Metric | Value |
| --- | ---: |
| Count | 100 |
| Min | 1434.0 ms |
| p50 | 2160.8 ms |
| p95 | 3371.9 ms |
| Max | 5388.0 ms |

First-token / first-delta latency:

| Metric | Value |
| --- | ---: |
| Count | 100 |
| Min | 817.1 ms |
| p50 | 1171.2 ms |
| p95 | 2155.2 ms |
| Max | 4241.7 ms |

Provider elapsed time:

| Metric | Value |
| --- | ---: |
| Count | 100 |
| Min | 1401.9 ms |
| p50 | 2126.7 ms |
| p95 | 3337.0 ms |
| Max | 5367.5 ms |

Output characteristics:

| Metric | Value |
| --- | ---: |
| Answer chars p50 | 942 |
| Answer chars p95 | 1805 |
| SSE delta count p50 | 6 |
| SSE delta count p95 | 10 |
| Citation count | 4 per measured response |
| Fallback count | 0 |
| Prompt marker leak count | 0 |
| Citation text leak count | 0 |
| Non-200 owner responses | 0 |

## Interpretation

The user-visible streaming path is release-ready for the current MVP-C contract. The important UX win is that the first streamed delta arrives at p50 1171.2 ms while full completion p50 is 2160.8 ms. That means the user sees the answer begin roughly one second earlier than waiting for the whole provider call to finish.

The remaining latency is provider-dominated: provider p95 is 3337.0 ms while end-to-end p95 is 3371.9 ms. Spring proxying, persistence, and SSE delivery are not the main bottleneck in this run.

## Remaining Concerns

- The release gate currently creates real messages in the seeded E2E conversation. A dedicated disposable gate conversation or reset step would keep repeated runs cleaner.
- The full JSON artifact is useful for audit but large. CI should publish it as a build artifact and keep Markdown summaries compact.
- The current gate confirms citation metadata is present and text is not leaked. A separate UI E2E should still assert drawer rendering and source lookup behavior in the browser.
- Gemini keys used for local testing should be treated as exposed development credentials and rotated before long-lived staging or production use.

## Recommended Next Step

Move this gate into release automation:

- Add a manual CI workflow or documented quality-gate job for `scripts/run_chat_release_gate.py`.
- Store Gemini and E2E account credentials in CI secrets instead of local `.env` files.
- Track operational metrics for fallback rate, provider p95, first-delta p95, quota exhaustion, and concurrency saturation.

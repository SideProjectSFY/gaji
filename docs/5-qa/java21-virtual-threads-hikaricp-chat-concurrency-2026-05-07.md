# Java 21 Virtual Threads & HikariCP Chat Concurrency Hardening

Date: 2026-05-07

## Goal

MVP-B/C chat path latency is dominated by remote AI/RAG work. The backend should therefore avoid holding database connections during provider calls, allow cheap request threads with Java 21 virtual threads, and protect the AI generation path with explicit capacity limits so HikariCP is not used as an accidental backpressure mechanism.

## What Changed

- CI backend jobs now use Java 21, matching the Gradle toolchain and Docker images.
- Spring virtual threads are enabled by default with `SPRING_THREADS_VIRTUAL_ENABLED=true`.
- HikariCP settings are environment-tunable for dev, staging, and production.
- Actuator metrics are tagged with the application name for dashboards.
- The chat completion proxy has a dedicated AI generation semaphore.
- Saturated chat generation returns HTTP 503 instead of piling up unlimited blocked calls.

## Configuration Knobs

| Area | Env var | Default | Purpose |
| --- | --- | --- | --- |
| Java threads | `SPRING_THREADS_VIRTUAL_ENABLED` | `true` | Enables Spring Boot virtual threads on Java 21. |
| AI chat guard | `AI_CHAT_MAX_CONCURRENT_GENERATIONS` | `10` | Max simultaneous `/api/v1/ai/chat/completions` proxy calls. |
| AI chat guard | `AI_CHAT_ACQUIRE_TIMEOUT_MS` | `500` | Wait time before returning 503 when chat capacity is saturated. |
| Hikari | `DB_HIKARI_POOL_NAME` | `GajiApiHikariPool` | Stable pool name for metrics and logs. |
| Hikari | `DB_HIKARI_MAXIMUM_POOL_SIZE` | profile-specific | Max database connections. |
| Hikari | `DB_HIKARI_MINIMUM_IDLE` | profile-specific | Minimum idle database connections. |
| Hikari | `DB_HIKARI_CONNECTION_TIMEOUT_MS` | profile-specific | How long callers wait for a DB connection. |
| Hikari | `DB_HIKARI_VALIDATION_TIMEOUT_MS` | `5000` | Connection validation timeout. |
| Hikari | `DB_HIKARI_IDLE_TIMEOUT_MS` | profile-specific | Idle connection retirement window. |
| Hikari | `DB_HIKARI_MAX_LIFETIME_MS` | profile-specific | Max connection lifetime. |
| Hikari | `DB_HIKARI_LEAK_DETECTION_THRESHOLD_MS` | `60000` | Long checkout warning threshold. |

## Transaction Boundary Check

`MessageService.submitMessageWithChatCompletion` already follows the correct boundary:

1. Save and validate the user message in a short transaction.
2. Call Spring Boot/Gemini outside the database transaction.
3. Save the assistant response and metadata in a second short transaction.

This means a slow provider call should not occupy a Hikari connection for the full AI generation time.

## Metrics to Watch

Spring Actuator should expose the Hikari pool shape under the standard Micrometer names:

- `hikaricp.connections.active`
- `hikaricp.connections.idle`
- `hikaricp.connections.pending`
- `hikaricp.connections.timeout`
- `hikaricp.connections.max`
- `http.server.requests`

For release gates, correlate these with:

- `gaji.ai.chat.generation.active`
- `gaji.ai.chat.generation.available`
- `gaji.ai.chat.generation.saturated`
- chat p50/p95/p99 latency
- Spring Boot provider elapsed time
- RAG fallback rate
- AI chat 503 saturation count
- Gemini quota/rate-limit errors

## 5/20/50 Concurrency Gate

Run the provider-backed chat gate only when Gemini keys and quota are intentionally available.

```bash
cd /Users/yeongjae/gaji/gajiBE

python scripts/run_chat_release_gate.py \
  --base-url http://localhost:8000 \
  --novel-id <indexed-novel-uuid> \
  --concurrency 5 \
  --warmups 10 \
  --measured-requests 100

python scripts/run_chat_release_gate.py \
  --base-url http://localhost:8000 \
  --novel-id <indexed-novel-uuid> \
  --concurrency 20 \
  --warmups 10 \
  --measured-requests 100

python scripts/run_chat_release_gate.py \
  --base-url http://localhost:8000 \
  --novel-id <indexed-novel-uuid> \
  --concurrency 50 \
  --warmups 10 \
  --measured-requests 100
```

Recommended gate interpretation:

- PASS: p95 remains within the product target, fallback rate is within tolerance, Hikari pending stays near zero, and no sustained 503 saturation appears at target traffic.
- CONCERNS: p95 degrades mainly from Gemini latency or quota limits, while Hikari remains healthy.
- FAIL: Hikari pending/timeouts rise, user message persistence fails, or saturation persists at the expected MVP traffic level.

## Initial Sizing Guidance

Start with:

- `AI_CHAT_MAX_CONCURRENT_GENERATIONS=10`
- `DB_HIKARI_MAXIMUM_POOL_SIZE=10` for local/dev
- `DB_HIKARI_MAXIMUM_POOL_SIZE=20` for staging/prod until real traffic proves otherwise

Then tune from the gate:

- If Hikari pending rises while provider latency is normal, inspect transaction boundaries and DB query time before increasing the pool.
- If provider latency dominates and Hikari is stable, increasing Hikari will not help. Tune chat async/SSE behavior and provider concurrency instead.
- If 503 appears too early but Gemini quota is healthy, raise `AI_CHAT_MAX_CONCURRENT_GENERATIONS` gradually and retest at 5/20/50.

## Residual Work

- Add dashboard panels for Hikari pending/timeouts and AI chat saturation.
- The CI/manual workflow now runs the 5/20/50 provider-backed chat gate when `rag-mvp-release-gates` is manually dispatched with provider gates enabled.
- Run the provider-backed chat release gate with `GAJI_CHAT_GATE_TRANSPORT=stream` and record first-delta/p95 latency from a seeded environment after secrets/quota are provisioned.

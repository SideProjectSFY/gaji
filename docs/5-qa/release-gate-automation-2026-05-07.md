# RAG / Chat Release Gate Automation

Date: 2026-05-07

## Purpose

MVP-A through MVP-C now have working retrieval, grounded chat, citation/source lookup, and streaming delivery. This document explains how to run the release gates without relying on a local developer shell.

The canonical automation entry point is:

- `.github/workflows/rag-mvp-release-gates.yml`

The workflow has three layers:

| Layer | Trigger | Purpose |
| --- | --- | --- |
| Frontend/backend dry gates | Pull request and manual | Unit/build/E2E checks that do not spend provider quota |
| AI runner dry run | Pull request and manual | Validates release-gate scripts and configuration shape without Gemini calls |
| Provider-backed release gates | Manual only | Runs live RAG and streaming chat gates against configured services |

Both AI gate jobs install `gajiAI/requirements.txt` before running tests or gate scripts, so CI exercises the same app dependencies used by the local runner.

## Manual Provider Gate

Run the workflow manually from GitHub Actions:

1. Open `rag-mvp-release-gates`.
2. Choose `Run workflow`.
3. Set `run_provider_gates=true`.
4. Keep the default release contract unless intentionally testing a smaller run.

Default contract:

| Input | Default |
| --- | ---: |
| `rag_warmup_queries` | 10 |
| `rag_min_latency_samples` | 100 |
| `rag_concurrency` | 5 |
| `chat_transport` | `stream` |
| `chat_warmups` | 10 |
| `chat_measured_requests` | 100 |
| `chat_concurrency` | 5 |
| `chat_p95_latency_ms` | 8000 |

## Required Secrets

Provider-backed gates require live service URLs, seeded E2E accounts, a seeded conversation, and provider credentials.

| Secret | Used By | Notes |
| --- | --- | --- |
| `FASTAPI_BASE_URL` | RAG gate | Public or VPN-accessible FastAPI gate target |
| `SPRING_BASE_URL` | RAG/chat gates | Spring API gateway target |
| `GAJI_GATE_ADMIN_EMAIL` | RAG gate | Admin/developer account able to issue `rag:evaluate` |
| `GAJI_GATE_ADMIN_PASSWORD` | RAG gate | Stored only as GitHub secret |
| `GAJI_GATE_NOVEL_ID` | RAG gate | Indexed Pride and Prejudice novel id |
| `GAJI_CHAT_GATE_OWNER_EMAIL` | Chat gate | Owner of the seeded gate conversation |
| `GAJI_CHAT_GATE_OWNER_PASSWORD` | Chat gate | Stored only as GitHub secret |
| `GAJI_CHAT_GATE_OTHER_EMAIL` | Chat gate | Authenticated non-owner used for 403 ownership check |
| `GAJI_CHAT_GATE_OTHER_PASSWORD` | Chat gate | Stored only as GitHub secret |
| `GAJI_CHAT_GATE_CONVERSATION_ID` | Chat gate | Seeded conversation with indexed novel context |
| `GEMINI_API_KEY` or `GEMINI_API_KEYS` | Provider config | Use GitHub secrets; rotate local keys before staging/prod |
| `RAG_READ_TOKEN` | Optional RAG shortcut | Avoids broker login for preflight if supplied |
| `RAG_EVALUATE_TOKEN` | Optional RAG shortcut | Avoids broker login for full evaluation if supplied |

Do not commit `.env` values or paste keys into reports. The workflow validates that required secrets exist but never prints their values.

## Expected Artifacts

Each provider-backed run uploads:

- `rag_release_gate_*.json`
- `chat_release_gate_*.json`
- GitHub job summary with RAG quality and chat streaming metrics

The chat summary highlights:

- request p50/p95/max
- first-delta p50/p95/max
- fallback count
- prompt-marker leak count
- citation text leak count
- failed assertions

The RAG summary highlights:

- release gate pass/fail
- Hit@10 by mode
- nDCG@10 by mode
- p95 latency by mode

## Operational Metrics To Track

Move these from release reports into staging/prod observability dashboards:

| Metric | Why It Matters | Suggested Initial Gate |
| --- | --- | --- |
| Chat request p95 | User-perceived completion delay | `< 8000 ms` |
| Chat first-delta p95 | User-perceived responsiveness | Track trend; current local full gate was `2155.2 ms` |
| Provider elapsed p95 | Separates Gemini latency from app overhead | Track trend |
| Fallback rate | Grounding/retrieval health | `0` for release gate |
| `grounding_status != grounded` rate | RAG answer quality | `0` for release gate |
| Citation text leak count | Debug/source exposure safety | `0` |
| Prompt-marker leak count | Prompt injection resistance | `0` |
| Gemini quota exhaustion count | Provider capacity planning | Alert on first occurrence |
| `gaji.ai.chat.generation.saturated` | Local concurrency limiter saturation | Alert when non-zero in steady traffic |
| Hikari active/idle/wait metrics | DB pool pressure during chat writes | Alert before connection starvation |

## Failure Triage

Common failure modes:

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| Provider job fails before gates start | Missing GitHub secret | Add the missing secret listed by the validation step |
| RAG gate is `blocked` with embedding quota | Gemini embedding quota exhausted | Rotate to allowed key pool or pause release |
| Chat owner requests return 404 | Spring deployment does not expose streaming endpoint | Deploy current backend and rerun smoke |
| Chat owner requests return 5xx | FastAPI/Gemini failure or Spring proxy failure | Inspect uploaded JSON, Spring logs, FastAPI logs |
| Other-user probe is not 403 | Conversation ownership regression | Block release |
| Citation text leak count > 0 | Debug/source exposure regression | Block release |
| First delta appears only at completion | Streaming regression | Block release for MVP-C UX |

## Current Baseline

Latest local provider-backed full run:

- Report: `docs/5-qa/mvp-c-streaming-chat-release-gate-2026-05-07.md`
- Artifact: `docs/5-qa/release-gate-runs/chat_release_gate_1778152222.json`
- Decision: `PASS`
- Chat request p95: `3371.9 ms`
- First-delta p95: `2155.2 ms`
- Fallback count: `0`
- Citation text leak count: `0`

Latest post-review gate closure:

- RAG artifact: `docs/5-qa/release-gate-runs/rag_release_gate_1778152342.json`
- RAG decision: `PASS`
- Hybrid `FalsePositive@10`: `0.0`
- Stream artifact: `docs/5-qa/release-gate-runs/chat_release_gate_1778152361.json`
- Stream decision: `PASS`
- Smoke artifact: `docs/5-qa/release-gate-runs/staging_smoke_1778152859.json`
- Smoke decision: `PASS`

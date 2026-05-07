# Gaji Hybrid RAG MVP Implementation Summary and Performance Review

Date: 2026-05-07

## Executive Summary

Gaji now has a working grounded AI chat foundation.

In plain language: instead of letting the AI answer from vague memory, the system now searches the actual novel text, uses the most relevant passages as evidence, answers the learner, stores citation metadata, and lets the user inspect the source passages through the chat UI.

The implemented scope covers:

- **MVP-A: Hybrid RAG search substrate**
- **MVP-B: Hybrid RAG chat integration**
- **MVP-C: Citation source drawer, grounding UX, observability, and E2E tests**
- **Next story prepared: Release Automation and Operational Gates**

Current release posture:

- Retrieval quality gate: **PASS**
- Learner chat integration gate: **PASS**
- Citation/source drawer implementation: **PASS**
- Frontend unit/build/E2E gate: **PASS**
- Remaining operational work: **CI/manual release automation and secret management**

## What We Built, For Non-Developers

### 1. A Search Engine for the Novel

The system can now search `Pride and Prejudice` in two ways:

- **Keyword search**: finds passages with matching words such as "Darcy", "proposal", or "inheritance".
- **Meaning search**: finds passages that are semantically related even when the exact words differ.

These two methods are combined into **hybrid search**, which gives the product both lexical precision and semantic flexibility.

### 2. AI Chat That Uses Evidence

When a learner asks a question, the AI service now:

1. Finds relevant novel passages.
2. Wraps those passages as source material.
3. Generates an answer based on the evidence.
4. Returns citation metadata with the answer.
5. Avoids exposing raw passage text directly in the chat-completion response.

This means Gaji can say:

> The AI answer is grounded in specific source passages from the novel, not just generated from general model memory.

### 3. Source Visibility in the Chat UI

The frontend now shows citation chips under grounded AI answers.

When the user clicks a citation:

- A source drawer opens.
- The drawer shows rank, chapter, passage ID, and source text when policy allows it.
- If source text is unavailable, the UI shows a clear policy message.
- Fallback or ungrounded answers are visibly marked.

This gives users a simple answer to:

> "Where did this AI answer come from?"

### 4. Safety and Trust Controls

The implementation includes guardrails:

- Users cannot inspect arbitrary novels they do not own or have access to.
- Admin/developer-only RAG scopes are separated from learner chat scope.
- Debug/source text access is separated from normal chat completion.
- Prompt-injection-like text inside retrieved passages is treated as source material, not as system instruction.
- Fallback responses are explicitly marked with `grounding_status`, `fallback_used`, and `fallback_reason`.

### 5. Quality Gates and Reports

The team added repeatable evaluation scripts and reports for:

- Retrieval quality
- Chat grounding
- Citation metadata
- Text leakage prevention
- Authorization
- Latency
- Fallback behavior
- Gemini quota exhaustion signals

## Technical Implementation Summary

## MVP-A: Hybrid RAG Search Substrate

### Services and Storage

- Canonical AI service: `gajiAI/app` FastAPI.
- Vector search store: ChromaDB.
- Lexical search store: Elasticsearch.
- Metadata persistence: PostgreSQL through Spring Boot internal APIs.
- Cache/storage coordination: Redis where needed.
- Embedding provider: Gemini embedding model.

### Indexed Corpus

- MVP novel: `Pride and Prejudice`
- Source novel ID: `gutenberg:1342`
- Passage IDs are canonical and manifest-stable.
- ChromaDB IDs and Elasticsearch `_id` values use the same passage ID.
- PostgreSQL stores manifest/readiness metadata, but not passage text or embeddings.

### Search Modes

Implemented API:

- `POST /v1/rag/index/novels/{novel_id}`
- `POST /v1/rag/search/passages`
- `POST /v1/rag/search/evaluate`
- `POST /v1/rag/sources/passages`

Search modes:

- `bm25`
- `vector`
- `hybrid`

Final hybrid policy:

- `vector_primary_rrf_fallback`
- Vector-backed candidates preserve vector ranking when vector retrieval is healthy.
- BM25 fills gaps and remains available for fallback/debug evidence.
- RRF component scores/ranks remain visible for observability.

### MVP-A Final Retrieval Metrics

Latest release gate:

| Mode | Hit@10 | MRR | nDCG@10 | FalsePositive@10 | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | 0.600 | 0.508 | 0.272 | 0.000 | 6.88ms |
| Vector | 1.000 | 0.910 | 0.886 | 0.000 | 19.02ms |
| Hybrid | 1.000 | 0.910 | 0.886 | 0.000 | 20.17ms |

Interpretation:

- Hybrid strongly beats BM25.
- Hybrid does not regress versus vector on Hit@10, MRR, or nDCG@10.
- Retrieval latency is already low compared with model generation latency.

## MVP-B: Learner-Facing RAG Chat Integration

### Chat Flow

Implemented learner path:

```text
Frontend chat
  -> Spring conversation endpoint
  -> AI broker token
  -> FastAPI /v1/chat/completions
  -> hybrid RAG search
  -> Gemini generation
  -> Spring persists user/assistant messages
  -> frontend renders answer and citation metadata
```

Important endpoints:

- FastAPI: `POST /v1/chat/completions`
- Spring generic AI proxy: `POST /api/v1/ai/chat/completions`
- Spring learner chat endpoint: `POST /api/v1/conversations/{conversationId}/messages/chat-completion`

### Prompt and Citation Safety

Implemented:

- Retrieval query is separated from the generation prompt.
- Retrieved passage text is wrapped as source material.
- Prompt-control-looking text is escaped/quarantined.
- Generated answer receives citation metadata.
- Raw passage text is not returned in chat-completion citation payloads.
- Fallback answers are marked as ungrounded when retrieval or generation fails.

### Persistence

PostgreSQL now stores RAG turn observability metadata:

- conversation ID
- user message ID
- assistant message ID
- novel ID
- provider/model
- mode
- grounding status
- fallback status/reason
- ranking policy
- query source
- passage/citation counts
- token usage
- retrieval timing
- provider elapsed time
- citation passage IDs and rank metadata

PostgreSQL explicitly does **not** store:

- passage text
- embeddings
- full prompt/context

## MVP-C: Citation Source Drawer and Grounding UX

### Frontend Behavior

Implemented in `gajiFE/src/components/chat/ChatMessage.vue`:

- Citation chips under AI answers.
- Grounding status badge.
- Fallback status and fallback reason badge.
- RAG metadata ID badge.
- Provider latency badge.
- Source drawer on citation click.
- Loading, error, missing-source, and unavailable-source states.

### Source Lookup

Implemented source lookup path:

```text
Frontend citation click
  -> Spring GET /api/v1/conversations/{conversationId}/messages/{assistantMessageId}/rag-sources
  -> Spring validates owner/operator
  -> Spring reads persisted citation IDs
  -> Spring issues bounded rag:read broker token
  -> FastAPI POST /v1/rag/sources/passages
  -> Elasticsearch exact passage lookup
  -> source drawer renders allowed text
```

### E2E Coverage

Playwright tests were added:

- `gajiFE/e2e/rag-citation-source-drawer.spec.ts`

Covered scenarios:

- Grounded answer shows citation chips, QA metadata, and source drawer.
- Retrieval fallback answer is visibly ungrounded and does not show a source drawer.
- Source-unavailable policy state is shown when passage text is not available.

Latest frontend release gate:

- `pnpm test:run`: 28 files, 271 tests passed.
- `pnpm build:check`: passed.
- `pnpm run test:e2e:chromium`: 3 passed.

## Security and Authorization

Implemented scope boundaries:

- `ai:chat:complete`: chat completion.
- `rag:read`: bounded RAG/source lookup.
- `rag:debug`: debug text.
- `rag:evaluate`: evaluation.
- `rag:index`: indexing.

Role/ownership rules:

- Learner chat requires conversation ownership.
- Non-owner learner write is rejected.
- Regular users cannot mint arbitrary RAG admin/debug scopes.
- RAG admin/debug/index/evaluate is limited to engineering/operator roles.
- Source lookup re-checks conversation ownership and novel claims.

Important security outcome:

- Normal chat responses include citations, not raw retrieved passage text.
- Source passage text is only retrieved through a separate owner/operator-checked path.

## BMAD Party-Mode Review Summary

### Mary, Business Analyst

The clearest product value is trust. Gaji can now claim that AI answers are tied to source evidence. The next product-facing message should avoid overclaiming "perfect correctness" and instead say "grounded, inspectable, and measured."

### Winston, Architect

The architecture is now correctly layered:

- Spring owns user/conversation metadata and authorization.
- FastAPI owns retrieval, embeddings, and generation.
- PostgreSQL stores metadata only.
- ChromaDB and Elasticsearch store retrieval indexes.

The highest architectural risk is not search latency; it is operational coupling to synchronous provider generation and provider quota.

### Quinn, QA Engineer

The implementation has meaningful gates now:

- retrieval quality gate
- chat integration gate
- source drawer E2E gate
- fallback and leakage checks

The next quality gap is automation: these gates should run predictably in CI/manual release workflows without burning Gemini quota on every PR.

### Paige, Technical Writer

The simplest non-developer explanation is:

> Gaji now answers with evidence. It searches the book, answers from the matching passages, and lets the user open the sources behind the answer.

## Performance Review

## Current Performance Picture

### Retrieval

Retrieval is fast:

- Hybrid p95: about 20ms in the latest MVP-A gate.
- BM25 p95: under 10ms.
- Vector p95: about 19ms.

Conclusion:

- Retrieval is not the main user-facing bottleneck right now.
- Retrieval quality and no-regression policy are good enough for MVP continuation.

### Generation and Chat

Provider-backed chat is the main latency source:

- MVP-B live sample: about 2.8s to 5.1s.
- MVP-C larger gate with preferred Gemini key:
  - 50 measured requests
  - 5 concurrency
  - p50: 2345.4ms
  - p95: 3427.8ms
  - max: 3865.4ms
  - fallback used: false
  - all responses grounded

Conclusion:

- Current synchronous chat is usable for MVP.
- It may feel slow during real learner sessions if users expect instant chat.

### Frontend Bundle

Build passes, but Vite warns about the main JS chunk:

- main JS: about 1.7MB
- gzip: about 506KB

Conclusion:

- Not a release blocker for the current RAG scope.
- Worth addressing before broader beta or mobile-heavy usage.

## Recommended Performance Improvements

### P0: Operational Quota and Secret Management

Why it matters:

- Previous failures were caused by Gemini quota exhaustion, not by broken RAG logic.
- Provider-backed release gates can burn quota quickly.

Recommended work:

- Move Gemini keys to GitHub Actions secrets or a secret manager.
- Rotate any keys that were pasted into chat or local logs.
- Keep provider-backed full gates manual, not PR-triggered.
- Use dry-run/config-check gates on pull requests.
- Track quota exhaustion as a first-class release signal.

Status:

- Next story prepared: `Release Automation and Operational Gates`.

### P1: Chat UX Latency Reduction

Why it matters:

- Retrieval is about 20ms p95, but full chat is 2-4 seconds p95.
- Users feel the generation latency, not the search latency.

Recommended work:

- Add streaming/SSE so the answer starts appearing earlier.
- Or move chat generation to an async job with visible "thinking/generating" state.
- Keep the current synchronous path as fallback.
- Add frontend timing states for retrieval, generation, and source lookup.

Expected impact:

- Does not necessarily reduce total backend time.
- Strongly improves perceived responsiveness.

### P1: Frontend Bundle Splitting

Why it matters:

- Main JS chunk is large.
- Large chunks hurt first load and can make chat feel slower before interaction.

Recommended work:

- Route-level lazy loading for heavy pages/components.
- Manual chunks for `three`, Tres, PrimeVue, and large visual dependencies.
- Review static plus dynamic imports that currently prevent chunk splitting.

Expected impact:

- Faster initial page load.
- Cleaner build output.

### P1: Release Gate Automation

Why it matters:

- The system now has good gates, but they are not yet fully automated.

Recommended work:

- Add GitHub Actions workflow for:
  - frontend unit/build/E2E
  - AI runner dry-run checks
  - manual provider-backed full gates
- Upload JSON/Markdown reports.
- Write gate summaries to GitHub Actions job summaries.
- Ensure submodules are checked out recursively.

Expected impact:

- Fewer manual mistakes before release.
- Better repeatability for stakeholders.

### P2: Retrieval Scaling Preparation

Why it matters:

- Retrieval is fast for one MVP novel.
- More novels and larger corpora may change this.

Recommended work:

- Monitor candidate pool size and latency as corpus grows.
- Keep `candidate_k_vector` and `candidate_k_bm25` configurable.
- Add per-store latency dashboards for ChromaDB and Elasticsearch.
- Consider collection/index sharding by novel or corpus group when corpus size grows.
- Evaluate reranking only after more novels and richer golden sets exist.

Expected impact:

- Avoids premature optimization now.
- Keeps a clear path for scaling later.

### P2: Source Lookup Caching

Why it matters:

- Source drawer clicks call Spring and FastAPI for exact passage lookup.
- The same assistant message citations may be opened repeatedly.

Recommended work:

- Cache source lookup result client-side per assistant message.
- Optionally add short-lived backend cache for exact passage source responses.
- Keep authorization checks on every backend call if backend cache is added.

Expected impact:

- Faster repeated drawer opens.
- Lower Elasticsearch load.

### P2: Test Noise Cleanup

Why it matters:

- Tests pass, but warning noise makes real issues harder to spot.

Recommended work:

- Clean Vitest mocks for router, 3D/Tres components, and i18n HTML warnings.
- Treat new warnings as meaningful signal after cleanup.

Expected impact:

- Better developer confidence.
- Easier CI triage.

## What We Can Say Publicly/Internal Demo-Safely

Safe claim:

> Gaji now has a grounded AI chat prototype. It searches the novel, uses matching passages as source evidence, returns answers with citation metadata, and lets the user inspect the sources behind an answer.

Safe technical claim:

> The MVP uses a hybrid RAG architecture with FastAPI for AI/RAG, Spring Boot for user/conversation metadata and authorization, ChromaDB for vector search, Elasticsearch for BM25/source lookup, PostgreSQL for metadata persistence, and Gemini for embeddings/generation.

Safe quality claim:

> Retrieval quality and latency passed the current release gate for `Pride and Prejudice`, and learner chat passed live grounded-response gates with citation metadata and no passage-text leakage in the chat completion payload.

Do not overclaim yet:

- Do not claim all novels are supported in production quality.
- Do not claim the AI answer is always correct.
- Do not claim provider quota is solved operationally until CI/secret management is complete.
- Do not claim streaming chat is implemented.

## Next Recommended Story

Implement:

- `Story 11.1: Release Automation and Operational Gates`

Main goals:

- Wire frontend and RAG gates into CI/manual workflows.
- Add dry-run release gate modes that do not consume Gemini quota.
- Store Gemini keys only in secrets.
- Upload release artifacts.
- Report fallback rate, quota exhaustion, and p95 latency automatically.

Story file:

- `_bmad-output/implementation-artifacts/stories/epic-11-story-11.1-release-automation-operational-gates.md`

## Source Documents

- `docs/5-qa/hybrid-rag-mvp-a-completion-report-2026-05-07.md`
- `docs/5-qa/hybrid-rag-mvp-a-release-gate-rerun-2026-05-07.md`
- `docs/5-qa/mvp-b-release-gate-2026-05-07.md`
- `docs/5-qa/mvp-c-rag-chat-observability-2026-05-07.md`
- `docs/5-qa/mvp-c-citation-source-lookup-2026-05-07.md`
- `gajiAI/scripts/run_rag_release_gate.py`
- `gajiAI/scripts/run_chat_release_gate.py`
- `gajiFE/e2e/rag-citation-source-drawer.spec.ts`
- `gajiFE/src/components/chat/ChatMessage.vue`
- `gajiBE/domains/chat-domain/src/main/java/com/gaji/chat/application/MessageService.java`

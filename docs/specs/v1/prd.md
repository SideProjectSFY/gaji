# Product Requirements Document (Modernization)

**Product:** gaji platform modernization  
**Version:** 2.0  
**Date:** 2026-02-16

## 1. Product Goal

Modernize the platform architecture to improve maintainability, delivery speed, and AI interaction reliability by:

1. Refactoring backend to DDD bounded contexts.
2. Migrating frontend from Vue 3 to Next.js.
3. Establishing secure direct AI interaction through server gateway boundaries.

## 2. Problem Statement

Current system constraints:

1. Backend domain logic is spread across technical layers, increasing change cost.
2. Frontend stack split and growth pressure make feature delivery slower.
3. AI integration path is tightly coupled and hard to evolve safely.

## 3. Scope

### In Scope

1. Spring backend architectural restructuring to DDD module boundaries.
2. Next.js domain-based frontend baseline and route migration.
3. Spring auth validation and secure downstream call path.
4. Documentation and structure alignment with BMAD v6 outputs.

### Out of Scope

1. Full business feature redesign.
2. New product verticals unrelated to migration.
3. Rewriting all historical artifacts from scratch.

## 4. Personas

1. Reader/User: explores books, scenarios, and chats with AI characters.
2. Creator: creates and forks scenarios/conversations.
3. Operator/Developer: maintains service quality and shipping velocity.

## 5. Functional Requirements

## FR-1 Backend DDD Boundary

1. System must define bounded contexts for identity, catalog, scenario, conversation, social, search, and AI orchestration.
2. System must enforce dependency rules by layer and context.

## FR-2 Frontend Domain Structure

1. System must organize frontend by domain/features.
2. UI and logic must be separated (`ui` vs `hooks` / `application`).
3. SSR/CSR modules must be distinguishable by `SS/CS` naming.
4. Frontend styling and UI foundation must standardize on PandaCSS + Park UI.

## FR-3 Gateway Pattern for Browser Calls

1. Browser must call Next.js route handlers (`/api/*`) instead of direct downstream services.
2. Route handlers must orchestrate server-side token and downstream calls.

## FR-4 AI Access Security

1. Spring must issue short-lived AI access token.
2. AI calls must include scoped token claims.
3. Sensitive credentials must remain server-side only.

## FR-5 Artifact Management

1. Epic/story implementation artifacts must be stored under `_bmad-output/implementation-artifacts`.
2. `docs` must provide lifecycle navigation and references.

## 6. Non-Functional Requirements

## NFR-1 Maintainability

1. Minimize cross-domain coupling.
2. Keep business rules in domain/application layers.

## NFR-2 Reliability

1. Route gateway and AI calls must be observable (errors, latency, retries).
2. Rollback switch must be available for major path changes.

## NFR-3 Security

1. Token lifetime must be short.
2. Token scope and ownership checks must be mandatory.

## NFR-4 Documentation Quality

1. Documentation must follow BMAD v6 lifecycle organization.
2. Core references must be discoverable via version folders under `/Users/yeongjae/gaji/docs/specs/`.

## 7. Success Metrics

1. Faster change impact analysis by bounded context.
2. Reduced frontend feature lead time in migrated routes.
3. Stable AI interaction error rate after gateway migration.
4. Documentation discoverability improved through BMAD v6 structure.

## 8. Dependencies

1. Spring security/token capability updates.
2. Next.js route handler and domain module migration.
3. Spring RAG module token verification compatibility.
4. PandaCSS codegen pipeline and Park UI component integration.

## 9. Risks and Mitigations

1. Boundary leakage in DDD modules.
   - Mitigation: architecture tests and review gates.
2. Migration regression between Vue and Next.js routes.
   - Mitigation: phased rollout and parity checks.
3. AI auth mismatch between issuer and consumer.
   - Mitigation: strict claim contract and verification tests.

## 10. Deliverables

1. Updated architecture definition: `/Users/yeongjae/gaji/docs/specs/v1/architecture.md`
2. Version-separated spec folders: `/Users/yeongjae/gaji/docs/specs/v1/` and `/Users/yeongjae/gaji/docs/specs/mvp-v2/`
3. Implementation artifacts in output folder: `/Users/yeongjae/gaji/_bmad-output/implementation-artifacts/`

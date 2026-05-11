---
stepsCompleted: [1,2,3]
inputDocuments:
  - /Users/min-yeongjae/gaji/_bmad-output/migration-plan-ddd-nextjs-direct-ai.md
  - /Users/min-yeongjae/gaji/architecture.md
  - /Users/min-yeongjae/gaji/gajiBE/docs/DDD_PHASE1_MODULE_MAPPING.md
  - /Users/min-yeongjae/gaji/gajiBE/docs/DDD_SPRING_MODULITH_BLUEPRINT.md
  - /Users/min-yeongjae/gaji/gajiFE/FRONTEND_RULES.md
---

# gaji - Epic Breakdown

> Status: Superseded for V2 execution.  
> Authoritative V2 epic baseline: `/Users/yeongjae/gaji/docs/specs/mvp-v2/epics-ux-aligned.md`

## Overview

This document provides the complete epic and story breakdown for gaji, decomposing the requirements from the migration plan and architecture documents into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Refactor Spring Boot backend into DDD modular monolith bounded contexts (`identity-access`, `catalog`, `scenario`, `conversation`, `social`, `search-discovery`, `ai-orchestration`).
FR2: Organize each backend context into layered packages (`domain`, `application`, `infrastructure`, `interfaces`) with enforced dependency direction.
FR3: Preserve business API flow as `Next.js FE -> Spring Boot`.
FR4: Implement secure AI direct flow with effective runtime path `FE gateway -> AI` and Spring-issued short-lived AI access token.
FR5: Implement Spring auth boundary endpoint in backend (`POST /api/v1/ai/chat/completions`) with claim/scope issuance.
FR6: Support dual AI client mode during migration: legacy (`FE -> BE -> AI`) and new direct mode.
FR7: Migrate frontend from Vue 3 SPA to Next.js App Router incrementally by route and domain.
FR8: Enforce frontend server-boundary data access: browser calls only `src/app/api/*`, route handlers orchestrate downstream calls.
FR9: Migrate key user journeys (book browsing, scenario lifecycle, conversation flows, social features) to Next.js with parity.
FR10: Implement feature flags for route cutover and AI traffic control (`ff.nextjs.route.*`, `ff.ai.direct.enabled`, `ff.ai.direct.percent`).
FR11: Add ArchUnit and Modulith checks for module boundary and allowed dependency rules.
FR12: Document and enforce aggregate/repository rules (one repository per aggregate root, invariant enforcement inside aggregate behavior).
FR13: Provide rollback path for AI direct mode and route-level frontend cutover.
FR14: Complete production cutover and decommission legacy Vue deployment and BE AI proxy path after stabilization window.
FR15: Produce migration design artifacts (context map, aggregate catalog, ubiquitous language glossary, flow diagrams, ADR set).

### NonFunctional Requirements

NFR1: Migration must be incremental and avoid big-bang cutover (target 12-18 weeks phased rollout).
NFR2: API compatibility must be maintained or explicitly versioned with migration notice.
NFR3: Security for AI path must include short TTL tokens, signature/claim validation, scope enforcement, and ownership checks.
NFR4: Sensitive credentials/tokens must remain on server boundary and never be exposed to browser or AI provider.
NFR5: Reliability must include emergency kill switch and traffic rollback capability for both AI and frontend routes.
NFR6: Observability must track latency (p95), error rates, retries, provider usage/cost, and migration parity KPIs.
NFR7: Performance budgets must include frontend LCP and bundle constraints with monitoring during migration.
NFR8: Architecture quality gates must fail CI on forbidden dependency violations.
NFR9: Deployment quality requires staged canary progression (5% -> 20% -> 50% -> 100%) with hold periods.
NFR10: Maintainability requires strict bounded-context separation and minimal shared-kernel scope.
NFR11: Frontend implementation must comply with defined UI stack and structure constraints (PandaCSS, Park UI, Ark UI, domain folders).
NFR12: Batch/persistence exceptions must be explicitly controlled by ADR and drift tests.

### Additional Requirements

- Current backend state includes Phase-1 physical split and must proceed to stricter context package boundaries and dependency enforcement.
- Existing controller/service/mapper/entity mapping in phase document indicates migration is already in-flight and must preserve running behavior while hardening boundaries.
- Modulith-aligned module verification is required: no cyclic dependencies and no illegal internal package access.
- Frontend data flow must enforce gateway pattern through Next.js route handlers rather than direct browser-to-downstream calls.
- Shared UI and domain UI placement in Next.js must follow existing frontend rules (`src/components` for shared wrappers, `src/domains/*/components` for domain UI).
- AI direct flow should still preserve controlled gateway behavior on the server side (route handlers), even if browser no longer calls Spring for AI payload forwarding.
- Migration backlog must include ADR creation and architecture decisions as deliverables, not optional artifacts.
- Definition of Done per migrated context must include security, observability, rollback, and dependency-rule compliance.

### FR Coverage Map

FR1: Epic 2 - DDD bounded-context backend migration
FR2: Epic 2 - Layered package and dependency enforcement
FR3: Epic 3 - Business API continuity from Next.js
FR4: Epic 4 - Secure direct AI flow
FR5: Epic 4 - Spring auth boundary capability
FR6: Epic 4 - Dual AI mode operation
FR7: Epic 3 - Incremental Next.js migration
FR8: Epic 3 - Frontend server-boundary access pattern
FR9: Epic 3 - User journey parity migration
FR10: Epic 1 - Feature-flag and traffic control baseline
FR11: Epic 2 - Architecture test enforcement
FR12: Epic 2 - Aggregate/repository implementation standards
FR13: Epic 1 - Rollback playbook and kill-switch readiness
FR14: Epic 5 - Full cutover and decommission
FR15: Epic 1 - Migration ADR/context map/design artifacts

## Epic List

### Epic 1: Migration Safety and Operational Control
Establish migration guardrails, rollout controls, and rollback readiness so users can continue using core features safely during modernization.
**FRs covered:** FR10, FR13, FR15

### Epic 2: Backend Domain Integrity and Stable Contracts
Refactor backend into bounded contexts with strict layering and architecture tests while preserving externally consumed API behavior.
**FRs covered:** FR1, FR2, FR11, FR12

### Epic 3: Next.js User Journey Parity
Migrate high-value user journeys from Vue to Next.js using server-boundary route handlers and maintain business API flow continuity.
**FRs covered:** FR3, FR7, FR8, FR9

### Epic 4: Secure Direct AI Experience
Enable direct AI interactions through a secure token-brokered path and controlled dual-mode rollout.
**FRs covered:** FR4, FR5, FR6

### Epic 5: Production Cutover and Legacy Retirement
Complete traffic cutover, validate stability, and remove legacy runtime paths safely.
**FRs covered:** FR14

## Epic 1: Migration Safety and Operational Control

Deliver migration controls that protect users from disruption during phased modernization.

### Story 1.1: Feature Flag Control Plane for Migration

As a platform operator,
I want route and AI traffic feature flags in place,
So that I can control migration exposure safely.

**Acceptance Criteria:**

**Given** migration flags are configured in environment and config service
**When** operators update `ff.nextjs.route.*`, `ff.ai.direct.enabled`, or `ff.ai.direct.percent`
**Then** traffic behavior changes without redeploy
**And** all flag evaluations are observable in logs/metrics.

### Story 1.2: AI and Route Rollback Playbook Automation

As an on-call engineer,
I want a tested rollback playbook for AI direct path and Next.js route flags,
So that incidents can be mitigated quickly.

**Acceptance Criteria:**

**Given** AI direct mode is enabled in staging
**When** synthetic error thresholds are exceeded
**Then** the system can switch to legacy AI path and legacy routes by flag change only
**And** rollback runbook steps and ownership are documented and rehearsed.

### Story 1.3: Migration Design Artifact Baseline

As a product and engineering team,
I want required ADR and domain design artifacts prepared,
So that implementation decisions remain consistent across teams.

**Acceptance Criteria:**

**Given** migration scope is approved
**When** architecture artifacts are generated
**Then** context map, aggregate catalog, ubiquitous language glossary, and key ADRs are available
**And** each artifact is versioned and linked from a single index document.

## Epic 2: Backend Domain Integrity and Stable Contracts

Harden backend boundaries with DDD modules and enforce dependency rules without breaking API consumers.

### Story 2.1: Context Package Standardization by Domain

As a backend developer,
I want each domain organized into `domain/application/infrastructure/interfaces`,
So that ownership and dependency direction are explicit.

**Acceptance Criteria:**

**Given** current modular directories exist
**When** domain code is reorganized
**Then** each bounded context follows the standard package layout
**And** compile/test passes with no endpoint regression.

### Story 2.2: Cross-Domain Access via Facade-Only Policy

As a backend developer,
I want cross-domain reads and validation routed through Facades,
So that application and interfaces layers do not directly depend on foreign mappers.

**Acceptance Criteria:**

**Given** multiple domains require foreign data access
**When** cross-domain logic is implemented
**Then** `application` and `interfaces` use foreign `application` Facades only
**And** no cross-domain mapper import remains in those layers.

### Story 2.3: ArchUnit and Modulith CI Gate Enforcement

As a platform maintainer,
I want architecture checks to fail CI on boundary violations,
So that regressions are prevented automatically.

**Acceptance Criteria:**

**Given** architecture test suite is configured
**When** a forbidden dependency is introduced
**Then** CI fails with a clear rule violation message
**And** rules cover interfaces-to-mapper prohibition and cross-domain mapper prohibition.

### Story 2.4: Aggregate and Repository Rule Compliance

As a backend architect,
I want aggregate and repository conventions codified and applied,
So that domain invariants are enforced consistently.

**Acceptance Criteria:**

**Given** domain entities and repositories are being migrated
**When** aggregate boundaries are reviewed
**Then** one repository per aggregate root is enforced
**And** invariant-changing behavior resides in aggregate methods, not external setters.

## Epic 3: Next.js User Journey Parity

Migrate user-facing journeys to Next.js with parity and secure server-boundary request handling.

### Story 3.1: Next.js Route Handler Gateway Baseline

As a frontend engineer,
I want browser requests constrained to `src/app/api/*` route handlers,
So that sensitive integration logic stays server-side.

**Acceptance Criteria:**

**Given** Next.js app routing is active
**When** browser triggers data operations
**Then** requests flow through `src/app/api/*` handlers only
**And** downstream calls from browser to protected services are blocked.

### Story 3.2: Catalog Journey Migration (Browse and Detail)

As an end user,
I want book browsing and detail pages in Next.js with existing behavior,
So that discovery experience remains stable during migration.

**Acceptance Criteria:**

**Given** catalog routes are flagged on
**When** users browse and open book detail pages
**Then** results match legacy behavior for core fields and sorting
**And** parity tests validate response shape and key UI interactions.

### Story 3.3: Scenario and Conversation Journey Migration

As an end user,
I want scenario creation and conversation flows to work in Next.js,
So that core product interactions remain uninterrupted.

**Acceptance Criteria:**

**Given** scenario and conversation routes are enabled
**When** users create scenarios and interact in chat
**Then** flow parity with legacy path is preserved for core actions
**And** route handlers enforce existing auth/session constraints.

### Story 3.4: Social and Search Journey Migration

As an end user,
I want social interactions and search to work in Next.js,
So that engagement features remain available during cutover.

**Acceptance Criteria:**

**Given** social and search migration routes are active
**When** users perform follow/like/comment/memo and global search actions
**Then** behavior and data visibility rules match legacy implementation
**And** no direct browser access to private backend integrations occurs.

## Epic 4: Secure Direct AI Experience

Deliver secure and observable AI direct flow with gradual traffic adoption.

### Story 4.1: AI Token Broker Endpoint in Spring

As a signed-in user,
I want a short-lived AI access token issued by Spring,
So that AI requests can be authorized without exposing core credentials.

**Acceptance Criteria:**

**Given** authenticated user context
**When** FE requests `POST /api/v1/ai/chat/completions`
**Then** Spring returns a short-TTL signed token with audience and scope claims
**And** issuance is audited with request and user correlation identifiers.

### Story 4.2: Next.js AI Route Handler Direct Invocation

As a user sending AI prompts,
I want the Next.js gateway to call AI directly using Spring auth token,
So that responses are lower-latency and secure.

**Acceptance Criteria:**

**Given** AI direct mode is enabled by flag
**When** FE submits AI chat/generation through route handlers
**Then** route handler obtains Spring auth token and calls Spring RAG module directly
**And** token validation failures return sanitized, user-safe errors.

### Story 4.3: Dual-Mode AI Client and Controlled Canary

As an operator,
I want dual AI routing modes with percentage rollout,
So that I can canary direct AI safely.

**Acceptance Criteria:**

**Given** both legacy and direct paths are available
**When** `ff.ai.direct.percent` is adjusted
**Then** traffic splits according to configured percentage
**And** rollback to 0% direct restores legacy behavior immediately.

## Epic 5: Production Cutover and Legacy Retirement

Complete migration transition with confidence and remove obsolete runtime paths.

### Story 5.1: Full Traffic Cutover Validation

As an operator,
I want defined cutover checkpoints and acceptance metrics,
So that full migration happens only after stability is proven.

**Acceptance Criteria:**

**Given** staged canary milestones are complete
**When** traffic is promoted to 100% for Next.js and direct AI
**Then** p95 latency, error rate, and critical journey success metrics meet thresholds
**And** rollback remains available throughout the validation window.

### Story 5.2: Legacy Path Decommission and Hard Gate

As a platform maintainer,
I want legacy Vue deployment and BE AI proxy removed after stabilization,
So that technical debt and operational overhead are reduced.

**Acceptance Criteria:**

**Given** stabilization window has passed with green KPIs
**When** decommission tasks execute
**Then** legacy runtime paths are removed from deployment and routing configuration
**And** CI/ops checks prevent accidental reintroduction of deprecated paths.

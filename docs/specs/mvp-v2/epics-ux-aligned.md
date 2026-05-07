---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
authoritative: true
supersedes:
  - /Users/yeongjae/gaji/docs/specs/v1/epics-v1-legacy.md
inputDocuments:
  - /Users/yeongjae/gaji/docs/specs/mvp-v2/product-brief-gaji-2026-02-25.md
  - /Users/yeongjae/gaji/docs/specs/mvp-v2/ux-design-specification.md
  - /Users/yeongjae/gaji/docs/specs/mvp-v2/architecture-ux-aligned.md
  - /Users/yeongjae/gaji/docs/specs/v1/prd.md
---

# gaji - Epic Breakdown (UX-Aligned)

## Overview

This epic breakdown aligns implementation directly to the finalized UX specification and architecture decisions.
Primary implementation invariant: `Continue > Path-state > Fork` across desktop-first adaptive layouts, with deterministic fallback behavior.

## Authority Decision

- This file is the single authoritative epic/story baseline for V2 implementation.
- `/Users/yeongjae/gaji/docs/specs/v1/epics-v1-legacy.md` is superseded for V2 execution and retained only as legacy archived reference.

## MVP2 Cutline

### Must Include (MVP2 Release Blockers)
- Epic 1 Story 1.1, 1.2, 1.3
- Epic 2 Story 2.1, 2.2, 2.3
- Epic 3 Story 3.1, 3.2
- Epic 3 Story 3.3
- Epic 4 Story 4.1, 4.2
- Epic 4 Story 4.3
- Epic 5 Story 5.2
- Epic 6 Story 6.1, 6.2, 6.3, 6.4
- Epic 7 Story 7.3, 7.4
- Epic 8 Story 8.1, 8.2, 8.3

### Explicitly Excluded from MVP2
- Adaptive hint enhancements beyond deterministic baseline
- Non-essential visual polish unrelated to continuity/safety/compliance
- New product vertical features outside continue/fork/recovery scope

## Requirements Inventory

### Functional Requirements
- Deterministic continue flow to last confirmed moment.
- One-action in-context fork creation with idempotency.
- Recovery flow that preserves draft and provides calm, actionable guidance.
- Persistent base/fork path-state visibility.
- Non-blocking confirmation patterns.
- Journey metrics emission at completion points.
- PRD FR-1 backend bounded-context and dependency-boundary enforcement.
- PRD FR-3 gateway-only browser access with explicit API contract versioning.
- PRD FR-4 short-lived token, scoped claims, ownership checks for AI access.

### NonFunctional Requirements
- WCAG AA accessibility target.
- Keyboard-first interaction fidelity.
- Visual hierarchy regression treated as release blocker.
- Canonical state consistency across retries/concurrency.
- p95 resume/fork/recovery interaction latency <= 800ms (excluding model generation time).
- Error budget: core journey failure rate < 1.0% rolling 7 days.
- Retry budget: recoverable failures auto-recover or user-retry success >= 99%.
- Security budget: zero critical token-scope or ownership validation defects in release gate.

### Additional Requirements
- Brand tokens are fixed for V2:
  - colors: `#1D4ED8`, `#0EA5E9`, `#F8FAFC`, `#FFFFFF`, `#0F172A`, `#64748B`, `#166534`, `#B45309`, `#B91C1C`, `#1E40AF`, `#0E7490`
  - fonts: `Pretendard`, `Noto Sans KR`, `Segoe UI`
  - base spacing unit: `8px`
- Adaptive cue layer is optional and must degrade to baseline direction.
- No direct browser-to-downstream calls; gateway boundary enforced.

### FR Coverage Map
- Continue journey -> Epic 2
- Fork journey -> Epic 3
- Recovery journey -> Epic 4
- Visual hierarchy + design system -> Epic 1
- Responsive/accessibility compliance -> Epic 5
- Quality gates + rollout controls -> Epic 6
- PRD FR1 (DDD bounded contexts + dependency rules) -> Epic 8 Story 8.1
- PRD FR3 (gateway-only browser calls + server orchestration) -> Epic 8 Story 8.2
- PRD FR4 (token TTL/scope/ownership security) -> Epic 8 Story 8.3
- PRD FR-2.2 (`ui` vs `hooks`/`application`) -> Epic 7 Story 7.1
- PRD FR-2.3 (`SS/CS` naming) -> Epic 7 Story 7.2
- PRD FR-5.1 (implementation artifact location policy) -> Epic 7 Story 7.3
- PRD FR-5.2 (`docs` lifecycle navigation) -> Epic 7 Story 7.4

## Epic List

### Epic 1: Design System Foundation & Continuity UI Contracts
Establish Park UI + PandaCSS foundation with stable custom component contracts for continuity-critical interactions.

### Epic 2: Continue Story Path Experience
Implement return-and-continue flow with one-glance clarity and deterministic context restoration.

### Epic 3: In-Context Fork Experience
Implement one-action fork creation and branch continuation with explicit path confirmation and idempotent behavior.

### Epic 4: Recovery & Safe Resume Experience
Implement interruption recovery flow with draft preservation and calm, non-technical guidance.

### Epic 5: Responsive + Accessibility Compliance
Implement desktop-first adaptive behavior and WCAG AA conformance across core journeys.

### Epic 6: Quality Gates, Telemetry, and Rollout Safety
Implement regression blockers, journey metric contracts, and fallback verification in CI/release process.

### Epic 7: Frontend Structure and Documentation Governance
Close PRD structure/governance gaps required for implementation traceability and maintainability.

### Epic 8: Platform Contract and Security Alignment
Restore PRD modernization scope by enforcing backend boundary, gateway contract, and AI security requirements.

## Dependency Strategy

### Epic Dependency Matrix
- Epic 1 -> prerequisite for Epics 2, 3, 4
- Epic 2 -> prerequisite for Epic 6 telemetry validation and Epic 5 scenario coverage
- Epic 3 -> prerequisite for Epic 6 risk monitoring and Epic 5 fork coverage
- Epic 4 -> prerequisite for Epic 6 recovery monitoring and fallback confidence
- Epic 5 -> can execute in parallel after Epics 1/2/3 foundations
- Epic 6 -> requires Epics 2/3/4 event surfaces and Epic 1 visual primitives
- Epic 7 -> independent governance stream; must complete before release sign-off
- Epic 8 -> platform stream; required before release sign-off

### Forward-Dependency Rule
- No story may require an unstarted higher-numbered story in the same epic.
- Cross-epic dependency must reference only completed or in-progress prerequisite epics listed above.

## Epic 1: Design System Foundation & Continuity UI Contracts

Build token-governed UI foundation and custom components required by UX spec.

### Story 1.1: Token Schema & Theme Setup
As a frontend engineer,
I want a fixed semantic token schema in PandaCSS,
So that components remain consistent before/after brand value replacement.

**Acceptance Criteria:**

**Given** the design system setup
**When** theme tokens are configured
**Then** semantic tokens include primary/secondary/text/background/state/path roles
**And** unresolved brand values can remain placeholders without schema change.

### Story 1.2: Resume Card Component
As a returning learner,
I want a clear Resume Card,
So that I can continue instantly from the right story point.

**Acceptance Criteria:**

**Given** a user with an active path
**When** the return view loads
**Then** Resume Card is visually primary over all adjacent actions
**And** component supports default/loading/restored/fallback/error-retry states.

### Story 1.3: Path Indicator Component
As a learner,
I want persistent base/fork context cues,
So that I always know which path I’m writing in.

**Acceptance Criteria:**

**Given** conversation context
**When** base or fork path is active
**Then** indicator displays explicit state with non-color cue support
**And** indicator never visually outranks Resume action.

### Story 1.4: Inline Fork Trigger Component
As a learner,
I want a one-action fork trigger in context,
So that I can branch at curiosity moments without losing flow.

**Acceptance Criteria:**

**Given** active conversation turn
**When** user triggers fork
**Then** component preserves draft/focus/scroll
**And** supports idle/submitting/confirmed/failed-retry/idempotent-repeat-handled states.

## Epic 2: Continue Story Path Experience

Implement deterministic continue journey with trust-preserving confirmations.

### Story 2.1: Continue Entry Orchestration
As a returning learner,
I want the app to resolve my active path automatically,
So that I can continue with one glance.

**Acceptance Criteria:**

**Given** user opens the app
**When** active path exists
**Then** system routes to Continue Story Path entry
**And** context restore confirmation is shown non-blockingly.
**And** first primary actionable control is visible within 3 seconds at p95 on baseline desktop network.

### Story 2.2: Continue API Contract
As a backend engineer,
I want a continue command contract,
So that canonical state and UI confirmations are consistent.

**Acceptance Criteria:**

**Given** continue request
**When** context resolve succeeds
**Then** response includes status, pathContext, and nextActionHint
**And** path changes are reflected only after confirmation.

### Story 2.3: Continue Journey Telemetry
As a product analyst,
I want completion metrics for continue journey,
So that journey performance can be monitored reliably.

**Acceptance Criteria:**

**Given** user sends next message after continue
**When** completion condition is met
**Then** `journey_continue_completed` is emitted once
**And** duplicates are prevented in retry scenarios.

## Epic 3: In-Context Fork Experience

Implement safe fork creation and continuation with explicit state transitions.

### Story 3.1: Fork Command with Idempotency
As a platform engineer,
I want idempotent fork creation,
So that repeated triggers never create duplicate visible forks.

**Acceptance Criteria:**

**Given** repeated fork requests with same idempotency key
**When** backend processes command
**Then** only one fork outcome is confirmed
**And** response supports safe retry semantics.

### Story 3.2: Fork Confirmation UX
As a learner,
I want clear confirmation when switching to a fork,
So that I trust where I’m writing.

**Acceptance Criteria:**

**Given** fork success
**When** UI updates
**Then** fork context chip + inline confirmation appears
**And** composer remains focused and ready.
**And** fork target context comprehension check passes >= 90% in scripted usability test (n>=20).

### Story 3.3: Fork Journey Telemetry
As a product analyst,
I want fork completion metrics,
So that branch behavior can be measured accurately.

**Acceptance Criteria:**

**Given** user continues writing in newly confirmed fork
**When** completion condition is met
**Then** `journey_fork_completed` is emitted once
**And** emission happens only at journey completion node.

## Epic 4: Recovery & Safe Resume Experience

Implement recovery-first flows that preserve trust and momentum.

### Story 4.1: Recovery State Resolver
As a learner,
I want safe recovery after interruption,
So that I can resume without losing progress.

**Acceptance Criteria:**

**Given** interruption/error state
**When** recovery runs
**Then** system restores draft + last confirmed moment when possible
**And** otherwise restores last confirmed moment with clear guidance.

### Story 4.2: Recovery Messaging Pattern
As a UX writer,
I want calm non-technical recovery messaging,
So that users understand next steps without anxiety.

**Acceptance Criteria:**

**Given** recovery-required state
**When** message is rendered
**Then** copy avoids technical internals
**And** presents one clear next action.
**And** fallback copy readability target is <= Grade 8 (automated readability check).

### Story 4.3: Recovery Journey Telemetry
As a product analyst,
I want recovery completion metrics,
So that reliability impact can be tracked.

**Acceptance Criteria:**

**Given** user resumes writing after recovery
**When** completion condition is met
**Then** `journey_recovery_completed` is emitted once
**And** event includes journey context for analysis.

## Epic 5: Responsive + Accessibility Compliance

Guarantee consistent hierarchy and inclusive interaction across breakpoints.

### Story 5.1: Desktop-First Adaptive Layout
As a frontend engineer,
I want controlled breakpoint behavior,
So that desktop keyboard-first flow remains primary while adapting cleanly.

**Acceptance Criteria:**

**Given** mobile/tablet/desktop breakpoints
**When** layout adapts
**Then** hierarchy remains `Continue > Path-state > Fork`
**And** core journey actions remain one-glance understandable (first-action discovery <= 5 seconds for >= 90% test participants).

### Story 5.2: WCAG AA Baseline for Core Journeys
As an accessibility stakeholder,
I want WCAG AA compliance in core flows,
So that the product is usable for diverse users.

**Acceptance Criteria:**

**Given** core journey screens
**When** accessibility checks run
**Then** contrast, focus visibility, keyboard navigation pass
**And** screen-reader sanity checks pass for dynamic states.

### Story 5.3: Accessibility and Responsive Test Harness
As a QA engineer,
I want automated + manual validation workflows,
So that regressions are caught before release.

**Acceptance Criteria:**

**Given** CI pipeline
**When** test suite executes
**Then** responsive viewport checks and a11y scans run
**And** keyboard-only flow tests are included for critical journeys.
**And** CI job `qa-v2-accessibility-gate` runs axe-core scan + Playwright keyboard suite on each PR.

## Epic 6: Quality Gates, Telemetry, and Rollout Safety

Operationalize release blockers and fallback invariants.

### Story 6.1: Visual Hierarchy Regression Gate
As a release manager,
I want hierarchy regressions blocked,
So that UX priorities never drift in production.

**Acceptance Criteria:**

**Given** PR validation
**When** visual regression detects hierarchy break
**Then** merge is blocked
**And** report identifies impacted component/state.
**And** baseline source, diff threshold (<= 0.5%), and viewport set (1366x768, 1024x768, 768x1024, 390x844) are versioned in `tests/visual/visual-baseline.config.json`.

### Story 6.2: Adaptive Layer Fallback Verification
As an architect,
I want deterministic fallback verification,
So that adaptive-cue failures never cause undefined UX states.

**Acceptance Criteria:**

**Given** adaptive layer unavailable/failing
**When** user enters core flow
**Then** UI degrades to baseline direction deterministically
**And** hierarchy/order remains unchanged.

### Story 6.3: Journey Risk Monitoring
As a product owner,
I want monitoring on confusion signals,
So that early UX trust issues are detected quickly.

**Acceptance Criteria:**

**Given** production telemetry
**When** recovery confusion or fork-confirmation uncertainty rises
**Then** alert threshold triggers investigation
**And** dashboard links to affected journey and release.
**And** event schema includes `event_id`, `journey_name`, `path_type`, `completion_ms`, `retry_count`, `release_id`, and `user_segment` with idempotent dedupe key `event_id`.
**And** ownership is assigned to Product Analytics with weekly sampling QA check (>= 5% event audit).

### Story 6.4: Telemetry Contract and Ownership Gate
As a data governance lead,
I want a versioned telemetry contract and ownership matrix,
So that metrics remain trustworthy across releases.

**Acceptance Criteria:**

**Given** journey events are emitted
**When** telemetry contract validation runs
**Then** event schema version, producer, owner, and quality SLO are validated in CI
**And** schema-breaking changes require version bump and migration notes.

## Epic 7: Frontend Structure and Documentation Governance

Resolve remaining PRD governance and frontend structure requirements not previously mapped.

### Story 7.1: UI and Logic Separation Guardrails
As a frontend maintainer,
I want enforced separation between UI and behavior/application layers,
So that feature changes stay maintainable and testable.

**Acceptance Criteria:**

**Given** domain feature modules
**When** code is reviewed or linted
**Then** presentational code remains in `ui/components` and behavior in `hooks` or `application`
**And** CI fails when forbidden cross-layer imports are introduced.

### Story 7.2: SSR/CSR Naming Convention Enforcement
As a frontend engineer,
I want SSR/CSR boundaries encoded in conventions compatible with Next.js,
So that server/client intent remains explicit without breaking framework file rules.

**Acceptance Criteria:**

**Given** new or migrated modules
**When** rendering-mode specific logic is introduced
**Then** naming convention applies to module/export identifiers (`SS*`/`CS*`) while Next.js reserved filenames remain exempt
**And** lint/check script reports violations in pull requests.

### Story 7.3: Implementation Artifact Location Compliance
As a scrum master,
I want artifact output policy validated automatically,
So that BMAD traceability remains consistent.

**Acceptance Criteria:**

**Given** story/epic documents generated for V2
**When** validation runs
**Then** implementation artifacts are stored under `_bmad-output/implementation-artifacts`
**And** non-compliant paths are flagged as release-process violations via `scripts/validate-artifact-paths.sh` in CI job `docs-artifact-gate`.

### Story 7.4: Docs Version Folder Separation Gate
As a product owner,
I want lifecycle navigation entries enforced in docs,
So that stakeholders can locate current planning and implementation artifacts quickly.

**Acceptance Criteria:**

**Given** updated V2 planning/implementation artifacts
**When** docs validation runs
**Then** required V1 and MVP V2 specs exist under `/Users/yeongjae/gaji/docs/specs/v1/` and `/Users/yeongjae/gaji/docs/specs/mvp-v2/`
**And** missing required files or reintroduced index-routing files fail documentation quality checks via `scripts/validate-spec-version-folders.sh` in CI job `docs-version-folder-gate`.

## Epic 8: Platform Contract and Security Alignment

Close PRD modernization gaps for backend boundaries, gateway contracts, and AI security.

### Story 8.1: DDD Boundary Enforcement Gate
As a backend architect,
I want bounded-context dependency rules enforced continuously,
So that backend maintainability and domain isolation are preserved.

**Acceptance Criteria:**

**Given** backend modules and CI checks
**When** architecture tests run
**Then** cross-context forbidden dependencies fail CI
**And** architecture report is published per build with violations and owning team.

### Story 8.2: Gateway Contract Versioning and Error Spec
As a platform engineer,
I want explicit endpoint/version/error contracts for continue/fork/recovery APIs,
So that frontend and backend evolve without ambiguity.

**Acceptance Criteria:**

**Given** continue/fork/recovery API surface
**When** contract tests run
**Then** endpoints are versioned under `/api/v2/*` with typed request/response and error code matrix
**And** backward-compatible change rules and deprecation windows are documented.

### Story 8.3: AI Token Security Policy Gate
As a security engineer,
I want token TTL/scope/ownership checks enforced by tests and runtime policy,
So that direct AI access remains secure by default.

**Acceptance Criteria:**

**Given** AI token issuance and validation flow
**When** security gate runs
**Then** token TTL <= 5 minutes, mandatory scope claims, and ownership checks are verified
**And** any missing/invalid claims are denied and audited with correlation IDs.

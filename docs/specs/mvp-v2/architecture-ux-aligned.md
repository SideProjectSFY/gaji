---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
  - 7
  - 8
inputDocuments:
  - /Users/yeongjae/gaji/docs/specs/mvp-v2/product-brief-gaji-2026-02-25.md
  - /Users/yeongjae/gaji/docs/specs/mvp-v2/ux-design-specification.md
  - /Users/yeongjae/gaji/docs/specs/v1/prd.md
workflowType: 'architecture'
project_name: 'gaji'
user_name: 'yeongjae'
date: '2026-02-26'
workflow_completed: true
workflow_completed_at: '2026-02-26'
---

# Architecture Decision Document (UX-Aligned)

## Project Context Analysis

### Requirements Overview
- Product direction is continuity-first story conversation with explicit branching.
- Core UX invariant: `Continue > Path-state cue > Fork` across all states and breakpoints.
- Required journey outcomes:
  - `journey_continue_completed`
  - `journey_fork_completed`
  - `journey_recovery_completed`
- Visual/design constraints:
  - Base direction: Direction 01
  - Reliability cues from Direction 05
  - Calm recovery tone from Direction 07
  - Subtle adaptive cues from Direction 08 only if non-blocking

### Technical Constraints & Dependencies
- Frontend baseline: Next.js + Park UI + PandaCSS.
- Security and AI boundary: browser -> Next.js `/api/*` -> backend services.
- Conversation state must be canonical server-side with deterministic resume/fork behavior.
- Brand tokens remain `TBD from Brand Source`; token schema is fixed and must not drift.

### Cross-Cutting Concerns Identified
- State consistency under concurrency/retries.
- UX trust and one-glance clarity.
- Accessibility (WCAG AA) + keyboard-first interaction.
- Regression control for hierarchy and fallback behavior.

## Starter Template Evaluation

### Primary Technology Domain
- Web-first conversational platform (desktop-priority adaptive UX).

### Starter Options Considered
1. Full custom stack without UI system.
2. Established heavyweight UI system with limited tailoring.
3. Themeable component foundation with token governance.

### Selected Starter: Themeable Foundation (Recommended)
- Selected: Park UI + PandaCSS + custom continuity-critical components.
- Why:
  - Fast implementation with stable primitives.
  - Strong alignment with UX hierarchy and fallback invariants.
  - Lower drift risk through tokenized styling and contract-based custom components.

## Core Architectural Decisions

### Decision Priority Analysis
1. Canonical conversation state and branch integrity.
2. API boundary and error/fallback semantics.
3. Frontend component contracts and interaction hierarchy.
4. Accessibility/responsive compliance.
5. Observability + release gates.

### Data Architecture
- Canonical entities:
  - ConversationPath (base/fork)
  - PathPointer (active + last confirmed moment)
  - DraftState (recoverable client-side buffer + server reconciliation)
- Persistence rules:
  - Canonical state commits only on confirmed successful action.
  - Fork creation is idempotent (request key required).
  - Recovery routes to last confirmed moment when certainty is low.

### Authentication & Security
- Browser never calls downstream services directly.
- All calls go through Next.js route handlers (`/api/*`).
- Token issuance/verification remains server-side only.
- Errors shown to users remain non-technical; technical detail is logged server-side.

### API & Communication Patterns
- API style: command-oriented endpoints for journey-critical actions:
  - Continue resume resolve
  - Fork create
  - Recovery reconcile
- Response contracts include:
  - `status` (confirmed/recovered/retryable)
  - `pathContext` (base/fork label)
  - `nextActionHint` (user-facing non-technical guidance)
- Retry semantics:
  - Safe retries for idempotent operations.
  - No duplicate fork visible outcomes.

### Frontend Architecture
- View-model split:
  - Journey orchestration hooks
  - Presentational components from Park UI + custom continuity components
- Mandatory custom components:
  - Resume Card
  - Base/Fork Path Indicator
  - Inline Fork Trigger
- Visual precedence lock:
  - Resume primary, path-state contextual, fork secondary.

### Infrastructure & Deployment
- Feature flags for adaptive cue layer.
- Deterministic fallback to baseline direction when adaptive layer fails.
- Release blockers:
  - Hierarchy regressions
  - Path-state ambiguity regressions
  - Recovery-flow draft-loss regressions

### Decision Impact Analysis
- Reduces implementation ambiguity across frontend/backend teams.
- Aligns technical behavior with trust-critical UX outcomes.
- Enables metric-driven rollout without weakening continuity guarantees.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined
- Naming patterns
- Structure patterns
- Format patterns
- Communication patterns
- Process patterns

### Naming Patterns
- Events: `journey_<name>_completed`
- Component contracts: `<component>.<eventName>` (stable and versioned)
- Path context enums: `base`, `fork`, `recovery`

### Structure Patterns
- Journey flow template:
  - Start -> Decision -> Action -> Confirmation -> Completion
  - Failure -> Recovery -> Rejoin
- Component state matrix (minimum):
  - default, loading/submitting, success/confirmed, failure, retry/recovery

### Format Patterns
- User feedback format:
  - one-line state + one-line next action
- Recovery copy format:
  - calm tone, no technical internals

### Communication Patterns
- User-facing rule: path changes only after system confirmation.
- Engineering-facing rule: canonical state write on confirmed action only.
- Analytics rule: completion key emitted only at completion node.

### Process Patterns
- PR gate checks:
  - hierarchy invariant check
  - accessibility baseline check
  - visual regression check for continuity-critical surfaces
- Rollout checks:
  - fallback-to-baseline verification
  - no duplicate fork regression

### Enforcement Guidelines
- Any exception to hierarchy or fallback invariant requires architecture review.
- Any token bypass is forbidden in custom components.

## Project Structure & Boundaries

### Complete Project Directory Structure
```text
apps/
  web/
    src/
      app/
      features/
        conversation/
          components/
            ResumeCard.tsx
            PathIndicator.tsx
            InlineForkTrigger.tsx
          hooks/
            useContinueFlow.ts
            useForkFlow.ts
            useRecoveryFlow.ts
          api/
            commands.ts
          model/
            types.ts
      design-system/
        tokens/
        theme/
      shared/
        accessibility/
        telemetry/

services/
  api-gateway/
  conversation/
  identity/
  ai-orchestration/

packages/
  contracts/
    journey-events.ts
    path-context.ts
```

### Architectural Boundaries
- UI layer never owns canonical journey truth.
- Conversation service owns canonical path and confirmation semantics.
- Gateway owns token and downstream orchestration boundaries.

### Requirements to Structure Mapping
- Continue journey -> `features/conversation/useContinueFlow`
- Fork journey -> `features/conversation/useForkFlow`
- Recovery journey -> `features/conversation/useRecoveryFlow`
- Metrics keys -> `packages/contracts/journey-events.ts`

### Integration Points
- Web app <-> Gateway: `/api/continue`, `/api/fork`, `/api/recovery`
- Gateway <-> Conversation service: canonical path actions
- Web app <-> telemetry: journey completion + risk node instrumentation

### File Organization Patterns
- Feature-first organization with explicit contracts package.
- Custom continuity components colocated with flow hooks.

### Development Workflow Integration
- Story implementation sequence follows epic ordering.
- Each story must include accessibility + fallback tests.

## Architecture Validation Results

### Coherence Validation ✅
- UX hierarchy, component strategy, and API behavior are consistent.
- Fallback rules align between design direction and runtime behavior.

### Requirements Coverage Validation ✅
- Continue/fork/recovery journeys each mapped to architecture modules and APIs.
- Metric keys and trust touchpoints are preserved.

### Implementation Readiness Validation ✅
- Decision-complete contracts and boundaries are defined.
- Release blockers and quality gates are explicit.

### Gap Analysis Results
- Remaining gap: real brand token values from brand source.
- Mitigation: keep schema fixed, replace values only after accessibility validation.

### Architecture Completeness Checklist
- [x] Project context and constraints
- [x] Core decisions and tradeoffs
- [x] Consistency patterns and enforcement
- [x] Structure and boundaries
- [x] Validation and handoff

### Architecture Readiness Assessment
- Ready for epic/story decomposition and implementation planning.

### Implementation Handoff
- Use this document + UX spec as source of truth for story generation.

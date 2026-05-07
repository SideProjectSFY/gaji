---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
inputDocuments:
  - /Users/yeongjae/gaji/docs/1-analysis/use-case.md
  - /Users/yeongjae/gaji/docs/2-plan/gantt-chart.md
  - /Users/yeongjae/gaji/docs/2-plan/plans/frontend-3d-interaction-spec.md
  - /Users/yeongjae/gaji/docs/2-plan/plans/ga4-tracking-strategy.md
  - /Users/yeongjae/gaji/docs/specs/v1/prd.md
  - /Users/yeongjae/gaji/docs/2-plan/screen-specification.md
  - /Users/yeongjae/gaji/docs/3-solutioning/api-documentation.md
  - /Users/yeongjae/gaji/docs/specs/v1/architecture.md
  - /Users/yeongjae/gaji/docs/3-solutioning/class-diagram.md
  - /Users/yeongjae/gaji/docs/3-solutioning/deploy-strategy.md
  - /Users/yeongjae/gaji/docs/3-solutioning/erd.md
  - /Users/yeongjae/gaji/docs/3-solutioning/security.md
  - /Users/yeongjae/gaji/docs/4-implementation/automation-gutenberg-batch.md
  - /Users/yeongjae/gaji/docs/5-qa/assessments/epic-10-story-10.5-qa-assessment-20260219.md
  - /Users/yeongjae/gaji/docs/5-qa/assessments/epic-9-story-9.5-qa-assessment-20260218.md
  - /Users/yeongjae/gaji/docs/5-qa/checklists/playwright-failure-checklist.md
  - /Users/yeongjae/gaji/docs/5-qa/test-users.md
  - /Users/yeongjae/gaji/docs/99-archive/path-migration-map.md
  - /Users/yeongjae/gaji/docs/RAG_ANALYSIS.md
  - /Users/yeongjae/gaji/docs/README.md
  - /Users/yeongjae/gaji/docs/backend_architecture.md
date: 2026-02-25
author: yeongjae
workflow_completed: true
workflow_completed_at: 2026-02-25
---

# Product Brief: gaji

<!-- Content will be appended sequentially through collaborative workflow steps -->


## Executive Summary

gaji is a self-directed language learning platform for grade 5-6 and middle school students who are losing interest in reading due to rigid, textbook-style learning. Instead of assignment-only progression, gaji delivers reading-first language growth through persistent character-based story conversations.

The platform solves a critical weakness in existing chatbot learning products: isolated chat sessions with broken continuity. gaji applies a per-user conversation model and a controlled fork system (up to 3 top branches) to preserve narrative continuity while enabling meaningful exploration. Early success will be measured through WAU and reading-habit behavior signals.

---

## Core Vision

### Problem Statement

Students in upper elementary and middle school cannot study language in a truly self-directed way. Most available options are rigid, task-driven, and academically framed, making learning feel dry and externally imposed.

### Problem Impact

If this remains unsolved, students build weak reading habits and interact with language learning mainly as an obligation rather than a sustained personal practice.

### Why Existing Solutions Fall Short

Workbook-first platforms (e.g., 구몬) and challenge-first platforms (e.g., Duolingo) optimize step-by-step assignment completion. They provide structure but under-serve reading-driven autonomy and narrative continuity. Many character-chat products are also session-isolated, resetting motivation and context each time.

### Proposed Solution

Redesign gaji for grade 5-6 and middle school learners with a continuity-centered experience:
- Maintain per-user conversation continuity with deterministic resume behavior.
- Enable controlled branching via fork architecture with up to 3 top branches.
- Launch with a shared core UI plus age-adaptive guidance from day 1.
- Deliver reading-first interaction loops supported by a continuous, age-appropriate content pipeline.
- Track early outcomes with WAU (20-100 target), 7-day story return rate, and weekly reading+chat time.

### Key Differentiators

- Fork architecture that enables controlled creative freedom rather than branching chaos.
- Persistent per-user continuity that compounds engagement across sessions.
- Content pipeline designed for sustained reading motivation and language immersion.
- Pragmatic age adaptation (feature-flagged guidance) without fragmenting product architecture.


## Target Users

### Primary Users

#### Persona 1: Minseo Kim (Grade 5-6 Explorer)

- Age/Context: 11 years old, elementary grade 5 student.
- Device Pattern: Mobile-first, short guided sessions (8-15 minutes), occasional web use on family laptop.
- Personality: Curious and imaginative, but quickly disengages from repetitive workbook-style tasks.
- Current Problem Experience:
- Uses assignment-based tools when required, but rarely reads voluntarily.
- Existing language products feel rigid and disconnected from story continuity.
- Motivation/Goals:
- Wants language learning to feel like story participation, not forced tasks.
- Wants to continue familiar character contexts instead of restarting.
- Success Definition:
- Voluntarily returns at least 2 times in week 1.
- Repeatedly uses "Continue Story Path" and begins building reading habit.

#### Persona 2: Jiwon Park (Middle School Narrative Builder)

- Age/Context: 14 years old, middle school student.
- Device Pattern: Web-first for deep sessions (20-40 minutes), mobile for quick resume/follow-up.
- Personality: Creative, autonomy-seeking, motivated by meaningful choices and progression.
- Current Problem Experience:
- Challenge-style apps feel too scripted and lose novelty.
- Character chat tools without continuity feel shallow over time.
- Motivation/Goals:
- Build and revisit personal narrative paths with characters.
- Compare alternatives by branching from meaningful moments.
- Success Definition:
- Maintains weekly reading+chat routine.
- Uses "Try Another Story Path" (fork) intentionally while preserving continuity.

### Secondary Users

#### Persona 3: Eunji Lee (Parent, Decision-Maker)

- Role: Primary adopter/payer.
- Core Need: Safe, productive language practice for child, not passive screen time.
- Current Problem Experience:
- Existing options are either too rigid (worksheet-like) or too unstructured.
- Hard to verify if child engagement is educationally meaningful.
- Success Definition:
- Child returns voluntarily and consistently.
- Parent can see concise weekly signals: active days, resumed story count, branch activity.
- Trust Requirements:
- Parent-linked child account model.
- Basic consent/safety controls and visibility into learning continuity.

### User Journey

#### Discovery

- Parent discovers gaji via recommendations, app stores, or education communities.
- Core message: "Story continuity progression, not worksheet progression."

#### Onboarding

- Parent sets learner profile and enables child account.
- Dual-track first-run:
- Student track: fast start with character-context preview.
- Parent track: concise productive-engagement promise and week-1 goals.
- Age-adaptive guidance is applied from day 1 within a unified product shell.
- Grade 5-6 onboarding capped at 3 steps to reduce early drop-off.

#### Core Usage

- Student starts from chapter-character relationship context.
- Student either:
- starts a new guided scenario conversation, or
- chooses "Try Another Story Path" from an interesting conversation moment.
- System preserves per-user continuity and enforces max 3 top-level branches with archive/resume logic.

#### Success Moment (Aha)

- Student: "I can continue my own evolving story, not start over every time."
- Parent: "My child is returning voluntarily, and this is productive engagement."

#### Long-term Routine

- Student returns weekly to continue/resume/fork meaningful story paths.
- Reading and conversation form a continuity-based habit loop.
- Parent sees steady, trustable progress signals and keeps adoption active.


## Success Metrics

Success for gaji is defined as sustained, self-directed language practice through continuity-based reading and character conversation behavior.

### User Success Metrics

- First-Week Self-Led Conversation Completion Rate:
  - Definition: % of new learners who complete at least 1 self-led conversation (>=8 turns) within first 7 days.
  - Target: >= 55%
- 7-Day Story Return Rate:
  - Definition: % of new learners who return to the same story path within 7 days.
  - Target: >= 35%
- Weekly Reading+Chat Time per Active User:
  - Definition: average weekly minutes spent in reading-linked conversation sessions per WAU.
  - Target: >= 25 minutes
- Learner-Initiated Session Rate:
  - Definition: % of sessions where learner sends the first message (self-directed start).
  - Target: >= 60%
- Week-1 Voluntary Return Signal:
  - Definition: % of new learners who voluntarily return 2+ times in week 1.
  - Target: >= 40%
- Meaningful Continuity Action Rate:
  - Definition: % of WAU performing at least 1 qualified continuity action (resume or intentional branch) weekly.
  - Target: >= 50%
  - Qualification Rule: intentional branch counts only if created after >=4 turns in the source conversation.

### Business Objectives

- Primary Objective: user growth through continuity-driven engagement.
- 3-Month Objective:
  - Reach WAU 200 while maintaining all core user-value KPI thresholds.
- 12-Month Objective:
  - Reach WAU 2,000 while maintaining all core user-value KPI thresholds.
- Strategic Objective:
  - Build a defensible continuity-learning category position between worksheet-style learning and unstructured chatbot play.

### Key Performance Indicators

#### Leading Indicators

- First-Week Self-Led Conversation Completion Rate (target >= 55%)
- Learner-Initiated Session Rate (target >= 60%)
- Meaningful Continuity Action Rate (target >= 50%)

#### Lagging Indicators

- 7-Day Story Return Rate (target >= 35%)
- WAU (target 200 by month 3, 2,000 by month 12)
- Weekly Reading+Chat Time per Active User (target >= 25 minutes)

### Metric Definitions and Integrity Rules

- Turn Definition:
  - 1 turn = 1 learner message + 1 assistant response pair.
- WAU Dedupe Rule:
  - Deduplicate by stable learner account ID across web/mobile.
- Learner-Initiated Session Rule:
  - Exclude system-triggered auto-resume sessions from initiated-session metric.
- Anti-Gaming Rule:
  - "Intentional branch" contributes to KPI only when branch action occurs after >=4 turns in source conversation.
- Aggregation Rule:
  - Keep raw events append-only; compute qualified KPI metrics in derived daily aggregation tables.


## MVP Scope

### Core Features

MVP v2 will be delivered in 8 weeks, leveraging existing systems in `gajiFE-next`, `gajiBE`, and `gajiAI`, while executing a major UI transformation.

1. Parent-linked child account with minimal consent flow.
2. Chapter-context character conversation experience (web/mobile).
3. Per-user continuity with resume-last-active-path behavior.
4. Fork system with max 3 top-level branches and archive/unarchive path management.
5. Age-adaptive onboarding guidance (grade 5-6 vs middle school) in a unified product shell.
6. Parent weekly summary card:
   - active days
   - resumed story count
   - branch activity
7. Safety baseline for risky prompts with logging/audit visibility.
8. UI transformation package (major redesign):
   - new visual direction and design-system tokens
   - rebuilt core component set
   - redesigned core journeys (onboarding, conversation continuity, fork/archive flows, parent summary)
   - feature-flagged v2 rollout path

### Out of Scope for MVP

1. Full parent control center (time limits, advanced policy controls).
2. Expanded social/community roadmap features (beyond current baseline).
3. School/teacher dashboards and institutional integrations.
4. Deep dual-product split by segment (separate apps/architecture).
5. Advanced monetization or partner packaging workflows.

### MVP Success Criteria

1. Delivery:
   - MVP v2 shipped within 8 weeks.
2. User-value thresholds maintained:
   - First-week self-led conversation completion >= 55%
   - 7-day story return rate >= 35%
   - Weekly reading+chat time per active user >= 25 minutes
   - Learner-initiated session rate >= 60%
   - Meaningful continuity action rate >= 50%
3. Growth trajectory:
   - WAU trend supports month-3 target of 200.
4. Trust baseline validated:
   - Parent-linked account/consent flow functional.
   - Safety baseline active for risky prompts.
5. Continuity integrity validated:
   - top-branch cap (3) enforced.
   - resume and branch states stable across sessions.
6. UI transformation quality gates:
   - core journey parity passes in v2 UI
   - no critical mobile/desktop regressions in primary flows
   - KPI event integrity preserved after UI migration

### Future Vision

If MVP v2 validates the continuity-learning model, gaji evolves into:

1. Full parent trust/control suite (time guidance, richer progress insights).
2. Continuity intelligence layer (branch recommendations and path coaching).
3. Youth-safe social learning expansion.
4. School and educator ecosystem integration.
5. Broader segment and localization expansion supported by mature design infrastructure.

### 8-Week Execution Plan (UI Transformation Included)

1. Week 1:
   - UX audit and IA freeze
   - event contract + KPI schema lock
   - continuity hierarchy freeze (“Continue Story Path” primary)
2. Week 2:
   - design-system tokens/components baseline
   - backend rules for branch cap and continuity invariants
3. Week 3-4:
   - core journey redesign/prototyping and implementation start
   - onboarding age-adaptive guidance + continuity flows
4. Week 5-6:
   - v2 app shell + major screen migration
   - parent-link/consent + weekly summary integration
5. Week 7:
   - stabilization, E2E, responsive/accessibility/performance checks
6. Week 8:
   - launch hardening, bug triage, feature-flagged release readiness

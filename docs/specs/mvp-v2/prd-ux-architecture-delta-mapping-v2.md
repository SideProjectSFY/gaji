# PRD-UX-Architecture Delta Mapping (V2)

**Date:** 2026-02-26  
**Project:** gaji  
**Purpose:** Reconcile planning deltas between PRD (`docs/specs/v1/prd.md`), UX spec, and UX-aligned architecture/epics.

## Baseline Sources

- PRD: `/Users/yeongjae/gaji/docs/specs/v1/prd.md`
- UX: `/Users/yeongjae/gaji/docs/specs/mvp-v2/ux-design-specification.md`
- Architecture: `/Users/yeongjae/gaji/docs/specs/mvp-v2/architecture-ux-aligned.md`
- Authoritative Epics: `/Users/yeongjae/gaji/docs/specs/mvp-v2/epics-ux-aligned.md`

## Decision

- Authoritative epic/story source for V2 is `epics-ux-aligned.md`.
- Legacy epic baseline is superseded for V2 execution and archived at `/Users/yeongjae/gaji/docs/specs/v1/epics-v1-legacy.md`.

## Delta Matrix

| Area | PRD Requirement | UX/Architecture State | Resolution in Authoritative Epics |
| --- | --- | --- | --- |
| Frontend layering | FR4: UI and logic separation (`ui` vs `hooks`/`application`) | Implicit but not enforceable in prior stories | Epic 7 Story 7.1 adds CI-enforced separation rule |
| Render-mode clarity | FR5: SSR/CSR distinguishable by `SS/CS` naming | Not explicitly covered | Epic 7 Story 7.2 adds naming convention check gate |
| Artifact traceability | FR12: implementation artifacts under `_bmad-output/implementation-artifacts` | Process intent existed, no explicit story AC | Epic 7 Story 7.3 adds compliance validation |
| Docs discoverability | FR13: lifecycle navigation in docs | Mentioned in PRD only | Epic 7 Story 7.4 adds version-folder separation gate under `/Users/yeongjae/gaji/docs/specs/` |
| Continuity UX priorities | Continue/Fork/Recovery hierarchy and fallback | Explicit in UX + architecture | Preserved across Epics 1-6; no change |

## Invariants Preserved

- Interaction hierarchy invariant: `Continue > Path-state > Fork`
- Journey metric keys:
  - `journey_continue_completed`
  - `journey_fork_completed`
  - `journey_recovery_completed`
- Gateway boundary invariant: browser -> Next.js `/api/*` -> downstream services
- Accessibility and interaction target: desktop-first adaptive + WCAG AA + keyboard-first

## Implementation Rule

- Sprint planning and story generation for V2 must use only `epics-ux-aligned.md` as source of truth.

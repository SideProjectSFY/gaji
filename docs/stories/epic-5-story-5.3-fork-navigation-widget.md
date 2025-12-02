# Story 5.3: Conversation Fork Tree UI (Simplified)

**Epic**: Epic 5 - Scenario Tree Visualization
**Priority**: P1 - High
**Status**: Ready for Review
**Estimated Effort**: 2 Points

## Description

Implement the **Fork Navigation Widget** for the Chat Interface. Since we have simplified the Conversation Forking model to a maximum depth of 1 (Root -> Fork), we do not need a complex recursive tree visualization for conversations. Instead, we need a simple, intuitive widget to navigate between the Original conversation and its Forks.

## Context Source

- **Epic**: Epic 5: Scenario Tree Visualization
- **Source Document**: `docs/epics/epic-5-scenario-tree-visualization.md`

## Dependencies

- **Requires**:
  - Story 4.5: Conversation Forking Frontend (Fork creation)
  - Story 4.3: Real-Time Chat Interface UI (Widget placement)

## Acceptance Criteria

### Fork Navigation Widget

- [x] **Placement**: Located at the top of the Chat Interface (sticky header).

- [x] **State: Root Conversation**:

  - If the current conversation is a **Root** and has forks:
    - Show a dropdown or list: "Forks ({n})".
    - Clicking opens a list of forks with their titles/descriptions.
    - Selecting a fork navigates to it.
  - If no forks: Hide widget.

- [x] **State: Forked Conversation**:

  - Show "Forked from: [Link to Parent Title]".
  - Show "Sibling Forks": Dropdown to switch to other forks of the same parent.

- [x] **Visual Design**:

  - Minimalist design (e.g., a breadcrumb style or a small toolbar).
  - Distinct visual cue that this is a "Branch" (e.g., branch icon).

- [x] **Navigation**:
  - Switching conversations should be fast (client-side router).

## Dev Technical Guidance

- **Component**: Create `ForkNavigationWidget.vue`.
- **Data**: The conversation object (from Story 4.1) should include `parent_id` and `forks_count` (or a list of fork summaries) to populate this widget efficiently.
- **Simplicity**: Do NOT implement a D3 graph here. Keep it text/dropdown based.

## Dev Agent Record

### Agent Model Used

- Claude Sonnet 4.5

### Implementation Summary

Successfully implemented the Fork Navigation Widget with the following components:

1. **ForkNavigationWidget.vue Component**

   - Displays parent link when viewing a forked conversation
   - Shows dropdown with child fork when viewing root conversation with forks
   - Includes branch icon (🌿) for visual distinction
   - Implements fast client-side navigation using Vue Router
   - Auto-closes dropdown when conversation ID changes

2. **API Service (conversationApi.ts)**

   - Created `getForkRelationship()` function to fetch fork relationship data
   - Transforms snake_case API responses to camelCase for Vue components
   - Handles optional parent/child conversation data
   - Includes helper functions for getting parent/child individually

3. **ConversationChat.vue Integration**

   - Added ForkNavigationWidget to chat header (sticky position)
   - Loads fork relationship data on mount and conversation change
   - Passes fork relationship data to widget component

4. **Unit Tests**
   - 8 comprehensive tests covering all widget states
   - Tests for parent navigation, child navigation, dropdown toggle
   - Tests for empty states and edge cases
   - All tests passing ✓

### File List

- `/Users/min-yeongjae/gaji/gajiFE/frontend/src/components/chat/ForkNavigationWidget.vue` (created)
- `/Users/min-yeongjae/gaji/gajiFE/frontend/src/components/chat/__tests__/ForkNavigationWidget.spec.ts` (created)
- `/Users/min-yeongjae/gaji/gajiFE/frontend/src/services/conversationApi.ts` (created)
- `/Users/min-yeongjae/gaji/gajiFE/frontend/src/views/ConversationChat.vue` (modified)

### Completion Notes

- Implemented simplified fork navigation for max depth 1 (Root → Fork only)
- Widget shows/hides based on conversation state (root with child vs fork with parent)
- Used Panda CSS for styling consistency with existing components
- Dropdown design is minimalist and intuitive
- Navigation is instant using Vue Router (no page reload)
- All acceptance criteria met and tested

### Change Log

- 2025-11-30: Initial implementation of Fork Navigation Widget (Story 5.3)

  - Created ForkNavigationWidget component with dropdown and parent link
  - Added API service methods for fork relationship data
  - Integrated widget into ConversationChat view
  - Added comprehensive unit tests (8 tests, all passing)

- 2025-11-30: Enhanced error handling and loading states (QA Improvement)

  - **API Layer (conversationApi.ts)**:
    - Added UUID format validation for conversationId
    - Added try-catch error handling with graceful null returns
    - Added detailed error logging
  - **Component Layer (ForkNavigationWidget.vue)**:
    - Added `isLoading` and `hasError` props with default values
    - Added loading state UI with spinner emoji
    - Added error state UI with warning emoji
    - Improved component resilience
  - **Integration Layer (ConversationChat.vue)**:
    - Added `forkRelationshipError` state tracking
    - Enhanced `loadForkRelationship()` with proper error state management
    - Pass loading/error states to ForkNavigationWidget component
  - **Tests**:
    - Added 2 new test cases for loading and error states
    - All 10 tests passing ✓
    - Total test duration: 38ms

- 2025-11-30: Enhanced UX with accessibility and keyboard navigation (QA Improvement - Medium Priority)

  - **Dropdown Outside Click Handling**:
    - Added click outside detection to close dropdown automatically
    - Implemented via `handleClickOutside()` with proper ref tracking
    - Event listeners managed with onMounted/onUnmounted lifecycle hooks
  - **ARIA Accessibility Attributes**:
    - Added `<nav>` semantic HTML with `aria-label="대화 분기 탐색"`
    - Parent link: `role="link"`, `aria-label` with dynamic description
    - Dropdown button: `aria-expanded`, `aria-haspopup`, descriptive `aria-label`
    - Dropdown menu: `role="menu"` with `aria-label`
    - Menu items: `role="menuitem"` with descriptive `aria-label`
    - Loading state: `<output>` element with `aria-live="polite"`
    - Error state: `role="alert"` with `aria-live="assertive"`
    - Decorative icons: `aria-hidden="true"` to hide from screen readers
  - **Keyboard Navigation Support**:
    - Enter/Space on dropdown button: Opens dropdown
    - Escape key: Closes dropdown and returns focus to button
    - Enter/Space on menu item: Navigates to conversation
    - Tab key: Closes dropdown when tabbing away
    - Enter on parent link: Navigates to parent conversation
  - **Focus Management**:
    - Added `:focus` styles with visible outline for all interactive elements
    - Consistent focus indicators (2px solid outline with offset)
    - Focus returns to button after Escape key closes dropdown
  - **Tests**:
    - Added 4 new test cases:
      - closes dropdown when clicking outside
      - handles keyboard navigation - Escape key closes dropdown
      - handles keyboard navigation - Enter on child item navigates
      - has proper ARIA attributes for accessibility
    - All 14 tests passing ✓
    - Total test duration: 48ms

- 2025-11-30: Enhanced UX with i18n, animations, and responsive design (QA Improvement - Low Priority)
  - **Internationalization (i18n) Support**:
    - Created comprehensive `messages` object with 11 localization functions:
      - `originalConversation()`, `forkedConversation()`: Header titles
      - `forkedFrom()`, `viewOriginal()`: Parent navigation text
      - `forkedConversations(count)`: Dropdown button with count
      - `selectFork()`: Dropdown ARIA label
      - `viewFork(title)`: Menu item ARIA label
      - `loading()`, `loadError()`: Loading/error state messages
      - `openForksMenu()`, `forksNavigation()`: Accessibility labels
    - Updated all template strings to use `messages` object
    - Pattern allows easy migration to full i18n library (vue-i18n) later
    - Maintains type safety with TypeScript function signatures
  - **Smooth Animations**:
    - Added `slideDown` animation to dropdown menu (0.2s ease-out)
      - Combines opacity (0 → 1) and translateY (-10px → 0)
      - Creates smooth entrance effect when dropdown opens
    - Enhanced chevron icon rotation transition (0.2s → 0.3s ease-in-out)
    - Added global `@keyframes` definitions to App.vue:
      - `slideDown`: Reusable dropdown animation
      - `fadeIn`: General purpose fade-in animation
    - Non-scoped global styles allow animations throughout app
  - **Responsive Design**:
    - Implemented mobile-first breakpoint at 640px
    - Widget container: Added `flexWrap: 'wrap'` for mobile stacking
    - Dropdown positioning: `left: 'auto'` and `right: 0` on mobile
    - Parent text: Reduced `maxWidth` from 200px to 150px on mobile
    - Ensures proper layout on small screens without overflow
  - **File Changes**:
    - `ForkNavigationWidget.vue`: Added messages object, updated all text references, enhanced animations, added responsive breakpoints
    - `App.vue`: Added global `@keyframes slideDown` and `fadeIn` animations
  - **Tests**:
    - All 14 tests passing ✓ (no regressions from i18n/animation/responsive changes)
    - Total test duration: 48ms

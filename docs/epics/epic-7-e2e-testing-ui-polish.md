# Epic 7: E2E Testing & UI Polish

## Epic Goal

Implement comprehensive end-to-end testing across all user journeys and polish UI components to match the design specifications from mockups, ensuring a production-ready, visually consistent, and thoroughly tested user experience.

## User Value

Users will experience:

- **Visual Consistency**: Professional, polished UI matching design specifications across all screens
- **Reliability**: Thoroughly tested features with minimal bugs and edge cases handled
- **Smooth User Experience**: Refined interactions, animations, and responsive design
- **Confidence**: Stable platform with validated critical user journeys

## Epic Context

**Design Assets**: 10 screen mockups available in `docs/mocks/`

- Login.png
- Register.png
- Main.png
- Books.png
- Book Detail.png
- Integrated Search.png
- Character-chat-page.png
- Conversations.png
- Profile.png
- About.png

**Testing Scope**: E2E tests covering all critical user journeys from Epic 0-6
**UI Polish Scope**: Alignment with mockup designs, responsive behavior, accessibility improvements

## Timeline

**Week 8-10 of MVP development** (可 parallel with Epic 6)

- **E2E Test Foundation**: Days 1-3 (Stories 7.1-7.2) - 가 Epic 0-6 완료 후 시작
- **Core Journey Testing**: Days 4-6 (Stories 7.3-7.4) - Epic 1-4 기능 검증
- **UI Polish - Authentication & Discovery**: Days 7-9 (Stories 7.5-7.6) - 디자인 시스템 구축
- **UI Polish - Conversation & User Features**: Days 10-12 (Stories 7.7-7.8) - 최종 폴리싱

## Stories Overview

### Phase 1: E2E Testing Foundation (~16 hours)

**Stories 7.1-7.2**: Playwright setup, Flyway-based test data management, authentication flows. Uses existing Docker infrastructure with runtime seeding. CI/CD integration deferred to Story 7.9.

### Phase 2: Critical Journey Testing (~16 hours)

**Stories 7.3-7.4**: Scenario creation/forking flows, conversation flows with AI responses

### Phase 3: UI Polish - Discovery & Navigation (~16 hours)

**Stories 7.5-7.6**: Login/Register screens, Main/Books/Book Detail pages, navigation patterns

### Phase 4: UI Polish - Core Features (~16 hours)

**Stories 7.7-7.8**: Character chat interface, Conversations list, Profile/About pages, search experience

**Total Epic Effort**: ~64 hours (~10-12 working days for 2 engineers, accounting for iteration)

## Stories

### Story 7.1: E2E Testing Foundation - Playwright Setup & Authentication Tests

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-7-story-7.1-playwright-setup-authentication-tests.md`

**Description**: Initialize Playwright testing framework with TypeScript support, configure test environments (dev/staging), implement test data management strategy, and create E2E tests for authentication flows (login, register, logout).

**Acceptance Criteria**:

- [ ] Playwright installed and configured with TypeScript
- [ ] Test environment configuration (dev: localhost, staging: deployed environment)
- [ ] Test data factory/fixtures for users, books, scenarios
- [ ] CI/CD integration (GitHub Actions) runs tests on PR
- [ ] Authentication E2E tests:
  - [ ] User registration with validation errors
  - [ ] User login with invalid/valid credentials
  - [ ] JWT token storage and persistence
  - [ ] Logout clears authentication state
- [ ] Test reports generated (HTML, JSON)
- [ ] Screenshot/video capture on test failures
- [ ] Page Object Model (POM) pattern for reusable components

**Technical Notes**:

- Use `@playwright/test` with TypeScript
- Configure separate test databases or use transaction rollback
- Implement helper utilities for API setup (create test users, seed books)
- Mock Gemini API responses for consistent AI testing

**Effort Estimate**: 8 hours

---

### Story 7.2: E2E Testing - Test Data Management & Flyway-Based Cleanup

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-7-story-7.2-test-data-cicd.md`

**Description**: Establish robust test data management with runtime database seeding via API, implement Flyway-based cleanup for test isolation, and create reusable test utilities for common operations. Uses existing Docker infrastructure with simplified architecture.

**Architectural Decision**: Uses existing `docker-compose.yml` with Flyway clean/migrate for database cleanup instead of separate test configuration. CI/CD integration deferred to Story 7.9 after test suite validation.

**Acceptance Criteria**:

- [x] Database seeding via runtime API calls (3 books, 4 scenarios, 3 users)
- [x] Test isolation using Flyway clean + migrate in global-setup
- [x] Development environment configured with `flyway.clean-disabled: false`
- [x] Production environment secured with `flyway.clean-disabled: true`
- [x] Test utilities library with 15+ helper functions:
  - [x] `loginAsUser(email, password)`
  - [x] `createScenario(bookId, scenarioData)`
  - [x] `startConversation(scenarioId)`
  - [x] `mockAIResponse(conversationId, message)`
  - [x] `waitForToast()`, `takeDebugScreenshot()`, and more
- [x] Sequential test execution configured (single worker for data isolation)
- [x] Global setup/teardown with service health checks
- [ ] Performance validation: E2E suite completes in < 10 minutes (validate in Story 7.8)
- [ ] Backend cleanup endpoints implemented (blocking remaining work)

**Technical Notes**:

- Uses Flyway clean/migrate for database cleanup (no SQL init scripts needed)
- Runtime seeding via REST API calls (more flexible than SQL)
- Development profile allows Flyway clean via `spring.flyway.clean-disabled: false`
- Production profile prevents Flyway clean via `spring.flyway.clean-disabled: true`
- Uses existing docker-compose.yml (ports: 8080, 8000, 5432, 6379)
- Sequential execution (`workers: 1`) ensures test data isolation
- Mock Gemini API responses for consistent AI testing

**Current Status**: Frontend implementation complete ✅, Backend cleanup endpoints required ❌

**Effort Estimate**: 8 hours (6h complete, 2-4h backend remaining)

---

### Story 7.3: E2E Testing - Scenario Creation & Forking Flows

**Priority: P1 - High**

**Story File**: `docs/stories/epic-7-story-7.3-scenario-creation-forking-tests.md`

**Description**: Implement comprehensive E2E tests covering scenario creation workflows (including validation), scenario browsing/filtering, and scenario forking (both conversation-level and meta-level forks).

**Acceptance Criteria**:

- [ ] Scenario Creation Tests:
  - [ ] Open unified scenario creation modal from Book Detail page
  - [ ] Validation: at least one type with 10+ characters enforced
  - [ ] Validation: real-time character counter updates
  - [ ] Validation: submit button disabled when invalid
  - [ ] Validation: error message displays for invalid inputs
  - [ ] Valid scenario creates successfully and redirects to chat
  - [ ] Created scenario appears in book's scenario list
- [ ] Scenario Browsing Tests:
  - [ ] Filter scenarios by book
  - [ ] Search scenarios by title/description
  - [ ] Sort scenarios by popularity, recency
  - [ ] Pagination works correctly
- [ ] Scenario Forking Tests:
  - [ ] Conversation-level fork: create new branch in existing scenario
  - [ ] Meta-fork: create new scenario based on existing one
  - [ ] Fork displays relationship to original scenario
  - [ ] Fork counter increments on original scenario
- [ ] Edge Cases:
  - [ ] Empty scenario lists display "No scenarios yet. Create the first one!" message
  - [ ] Invalid book IDs return 404 with user-friendly error page
  - [ ] Network errors show Toast notification with retry option
  - [ ] Whitespace-only inputs treated as empty (validation fails)
  - [ ] Concurrent scenario creation: handle duplicate title gracefully

**Technical Notes**:

- Test all three scenario types (character, event, setting changes) independently
- Verify PostgreSQL scenario metadata persists correctly (check vectordb_passage_ids array)
- Test meta-forking preserves parent scenario context properly
- Validate UI updates after fork creation (fork_count increments)
- Mock FastAPI VectorDB responses for consistent character search results

**Effort Estimate**: 8 hours

---

### Story 7.4: E2E Testing - Conversation Flows & AI Interactions

**Priority: P1 - High**

**Story File**: `docs/stories/epic-7-story-7.4-conversation-flows-ai-tests.md`

**Description**: Create E2E tests for conversation flows including sending messages, receiving AI responses via Long Polling (2-second intervals), conversation forking (ROOT-only, max depth 1), and conversation history persistence.

**Acceptance Criteria**:

- [ ] Conversation Start Tests:
  - [ ] Start conversation from scenario
  - [ ] Initial AI greeting appears
  - [ ] Conversation context includes scenario details
- [ ] Message Exchange Tests:
  - [ ] User sends message
  - [ ] AI response streams via SSE (mocked)
  - [ ] Message appears in conversation history
  - [ ] Scroll to bottom on new messages
- [ ] Conversation Forking Tests:
  - [ ] Fork conversation at any message
  - [ ] New fork displays divergence point
  - [ ] Original conversation remains unchanged
  - [ ] Navigate between fork branches
- [ ] Conversation Management Tests:
  - [ ] List all user conversations
  - [ ] Filter conversations by book/scenario
  - [ ] Delete conversation (with confirmation)
  - [ ] Conversation persistence after page reload
- [ ] Edge Cases:
  - [ ] AI service unavailable: "AI is temporarily unavailable. Please try again." displays
  - [ ] Long messages (>2000 chars): character counter shows, truncation warning
  - [ ] Rapid message sending: rate limiting triggers Toast "Please wait before sending another message"
  - [ ] Network interruption during polling: reconnection behavior with exponential backoff
  - [ ] Fork from ROOT conversation: depth limit (max 1) enforced
  - [ ] Message copy on fork: min(6, total) messages copied correctly

**Technical Notes**:

- Mock Gemini API responses for predictable testing (use fixtures for common responses)
- Test Long Polling mechanism: verify 2-second intervals, progress updates (0-100%)
- Verify Redis conversation context management (scenario context + message history)
- Test conversation tree visualization for forked conversations
- Validate ROOT-only forking constraint (attempts to fork non-ROOT conversations fail)

**Effort Estimate**: 8 hours

---

### Story 7.5: UI Polish - Authentication Screens & Main Navigation

**Priority: P1 - High**

**Story File**: `docs/stories/epic-7-story-7.5-ui-polish-auth-navigation.md`

**Description**: Refine Login and Register screens to match mockup designs, implement responsive layouts, add loading states and error handling, and polish Main navigation header with search integration.

**Acceptance Criteria**:

**Login Screen (`Login.png`):**

- [ ] Visual design matches mockup:
  - [ ] Logo and branding placement
  - [ ] Form layout and spacing (PandaCSS)
  - [ ] Button styles (PrimeVue theming)
  - [ ] Link to Register page
- [ ] Input validation with inline error messages
- [ ] Loading spinner during authentication
- [ ] Success/error toast notifications
- [ ] "Remember me" functionality (optional)
- [ ] Responsive: mobile/tablet/desktop layouts

**Register Screen (`Register.png`):**

- [ ] Visual design matches mockup
- [ ] Password strength indicator
- [ ] Email format validation
- [ ] Duplicate email error handling
- [ ] Terms of service checkbox (if in mockup)
- [ ] Redirect to login after successful registration

**Main Navigation (`Main.png`):**

- [ ] Header with logo, search bar, user menu
- [ ] Integrated search (see `Integrated Search.png`)
- [ ] Active navigation state indicators
- [ ] Responsive mobile menu (hamburger icon)
- [ ] User avatar/profile dropdown
- [ ] Smooth transitions and animations

**Technical Notes**:

- Use PandaCSS utility classes for styling consistency
- PrimeVue components: Button, InputText, Password, Toast
- Implement proper focus states for accessibility
- Add animations using PandaCSS animations or CSS transitions

**Effort Estimate**: 8 hours

---

### Story 7.6: UI Polish - Books Discovery & Book Detail Pages

**Priority: P1 - High**

**Story File**: `docs/stories/epic-7-story-7.6-ui-polish-books-pages.md`

**Description**: Polish Books browse page and Book Detail page to match mockup designs, implement book cards grid layout, filtering/sorting, and rich book detail view with scenario listings.

**Acceptance Criteria**:

**Books Page (`Books.png`):**

- [ ] Visual design matches mockup:
  - [ ] Book card grid layout (responsive: 1/2/3/4 columns)
  - [ ] Book cover images with fallback
  - [ ] Book title, author, excerpt/description
  - [ ] Hover effects and transitions
- [ ] Filtering options:
  - [ ] By genre/category
  - [ ] By popularity, publication date
- [ ] Search integration (query from header)
- [ ] Pagination or infinite scroll
- [ ] Loading skeleton states
- [ ] Empty state when no books match filters

**Book Detail Page (`Book Detail.png`):**

- [ ] Visual design matches mockup:
  - [ ] Large book cover
  - [ ] Full book metadata (title, author, description, stats)
  - [ ] "Create Scenario" prominent CTA button
  - [ ] Scenario list for this book
- [ ] Scenario cards:
  - [ ] Scenario title, description
  - [ ] Engagement metrics (conversation count, fork count)
  - [ ] "Start Conversation" button
- [ ] Related books section (optional)
- [ ] Breadcrumb navigation
- [ ] Responsive layout

**Technical Notes**:

- Use PandaCSS grid system for responsive layouts
- PrimeVue components: Card, Skeleton, Button, Badge
- Implement lazy loading for book cover images
- Optimize scenario list performance (pagination if > 20 scenarios)

**Effort Estimate**: 8 hours

---

### Story 7.7: UI Polish - Character Chat Interface & Conversations List

**Priority: P1 - High**

**Story File**: `docs/stories/epic-7-story-7.7-ui-polish-chat-conversations.md`

**Description**: Refine character chat interface to match mockup design, implement message bubbles, typing indicators, Long Polling UI with progress indicators (0-100%), and polish Conversations list page with filtering and organization.

**Acceptance Criteria**:

**Character Chat Page (`Character-chat-page.png`):**

- [ ] Visual design matches mockup:
  - [ ] Message bubbles (user vs AI styling, different colors/alignment)
  - [ ] Avatar images (user, character from VectorDB)
  - [ ] Timestamp display (relative time: "2 minutes ago")
  - [ ] Message input area with send button (disabled while AI responding)
- [ ] AI typing indicator during Long Polling with progress bar (0-100%)
- [ ] Long Polling UI: progress updates every 2 seconds, smooth message appearance
- [ ] Scroll to bottom on new messages (smooth scroll animation)
- [ ] "Fork Conversation" button visible only on ROOT conversations
- [ ] Scenario context panel (collapsible):
  - [ ] Displays current scenario details
  - [ ] Shows divergence point if forked
- [ ] Mobile-optimized chat layout
- [ ] Animations: message fade-in, smooth scroll

**Conversations List Page (`Conversations.png`):**

- [ ] Visual design matches mockup:
  - [ ] Conversation card layout
  - [ ] Book/scenario information
  - [ ] Last message preview
  - [ ] Timestamp of last activity
- [ ] Filtering options:
  - [ ] By book
  - [ ] By date range
  - [ ] Active vs archived
- [ ] Search conversations
- [ ] Sorting: recent, oldest, most active
- [ ] Delete conversation action (with confirmation modal)
- [ ] Empty state when no conversations exist

**Technical Notes**:

- Use PrimeVue ScrollPanel for chat container
- Implement virtualized scrolling for long conversation histories
- PrimeVue components: InputTextarea, Button, Avatar, Chip
- Handle SSE connection errors gracefully with reconnection logic

**Effort Estimate**: 8 hours

---

### Story 7.8: UI Polish - Profile, About, & Integrated Search

**Priority: P2 - Medium**

**Story File**: `docs/stories/epic-7-story-7.8-ui-polish-profile-search.md`

**Description**: Polish Profile page, About page, and Integrated Search experience to match mockup designs, implement user settings, platform information, and advanced search functionality.

**Acceptance Criteria**:

**Profile Page (`Profile.png`):**

- [ ] Visual design matches mockup:
  - [ ] User avatar (editable)
  - [ ] User information display/edit form
  - [ ] Email, username, bio
- [ ] Account settings:
  - [ ] Change password
  - [ ] Email preferences (optional)
  - [ ] Privacy settings
- [ ] User statistics:
  - [ ] Total conversations
  - [ ] Scenarios created
  - [ ] Forks contributed
- [ ] Save changes with validation
- [ ] Success/error notifications

**About Page (`About.png`):**

- [ ] Visual design matches mockup:
  - [ ] Platform description and mission
  - [ ] Feature highlights
  - [ ] How-to guide or tutorial links
- [ ] FAQ section (optional)
- [ ] Contact information or feedback form
- [ ] Social media links
- [ ] Version information

**Integrated Search (`Integrated Search.png`):**

- [ ] Visual design matches mockup:
  - [ ] Search dropdown from header
  - [ ] Search results grouped by type:
    - [ ] Books
    - [ ] Scenarios
    - [ ] Conversations (if user is logged in)
- [ ] Autocomplete/suggestions as user types
- [ ] "View all results" link for each category
- [ ] Keyboard navigation (arrow keys, enter to select)
- [ ] Recent searches (stored locally)
- [ ] Loading states and empty states
- [ ] Responsive: full-screen on mobile

**Technical Notes**:

- PrimeVue components: AutoComplete, Dropdown, Fieldset, FileUpload (avatar)
- Implement debounced search to avoid excessive API calls
- Use local storage for recent searches
- Optimize search indexing on backend (PostgreSQL full-text search or Elasticsearch)

**Effort Estimate**: 8 hours

---

## Success Metrics

- **Test Coverage**: ≥ 80% E2E coverage for critical user journeys
- **Visual Consistency**: 100% of screens match mockup designs (reviewed by design/PM)
- **Test Reliability**: < 5% flaky test rate in CI/CD
- **Performance**: E2E test suite completes in < 10 minutes
- **Accessibility**: WCAG 2.1 AA compliance for all polished UI components
- **User Feedback**: Positive feedback on UI polish in beta testing

## Dependencies

- **Epics 0-6 completed**: All features implemented and functional
- **Design mockups**: Available in `docs/mocks/` (confirmed)
- **Playwright setup**: Development environment supports Playwright browser automation
- **Docker infrastructure**: Existing `docker-compose.yml` with services (PostgreSQL, Redis, Backend, AI)
- **Flyway configuration**: Development environment with `flyway.clean-disabled: false` for test cleanup
- **Backend cleanup endpoints**: Required for Story 7.2 completion (test data cleanup)
- **CI/CD infrastructure**: Deferred to Story 7.9 after test suite validation

## Risks & Mitigations

| Risk                               | Impact | Mitigation                                                                   |
| ---------------------------------- | ------ | ---------------------------------------------------------------------------- |
| E2E tests are flaky/unreliable     | High   | Implement retry logic, proper waits, mock external APIs                      |
| Backend cleanup endpoints delayed  | High   | Frontend infrastructure ready; proceed with Story 7.3+ using available tools |
| Flyway clean in dev environment    | Medium | Explicit configuration with `clean-disabled: false` in dev only              |
| Mockup designs missing details     | Medium | Collaborate with designer for clarifications, use existing design system     |
| UI polish scope creeps             | Medium | Strictly adhere to mockup specifications, defer enhancements to future epics |
| Test data isolation issues         | Low    | Sequential execution (`workers: 1`) ensures single test at a time            |
| Accessibility requirements complex | Low    | Use PrimeVue's built-in ARIA support, add manual testing                     |

## Definition of Done

- [ ] All 8 stories (7.1-7.8) completed with acceptance criteria met
- [ ] Story 7.9 (CI/CD integration) can be initiated once test suite validated
- [ ] E2E test suite running reliably in local development environment
- [ ] All screens visually match mockup designs (reviewed and approved)
- [ ] No critical or high-severity bugs from testing
- [ ] Responsive design validated on mobile/tablet/desktop
- [ ] Documentation updated (test setup, UI component guidelines)
- [ ] Code reviewed and merged to main branch
- [ ] Stakeholder demo completed and approved

**Note**: CI/CD pipeline integration (GitHub Actions) is deferred to Story 7.9 after core test suite is proven stable.

## Notes

- This epic focuses on **quality assurance and user experience refinement** rather than new feature development
- E2E tests will serve as regression suite for future development
- UI polish establishes design system patterns for future features
- Consider recording E2E test videos for documentation and training purposes
- May identify bugs or UX improvements for backlog in future sprints

### Architectural Decisions (Story 7.2)

**Simplified Test Infrastructure Approach:**

The original Story 7.2 design included separate test Docker configuration (`docker-compose.test.yml`), SQL initialization scripts, and immediate CI/CD integration. After analysis, we simplified to:

1. **Use Existing Infrastructure**: Tests use production `docker-compose.yml` (not separate test config)
2. **Runtime Seeding**: Database seeding via REST API calls (not SQL scripts)
3. **Flyway-Based Cleanup**: Use `flywayClean` + `flywayMigrate` for test isolation
4. **Defer CI/CD**: CI/CD integration moved to Story 7.9 (after test suite validation)

**Benefits:**

- ✅ Reduced configuration files (single Docker compose, no init SQL scripts)
- ✅ Simplified maintenance (same infrastructure for dev and test)
- ✅ Consistency between environments
- ✅ Easier local development

**Trade-offs:**

- ⚠️ Cannot run dev and test simultaneously (same ports)
- ⚠️ Manual Docker service management required
- ⚠️ Slower startup than SQL-based seeding (runtime API calls)

**Configuration Safety:**

- Development: `flyway.clean-disabled: false` (allows database cleanup for E2E tests)
- Staging: `flyway.clean-disabled: true` (prevents accidental data loss)
- Production: `flyway.clean-disabled: true`, `ddl-auto: none` (maximum security)

### Future Story: 7.9 - CI/CD E2E Test Integration

**Scope**: Automate E2E test execution in GitHub Actions CI/CD pipeline

**Prerequisites**:

- Stories 7.1-7.8 complete with stable test suite
- Backend cleanup endpoints implemented
- Test performance validated (< 10 minutes)
- Service health checks proven reliable

**Acceptance Criteria**:

- [ ] GitHub Actions workflow runs E2E tests on PR to main/develop
- [ ] Docker containers spin up automatically (PostgreSQL, Redis, Backend, AI)
- [ ] Flyway clean + migrate ensures clean test database
- [ ] Test artifacts uploaded (reports, screenshots, videos)
- [ ] PR fails if tests fail
- [ ] Parallel test execution optimized for CI environment

**Estimated Effort**: 4-6 hours (infrastructure proven, just automation)

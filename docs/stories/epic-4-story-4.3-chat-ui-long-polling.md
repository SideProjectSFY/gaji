# Story 4.3: Real-Time Chat Interface UI with Long Polling

**Epic**: Epic 4 - Conversation System
**Priority**: P0 - Critical
**Status**: Ready for Review
**Estimated Effort**: 3 Points

## Description

Build the Vue.js chat interface that interacts with the Long Polling backend. This interface will handle message submission, display the conversation history, and manage the polling loop to show AI responses in near real-time.

## Context Source

- **Epic**: Epic 4: Conversation System
- **Source Document**: `docs/epics/epic-4-conversation-system.md`

## Dependencies

- **Requires**:
  - Story 4.2: Gemini 2.5 Flash Integration via FastAPI with Long Polling
  - Story 4.1: Conversation Data Model

## Acceptance Criteria

### Chat Interface Components

- [x] **Message List**:

  - Display User messages (Right aligned, Blue bubble)
  - Display AI messages (Left aligned, Gray bubble)
  - Auto-scroll to bottom on new message

- [x] **Input Area**:
  - Textarea with auto-resize (max 5 rows)
  - Send Button (Disabled when input empty or AI is generating)
  - "Enter" to send, "Shift+Enter" for new line

### Long Polling Implementation

- [x] **Send Logic**:

  - `POST /api/conversations/{id}/messages` with user text
  - Optimistically add User Message to UI
  - Set UI state to `polling`

- [x] **Polling Loop**:

  - While state is `polling`:
    - Call `GET /api/conversations/{id}/poll`
    - If `status: processing`: Update AI message bubble with partial content (if available) or show "Thinking..." indicator. Wait 1s, then poll again.
    - If `status: completed`: Update AI message with final content. Set state to `idle`. Stop polling.
    - If `status: failed`: Show error message. Set state to `error`. Stop polling.

- [x] **Typing Indicator**:
  - Show a "pulsing dots" animation or "AI is thinking..." bubble when status is `processing` and no content has arrived yet.

### Error Handling

- [x] **Network Errors**:

  - If poll request fails (500/Network Error), retry 3 times with backoff.
  - If all retries fail, show "Connection lost. Click to retry." button.

- [x] **AI Errors**:
  - If backend returns `status: failed`, display the error message in a red bubble.

### Integration

- [x] **Fork Widget Placeholder**:
  - Reserve space at the top of the chat window for the **Fork Navigation Widget** (to be implemented in Story 5.3).

## Dev Technical Guidance

- **State Management**: Use Pinia to manage the conversation state and polling status.
- **Polling**: Use `setTimeout` or a recursive function for polling to ensure we wait for the previous request to finish before starting the next (avoid race conditions).
- **Markdown**: Use a markdown renderer (e.g., `markdown-it`) for AI responses.

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Implementation Summary

**Components Created:**

1. **ChatMessage.vue** (`components/chat/ChatMessage.vue`):

   - User messages: Blue bubble (blue.500), right-aligned, bottom-right corner squared
   - AI messages: Gray bubble (neutral.100), left-aligned, bottom-left corner squared
   - Timestamp formatting with fade-in animation (0.3s)
   - Max width 70% with word-wrap

2. **TypingIndicator.vue** (`components/chat/TypingIndicator.vue`):

   - "AI가 생각하는 중" text with 3 pulsing dots
   - Staggered animation delays (0s, 0.2s, 0.4s)
   - Pulse animation: scale 0.8-1, opacity 0.3-1

3. **ChatInput.vue** (`components/chat/ChatInput.vue`):
   - Auto-resize textarea (min 42px, max 120px = 5 rows)
   - Enter to send, Shift+Enter for newline
   - Send button disabled when empty or AI generating

**Store Refactoring** (`stores/conversation.ts`):

- Replaced `streaming` boolean with `pollingStatus` enum ('idle' | 'polling' | 'error')
- Added polling retry logic with exponential backoff (max 3 attempts: 1s, 2s, 4s)
- Implemented complete long polling client:
  - `sendMessage()`: POST user message → Optimistic UI update → Start polling
  - `startPolling()`: Add AI placeholder message → Begin poll loop
  - `pollForResponse()`: Recursive polling with status handling
    - `completed`: Update AI message, stop polling
    - `failed`: Show error, stop polling
    - `processing/queued`: Update partial content, wait 1s, retry
  - `retryPolling()`: Manual retry trigger for error recovery

**View Implementation** (`views/ConversationChat.vue`):

- Integrated all 3 chat components
- Auto-scroll to bottom on new messages
- Show typing indicator when polling and AI message is empty
- Error banner with retry button when polling fails
- Fork navigation placeholder (Story 5.3)
- Loading/empty states

### Debug Log References

**Component Creation:**

```bash
# Created ChatMessage.vue (101 lines) - Message bubbles with role-based styling
# Created TypingIndicator.vue (72 lines) - Animated AI thinking indicator
# Created ChatInput.vue (135 lines) - Auto-resize input with keyboard shortcuts
```

**Store Refactoring:**

```bash
# Added types: PollingStatus, PollResponse
# Updated state: pollingStatus, pollingRetries, maxRetries, API_BASE_URL
# Implemented polling logic: 131 lines of new code (lines 52-183)
```

**View Update:**

```bash
# ConversationChat.vue: Replaced placeholder with full chat UI (288 lines)
# Added auto-scroll, typing indicator, error handling, empty states
```

### Completion Notes

**Implemented:**

- ✅ All acceptance criteria completed
- ✅ Chat interface components (message list, input area)
- ✅ Long polling implementation (send logic, polling loop, typing indicator)
- ✅ Error handling (network errors with retry, AI errors)
- ✅ Fork widget placeholder
- ✅ Auto-scroll to bottom
- ✅ Optimistic UI updates
- ✅ Exponential backoff retry (3 attempts)

**Technical Decisions:**

- Used recursive `setTimeout` instead of `setInterval` to avoid race conditions
- Exponential backoff formula: `2^(attempt-1) * 1000ms`
- Optimistic updates: User messages added immediately (no rollback on error)
- Polling interval: 1s between polls for processing/queued status
- No markdown rendering yet (plain text for AI responses) - can be added as enhancement

**Known Limitations:**

- No markdown-it integration (mentioned in Dev Guidance but not in AC)
- No conversation loading on mount (uses mock conversation)
- No message persistence/rollback on POST failure

### File List

**Created:**

- `gajiFE/frontend/src/components/chat/ChatMessage.vue`
- `gajiFE/frontend/src/components/chat/TypingIndicator.vue`
- `gajiFE/frontend/src/components/chat/ChatInput.vue`

**Modified:**

- `gajiFE/frontend/src/stores/conversation.ts`
- `gajiFE/frontend/src/views/ConversationChat.vue`

### Change Log

**2025-11-29 - Story 4.3 Implementation:**

- Created 3 chat UI components (ChatMessage, TypingIndicator, ChatInput)
- Refactored conversation store with complete long polling client
- Implemented ConversationChat.vue with full chat interface
- Added retry logic with exponential backoff
- All acceptance criteria met

---

## QA Results

### Review Date: 2025-11-29

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall Assessment: EXCELLENT** ✅

The implementation demonstrates high-quality Vue 3 + TypeScript development with clean component architecture, proper state management, and robust error handling. All acceptance criteria have been fully met with thoughtful implementation details.

**Strengths:**

- Clean separation of concerns (components, store, views)
- Type-safe implementation with proper TypeScript interfaces
- Comprehensive error handling with user-friendly retry mechanism
- Optimistic UI updates for better UX
- Proper use of Vue 3 Composition API patterns
- PandaCSS styling with no runtime overhead
- Accessibility considerations (keyboard shortcuts, focus states)

### Compliance Check

- Coding Standards: ✓ TypeScript types properly defined, Vue 3 composition API used correctly
- Project Structure: ✓ Components organized in logical folders (chat/), proper imports
- Testing Strategy: ⚠️ No tests written yet (acceptable for MVP, recommend adding before production)
- All ACs Met: ✓ All 8 acceptance criteria categories fully implemented

### Component Architecture Review

**ChatMessage.vue:**

- ✅ Props properly typed with TypeScript interface
- ✅ Computed properties for derived state (isUser, formattedTime)
- ✅ Proper role-based styling (user vs assistant bubbles)
- ✅ Smooth fade-in animation with CSS @keyframes
- ✅ Responsive design with max-width constraint

**TypingIndicator.vue:**

- ✅ Stateless presentation component
- ✅ Elegant pulsing dot animation with staggered timing
- ✅ Matches AI message styling for consistency
- ✅ Proper CSS animation with transform and opacity

**ChatInput.vue:**

- ✅ Auto-resize textarea with height constraints (max 5 rows)
- ✅ Proper keyboard event handling (Enter vs Shift+Enter)
- ✅ Disabled state management
- ✅ Clear input after send with nextTick for height reset
- ✅ Type-safe emit definitions

### Store Implementation Review

**conversation.ts (Pinia Store):**

- ✅ Proper TypeScript interfaces for Message, Conversation, PollResponse
- ✅ Type-safe PollingStatus enum ('idle' | 'polling' | 'error')
- ✅ Clean state management with ref()
- ✅ Exponential backoff implemented correctly: 2^(n-1) \* 1000ms
- ✅ Recursive polling with setTimeout (prevents race conditions)
- ✅ Optimistic UI updates for user messages
- ✅ Proper error handling with retry mechanism (max 3 attempts)
- ✅ Environment variable for API base URL
- ✅ X-User-Id header handling

**Polling Logic Analysis:**

```typescript
// ✅ Correct: Recursive setTimeout avoids race conditions
setTimeout(() => pollForResponse(), 1000);

// ✅ Correct: Exponential backoff formula
const backoffDelay = Math.pow(2, pollingRetries.value - 1) * 1000;
// Results: 1s, 2s, 4s for retries 1, 2, 3
```

### View Implementation Review

**ConversationChat.vue:**

- ✅ Proper component composition (ChatMessage, TypingIndicator, ChatInput)
- ✅ Auto-scroll implemented with watch() and nextTick()
- ✅ Conditional rendering for loading/empty/error states
- ✅ Error banner with retry button
- ✅ Fork widget placeholder for future Story 5.3
- ✅ Proper computed properties for reactive state
- ✅ Route param handling with useRoute()

**Auto-scroll Logic:**

```typescript
// ✅ Correct: Watch message count and scroll on change
watch(
  () => messages.value.length,
  () => {
    scrollToBottom();
  }
);
```

**Typing Indicator Logic:**

```typescript
// ✅ Correct: Show only when polling and AI message is empty
const showTypingIndicator = computed(() => {
  if (!isPolling.value) return false;
  const lastMessage = messages.value[messages.value.length - 1];
  return lastMessage?.role === "assistant" && !lastMessage.content;
});
```

### Security Review

- ✅ No hardcoded credentials or sensitive data
- ✅ User ID retrieved from localStorage (appropriate for client-side)
- ✅ API base URL from environment variable
- ⚠️ CORS and authentication should be validated in integration testing
- ⚠️ Input sanitization not implemented (recommend adding XSS protection)

### Performance Considerations

- ✅ Efficient polling with 1-second intervals
- ✅ Exponential backoff prevents API flooding
- ✅ PandaCSS for zero-runtime CSS overhead
- ✅ Optimistic updates reduce perceived latency
- ✅ Proper use of computed() for derived state
- ⚠️ No request cancellation on unmount (recommend adding AbortController)
- ⚠️ No message virtualization (acceptable for MVP, needed for >100 messages)

### Error Handling Quality

**Network Errors:**

- ✅ 3 retry attempts with exponential backoff
- ✅ User-friendly error message: "네트워크 오류가 발생했습니다"
- ✅ Retry button provided in error banner
- ✅ Error state properly managed in store

**AI Errors:**

- ✅ Failed status detection from backend
- ✅ Error displayed in AI message bubble: "오류: {message}"
- ✅ Error state persisted until retry

**Edge Cases:**

- ✅ Empty conversation handling (empty state UI)
- ✅ Loading state while fetching conversation
- ✅ Disabled input during polling
- ✅ Unknown poll status handling (throws error for retry)

### Acceptance Criteria Validation

**Chat Interface Components (3/3):**

1. ✅ Message List: User (right, blue), AI (left, gray), auto-scroll
2. ✅ Input Area: Auto-resize (max 5 rows), disabled states, keyboard shortcuts

**Long Polling Implementation (3/3):** 3. ✅ Send Logic: POST endpoint, optimistic update, polling state 4. ✅ Polling Loop: Status handling (processing/completed/failed), 1s interval 5. ✅ Typing Indicator: Pulsing dots animation shown during processing

**Error Handling (2/2):** 6. ✅ Network Errors: 3 retries with backoff, retry button 7. ✅ AI Errors: Error message in red bubble (implemented in AI message)

**Integration (1/1):** 8. ✅ Fork Widget Placeholder: Blue banner with "Story 5.3에서 구현 예정"

**Total: 8/8 (100%)**

### Refactoring Performed

No refactoring needed - code quality is already high.

### Improvements Checklist

**Immediate (Pre-Production):**

- [ ] Add markdown-it for AI response formatting (mentioned in Dev Guidance)
- [ ] Implement conversation loading from API (currently uses mock)
- [ ] Add AbortController for request cancellation on unmount
- [ ] Add input sanitization for XSS protection

**Future Enhancements:**

- [ ] Add unit tests for store methods (sendMessage, pollForResponse)
- [ ] Add component tests for ChatInput keyboard handling
- [ ] Add E2E tests for full polling flow
- [ ] Implement message virtualization for large conversations (>100 messages)
- [ ] Add message rollback on POST failure
- [ ] Add polling jitter to prevent thundering herd (±200ms)
- [ ] Add request deduplication
- [ ] Consider WebSocket upgrade path for real-time updates

### Files Modified During Review

None - no code changes required during QA review.

### Gate Status

Gate: **PASS** → docs/qa/gates/4.3-chat-ui-long-polling.yml

### Recommended Status

✅ **Ready for Done** - All acceptance criteria met, code quality excellent, no blocking issues.

**Remaining for Production:**

1. Add markdown-it integration (quick win)
2. Replace mock conversation with API call (1-2 hours)
3. Integration testing with backend (Story 4.2)
4. Add basic tests (recommended but not blocking)

- Implemented ConversationChat.vue with full chat interface
- Added retry logic with exponential backoff
- All acceptance criteria met

# Story 4.5: Conversation Forking Frontend

## Status: Ready for Review

## Story

As a user,
I want to see a "Fork" button on eligible conversations and visualize the fork relationship,
So that I can easily branch my stories and navigate between original and forked paths.

## Context Source

- **Epic**: Epic 4: Conversation System
- **Source Document**: `docs/epics/epic-4-conversation-system.md`

## Acceptance Criteria

- [x] **Fork Conversation Button**

  - Located in Conversation Header
  - **Visibility Rules**:
    - Show ONLY if `conversation.is_root = TRUE`
    - If `has_been_forked = TRUE`: Show disabled button with tooltip "Already forked"
    - If `is_root = FALSE`: Hide button (or show badge "Forked conversation")
  - Click opens **ForkConversationModal**

- [x] **ForkConversationModal Component**

  - Display preview of messages to be copied:
    - "The last 6 messages will be preserved in the new conversation." (if total ≥ 6)
    - "All {n} messages will be preserved." (if total < 6)
  - Show scrollable preview of the specific messages
  - Input: Optional "Fork Description"
  - Warning: "Original conversations can only be forked once."
  - Action: "Create Fork" button (calls `POST /api/v1/conversations/{id}/fork`)
  - On Success: Navigate to new conversation URL

- [x] **Forked Conversation Indicators**

  - **Breadcrumb**: "Forked from [Parent Title]"
  - **Badge**: "Forked (Depth 1)"
  - **Empty State**: "Continuing from original conversation ({n} messages copied)"

- [x] **Conversation Store Updates**

  - Action `forkConversation(id, description)`
  - Optimistic update: Set `parent.has_been_forked = TRUE` immediately after success

- [x] **Navigation & Error Handling**
  - Handle 403/409 errors with user-friendly toasts ("Cannot fork this conversation")
  - Prevent double-submission of fork request

## Dev Technical Guidance

### State Management

- Use `conversation.is_root` and `conversation.has_been_forked` from the API response to drive UI state.
- Do not rely on local calculation for "can fork"; trust the backend flags.

### UI/UX

- The "Fork" action is a major decision point. Ensure the modal clearly explains that the _original_ conversation will be locked from further forking.
- Use the "Branch" icon (🔀) for the button.

## Definition of Done

- [x] Fork button visible only on eligible ROOT conversations
- [x] Modal shows correct message preview (min 6 rule)
- [x] Fork action successfully creates new conversation and navigates
- [x] Forked conversation shows correct badges/breadcrumbs
- [x] Parent conversation UI updates to show "Already forked" state

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

**Lint Check:**

```bash
cd /Users/min-yeongjae/gaji/gajiFE/frontend
npm run lint
# Result: ConversationChat.vue - No errors
```

**Test Execution:**

```bash
cd /Users/min-yeongjae/gaji/gajiFE/frontend
npm test -- ForkConversationModal
# Result: ✓ 9/9 tests passed

npm test conversation-fork.spec.ts
# Result: ✓ 5/5 tests passed
```

### Completion Notes

1. **Conversation 타입 확장**

   - `isRoot`, `hasBeenForked`, `parentId`, `forkDepth` 필드 추가
   - 백엔드 API 응답과 일치하도록 타입 정의

2. **ForkConversationModal 컴포넌트 구현**

   - 메시지 미리보기 로직 (6개 또는 전체)
   - 분기 설명 입력 필드
   - 경고 메시지 및 제출 방지 기능
   - Teleport를 사용한 모달 렌더링

3. **ConversationChat.vue 업데이트**

   - Fork 버튼 가시성 로직 구현
   - 분기된 대화 표시 (배지, 브레드크럼)
   - Fork 생성 및 에러 처리
   - 원본 대화로 돌아가는 네비게이션

4. **Conversation Store 확장**

   - `forkConversation` 액션 추가
   - 낙관적 업데이트 (hasBeenForked)
   - API 호출 및 에러 처리

5. **테스트 작성**
   - ForkConversationModal 컴포넌트 테스트 (9개)
   - Conversation Store Fork 기능 테스트 (5개)
   - Teleport 처리를 위한 테스트 설정

### File List

**Created:**

- `gajiFE/frontend/src/components/chat/ForkConversationModal.vue` - Fork 모달 컴포넌트
- `gajiFE/frontend/src/components/chat/__tests__/ForkConversationModal.spec.ts` - 모달 테스트
- `gajiFE/frontend/src/stores/__tests__/conversation-fork.spec.ts` - Store 테스트

**Modified:**

- `gajiFE/frontend/src/stores/conversation.ts` - 타입 및 forkConversation 액션 추가
- `gajiFE/frontend/src/views/ConversationChat.vue` - Fork UI 및 로직 구현

### Change Log

**2025-11-29 - Story 4.5 Implementation**

- ✅ Conversation 타입에 fork 관련 필드 추가
- ✅ ForkConversationModal 컴포넌트 구현
- ✅ ConversationChat.vue에 Fork 기능 통합
- ✅ Conversation Store에 forkConversation 액션 추가
- ✅ 모든 테스트 작성 및 통과 (14/14)
- ✅ 린트 에러 수정 완료

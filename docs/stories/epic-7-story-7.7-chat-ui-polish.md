# Story 7.7 - Chat & Conversations UI Polish

**Epic**: Epic 7 - E2E Testing & UI Polish  
**Priority**: P1 - High  
**Estimated Effort**: 8 hours  
**Status**: Ready for Review

---

## Description

Polish chat message bubbles and conversations list sidebar UI

---

## Problem & Opportunity

**Epic 7 Context**: E2E Testing & UI Polish - Week 8-10

**Problem**:

- Unclear distinction between user/assistant message bubbles
- No typing indicator animation
- Conversations list sidebar UX needs improvement
- Unstable auto-scroll behavior
- Missing message copy functionality

**Opportunity**:

- Improved readability with clear message distinction
- Enhanced AI response waiting experience with animations
- Quick switching between conversations with sidebar
- Smooth scrolling with PrimeVue ScrollPanel
- Increased convenience with message copy button

---

## Proposed Implementation

### Overview

This story focuses on **polish-only** improvements to existing chat and conversation components. No major UI restructuring - only refinements to message display, typing indicators, scroll behavior, accessibility, and visual feedback.

### Existing Components to Polish

**Files:**

- `gajiFE/src/views/ConversationChat.vue`
- `gajiFE/src/views/Conversations.vue`
- `gajiFE/src/components/chat/ChatMessage.vue`
- `gajiFE/src/components/chat/ChatInput.vue`
- `gajiFE/src/components/chat/TypingIndicator.vue`

### 1. Message Display Polish (ChatMessage.vue)

```vue
<!-- gajiFE/frontend/src/components/MessageBubble.vue -->
<script setup lang="ts">
import { computed } from "vue";
import { useClipboard } from "@vueuse/core";
import Button from "primevue/button";
import { useToast } from "primevue/usetoast";
import { css } from "@/styled-system/css";
import { flex, vstack } from "@/styled-system/patterns";

interface Props {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  isLatest?: boolean;
}

const props = defineProps<Props>();
const toast = useToast();

const { copy, copied } = useClipboard({ source: props.content });

const formattedTime = computed(() => {
  const date = new Date(props.timestamp);
  return date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });
});

const handleCopy = async () => {
  await copy();
  toast.add({
    severity: "success",
    summary: "복사 완료",
    detail: "메시지가 클립보드에 복사되었습니다",
    life: 2000,
  });
};

const isUser = computed(() => props.role === "user");
</script>

<template>
  <div
    :class="containerStyles"
    :data-role="role"
    :data-testid="`message-${role}`"
  >
    <div :class="bubbleStyles">
      <div :class="contentStyles" v-html="content"></div>

      <div :class="metaStyles">
        <span :class="timestampStyles">{{ formattedTime }}</span>

        <Button
          icon="pi pi-copy"
          text
          rounded
          size="small"
          :class="copyButtonStyles"
          @click="handleCopy"
          :data-testid="`copy-button-${role}`"
          aria-label="메시지 복사"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
const containerStyles = css({
  display: 'flex',
  marginBottom: '4',
  '&[data-role="user"]': {
    justifyContent: 'flex-end',
  },
  '&[data-role="assistant"]': {
    justifyContent: 'flex-start',
  },
});

const bubbleStyles = css({
  maxWidth: { base: '85%', md: '70%' },
  padding: '3',
  borderRadius: 'lg',
  boxShadow: 'sm',
  position: 'relative',
  '[data-role="user"] &': {
    bg: 'blue.600',
    color: 'white',
    borderBottomRightRadius: 'sm',
  },
  '[data-role="assistant"] &': {
    bg: 'gray.100',
    color: 'gray.800',
    borderBottomLeftRadius: 'sm',
  },
  _hover: {
    '& [data-copy-button]': {
      opacity: '1',
    },
  },
});

const contentStyles = css({
  fontSize: 'md',
  lineHeight: '1.6',
  wordWrap: 'break-word',
  whiteSpace: 'pre-wrap',
});

const metaStyles = flex({
  justify: 'space-between',
  align: 'center',
  marginTop: '2',
  gap: '2',
});

const timestampStyles = css({
  fontSize: 'xs',
  '[data-role="user"] &': {
    color: 'blue.100',
  },
  '[data-role="assistant"] &': {
    color: 'gray.500',
  },
});

const copyButtonStyles = css({
  opacity: '0',
  transition: 'opacity 0.2s',
  '[data-role="user"] &': {
    color: 'white',
  },
  '[data-role="assistant"] &': {
    color: 'gray.600',
  },
});
</style>
```

### 2. Typing Indicator Component

```vue
<!-- gajiFE/frontend/src/components/TypingIndicator.vue -->
<script setup lang="ts">
import { css } from "@/styled-system/css";
import { flex } from "@/styled-system/patterns";
</script>

<template>
  <div :class="containerStyles" data-testid="typing-indicator">
    <div :class="bubbleStyles">
      <div :class="dotsContainerStyles">
        <div :class="dotStyles" :style="{ animationDelay: '0s' }"></div>
        <div :class="dotStyles" :style="{ animationDelay: '0.2s' }"></div>
        <div :class="dotStyles" :style="{ animationDelay: '0.4s' }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
const containerStyles = flex({
  justifyContent: 'flex-start',
  marginBottom: '4',
});

const bubbleStyles = css({
  bg: 'gray.100',
  padding: '3',
  borderRadius: 'lg',
  boxShadow: 'sm',
});

const dotsContainerStyles = flex({
  gap: '2',
  align: 'center',
});

const dotStyles = css({
  width: '8px',
  height: '8px',
  bg: 'gray.400',
  borderRadius: 'full',
  animation: 'bounce 1.4s infinite ease-in-out',
});

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
}
</style>
```

### 3. Chat Page with ScrollPanel

```vue
<!-- gajiFE/frontend/src/pages/ChatPage.vue -->
<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from "vue";
import { useRoute } from "vue-router";
import ScrollPanel from "primevue/scrollpanel";
import InputText from "primevue/inputtext";
import Button from "primevue/button";
import { conversationsService } from "@/services/conversations";
import { aiService } from "@/services/ai";
import MessageBubble from "@/components/MessageBubble.vue";
import TypingIndicator from "@/components/TypingIndicator.vue";
import { css } from "@/styled-system/css";
import { flex, vstack } from "@/styled-system/patterns";

const route = useRoute();

const conversationId = ref<number>(parseInt(route.params.id as string));
const messages = ref<any[]>([]);
const inputMessage = ref("");
const isLoading = ref(false);
const isTyping = ref(false);
const scrollPanel = ref<any>(null);

onMounted(async () => {
  await loadMessages();
  scrollToBottom();
});

watch(
  () => messages.value.length,
  () => {
    nextTick(() => scrollToBottom());
  }
);

const loadMessages = async () => {
  try {
    isLoading.value = true;
    messages.value = await conversationsService.getMessages(
      conversationId.value
    );
  } catch (error) {
    console.error("Failed to load messages:", error);
  } finally {
    isLoading.value = false;
  }
};

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isTyping.value) return;

  const userMessage = inputMessage.value.trim();
  inputMessage.value = "";

  // Add user message immediately
  messages.value.push({
    role: "user",
    content: userMessage,
    timestamp: new Date().toISOString(),
  });

  // Show typing indicator
  isTyping.value = true;

  try {
    // Start AI processing
    await aiService.sendMessage(conversationId.value, userMessage);

    // Long Polling for AI response
    const response = await pollAIResponse();

    // Add assistant message
    messages.value.push({
      role: "assistant",
      content: response.content,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Failed to send message:", error);
    // Show error message
    messages.value.push({
      role: "assistant",
      content:
        "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.",
      timestamp: new Date().toISOString(),
    });
  } finally {
    isTyping.value = false;
  }
};

const pollAIResponse = async (): Promise<{ content: string }> => {
  const maxAttempts = 15; // 30 seconds (2s interval)
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      const response = await aiService.pollResponse(conversationId.value);

      if (response.status === "completed") {
        return { content: response.content };
      }

      // Wait 2 seconds before next poll
      await new Promise((resolve) => setTimeout(resolve, 2000));
      attempts++;
    } catch (error) {
      throw error;
    }
  }

  throw new Error("AI response timeout");
};

const scrollToBottom = () => {
  if (scrollPanel.value) {
    const container = scrollPanel.value.$el.querySelector(
      ".p-scrollpanel-content"
    );
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
};

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};
</script>

<template>
  <div :class="containerStyles">
    <!-- Messages Area -->
    <ScrollPanel
      ref="scrollPanel"
      :class="scrollPanelStyles"
      data-testid="messages-scroll-panel"
    >
      <div :class="messagesContainerStyles">
        <!-- Loading State -->
        <div v-if="isLoading" :class="loadingStyles">
          <i class="pi pi-spin pi-spinner" :class="spinnerStyles"></i>
          <p>메시지를 불러오는 중...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="messages.length === 0" :class="emptyStateStyles">
          <i class="pi pi-comments" :class="emptyIconStyles"></i>
          <p>대화를 시작해보세요</p>
        </div>

        <!-- Messages -->
        <template v-else>
          <MessageBubble
            v-for="(message, index) in messages"
            :key="index"
            :role="message.role"
            :content="message.content"
            :timestamp="message.timestamp"
            :is-latest="index === messages.length - 1"
          />
        </template>

        <!-- Typing Indicator -->
        <TypingIndicator v-if="isTyping" />
      </div>
    </ScrollPanel>

    <!-- Input Area -->
    <div :class="inputContainerStyles">
      <InputText
        v-model="inputMessage"
        placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
        :class="inputStyles"
        :disabled="isTyping"
        @keypress="handleKeyPress"
        data-testid="message-input"
        aria-label="메시지 입력"
      />
      <Button
        icon="pi pi-send"
        :disabled="!inputMessage.trim() || isTyping"
        :loading="isTyping"
        @click="sendMessage"
        :class="sendButtonStyles"
        data-testid="send-button"
        aria-label="메시지 전송"
      />
    </div>
  </div>
</template>

<style scoped>
const containerStyles = vstack({
  height: 'full',
  gap: '0',
});

const scrollPanelStyles = css({
  flex: '1',
  width: 'full',
});

const messagesContainerStyles = vstack({
  padding: '6',
  gap: '0',
  minHeight: 'full',
});

const loadingStyles = vstack({
  gap: '4',
  align: 'center',
  justify: 'center',
  padding: '12',
  color: 'gray.500',
});

const spinnerStyles = css({
  fontSize: '2xl',
});

const emptyStateStyles = vstack({
  gap: '4',
  align: 'center',
  justify: 'center',
  padding: '12',
  color: 'gray.500',
  height: 'full',
});

const emptyIconStyles = css({
  fontSize: '4xl',
});

const inputContainerStyles = flex({
  gap: '2',
  padding: '4',
  borderTop: '1px solid',
  borderColor: 'gray.200',
  bg: 'white',
});

const inputStyles = css({
  flex: '1',
});

const sendButtonStyles = css({
  flexShrink: '0',
});
</style>
```

### 4. Conversations Sidebar

```vue
<!-- gajiFE/frontend/src/components/ConversationsSidebar.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import Sidebar from "primevue/sidebar";
import Button from "primevue/button";
import { conversationsService } from "@/services/conversations";
import { css } from "@/styled-system/css";
import { vstack, flex } from "@/styled-system/patterns";

interface Props {
  visible: boolean;
}

interface Emits {
  (e: "update:visible", value: boolean): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const router = useRouter();
const route = useRoute();

const conversations = ref<any[]>([]);
const isLoading = ref(false);

const currentConversationId = computed(() => {
  return parseInt(route.params.id as string);
});

onMounted(async () => {
  await loadConversations();
});

const loadConversations = async () => {
  try {
    isLoading.value = true;
    conversations.value = await conversationsService.getUserConversations();
  } catch (error) {
    console.error("Failed to load conversations:", error);
  } finally {
    isLoading.value = false;
  }
};

const selectConversation = (conversationId: number) => {
  router.push(`/conversations/${conversationId}`);
  emit("update:visible", false);
};

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "방금 전";
  if (diffMins < 60) return `${diffMins}분 전`;
  if (diffHours < 24) return `${diffHours}시간 전`;
  if (diffDays < 7) return `${diffDays}일 전`;

  return date.toLocaleDateString("ko-KR", { month: "short", day: "numeric" });
};
</script>

<template>
  <Sidebar
    :visible="visible"
    position="left"
    :class="sidebarStyles"
    @update:visible="emit('update:visible', $event)"
  >
    <template #header>
      <h2 :class="headerStyles">대화 목록</h2>
    </template>

    <!-- Loading State -->
    <div v-if="isLoading" :class="loadingStyles">
      <i class="pi pi-spin pi-spinner"></i>
      <p>불러오는 중...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="conversations.length === 0" :class="emptyStateStyles">
      <i class="pi pi-inbox" :class="emptyIconStyles"></i>
      <p>아직 대화가 없습니다</p>
      <Button
        label="새 대화 시작"
        icon="pi pi-plus"
        @click="router.push('/scenarios')"
      />
    </div>

    <!-- Conversations List -->
    <div v-else :class="conversationsListStyles">
      <div
        v-for="conversation in conversations"
        :key="conversation.id"
        :class="conversationItemStyles"
        :data-active="conversation.id === currentConversationId"
        :data-testid="`conversation-item-${conversation.id}`"
        @click="selectConversation(conversation.id)"
      >
        <div :class="conversationHeaderStyles">
          <h3 :class="conversationTitleStyles">
            {{ conversation.scenarioTitle }}
          </h3>
          <span :class="timestampStyles">
            {{ formatTimestamp(conversation.lastMessageAt) }}
          </span>
        </div>

        <p :class="lastMessageStyles">
          {{ conversation.lastMessage || "메시지가 없습니다" }}
        </p>

        <div :class="conversationMetaStyles">
          <span :class="metaItemStyles">
            <i class="pi pi-comments"></i>
            {{ conversation.messageCount }}
          </span>
          <span
            v-if="conversation.type === 'FORKED'"
            :class="forkedBadgeStyles"
          >
            <i class="pi pi-fork"></i>
            포크됨
          </span>
        </div>
      </div>
    </div>
  </Sidebar>
</template>

<style scoped>
const sidebarStyles = css({
  width: { base: '85vw', md: '400px' },
});

const headerStyles = css({
  fontSize: 'xl',
  fontWeight: 'bold',
  color: 'gray.800',
});

const loadingStyles = vstack({
  gap: '4',
  align: 'center',
  padding: '12',
  color: 'gray.500',
});

const emptyStateStyles = vstack({
  gap: '4',
  align: 'center',
  padding: '12',
  textAlign: 'center',
  color: 'gray.500',
});

const emptyIconStyles = css({
  fontSize: '4xl',
});

const conversationsListStyles = vstack({
  gap: '2',
});

const conversationItemStyles = css({
  padding: '4',
  borderRadius: 'md',
  cursor: 'pointer',
  transition: 'all 0.2s',
  borderLeft: '3px solid transparent',
  _hover: {
    bg: 'gray.100',
  },
  '&[data-active="true"]': {
    bg: 'blue.50',
    borderLeftColor: 'blue.600',
  },
});

const conversationHeaderStyles = flex({
  justify: 'space-between',
  align: 'center',
  marginBottom: '2',
});

const conversationTitleStyles = css({
  fontSize: 'md',
  fontWeight: 'semibold',
  color: 'gray.800',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
  flex: '1',
});

const timestampStyles = css({
  fontSize: 'xs',
  color: 'gray.500',
  flexShrink: '0',
  marginLeft: '2',
});

const lastMessageStyles = css({
  fontSize: 'sm',
  color: 'gray.600',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
  marginBottom: '2',
});

const conversationMetaStyles = flex({
  gap: '3',
  fontSize: 'xs',
  color: 'gray.500',
});

const metaItemStyles = flex({
  gap: '1',
  align: 'center',
});

const forkedBadgeStyles = flex({
  gap: '1',
  align: 'center',
  bg: 'purple.100',
  color: 'purple.700',
  padding: '1 2',
  borderRadius: 'full',
});
</style>
```

---

## 완료 기준(AC)

### ChatMessage Component Polish

- [x] User/Assistant message styling clearly distinguished
- [x] Timestamp displayed in readable format
- [x] Message copy functionality works (if exists, else add simple copy)
- [x] Text wrapping handles long messages properly
- [x] Responsive max-width (85% mobile, 70% desktop)
- [x] Accessibility: proper semantic HTML and ARIA
- [x] Smooth hover transitions for interactive elements

### TypingIndicator Component Polish

- [x] Animated dots display during AI response
- [x] Smooth bounce animation
- [x] Consistent styling with assistant messages
- [x] Shows/hides appropriately during message flow
- [x] Accessibility: aria-live for screen readers

### ConversationChat Page Polish

- [x] Messages auto-scroll to bottom on new message
- [x] Input field disabled during AI response
- [x] Send button shows loading state
- [x] Enter key sends message (Shift+Enter for newline if supported)
- [x] Error messages display clearly
- [x] Loading state on initial load
- [x] Empty state when no messages
- [x] Smooth scroll behavior

### Conversations List Polish

- [x] Current conversation highlighted
- [x] Scenario titles displayed clearly
- [x] Last message preview truncated appropriately
- [x] Relative timestamps (e.g., "2h ago")
- [x] Empty state shows when no conversations
- [x] Loading state during fetch
- [x] Hover effects on conversation items
- [x] Keyboard navigation functional

### Responsive Design

- [x] Chat layout works on mobile (<768px)
- [x] Message bubbles adapt to screen width
- [x] Input area remains accessible on mobile
- [x] Conversations list responsive (sidebar/overlay)

### Accessibility

- [x] All interactive elements keyboard accessible
- [x] ARIA labels on buttons and inputs
- [x] Focus indicators visible
- [x] Message role clearly identified (user/assistant)
- [x] Screen reader friendly timestamps

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (Preview)

### Completion Notes

- Polished ChatMessage.vue with copy functionality using @vueuse/core useClipboard
- Enhanced TypingIndicator.vue with bounce animation and aria-live for accessibility
- Updated ChatInput.vue with loading state, disabled state, and accessibility labels
- Refactored ConversationChat.vue to use ChatMessage, ChatInput, TypingIndicator components
- Added auto-scroll on new messages with smooth behavior
- Added loading state and empty state to ConversationChat
- Created ConversationsSidebar.vue component for conversation switching
- Added sidebar toggle button to ConversationChat page
- All new components have proper accessibility attributes (ARIA labels, keyboard navigation)
- Responsive design with mobile-first approach (85% width on mobile, 70% on desktop)
- Created unit tests for ChatMessage, ChatInput, TypingIndicator, and ConversationsSidebar

### File List

**Modified:**

- `gajiFE/src/components/chat/ChatMessage.vue` - Added copy functionality, responsive max-width, accessibility
- `gajiFE/src/components/chat/ChatInput.vue` - Added loading prop, accessibility labels, focus indicators
- `gajiFE/src/components/chat/TypingIndicator.vue` - Improved bounce animation, added aria-live
- `gajiFE/src/views/ConversationChat.vue` - Integrated components, added auto-scroll, loading/empty states, sidebar toggle

**Created:**

- `gajiFE/src/components/chat/ConversationsSidebar.vue` - New sidebar component for conversation list
- `gajiFE/src/components/chat/__tests__/ChatMessage.spec.ts` - Unit tests
- `gajiFE/src/components/chat/__tests__/ChatInput.spec.ts` - Unit tests
- `gajiFE/src/components/chat/__tests__/TypingIndicator.spec.ts` - Unit tests
- `gajiFE/src/components/chat/__tests__/ConversationsSidebar.spec.ts` - Unit tests

### Change Log

| Date       | Change                                   |
| ---------- | ---------------------------------------- |
| 2025-12-08 | Initial implementation of chat UI polish |

---

## 기술 노트

### Key Focus: Polish, Not Restructure

This story is about **incremental improvements** to existing chat components:

- ConversationChat.vue: Main chat page
- ChatMessage.vue: Individual message component
- ChatInput.vue: Input field component
- TypingIndicator.vue: Loading animation
- Conversations.vue: Conversations list

### Changes to Apply

**1. Message Display Improvements**

- Ensure clear visual distinction between user/assistant
- Add/improve copy message functionality
- Polish text wrapping and truncation
- Add smooth transitions

**2. Scroll Behavior**

- Implement auto-scroll on new messages using `nextTick` and `scrollTo`
- Add smooth scroll CSS
- Handle edge cases (user scrolled up)

**3. Loading States**

- Add typing indicator during AI response
- Show loading on initial page load
- Disable inputs during processing

**4. Accessibility**

- Add ARIA attributes
- Ensure keyboard navigation
- Add semantic HTML
- Screen reader support

### Implementation Notes

- **No major restructure**: Work within existing chat system
- **No new libraries**: Use existing Vue reactivity and CSS
- **Preserve functionality**: Only enhance, don't break
- **Test message flow**: Verify send/receive works smoothly

### Testing Approach

- Test message sending/receiving
- Verify auto-scroll behavior
- Test keyboard navigation
- Check responsive layouts
- Verify accessibility with keyboard-only navigation

---

## 관련 참고자료

- Epic 7: `docs/epics/epic-7-e2e-testing-ui-polish.md`
- Epic 4: Conversation System
- Epic 2: AI Integration
- PrimeVue ScrollPanel: https://primevue.org/scrollpanel/
- @vueuse/core: https://vueuse.org/core/useClipboard/

---

## 관련 이슈·블로커

**Dependencies**:

- Epic 4 completed (Conversation System) ✅
- ConversationChat.vue exists ✅
- ChatMessage, ChatInput, TypingIndicator components exist ✅
- No new libraries required

**Blockers**:

- None

**Parallel Work**:

- Story 7.5: Auth & Navigation UI Polish
- Story 7.6: Books UI Polish
- Story 7.8: Profile & Search UI Polish

**Notes**:

- This is a polish-only story - no major structural changes
- Focus on message display, scroll behavior, and accessibility
- Work within existing chat system

**Dependencies**:

- Epic 4 완료 (Conversation System)
- Epic 2 완료 (AI Integration)
- PrimeVue 설정
- PandaCSS 설정
- @vueuse/core 설치

**Blockers**:

- None

**Parallel Work**:

- Story 7.6: Books UI Polish
- Story 7.8: Profile & Search UI Polish

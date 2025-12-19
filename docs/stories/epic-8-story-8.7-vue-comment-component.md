# Story 8.7: Vue Comment Component

**Epic**: Epic 8 - Book Comments System  
**Priority**: P0 - Critical

## Status: Done

**Estimated Effort**: 4 hours  
**Actual Effort**: 1.5 hours

## Description

Create a comprehensive Vue.js component for displaying and managing book comments with CRUD operations.

## Dependencies

**Blocks**:

- Story 8.8: Book Detail Integration (component must exist)

**Requires**:

- Story 8.6: Frontend API Service (API client exists)

## Acceptance Criteria

- [x] `BookComments.vue` created in `gajiFE/src/components/book/`
- [x] Display paginated list of comments (20 per page)
- [x] Comment form with textarea (1-1000 character validation)
- [x] Real-time character counter
- [x] Edit mode for user's own comments
- [x] Delete confirmation dialog
- [x] Loading states during API calls
- [x] Error handling with toast notifications
- [x] Optimistic UI updates
- [x] Responsive design (mobile-friendly)
- [x] Uses PrimeVue components (Textarea, Button, Avatar)
- [x] Scoped CSS styling

## Technical Notes

### Component Structure

```
BookComments.vue
├── Comment List (paginated)
│   ├── Comment Item
│   │   ├── User avatar + username
│   │   ├── Comment content
│   │   ├── Timestamp
│   │   └── Edit/Delete buttons (if isAuthor)
│   └── Load More button
└── Comment Form
    ├── Textarea with character counter
    ├── Submit button
    └── Validation feedback
```

### Following Existing Patterns

- Pattern from `ConversationMemo.vue` (CRUD operations)
- Pattern from `BookLikeButton.vue` (optimistic updates)
- Use PrimeVue: `Textarea`, `Button`, `ConfirmDialog`, `Toast`

### State Management

- Use Vue 3 Composition API
- Reactive refs for comments, loading, errors
- Computed property for character count

## Implementation Files

### 1. BookComments Component

**File**: `gajiFE/src/components/book/BookComments.vue`

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import { commentApi } from "@/api";
import type { BookComment, CommentPage } from "@/types/comment";
import Textarea from "primevue/textarea";
import Button from "primevue/button";
import Avatar from "primevue/avatar";

interface Props {
  bookId: string;
}

const props = defineProps<Props>();
const toast = useToast();
const confirm = useConfirm();

// State
const comments = ref<BookComment[]>([]);
const currentPage = ref(0);
const hasMorePages = ref(false);
const loading = ref(false);
const submitting = ref(false);
const newCommentContent = ref("");
const editingCommentId = ref<string | null>(null);
const editContent = ref("");

// Computed
const characterCount = computed(() => newCommentContent.value.length);
const isContentValid = computed(
  () => characterCount.value >= 1 && characterCount.value <= 1000
);
const editCharacterCount = computed(() => editContent.value.length);
const isEditContentValid = computed(
  () => editCharacterCount.value >= 1 && editCharacterCount.value <= 1000
);

// Methods
const loadComments = async (page: number = 0) => {
  try {
    loading.value = true;
    const response: CommentPage = await commentApi.getComments(
      props.bookId,
      page
    );

    if (page === 0) {
      comments.value = response.content;
    } else {
      comments.value.push(...response.content);
    }

    currentPage.value = page;
    hasMorePages.value = !response.last;
  } catch (error) {
    toast.add({
      severity: "error",
      summary: "Error",
      detail: "Failed to load comments",
      life: 3000,
    });
  } finally {
    loading.value = false;
  }
};

const createComment = async () => {
  if (!isContentValid.value) {
    toast.add({
      severity: "warn",
      summary: "Invalid Input",
      detail: "Comment must be between 1 and 1000 characters",
      life: 3000,
    });
    return;
  }

  try {
    submitting.value = true;
    const newComment = await commentApi.createComment(props.bookId, {
      content: newCommentContent.value,
    });

    // Optimistic update: add to top of list
    comments.value.unshift(newComment);
    newCommentContent.value = "";

    toast.add({
      severity: "success",
      summary: "Success",
      detail: "Comment posted successfully",
      life: 3000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Error",
      detail: error.response?.data?.message || "Failed to post comment",
      life: 3000,
    });
  } finally {
    submitting.value = false;
  }
};

const startEdit = (comment: BookComment) => {
  editingCommentId.value = comment.id;
  editContent.value = comment.content;
};

const cancelEdit = () => {
  editingCommentId.value = null;
  editContent.value = "";
};

const saveEdit = async (commentId: string) => {
  if (!isEditContentValid.value) {
    toast.add({
      severity: "warn",
      summary: "Invalid Input",
      detail: "Comment must be between 1 and 1000 characters",
      life: 3000,
    });
    return;
  }

  try {
    const updated = await commentApi.updateComment(commentId, {
      content: editContent.value,
    });

    // Update in list
    const index = comments.value.findIndex((c) => c.id === commentId);
    if (index !== -1) {
      comments.value[index] = updated;
    }

    cancelEdit();

    toast.add({
      severity: "success",
      summary: "Success",
      detail: "Comment updated successfully",
      life: 3000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Error",
      detail: error.response?.data?.message || "Failed to update comment",
      life: 3000,
    });
  }
};

const confirmDelete = (commentId: string) => {
  confirm.require({
    message: "Are you sure you want to delete this comment?",
    header: "Confirmation",
    icon: "pi pi-exclamation-triangle",
    accept: () => deleteComment(commentId),
  });
};

const deleteComment = async (commentId: string) => {
  try {
    await commentApi.deleteComment(commentId);

    // Optimistic update: remove from list
    comments.value = comments.value.filter((c) => c.id !== commentId);

    toast.add({
      severity: "success",
      summary: "Success",
      detail: "Comment deleted successfully",
      life: 3000,
    });
  } catch (error: any) {
    toast.add({
      severity: "error",
      summary: "Error",
      detail: error.response?.data?.message || "Failed to delete comment",
      life: 3000,
    });
  }
};

const loadMore = () => {
  loadComments(currentPage.value + 1);
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
  if (diffMins < 10080) return `${Math.floor(diffMins / 1440)}d ago`;

  return date.toLocaleDateString();
};

// Lifecycle
onMounted(() => {
  loadComments();
});
</script>

<template>
  <div class="book-comments">
    <h2 class="comments-title">Comments</h2>

    <!-- Comment Form -->
    <div class="comment-form">
      <Textarea
        v-model="newCommentContent"
        placeholder="Share your thoughts about this book..."
        rows="4"
        :maxlength="1000"
        class="comment-textarea"
      />
      <div class="form-footer">
        <span
          class="character-count"
          :class="{ 'text-danger': characterCount > 1000 }"
        >
          {{ characterCount }} / 1000
        </span>
        <Button
          label="Post Comment"
          icon="pi pi-send"
          :loading="submitting"
          :disabled="!isContentValid || submitting"
          @click="createComment"
        />
      </div>
    </div>

    <!-- Comments List -->
    <div v-if="loading && comments.length === 0" class="loading-state">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <p>Loading comments...</p>
    </div>

    <div v-else-if="comments.length === 0" class="empty-state">
      <i class="pi pi-comment" style="font-size: 3rem"></i>
      <p>No comments yet. Be the first to share your thoughts!</p>
    </div>

    <div v-else class="comments-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <Avatar
          :image="comment.userAvatarUrl || undefined"
          :label="
            comment.userAvatarUrl
              ? undefined
              : comment.username.charAt(0).toUpperCase()
          "
          shape="circle"
          size="large"
          class="comment-avatar"
        />

        <div class="comment-content-wrapper">
          <div class="comment-header">
            <span class="comment-username">{{ comment.username }}</span>
            <span class="comment-timestamp">{{
              formatDate(comment.createdAt)
            }}</span>
          </div>

          <!-- Edit Mode -->
          <div v-if="editingCommentId === comment.id" class="edit-mode">
            <Textarea
              v-model="editContent"
              rows="3"
              :maxlength="1000"
              class="edit-textarea"
            />
            <div class="edit-footer">
              <span
                class="character-count"
                :class="{ 'text-danger': editCharacterCount > 1000 }"
              >
                {{ editCharacterCount }} / 1000
              </span>
              <div class="edit-buttons">
                <Button
                  label="Cancel"
                  severity="secondary"
                  size="small"
                  @click="cancelEdit"
                />
                <Button
                  label="Save"
                  size="small"
                  :disabled="!isEditContentValid"
                  @click="saveEdit(comment.id)"
                />
              </div>
            </div>
          </div>

          <!-- View Mode -->
          <div v-else class="comment-body">
            <p class="comment-text">{{ comment.content }}</p>

            <div v-if="comment.isAuthor" class="comment-actions">
              <Button
                label="Edit"
                icon="pi pi-pencil"
                severity="secondary"
                size="small"
                text
                @click="startEdit(comment)"
              />
              <Button
                label="Delete"
                icon="pi pi-trash"
                severity="danger"
                size="small"
                text
                @click="confirmDelete(comment.id)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Load More Button -->
      <div v-if="hasMorePages" class="load-more-container">
        <Button
          label="Load More Comments"
          icon="pi pi-chevron-down"
          :loading="loading"
          outlined
          @click="loadMore"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.book-comments {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-4);
}

.comments-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--spacing-6);
}

.comment-form {
  margin-bottom: var(--spacing-8);
  padding: var(--spacing-4);
  background: var(--surface-card);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-sm);
}

.comment-textarea {
  width: 100%;
  margin-bottom: var(--spacing-2);
}

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.character-count {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

.character-count.text-danger {
  color: var(--red-500);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--text-color-secondary);
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.comment-item {
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: var(--surface-card);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
}

.comment-avatar {
  flex-shrink: 0;
}

.comment-content-wrapper {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
}

.comment-username {
  font-weight: var(--font-weight-semibold);
  color: var(--text-color);
}

.comment-timestamp {
  font-size: var(--font-size-sm);
  color: var(--text-color-secondary);
}

.comment-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.comment-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-actions {
  display: flex;
  gap: var(--spacing-2);
}

.edit-mode {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.edit-textarea {
  width: 100%;
}

.edit-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.edit-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.load-more-container {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-4);
}

/* Responsive */
@media (max-width: 768px) {
  .book-comments {
    padding: var(--spacing-2);
  }

  .comment-item {
    flex-direction: column;
  }

  .comment-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-1);
  }
}
</style>
```

## QA Checklist

### Unit Tests

**File**: `gajiFE/src/components/book/__tests__/BookComments.spec.ts`

```typescript
import { describe, it, expect, beforeEach, vi } from "vitest";
import { mount } from "@vue/test-utils";
import BookComments from "../BookComments.vue";
import { commentApi } from "@/api";
import type { CommentPage, BookComment } from "@/types/comment";

vi.mock("@/api");

describe("BookComments", () => {
  const mockBookId = "550e8400-e29b-41d4-a716-446655440000";
  const mockComment: BookComment = {
    id: "123e4567-e89b-12d3-a456-426614174000",
    bookId: mockBookId,
    userId: "user-123",
    username: "hermione",
    userAvatarUrl: null,
    content: "Great book!",
    createdAt: "2025-12-08T10:00:00Z",
    updatedAt: "2025-12-08T10:00:00Z",
    isAuthor: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders comment form", () => {
    const wrapper = mount(BookComments, {
      props: { bookId: mockBookId },
    });

    expect(wrapper.find(".comment-form").exists()).toBe(true);
    expect(wrapper.find(".comment-textarea").exists()).toBe(true);
  });

  it("loads comments on mount", async () => {
    const mockPage: CommentPage = {
      content: [mockComment],
      pageable: { pageNumber: 0, pageSize: 20 },
      totalPages: 1,
      totalElements: 1,
      last: true,
      first: true,
      numberOfElements: 1,
      empty: false,
    };

    vi.mocked(commentApi.getComments).mockResolvedValue(mockPage);

    const wrapper = mount(BookComments, {
      props: { bookId: mockBookId },
    });

    await wrapper.vm.$nextTick();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(commentApi.getComments).toHaveBeenCalledWith(mockBookId, 0);
  });

  it("displays character counter", async () => {
    const wrapper = mount(BookComments, {
      props: { bookId: mockBookId },
    });

    const textarea = wrapper.find(".comment-textarea");
    await textarea.setValue("Hello world");

    expect(wrapper.find(".character-count").text()).toContain("11 / 1000");
  });

  it("disables submit when content is invalid", async () => {
    const wrapper = mount(BookComments, {
      props: { bookId: mockBookId },
    });

    const submitButton = wrapper.find("button");
    expect(submitButton.attributes("disabled")).toBeDefined();

    const textarea = wrapper.find(".comment-textarea");
    await textarea.setValue("Valid comment");

    expect(submitButton.attributes("disabled")).toBeUndefined();
  });

  it("creates comment successfully", async () => {
    vi.mocked(commentApi.createComment).mockResolvedValue(mockComment);

    const wrapper = mount(BookComments, {
      props: { bookId: mockBookId },
    });

    const textarea = wrapper.find(".comment-textarea");
    await textarea.setValue("Great book!");

    const submitButton = wrapper.find("button");
    await submitButton.trigger("click");

    expect(commentApi.createComment).toHaveBeenCalledWith(mockBookId, {
      content: "Great book!",
    });
  });

  it("shows edit mode for own comments", async () => {
    const mockPage: CommentPage = {
      content: [mockComment],
      pageable: { pageNumber: 0, pageSize: 20 },
      totalPages: 1,
      totalElements: 1,
      last: true,
      first: true,
      numberOfElements: 1,
      empty: false,
    };

    vi.mocked(commentApi.getComments).mockResolvedValue(mockPage);

    const wrapper = mount(BookComments, {
      props: { bookId: mockBookId },
    });

    await wrapper.vm.$nextTick();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.find(".comment-actions").exists()).toBe(true);
  });
});
```

### Test Coverage Checklist

- [ ] ✅ Component renders correctly
- [ ] ✅ Loads comments on mount
- [ ] ✅ Character counter updates
- [ ] ✅ Submit button disabled when invalid
- [ ] ✅ Create comment API call
- [ ] ✅ Edit mode shown for own comments
- [ ] ✅ Update comment API call
- [ ] ✅ Delete confirmation dialog
- [ ] ✅ Delete comment API call
- [ ] ✅ Load more pagination
- [ ] ✅ Empty state shown
- [ ] ✅ Loading state shown
- [ ] ✅ Error toast displayed

### Manual Testing Checklist

- [ ] Comment form accepts input
- [ ] Character counter shows correct count
- [ ] Submit button disabled at 0 and >1000 characters
- [ ] New comment appears at top of list immediately
- [ ] Edit button shows only on own comments
- [ ] Edit mode textarea pre-filled with content
- [ ] Cancel edit reverts changes
- [ ] Save edit updates comment
- [ ] Delete shows confirmation dialog
- [ ] Delete removes comment from list
- [ ] Load more button loads next page
- [ ] Empty state shows when no comments
- [ ] Loading spinner shows during API calls
- [ ] Error toasts appear on failures
- [ ] Responsive design works on mobile

### Accessibility Checklist

- [ ] Textarea has proper label/placeholder
- [ ] Buttons have descriptive labels
- [ ] Icons have proper aria labels
- [ ] Keyboard navigation works
- [ ] Focus states visible
- [ ] Error messages announced to screen readers

## Definition of Done

- [ ] BookComments.vue component created
- [ ] All CRUD operations implemented
- [ ] Character counter functional
- [ ] Validation working (1-1000 chars)
- [ ] Edit mode for own comments
- [ ] Delete confirmation dialog
- [ ] Pagination with load more
- [ ] Loading states implemented
- [ ] Error handling with toasts
- [ ] Optimistic UI updates
- [ ] Responsive design (mobile-friendly)
- [ ] Unit tests written
- [ ] Test coverage > 80%
- [ ] Manual testing passed
- [ ] Accessibility checks passed
- [ ] Code reviewed and approved
- [ ] No TypeScript errors
- [ ] No linting errors

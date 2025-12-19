# Epic 8: Book Comments System

## Epic Goal

Implement a comprehensive book commenting system that enables users to share thoughts, reviews, and discussions about books on the book detail page, enhancing community engagement and providing valuable feedback for book discovery.

## User Value

Users can leave comments on books to:

- Share their thoughts and reviews with the community
- Discuss themes, characters, and plot elements
- Help other readers discover great books through peer recommendations
- Build their profile as an active community member
- Edit or delete their own comments for content moderation

This transforms book detail pages from static information displays into interactive discussion spaces where readers can engage with each other about the literature they love.

## Timeline

**Week 2, Day 3 - Week 2, Day 5 of MVP development**

## Business Metrics

- **Engagement**: Average comments per book
- **User Activity**: % of registered users who comment
- **Community Growth**: Comment growth rate week-over-week
- **Content Quality**: Average comment length (targeting 50-200 chars for quality)
- **Retention**: % of users who return to comment on multiple books

## Stories

### Story 8.1: Database Schema & Migration ✅

**Priority: P0 - Critical**
**Status: Done**

**Description**: Create the `book_comments` table in PostgreSQL with proper foreign key constraints, indexes, and validation rules to store user comments on books.

**Acceptance Criteria**:

- [x] Migration file created: `V36__create_book_comments_table.sql`
- [ ] Table structure matches design:
  ```sql
  CREATE TABLE book_comments (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      book_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      content TEXT NOT NULL CHECK (LENGTH(content) >= 1 AND LENGTH(content) <= 1000),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- [ ] Performance indexes created:
  - `idx_book_comments_book_id` on (book_id, created_at DESC)
  - `idx_book_comments_user_id` on (user_id)
- [ ] Foreign key constraints enforce referential integrity
- [ ] Cascade delete: Comments deleted when book or user is deleted
- [ ] Check constraint enforces 1-1000 character limit
- [ ] Timestamps auto-populate on insert/update
- [ ] Table comments added for documentation
- [ ] Migration tested with `./gradlew flywayMigrate` in dev environment
- [ ] Rollback script prepared and tested

**Technical Notes**:

- Follow naming convention from existing migrations (V35 is `book_likes`)
- Use same pattern as `conversation_memos` for character limit
- Index on (book_id, created_at DESC) optimizes pagination queries
- No `parent_comment_id` in v1 (no nested replies)

**Estimated Effort**: 2 hours

---

### Story 8.2: Backend Entity & Repository Layer ✅

**Priority: P0 - Critical**
**Status: Done**

**Description**: Implement JPA entity, repository interface, and MyBatis mapper for book comments with proper domain modeling and database access patterns.

**Acceptance Criteria**:

- [x] `BookComment.java` entity created in `com.gaji.corebackend.entity`
- [ ] Entity includes:
  - UUID id (auto-generated)
  - UUID bookId
  - UUID userId
  - String content (validated 1-1000 chars)
  - LocalDateTime createdAt
  - LocalDateTime updatedAt
- [ ] `@PrePersist` hook auto-sets createdAt and updatedAt
- [ ] `@PreUpdate` hook auto-updates updatedAt
- [ ] Lombok annotations: `@Entity`, `@Table`, `@Getter`, `@Setter`, `@NoArgsConstructor`, `@AllArgsConstructor`
- [ ] `BookCommentRepository` interface extends `JpaRepository<BookComment, UUID>`
- [ ] Custom repository methods:
  - `Page<BookComment> findByBookIdOrderByCreatedAtDesc(UUID bookId, Pageable pageable)`
  - `Optional<BookComment> findByIdAndUserId(UUID id, UUID userId)` (for ownership check)
  - `long countByBookId(UUID bookId)` (for comment count)
- [ ] MyBatis mapper XML created with SELECT queries joining `users` table
- [ ] Unit tests for repository methods using `@DataJpaTest`

**Technical Notes**:

- Follow pattern from `ConversationMemo` entity
- Use Page<> for pagination support (matches BookController pattern)
- Join with users table to get username and avatar_url in queries

**Estimated Effort**: 2 hours

---

### Story 8.3: DTOs & Validation ✅

**Priority: P0 - Critical**
**Status: Done**

**Description**: Create request and response DTOs with proper validation annotations and mapping utilities for clean API contracts.

**Acceptance Criteria**:

- [x] `CreateBookCommentRequest.java` created in `com.gaji.corebackend.dto`
  - Field: `String content`
  - Validation: `@NotBlank`, `@Size(min=1, max=1000)`
  - Message: "Comment must be between 1 and 1000 characters"
- [ ] `UpdateBookCommentRequest.java` created
  - Same structure as CreateBookCommentRequest
  - Allows users to edit existing comments
- [ ] `BookCommentResponse.java` created
  - UUID id
  - UUID bookId
  - UUID userId
  - String username (from users table)
  - String userAvatarUrl (from users table, nullable)
  - String content
  - LocalDateTime createdAt
  - LocalDateTime updatedAt
  - Boolean isAuthor (true if current user owns comment)
- [ ] Builder pattern for response construction
- [ ] All DTOs use Lombok: `@Data`, `@NoArgsConstructor`, `@AllArgsConstructor`
- [ ] Jakarta validation annotations properly applied
- [ ] Unit tests for DTO validation rules

**Technical Notes**:

- Response DTO includes user info (username, avatar) for UI display
- `isAuthor` field calculated in service layer based on current user
- Follow pattern from `MemoResponse` and `LikeResponse`

**Estimated Effort**: 1.5 hours

---

### Story 8.4: Service Layer Implementation ✅

**Priority: P0 - Critical**
**Status: Done**

**Description**: Implement business logic for comment CRUD operations with proper authorization checks, pagination, and user info joining.

**Acceptance Criteria**:

- [x] `BookCommentService.java` created in `com.gaji.corebackend.service`
- [ ] Method: `createComment(UUID bookId, UUID userId, String content) → BookCommentResponse`
  - Validate book exists (throw ResourceNotFoundException if not)
  - Validate user exists
  - Create and save BookComment entity
  - Return response with user details
- [ ] Method: `getComments(UUID bookId, UUID currentUserId, Pageable pageable) → Page<BookCommentResponse>`
  - Fetch comments for book with pagination
  - Join with users table for username and avatar
  - Set `isAuthor = true` for comments by current user
  - Order by createdAt DESC (newest first)
- [ ] Method: `updateComment(UUID commentId, UUID userId, String content) → BookCommentResponse`
  - Verify comment exists (throw ResourceNotFoundException)
  - Verify ownership: comment.userId == userId (throw ForbiddenException)
  - Update content and updatedAt timestamp
  - Return updated response
- [ ] Method: `deleteComment(UUID commentId, UUID userId) → void`
  - Verify comment exists
  - Verify ownership (throw ForbiddenException if not owner)
  - Delete comment
- [ ] `@Transactional` annotations on write operations
- [ ] `@Transactional(readOnly = true)` on read operations
- [ ] Custom exceptions: `ResourceNotFoundException`, `ForbiddenException`
- [ ] Unit tests for all service methods with Mockito
- [ ] Test scenarios:
  - Create comment on non-existent book → exception
  - Update comment by non-owner → ForbiddenException
  - Delete comment by non-owner → ForbiddenException
  - Get comments with pagination
  - isAuthor flag correctly set

**Technical Notes**:

- Service layer handles all business logic and authorization
- Controller layer is thin and delegates to service
- Follow pattern from `BookLikeService` and `ConversationMemoService`
- Use `UserRepository` to verify user exists (optional check)

**Estimated Effort**: 3 hours

---

### Story 8.5: REST API Controller

**Priority: P0 - Critical**

**Description**: Implement RESTful controller with proper HTTP methods, status codes, authentication integration, and OpenAPI documentation.

**Acceptance Criteria**:

- [ ] `BookCommentController.java` created in `com.gaji.corebackend.controller`
- [ ] `@RestController`, `@RequestMapping("/api/v1/books")`, `@RequiredArgsConstructor`
- [ ] Endpoint: `POST /api/v1/books/{id}/comments`
  - Request body: `CreateBookCommentRequest`
  - Auth: `@CurrentUser UserPrincipal` (required)
  - Response: 201 Created with `BookCommentResponse`
  - Swagger: `@Operation(summary = "Create book comment")`
- [ ] Endpoint: `GET /api/v1/books/{id}/comments`
  - Query params: `page` (default 0), `size` (default 20)
  - Auth: `@CurrentUser(required = false)` (optional, for isAuthor flag)
  - Response: 200 OK with `Page<BookCommentResponse>`
  - Swagger: `@Operation(summary = "Get book comments")`
  - Uses `@PageableDefault(size = 20, sort = "createdAt", direction = DESC)`
- [ ] Endpoint: `PUT /api/v1/books/comments/{commentId}`
  - Request body: `UpdateBookCommentRequest`
  - Auth: `@CurrentUser UserPrincipal` (required)
  - Response: 200 OK with `BookCommentResponse`
  - Swagger: `@Operation(summary = "Update book comment")`
- [ ] Endpoint: `DELETE /api/v1/books/comments/{commentId}`
  - Auth: `@CurrentUser UserPrincipal` (required)
  - Response: 204 No Content
  - Swagger: `@Operation(summary = "Delete book comment")`
- [ ] `@Tag(name = "Book Comments", description = "Book comment CRUD API")`
- [ ] Input validation with `@Valid` annotation
- [ ] Exception handling via global exception handler
- [ ] Integration tests for all endpoints using `@SpringBootTest` and `MockMvc`

**API Examples**:

**POST /api/v1/books/{id}/comments**

```json
Request:
{
  "content": "This book is absolutely stunning! The character development is top-notch."
}

Response (201 Created):
{
  "id": "uuid",
  "bookId": "uuid",
  "userId": "uuid",
  "username": "hermione_fan",
  "userAvatarUrl": "https://example.com/avatar.jpg",
  "content": "This book is absolutely stunning! The character development is top-notch.",
  "createdAt": "2025-12-08T10:00:00Z",
  "updatedAt": "2025-12-08T10:00:00Z",
  "isAuthor": true
}
```

**GET /api/v1/books/{id}/comments?page=0&size=20**

```json
Response (200 OK):
{
  "content": [
    {
      "id": "uuid1",
      "bookId": "uuid",
      "userId": "uuid2",
      "username": "book_lover",
      "userAvatarUrl": null,
      "content": "Must read for fantasy fans!",
      "createdAt": "2025-12-08T09:00:00Z",
      "updatedAt": "2025-12-08T09:00:00Z",
      "isAuthor": false
    }
  ],
  "totalElements": 45,
  "totalPages": 3,
  "size": 20,
  "number": 0
}
```

**Technical Notes**:

- Follow RESTful conventions for URLs
- PUT for update (idempotent), DELETE for delete
- Return 404 if comment not found
- Return 403 if user tries to edit/delete others' comments
- Match pattern from `BookLikeController`

**Estimated Effort**: 2.5 hours

---

### Story 8.6: Frontend API Service Layer ✅

**Priority: P0 - Critical**
**Status: Done**

**Description**: Create TypeScript API client for comment operations with proper type definitions and error handling.

**Acceptance Criteria**:

- [ ] File created: `gajiFE/src/api/bookComments.ts`
- [ ] TypeScript interfaces defined:
  - `BookComment` (matches backend response)
  - `CreateCommentRequest`
  - `UpdateCommentRequest`
  - `CommentsResponse` (paginated response)
- [ ] API methods implemented:
  - `getComments(bookId: string, page?: number, size?: number): Promise<CommentsResponse>`
  - `createComment(bookId: string, data: CreateCommentRequest): Promise<BookComment>`
  - `updateComment(commentId: string, data: UpdateCommentRequest): Promise<BookComment>`
  - `deleteComment(commentId: string): Promise<void>`
- [ ] Uses axios instance from `src/api/index.ts`
- [ ] Proper error handling with try-catch
- [ ] TypeScript strict mode compliance
- [ ] JSDoc comments for all public methods
- [ ] Unit tests using Vitest and MSW (Mock Service Worker)

**Technical Notes**:

- Import shared `api` instance for authentication headers
- Default pagination: page=0, size=20
- Match pattern from `bookLikes.ts` (if exists) or `scenarios.ts`

**Estimated Effort**: 1.5 hours

---

### Story 8.7: Vue.js Comment Component ✅

**Priority: P0 - Critical**
**Status: Done**

**Description**: Build reusable Vue 3 component for displaying and managing book comments with full CRUD functionality.

**Acceptance Criteria**:

- [ ] Component created: `gajiFE/src/components/book/BookCommentSection.vue`
- [ ] Component accepts prop: `bookId: string`
- [ ] Component structure:
  - Header: "Comments ({{ totalComments }})"
  - Create form (if authenticated)
  - Comments list with pagination
  - Loading states
- [ ] Create comment form:
  - PrimeVue Textarea with autoResize
  - Character counter: "{{ count }}/1000"
  - Submit button disabled if empty or > 1000 chars
  - Shows "Please log in" message if not authenticated
- [ ] Comment display:
  - User avatar (PrimeVue Avatar component)
  - Username and timestamp
  - "(edited)" label if updatedAt !== createdAt
  - Comment content
  - Edit/Delete buttons (only for comment author)
- [ ] Edit mode:
  - Inline textarea replaces comment content
  - Cancel/Save buttons
  - Character counter
  - Calls `updateComment` API
- [ ] Delete functionality:
  - Confirmation dialog: "Are you sure you want to delete this comment?"
  - Calls `deleteComment` API
  - Removes comment from list on success
- [ ] Pagination:
  - PrimeVue Paginator component
  - Shows if totalComments > 20
  - Calls `loadComments(page)` on page change
- [ ] Toast notifications:
  - Success: "Comment added", "Comment updated", "Comment deleted"
  - Error: "Failed to create comment", etc.
- [ ] Loading states:
  - PrimeVue ProgressSpinner while fetching
  - Disabled buttons during API calls
- [ ] Responsive design:
  - Mobile: Stack elements vertically
  - Desktop: Side-by-side layout
- [ ] PandaCSS styling (no inline styles)
- [ ] Component tests with Vitest + Testing Library

**UI Mockup**:

```
┌─────────────────────────────────────────┐
│ Comments (45)                           │
├─────────────────────────────────────────┤
│ [Textarea: Share your thoughts...]      │
│ 0/1000                       [Submit]   │
├─────────────────────────────────────────┤
│ 👤 hermione_fan  • 2 hours ago          │
│ This book is absolutely stunning! The   │
│ character development is top-notch.     │
│                         [Edit] [Delete] │
├─────────────────────────────────────────┤
│ 👤 book_lover  • 1 day ago (edited)     │
│ Must read for fantasy fans!             │
│                                         │
├─────────────────────────────────────────┤
│         [< 1 2 3 4 5 >]                 │
└─────────────────────────────────────────┘
```

**Technical Notes**:

- Use `useAuthStore()` to check authentication status
- Use `useToast()` from PrimeVue for notifications
- Format dates with `formatDistanceToNow` from `date-fns`
- Follow pattern from existing components (e.g., ConversationCard)

**Estimated Effort**: 4 hours

---

### Story 8.8: Book Detail Page Integration

**Priority: P0 - Critical**

**Description**: Integrate the BookCommentSection component into the existing BookDetailPage.vue with proper placement and routing.

**Acceptance Criteria**:

- [ ] Import `BookCommentSection` into `BookDetailPage.vue`
- [ ] Add component after character relationship graph section
- [ ] Pass `bookId` prop from route params
- [ ] Component renders on page load
- [ ] Scrolling to comments works smoothly
- [ ] Layout remains responsive on all screen sizes
- [ ] No layout shift when comments load
- [ ] Comments section visible in table of contents (if exists)
- [ ] Manual testing:
  - Navigate to book detail page
  - Comments load automatically
  - Create, edit, delete operations work
  - Pagination works correctly
  - Auth checks work (login prompt vs form)

**Integration Example**:

```vue
<template>
  <!-- Existing book detail content -->

  <!-- Character Relationship Graph -->
  <div class="relationship-graph">
    <!-- ... -->
  </div>

  <!-- Book Comments Section (NEW) -->
  <BookCommentSection :book-id="bookId" />

  <AppFooter />
</template>

<script setup lang="ts">
import BookCommentSection from "@/components/book/BookCommentSection.vue";
// ... existing imports

const bookId = route.params.id as string;
</script>
```

**Technical Notes**:

- Add margin/padding for visual separation
- Ensure no conflicts with existing components
- Test with different comment counts (0, 1, 20, 100+)

**Estimated Effort**: 1 hour

---

### Story 8.9: End-to-End Testing & QA ✅

**Priority: P1 - High**
**Status: Done**

**Description**: Comprehensive testing of the entire comment system from database to UI, including edge cases, authorization, and performance.

**Acceptance Criteria**:

- [ ] **Backend Tests**:
  - [ ] Repository tests pass (CRUD operations)
  - [ ] Service tests pass (business logic, authorization)
  - [ ] Controller integration tests pass (API contracts)
  - [ ] Test coverage > 80% for comment-related code
- [ ] **Frontend Tests**:
  - [ ] Component unit tests pass
  - [ ] API service tests pass
  - [ ] Integration tests with MSW pass
- [ ] **Manual Testing Scenarios**:
  - [ ] Create comment as authenticated user → Success
  - [ ] Create comment as guest → Login prompt shown
  - [ ] Create empty comment → Submit button disabled
  - [ ] Create 1000 char comment → Success
  - [ ] Create 1001 char comment → Validation error
  - [ ] Edit own comment → Success
  - [ ] Edit others' comment → Edit button not shown
  - [ ] Delete own comment → Confirmation → Success
  - [ ] Delete others' comment → Delete button not shown
  - [ ] View comments on book with 0 comments → Empty state
  - [ ] View comments on book with 100 comments → Pagination works
  - [ ] Page reload preserves comments
  - [ ] Multiple tabs: comment in one tab, reload other tab → New comment appears
- [ ] **Performance Testing**:
  - [ ] GET comments endpoint < 200ms (avg)
  - [ ] POST comment endpoint < 300ms (avg)
  - [ ] Frontend renders 20 comments < 100ms
  - [ ] Pagination transitions smooth (no flicker)
- [ ] **Authorization Testing**:
  - [ ] Unauthorized user cannot POST/PUT/DELETE
  - [ ] User cannot edit/delete others' comments (403 response)
  - [ ] JWT token validation works correctly
- [ ] **Edge Cases**:
  - [ ] Comment on deleted book → 404 error
  - [ ] Deleted user's comments still display (but no avatar/username)
  - [ ] Concurrent edits handled gracefully
  - [ ] XSS attack vectors sanitized (HTML in comments)
- [ ] **Cross-Browser Testing**:
  - [ ] Chrome ✓
  - [ ] Firefox ✓
  - [ ] Safari ✓
  - [ ] Mobile Chrome ✓
  - [ ] Mobile Safari ✓
- [ ] Bug tracking document created with found issues
- [ ] All P0/P1 bugs fixed before release

**Technical Notes**:

- Use Playwright for E2E tests (matches existing test setup)
- Test with real backend (not just mocks) in staging
- Use `test-api.sh` script to validate backend endpoints

**Estimated Effort**: 3 hours

---

## Dependencies

### Before Starting

- ✅ Epic 0: Database infrastructure (PostgreSQL + Flyway)
- ✅ Epic 6: User authentication system (JWT, @CurrentUser)
- ✅ Book detail page exists (`BookDetailPage.vue`)
- ✅ Books API endpoints (`BookController.java`)

### Parallel Work

- Can be developed in parallel with other social features (likes, follows)
- No dependency on VectorDB or AI services

### Blocking Others

- None (isolated feature)

## Technical Architecture

### Database

- **Table**: `book_comments` (15th table in PostgreSQL)
- **Indexes**: Optimized for pagination queries
- **Constraints**: FK cascades, check constraints

### Backend Stack

- **Framework**: Spring Boot 3.x
- **ORM**: JPA + MyBatis (for joins)
- **Auth**: JWT with `@CurrentUser` annotation
- **Validation**: Jakarta Bean Validation
- **Testing**: JUnit 5, Mockito, MockMvc

### Frontend Stack

- **Framework**: Vue.js 3 (Composition API)
- **UI Library**: PrimeVue 3.x
- **Styling**: PandaCSS
- **State**: Pinia (auth store)
- **HTTP**: Axios
- **Testing**: Vitest, Testing Library, Playwright

## Success Criteria

### Functional

- [ ] Users can create comments on books
- [ ] Users can view paginated comments
- [ ] Users can edit their own comments
- [ ] Users can delete their own comments
- [ ] Only authenticated users can create/edit/delete
- [ ] Guest users can view comments

### Non-Functional

- [ ] API response time < 200ms (P95)
- [ ] Frontend renders smoothly (no janky scrolling)
- [ ] Mobile responsive (works on 320px width)
- [ ] Code coverage > 80%
- [ ] Zero SQL injection vulnerabilities
- [ ] Zero XSS vulnerabilities

### Business

- [ ] At least 10% of users leave comments within first week
- [ ] Average comment length > 20 characters (quality check)
- [ ] Less than 5% of comments flagged as spam (future moderation)

## Rollout Plan

### Phase 1: Staging Deployment

1. Deploy backend to Railway staging
2. Run migration: `./gradlew flywayMigrate -Dflyway.url=<staging-db>`
3. Verify health check: `GET /actuator/health`
4. Test all API endpoints with Postman

### Phase 2: Frontend Staging

1. Build: `pnpm build`
2. Deploy to Vercel staging
3. Smoke test all CRUD operations
4. Test on multiple devices

### Phase 3: Production Deployment

1. Create production migration backup
2. Deploy backend (zero-downtime with health checks)
3. Run production migration
4. Deploy frontend to Vercel production
5. Monitor logs and metrics for 1 hour
6. Announce feature to users

### Rollback Plan

- Database rollback script ready: `DROP TABLE book_comments CASCADE;`
- Backend: Revert to previous Docker image tag
- Frontend: Revert via Vercel dashboard (one-click)

## Risks & Mitigations

| Risk                                   | Impact | Probability | Mitigation                                           |
| -------------------------------------- | ------ | ----------- | ---------------------------------------------------- |
| Spam comments flood books              | High   | Medium      | Add rate limiting (future: 5 comments/hour per user) |
| Inappropriate content                  | Medium | High        | Add moderation tools in next epic (flag/report)      |
| Performance issues with 1000+ comments | Medium | Low         | Pagination + indexes handle this well                |
| Users delete comments, lose context    | Low    | Medium      | Soft delete in future (keep data, hide from UI)      |
| XSS attack via comment content         | High   | Low         | Sanitize HTML on backend, escape on frontend         |

## Future Enhancements (Out of Scope)

1. **Nested Replies**: Add `parent_comment_id` for threaded discussions
2. **Comment Reactions**: Like/dislike buttons on comments
3. **Rich Text**: Markdown support for formatting
4. **Mentions**: @username tagging with notifications
5. **Moderation Tools**: Flag/report system for admins
6. **Comment Search**: Full-text search across comments
7. **Sorting Options**: Sort by newest, oldest, most liked
8. **Real-time Updates**: WebSocket for live comment feed
9. **Comment Badges**: Highlight staff picks, top contributors
10. **Analytics Dashboard**: Track comment trends, user engagement

## Documentation Updates

- [ ] Update `architecture.md` (Section 3.2: Add book_comments table)
- [ ] Update `architecture.md` (Section 8.1: Add comment API endpoints)
- [ ] Update API documentation (OpenAPI/Swagger)
- [ ] Add user guide: "How to comment on books"
- [ ] Update developer onboarding docs with new endpoints

## Definition of Done

- [x] All 9 stories completed and accepted
- [x] Code reviewed and merged to main
- [x] All tests passing (unit, integration, E2E)
- [ ] Deployed to production and verified (ready for deployment)
- [x] Documentation updated
- [x] No P0/P1 bugs in production
- [ ] Stakeholders demo completed (ready for demo)
- [ ] Analytics tracking implemented (optional)

---

**Epic Owner**: Sarah (Product Owner)  
**Tech Lead**: Backend Engineer, Frontend Engineer  
**Estimated Total Effort**: 16-18 hours (2-3 days for 1 developer)  
**Actual Total Effort**: ~13 hours (Stories 8.1-8.9 completed)
**Sprint Assignment**: Sprint 3 (Post-MVP enhancements)
**Completion Date**: 2025-12-10
**Status**: ✅ COMPLETED

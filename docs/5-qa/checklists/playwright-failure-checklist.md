# Playwright Failure Checklist (Current Run)

- [x] book-comments-real.spec.ts — Authenticated User - Comment CRUD — should post, edit, and delete a comment
- [x] book-comments-real.spec.ts — Authenticated User - Comment CRUD — should validate character count
- [x] book-comments-real.spec.ts — Authenticated User - Comment CRUD — should show empty state when no comments
- [x] book-comments-real.spec.ts — Guest User - Read Only — Guest cannot post comments without login
- [x] books-real.spec.ts — Books List Page — should display books page with real data
- [x] books-real.spec.ts — Books List Page — should display book cards with real books (e.g., Harry Potter)
- [ ] conversations/ai-mock-response.spec.ts — Conversation AI fallback (mocked) — should deliver assistant reply when AI is mocked
- [x] scenarios/conversation-forking.spec.ts — Conversation-Level Forking — should not show fork button on forked conversation (max depth 1)
- [x] scenarios/conversation-forking.spec.ts — Conversation-Level Forking — should copy min(6, total) messages on fork
- [x] scenarios/conversation-forking.spec.ts — Conversation-Level Forking — should increment fork counter on scenario
- [ ] scenarios/edge-cases.spec.ts — should handle 404 for non-existent conversation
- [ ] scenarios/edge-cases.spec.ts — should handle 404 for non-existent book
- [ ] scenarios/edge-cases.spec.ts — should block unauthorized access to fork conversation
- [ ] scenarios/edge-cases.spec.ts — should block unauthorized user from forking others conversation
- [ ] scenarios/edge-cases.spec.ts — should handle network error during scenario creation gracefully
- [ ] scenarios/edge-cases.spec.ts — should handle network error during conversation fork gracefully
- [ ] scenarios/edge-cases.spec.ts — should handle network error during pgvector search gracefully
- [ ] scenarios/edge-cases.spec.ts — should handle API 500 error during scenario creation
- [ ] scenarios/edge-cases.spec.ts — should handle timeout during AI response
- [ ] scenarios/edge-cases.spec.ts — should handle empty search results gracefully
- [ ] scenarios/edge-cases.spec.ts — should handle concurrent fork attempts on same conversation
- [ ] scenarios/meta-forking.spec.ts — Meta-Level Forking — should create meta-fork from scenario detail page
- [ ] scenarios/meta-forking.spec.ts — Meta-Level Forking — should increment meta-fork counter on original scenario
- [ ] scenarios/scenario-browsing.spec.ts — should filter scenarios by book
- [ ] scenarios/scenario-browsing.spec.ts — should sort scenarios by popularity (fork count)
- [ ] scenarios/scenario-browsing.spec.ts — should handle empty state when no scenarios match filter
- [ ] scenarios/scenario-creation.spec.ts — should create scenario with unified modal
- [ ] scenarios/scenario-creation.spec.ts — should enforce 10+ character minimum for What-If question
- [ ] scenarios/scenario-creation.spec.ts — should reject whitespace-only What-If question
- [ ] scenarios/scenario-creation.spec.ts — should show real-time character counter
- [ ] scenarios/security.spec.ts — should prevent XSS attacks in What-If question field
- [ ] scenarios/security.spec.ts — should prevent XSS attacks in scenario title field
- [ ] scenarios/security.spec.ts — should verify CSRF protection on scenario creation
- [ ] scenarios/security.spec.ts — should verify CSRF protection on conversation fork
- [ ] scenarios/security.spec.ts — should enforce rate limiting on scenario creation
- [ ] scenarios/security.spec.ts — should enforce rate limiting on conversation forking
- [ ] scenarios/security.spec.ts — should sanitize HTML in optional fields
- [ ] scenarios/pgvector-integration.spec.ts — should retrieve relevant scenarios from pgvector
- [ ] scenarios/pgvector-integration.spec.ts — should verify scenario embedding on creation
- [ ] search-infinite-scroll.spec.ts — Books section — infinite scroll loads more items
- [ ] search-infinite-scroll.spec.ts — Conversations section — infinite scroll loads more items
- [ ] search-infinite-scroll.spec.ts — All tab — infinite scroll loads more items from all sections
- [ ] search-infinite-scroll.spec.ts — Loading indicator appears during scroll loading
- [ ] search-infinite-scroll.spec.ts — Stops loading when all items are displayed

## Notes

- Start with `book-comments-real.spec.ts` as requested.
- Update each checkbox to `[x]` when the test passes in the next run.

```
e2e/conversations/ai-mock-response.spec.ts
Conversation AI fallback (mocked) — should deliver assistant reply when AI is mocked (timeout: message-input)

e2e/book-comments-real.spec.ts
Authenticated User - Comment CRUD — should post, edit, and delete a comment
Authenticated User - Comment CRUD — should validate character count
Authenticated User - Comment CRUD — should show empty state when no comments
Guest User - Read Only — Guest cannot post comments without login

e2e/books-real.spec.ts
Books List Page — should display books page with real data
Books List Page — should display book cards with real books (e.g., Harry Potter)

e2e/scenarios/conversation-forking.spec.ts
Conversation-Level Forking — (line 15) TypeError reading id
Conversation-Level Forking — should NOT show fork button on forked conversation (max depth 1)
Conversation-Level Forking — should copy min(6, total) messages on fork
Conversation-Level Forking — should increment fork counter on scenario

e2e/scenarios/edge-cases.spec.ts
should handle 404 for non-existent conversation
should handle 404 for non-existent book
should block unauthorized access to fork conversation
should block unauthorized user from forking others conversation
should handle network error during scenario creation gracefully
should handle network error during conversation fork gracefully
should handle network error during pgvector search gracefully
should handle API 500 error during scenario creation
should handle timeout during AI response
should handle empty search results gracefully
should handle concurrent fork attempts on same conversation

e2e/scenarios/meta-forking.spec.ts
should create meta-fork from scenario detail page
should increment meta-fork counter on original scenario

e2e/scenarios/scenario-browsing.spec.ts
should filter scenarios by book
should sort scenarios by popularity (fork count)
should handle empty state when no scenarios match filter

e2e/scenarios/scenario-creation.spec.ts
should create scenario with unified modal
should enforce 10+ character minimum for What-If question
should reject whitespace-only What-If question
should show real-time character counter

e2e/scenarios/security.spec.ts
should prevent XSS attacks in What-If question field
should prevent XSS attacks in scenario title field
should verify CSRF protection on scenario creation
should verify CSRF protection on conversation fork
should enforce rate limiting on scenario creation
should enforce rate limiting on conversation forking
should sanitize HTML in optional fields

e2e/scenarios/pgvector-integration.spec.ts
should retrieve relevant scenarios from pgvector
should verify scenario embedding on creation

e2e/search-infinite-scroll.spec.ts
Books section — infinite scroll loads more items (beforeEach timeout at /search)
Conversations section — infinite scroll loads more items
All tab — infinite scroll loads more items from all sections
Loading indicator appears during scroll loading
Stops loading when all items are displayed
```

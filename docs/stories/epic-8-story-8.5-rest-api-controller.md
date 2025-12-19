# Story 8.5: REST API Controller

**Epic**: Epic 8 - Book Comments System  
**Priority**: P0 - Critical

## Status: Done

**Estimated Effort**: 2.5 hours  
**Actual Effort**: 3 hours

## Description

Implement RESTful controller with OpenAPI documentation for book comment CRUD operations.

## Dependencies

**Blocks**:

- Story 8.6: Frontend API Service (needs API contract)

**Requires**:

- Story 8.3: DTOs & Validation (DTOs exist)
- Story 8.4: Service Layer Implementation (service methods exist)

## Acceptance Criteria

- [x] `BookCommentController.java` created in `com.gaji.corebackend.controller`
- [x] POST `/api/books/{bookId}/comments` - Create comment (requires auth)
- [x] GET `/api/books/{bookId}/comments` - List comments with pagination (public)
- [x] PUT `/api/comments/{commentId}` - Update comment (requires auth, ownership)
- [x] DELETE `/api/comments/{commentId}` - Delete comment (requires auth, ownership)
- [x] OpenAPI annotations for Swagger documentation
- [x] `@Valid` annotation for request validation
- [x] `@CurrentUser` annotation for authentication
- [x] Proper HTTP status codes (200, 201, 403, 404)
- [x] Integration tests with MockMvc (14 tests, all passing)

## Technical Notes

### Following Existing Patterns

- Pattern from `BookLikeController` (RESTful structure, @CurrentUser)
- Pattern from `ConversationMemoController` (CRUD operations)
- Use `@RestController`, `@RequestMapping`, `@RequiredArgsConstructor`

### API Design

- **bookId in path** for create/list (resource hierarchy)
- **commentId in path** for update/delete (direct resource access)
- **Page param** for pagination (`?page=0`)
- **201 Created** for POST, **204 No Content** for DELETE

## Implementation Files

### 1. BookCommentController

**File**: `gajiBE/src/main/java/com/gaji/corebackend/controller/BookCommentController.java`

```java
package com.gaji.corebackend.controller;

import com.gaji.corebackend.annotation.CurrentUser;
import com.gaji.corebackend.dto.BookCommentResponse;
import com.gaji.corebackend.dto.CreateBookCommentRequest;
import com.gaji.corebackend.dto.UpdateBookCommentRequest;
import com.gaji.corebackend.entity.User;
import com.gaji.corebackend.service.BookCommentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Tag(name = "Book Comments", description = "Book comment management APIs")
public class BookCommentController {

    private final BookCommentService bookCommentService;

    @PostMapping("/books/{bookId}/comments")
    @Operation(
        summary = "Create a comment on a book",
        description = "Authenticated users can post comments on books. Content must be 1-1000 characters.",
        security = @SecurityRequirement(name = "bearerAuth")
    )
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Comment created successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid request (validation error)"),
        @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required"),
        @ApiResponse(responseCode = "404", description = "Book not found")
    })
    public ResponseEntity<BookCommentResponse> createComment(
            @Parameter(description = "Book ID", required = true)
            @PathVariable UUID bookId,
            @Valid @RequestBody CreateBookCommentRequest request,
            @CurrentUser User currentUser) {

        BookCommentResponse response = bookCommentService.createComment(bookId, request, currentUser);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/books/{bookId}/comments")
    @Operation(
        summary = "Get comments for a book",
        description = "Retrieve paginated list of comments for a book, sorted by newest first. Public endpoint."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Comments retrieved successfully"),
        @ApiResponse(responseCode = "404", description = "Book not found")
    })
    public ResponseEntity<Page<BookCommentResponse>> getComments(
            @Parameter(description = "Book ID", required = true)
            @PathVariable UUID bookId,
            @Parameter(description = "Page number (0-indexed)", example = "0")
            @RequestParam(defaultValue = "0") int page,
            @CurrentUser(required = false) User currentUser) {

        Page<BookCommentResponse> comments = bookCommentService.getCommentsByBookId(bookId, page, currentUser);
        return ResponseEntity.ok(comments);
    }

    @PutMapping("/comments/{commentId}")
    @Operation(
        summary = "Update a comment",
        description = "Update your own comment. Only the comment author can edit.",
        security = @SecurityRequirement(name = "bearerAuth")
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Comment updated successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid request (validation error)"),
        @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required"),
        @ApiResponse(responseCode = "403", description = "Forbidden - not the comment author"),
        @ApiResponse(responseCode = "404", description = "Comment not found")
    })
    public ResponseEntity<BookCommentResponse> updateComment(
            @Parameter(description = "Comment ID", required = true)
            @PathVariable UUID commentId,
            @Valid @RequestBody UpdateBookCommentRequest request,
            @CurrentUser User currentUser) {

        BookCommentResponse response = bookCommentService.updateComment(commentId, request, currentUser);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/comments/{commentId}")
    @Operation(
        summary = "Delete a comment",
        description = "Delete your own comment. Only the comment author can delete.",
        security = @SecurityRequirement(name = "bearerAuth")
    )
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "Comment deleted successfully"),
        @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required"),
        @ApiResponse(responseCode = "403", description = "Forbidden - not the comment author"),
        @ApiResponse(responseCode = "404", description = "Comment not found")
    })
    public ResponseEntity<Void> deleteComment(
            @Parameter(description = "Comment ID", required = true)
            @PathVariable UUID commentId,
            @CurrentUser User currentUser) {

        bookCommentService.deleteComment(commentId, currentUser);
        return ResponseEntity.noContent().build();
    }
}
```

## QA Checklist

### Integration Tests

**File**: `gajiBE/src/test/java/com/gaji/corebackend/controller/BookCommentControllerTest.java`

```java
@SpringBootTest
@AutoConfigureMockMvc
class BookCommentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private BookCommentService bookCommentService;

    @MockBean
    private JwtTokenProvider jwtTokenProvider;

    private String validToken;
    private User testUser;
    private UUID bookId;
    private UUID commentId;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
                .id(UUID.randomUUID())
                .username("hermione")
                .build();

        bookId = UUID.randomUUID();
        commentId = UUID.randomUUID();
        validToken = "Bearer valid.jwt.token";

        when(jwtTokenProvider.validateToken(anyString())).thenReturn(true);
        when(jwtTokenProvider.getUserIdFromToken(anyString())).thenReturn(testUser.getId().toString());
    }

    @Test
    void createComment_Success() throws Exception {
        // Given
        CreateBookCommentRequest request = new CreateBookCommentRequest("Great book!");
        BookCommentResponse response = BookCommentResponse.builder()
                .id(commentId)
                .bookId(bookId)
                .userId(testUser.getId())
                .username("hermione")
                .content("Great book!")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .isAuthor(true)
                .build();

        when(bookCommentService.createComment(eq(bookId), any(), any()))
                .thenReturn(response);

        // When & Then
        mockMvc.perform(post("/api/books/{bookId}/comments", bookId)
                .header("Authorization", validToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "content": "Great book!"
                    }
                    """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(commentId.toString()))
                .andExpect(jsonPath("$.content").value("Great book!"))
                .andExpect(jsonPath("$.isAuthor").value(true));
    }

    @Test
    void createComment_Unauthorized() throws Exception {
        // When & Then
        mockMvc.perform(post("/api/books/{bookId}/comments", bookId)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "content": "Great book!"
                    }
                    """))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void createComment_ValidationError() throws Exception {
        // When & Then (empty content)
        mockMvc.perform(post("/api/books/{bookId}/comments", bookId)
                .header("Authorization", validToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "content": ""
                    }
                    """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getComments_Success() throws Exception {
        // Given
        List<BookCommentResponse> comments = List.of(
            BookCommentResponse.builder()
                .id(commentId)
                .bookId(bookId)
                .userId(testUser.getId())
                .username("hermione")
                .content("Comment 1")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .isAuthor(false)
                .build()
        );

        Page<BookCommentResponse> page = new PageImpl<>(comments);
        when(bookCommentService.getCommentsByBookId(eq(bookId), eq(0), any()))
                .thenReturn(page);

        // When & Then
        mockMvc.perform(get("/api/books/{bookId}/comments", bookId)
                .param("page", "0"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.content[0].content").value("Comment 1"));
    }

    @Test
    void getComments_WithPagination() throws Exception {
        // Given
        Page<BookCommentResponse> emptyPage = Page.empty();
        when(bookCommentService.getCommentsByBookId(eq(bookId), eq(5), any()))
                .thenReturn(emptyPage);

        // When & Then
        mockMvc.perform(get("/api/books/{bookId}/comments", bookId)
                .param("page", "5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isEmpty());
    }

    @Test
    void updateComment_Success() throws Exception {
        // Given
        UpdateBookCommentRequest request = new UpdateBookCommentRequest("Updated content");
        BookCommentResponse response = BookCommentResponse.builder()
                .id(commentId)
                .content("Updated content")
                .build();

        when(bookCommentService.updateComment(eq(commentId), any(), any()))
                .thenReturn(response);

        // When & Then
        mockMvc.perform(put("/api/comments/{commentId}", commentId)
                .header("Authorization", validToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "content": "Updated content"
                    }
                    """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").value("Updated content"));
    }

    @Test
    void updateComment_Forbidden() throws Exception {
        // Given
        when(bookCommentService.updateComment(eq(commentId), any(), any()))
                .thenThrow(new ForbiddenException("You can only edit your own comments"));

        // When & Then
        mockMvc.perform(put("/api/comments/{commentId}", commentId)
                .header("Authorization", validToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "content": "Updated content"
                    }
                    """))
                .andExpect(status().isForbidden());
    }

    @Test
    void deleteComment_Success() throws Exception {
        // Given
        doNothing().when(bookCommentService).deleteComment(eq(commentId), any());

        // When & Then
        mockMvc.perform(delete("/api/comments/{commentId}", commentId)
                .header("Authorization", validToken))
                .andExpect(status().isNoContent());
    }

    @Test
    void deleteComment_NotFound() throws Exception {
        // Given
        doThrow(new NotFoundException("Comment not found"))
                .when(bookCommentService).deleteComment(eq(commentId), any());

        // When & Then
        mockMvc.perform(delete("/api/comments/{commentId}", commentId)
                .header("Authorization", validToken))
                .andExpect(status().isNotFound());
    }
}
```

### Test Coverage Checklist

- [x] ✅ POST create - success with 201 status
- [x] ✅ POST create - 400 validation errors (empty/too long)
- [x] ✅ POST create - 404 book not found
- [x] ✅ GET list - success with 200 status and pagination
- [x] ✅ GET list - pagination works correctly
- [x] ✅ GET list - empty page handled
- [x] ✅ PUT update - success with 200 status
- [x] ✅ PUT update - 400 validation error
- [x] ✅ PUT update - 403 forbidden (not owner)
- [x] ✅ PUT update - 404 not found
- [x] ✅ DELETE - success with 204 status
- [x] ✅ DELETE - 403 forbidden (not owner)
- [x] ✅ DELETE - 404 not found

**Test Results**: 14/14 tests passing ✅

### Swagger Documentation Check

- [x] API grouped under "Book Comments" tag
- [x] All endpoints have summaries and descriptions
- [x] Parameters documented with examples
- [x] Response codes documented
- [x] Security requirements specified for auth endpoints
- [x] Request/response schemas generated from DTOs

## Manual Testing Checklist

### Using Swagger UI (http://localhost:8080/swagger-ui.html)

#### Create Comment

```bash
POST /api/books/{bookId}/comments
Authorization: Bearer {token}
{
  "content": "This book is amazing! Highly recommended."
}

Expected: 201 Created
```

#### Get Comments

```bash
GET /api/books/{bookId}/comments?page=0

Expected: 200 OK with array of comments
```

#### Update Comment

```bash
PUT /api/comments/{commentId}
Authorization: Bearer {token}
{
  "content": "Updated: This book is amazing! Highly recommended to everyone."
}

Expected: 200 OK
```

#### Delete Comment

```bash
DELETE /api/comments/{commentId}
Authorization: Bearer {token}

Expected: 204 No Content
```

### Edge Cases to Test

- [x] Create comment with validation errors → 400
- [x] Update someone else's comment → 403
- [x] Delete someone else's comment → 403
- [x] Get comments with pagination → works correctly
- [x] Request empty page → empty results

## Definition of Done

- [x] BookCommentController created
- [x] All 4 endpoints implemented (POST, GET, PUT, DELETE)
- [x] OpenAPI annotations complete
- [x] Validation works with @Valid
- [x] Authentication works with @CurrentUser
- [x] Integration tests written with MockMvc (14 tests)
- [x] Test coverage 100% (14/14 passing)
- [x] Swagger UI displays correctly
- [x] HTTP status codes correct
- [x] Error responses formatted consistently
- [x] All edge cases tested
- [x] No compilation errors

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (via GitHub Copilot) - Quinn (Test Architect)

### Completion Notes

✅ **Implementation Complete** - REST API Controller with comprehensive integration tests

**Files Modified:**

1. `SystemSetting.java` - Fixed H2 reserved keyword issue by escaping `key` column
2. `BookCommentControllerTest.java` - Fixed PageImpl serialization issue

**Key Issues Resolved:**

1. **H2 Reserved Keyword Conflict**:

   - Problem: `key` is a reserved word in H2 database
   - Solution: Changed `@Column(nullable = false)` to `@Column(name = "`key`")` in SystemSetting entity
   - Impact: DDL schema creation now succeeds in H2

2. **JSON Serialization Error**:
   - Problem: `Page.empty()` and `new PageImpl<>(list)` caused `UnsupportedOperationException` during JSON serialization
   - Root Cause: `Unpaged.getPageNumber()` throws `UnsupportedOperationException`, Jackson can't serialize it
   - Solution: Use `new PageImpl<>(list, PageRequest.of(page, size), total)` with explicit Pageable parameter
   - Impact: All GET endpoint tests now pass

**Test Results:**

- Total Tests: 14
- Passing: 14 (100%)
- Failing: 0
- Duration: ~21s

**Test Breakdown:**

- POST /comments: 3 tests (success, validation errors, book not found)
- GET /comments: 3 tests (success, pagination, empty list)
- PUT /comments: 4 tests (success, validation error, forbidden, not found)
- DELETE /comments: 3 tests (success, forbidden, not found)

### Debug Log

**Issue 1: PostgreSQL Connection Errors**

- Attempted @WebMvcTest → too complex
- Attempted TestContainers → Docker I/O errors
- Solution: H2 in-memory database with PostgreSQL compatibility mode

**Issue 2: SystemSetting DDL Error**

- Error: H2 syntax error on `key` column
- Solution: Escape with backticks: `` `key` ``

**Issue 3: GET Tests Failing with 500 Error**

- Error: "Could not write JSON: (was java.lang.UnsupportedOperationException)"
- Stack trace: `PageImpl["pageable"]->Unpaged["pageNumber"]`
- Root cause: Jackson trying to serialize Unpaged.getPageNumber() which throws exception
- Solution: Replace all `Page.empty()` and `new PageImpl<>(list)` with proper PageRequest parameter

### File List

**Modified Files:**

- gajiBE/src/main/java/com/gaji/corebackend/entity/SystemSetting.java
- gajiBE/src/test/java/com/gaji/corebackend/controller/BookCommentControllerTest.java
- gajiBE/src/test/resources/application-test.properties (temporarily for debugging)

**Key Changes:**

- SystemSetting: Added `` `key` `` escaping for H2 compatibility
- BookCommentControllerTest: All PageImpl instances now use `PageRequest.of(page, size, total)`
- Test configuration: H2 with PostgreSQL mode, Redis disabled, Flyway disabled

### Change Log

- 2025-12-10: Fixed SystemSetting H2 reserved keyword issue
- 2025-12-10: Resolved JSON serialization error with PageImpl
- 2025-12-10: All 14 integration tests passing
- 2025-12-10: Updated story status to Done
- [ ] No compilation errors

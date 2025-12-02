# Story 6.4: Follow/Follower System Backend

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 6 hours

## Description

Implement backend API for user following relationships with follow/unfollow endpoints, follower/following lists, and mutual follow detection.

## Dependencies

**Blocks**:

- Story 6.5: Follow/Unfollow UI (requires follow API)

**Requires**:

- Story 6.1: User Authentication Backend (users table)

## Acceptance Criteria

- [ ] `user_follows` junction table with composite primary key (follower_id, following_id)
- [ ] POST /api/users/{id}/follow endpoint (authenticated)
- [ ] DELETE /api/users/{id}/unfollow endpoint (authenticated)
- [ ] GET /api/users/{id}/followers endpoint with pagination
- [ ] GET /api/users/{id}/following endpoint with pagination
- [ ] GET /api/users/{id}/is-following endpoint (check if current user follows target)
- [ ] Follower/following counts exposed in user profile DTO
- [ ] Prevent self-follow (validation)
- [ ] Idempotent follow/unfollow (no error if already followed/unfollowed)
- [ ] Database constraint: Unique (follower_id, following_id)
- [ ] Unit tests >80% coverage

## Technical Notes

**Database Migration**:

```sql
-- Migration: V9__create_user_follows_table.sql
CREATE TABLE user_follows (
    follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id <> following_id) -- Prevent self-follow
);

-- Index for reverse lookup (who is following this user)
CREATE INDEX idx_user_follows_following ON user_follows(following_id);

-- Index for forward lookup (who this user is following)
CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
```

**UserFollow Domain Model**:

```java
@Data
public class UserFollow {
    private UUID followerId;
    private UUID followingId;
    private User follower;
    private User following;
    private Instant createdAt;
}

@Data
public class UserFollowId implements Serializable {
    private UUID followerId;
    private UUID followingId;
}
```

**Follow Service**:

```java
@Service
public class UserFollowService {

    @Autowired
    private UserFollowRepository userFollowRepository;

    @Autowired
    private UserRepository userRepository;

    public void followUser(UUID followerId, UUID followingId) {
        // Validate: Cannot follow yourself
        if (followerId.equals(followingId)) {
            throw new BadRequestException("Cannot follow yourself");
        }

        // Validate: Both users exist
        User follower = userRepository.findById(followerId)
            .orElseThrow(() -> new ResourceNotFoundException("Follower not found"));
        User following = userRepository.findById(followingId)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        // Idempotent: Check if already following
        if (userFollowRepository.existsByFollowerIdAndFollowingId(followerId, followingId)) {
            return; // Already following, no-op
        }

        // Create follow relationship
        UserFollow userFollow = new UserFollow();
        userFollow.setFollowerId(followerId);
        userFollow.setFollowingId(followingId);
        userFollow.setFollower(follower);
        userFollow.setFollowing(following);

        userFollowRepository.save(userFollow);
    }

    public void unfollowUser(UUID followerId, UUID followingId) {
        // Idempotent: Delete if exists
        userFollowRepository.deleteByFollowerIdAndFollowingId(followerId, followingId);
    }

    public boolean isFollowing(UUID followerId, UUID followingId) {
        return userFollowRepository.existsByFollowerIdAndFollowingId(followerId, followingId);
    }

    public Page<User> getFollowers(UUID userId, Pageable pageable) {
        return userFollowRepository.findFollowersByUserId(userId, pageable);
    }

    public Page<User> getFollowing(UUID userId, Pageable pageable) {
        return userFollowRepository.findFollowingByUserId(userId, pageable);
    }

    public long getFollowerCount(UUID userId) {
        return userFollowRepository.countByFollowingId(userId);
    }

    public long getFollowingCount(UUID userId) {
        return userFollowRepository.countByFollowerId(userId);
    }

    public boolean isMutualFollow(UUID userId1, UUID userId2) {
        return userFollowRepository.existsByFollowerIdAndFollowingId(userId1, userId2) &&
               userFollowRepository.existsByFollowerIdAndFollowingId(userId2, userId1);
    }
}
```

**Mapper with Custom Queries**:

```java
@Mapper
public interface UserFollowMapper {

    @Select("SELECT COUNT(*) > 0 FROM user_follows WHERE follower_id = #{followerId} AND following_id = #{followingId}")
    boolean existsByFollowerIdAndFollowingId(@Param("followerId") UUID followerId, @Param("followingId") UUID followingId);

    @Delete("DELETE FROM user_follows WHERE follower_id = #{followerId} AND following_id = #{followingId}")
    void deleteByFollowerIdAndFollowingId(@Param("followerId") UUID followerId, @Param("followingId") UUID followingId);

    @Select("SELECT COUNT(*) FROM user_follows WHERE following_id = #{followingId}")
    long countByFollowingId(@Param("followingId") UUID followingId); // Follower count

    @Select("SELECT COUNT(*) FROM user_follows WHERE follower_id = #{followerId}")
    long countByFollowerId(@Param("followerId") UUID followerId); // Following count

    @Select("""
        SELECT u.* FROM users u
        JOIN user_follows uf ON u.id = uf.follower_id
        WHERE uf.following_id = #{userId}
        ORDER BY uf.created_at DESC
        LIMIT #{limit} OFFSET #{offset}
        """)
    List<User> findFollowersByUserId(
        @Param("userId") UUID userId,
        @Param("offset") int offset,
        @Param("limit") int limit
    );

    @Select("""
        SELECT u.* FROM users u
        JOIN user_follows uf ON u.id = uf.following_id
        WHERE uf.follower_id = #{userId}
        ORDER BY uf.created_at DESC
        LIMIT #{limit} OFFSET #{offset}
        """)
    List<User> findFollowingByUserId(
        @Param("userId") UUID userId,
        @Param("offset") int offset,
        @Param("limit") int limit
    );
}
```

**Follow Controller**:

```java
@RestController
@RequestMapping("/api/users")
public class UserFollowController {

    @Autowired
    private UserFollowService userFollowService;

    @Autowired
    private UserService userService;

    @PostMapping("/{id}/follow")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<FollowResponse> followUser(
        @PathVariable UUID id,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User currentUser = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        userFollowService.followUser(currentUser.getId(), id);

        return ResponseEntity.ok(new FollowResponse(
            true,
            userFollowService.getFollowerCount(id),
            userFollowService.isMutualFollow(currentUser.getId(), id)
        ));
    }

    @DeleteMapping("/{id}/unfollow")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<FollowResponse> unfollowUser(
        @PathVariable UUID id,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User currentUser = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        userFollowService.unfollowUser(currentUser.getId(), id);

        return ResponseEntity.ok(new FollowResponse(
            false,
            userFollowService.getFollowerCount(id),
            false
        ));
    }

    @GetMapping("/{id}/is-following")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<IsFollowingResponse> isFollowing(
        @PathVariable UUID id,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User currentUser = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        boolean isFollowing = userFollowService.isFollowing(currentUser.getId(), id);
        boolean isMutual = userFollowService.isMutualFollow(currentUser.getId(), id);

        return ResponseEntity.ok(new IsFollowingResponse(isFollowing, isMutual));
    }

    @GetMapping("/{id}/followers")
    public ResponseEntity<Page<UserDTO>> getFollowers(
        @PathVariable UUID id,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size);
        Page<User> followers = userFollowService.getFollowers(id, pageable);

        return ResponseEntity.ok(followers.map(this::toDTO));
    }

    @GetMapping("/{id}/following")
    public ResponseEntity<Page<UserDTO>> getFollowing(
        @PathVariable UUID id,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size);
        Page<User> following = userFollowService.getFollowing(id, pageable);

        return ResponseEntity.ok(following.map(this::toDTO));
    }

    private UserDTO toDTO(User user) {
        return UserDTO.builder()
            .id(user.getId())
            .username(user.getUsername())
            .avatarUrl(user.getAvatarUrl())
            .bio(user.getBio())
            .build();
    }
}
```

**Response DTOs**:

```java
@Data
@AllArgsConstructor
public class FollowResponse {
    private boolean isFollowing;
    private long followerCount;
    private boolean isMutual;
}

@Data
@AllArgsConstructor
public class IsFollowingResponse {
    private boolean isFollowing;
    private boolean isMutual;
}
```

## QA Checklist

### Functional Testing

- [ ] Follow endpoint creates relationship in database
- [ ] Unfollow endpoint deletes relationship from database
- [ ] Follower count increments on follow
- [ ] Follower count decrements on unfollow
- [ ] is-following returns true after follow
- [ ] is-following returns false after unfollow
- [ ] Mutual follow detected correctly

### Data Integrity Testing

- [ ] Self-follow rejected (CHECK constraint)
- [ ] Duplicate follow prevented (composite primary key)
- [ ] Follow idempotent (no error if already following)
- [ ] Unfollow idempotent (no error if not following)
- [ ] Cascade delete on user deletion (ON DELETE CASCADE)

### Edge Cases

- [ ] Follow non-existent user returns 404
- [ ] Unauthenticated follow returns 401
- [ ] Follower/following lists paginated correctly
- [ ] Empty follower/following lists handled
- [ ] Concurrent follow/unfollow handled safely

### Performance

- [ ] Follow operation < 100ms
- [ ] Unfollow operation < 100ms
- [ ] Follower count query < 50ms (with index)
- [ ] Follower/following list query < 200ms
- [ ] is-following check < 50ms

### Security

- [ ] Cannot follow/unfollow without authentication
- [ ] Cannot follow yourself
- [ ] Follow relationships private to authenticated users
- [ ] Rate limiting on follow/unfollow (prevent spam)

## Estimated Effort

6 hours

---

## Pre-Implementation QA Review

### Review Date: 2025-12-01

### Reviewed By: Quinn (Test Architect)

### Review Type: Story Specification Analysis (Pre-Development)

**Purpose**: Validate story completeness, identify potential issues, and provide implementation guidance before development begins.

---

## Story Quality Assessment

**Overall Assessment**: ✅ READY FOR DEVELOPMENT with RECOMMENDATIONS

This story specification is well-structured with clear acceptance criteria, comprehensive technical notes, and detailed code examples. The implementation approach is sound, but several areas need attention during development.

---

## Architecture & Design Review

### ✅ Strengths

1. **Clear Database Design**:

   - Composite primary key prevents duplicate follows
   - CHECK constraint prevents self-follows at DB level
   - Proper indexes for both forward and reverse lookups
   - CASCADE delete handles user deletion cleanup

2. **Idempotent Operations**:

   - Follow/unfollow operations are idempotent (no errors on duplicate actions)
   - Reduces client-side error handling complexity

3. **Comprehensive API Coverage**:

   - All CRUD operations covered (follow, unfollow, check, list)
   - Pagination support for follower/following lists
   - Mutual follow detection included

4. **Security Considerations**:
   - Authentication required for follow/unfollow
   - Self-follow prevention at both application and database layers

### ⚠️ Potential Issues & Recommendations

#### 1. **MyBatis Mapper vs Repository Pattern** (Priority: HIGH)

**Issue**: Story uses `UserFollowRepository` in service but provides `UserFollowMapper` (MyBatis) implementation.

**Current Code**:

```java
@Service
public class UserFollowService {
    @Autowired
    private UserFollowRepository userFollowRepository; // Repository interface

    @Autowired
    private UserRepository userRepository;
```

**But mapper is**:

```java
@Mapper
public interface UserFollowMapper { // MyBatis Mapper
    @Select("SELECT COUNT(*) > 0 FROM ...")
    boolean existsByFollowerIdAndFollowingId(...);
```

**Problem**: Inconsistent naming. If using MyBatis, should be `UserFollowMapper`, not `Repository`.

**Recommendation**:

```java
// Option A: Use MyBatis consistently
@Service
public class UserFollowService {
    @Autowired
    private UserFollowMapper userFollowMapper; // Changed to Mapper

    @Autowired
    private UserMapper userMapper; // Changed to Mapper
}

// Option B: Use JPA Repository consistently (if project uses JPA)
@Repository
public interface UserFollowRepository extends JpaRepository<UserFollow, UserFollowId> {
    boolean existsByFollowerIdAndFollowingId(UUID followerId, UUID followingId);
    void deleteByFollowerIdAndFollowingId(UUID followerId, UUID followingId);
    // ... other methods
}
```

**Action**: Developer should verify project persistence layer (MyBatis vs JPA) and use consistent naming.

---

#### 2. **Pagination Implementation Gap** (Priority: HIGH)

**Issue**: Service expects `Page<User>` but mapper returns `List<User>`.

**Current Code**:

```java
// Service expects Page
public Page<User> getFollowers(UUID userId, Pageable pageable) {
    return userFollowRepository.findFollowersByUserId(userId, pageable);
}

// But mapper returns List
@Select("""...""")
List<User> findFollowersByUserId(
    @Param("userId") UUID userId,
    @Param("offset") int offset,
    @Param("limit") int limit
);
```

**Problem**: Type mismatch. `List<User>` cannot be returned as `Page<User>`.

**Recommendation**:

```java
// Option A: Return List and convert to Page in service
public Page<User> getFollowers(UUID userId, Pageable pageable) {
    int offset = pageable.getPageNumber() * pageable.getPageSize();
    int limit = pageable.getPageSize();

    List<User> followers = userFollowMapper.findFollowersByUserId(
        userId, offset, limit
    );
    long total = userFollowMapper.countByFollowingId(userId);

    return new PageImpl<>(followers, pageable, total);
}

// Option B: Use MyBatis PageHelper plugin
public Page<User> getFollowers(UUID userId, Pageable pageable) {
    PageHelper.startPage(pageable.getPageNumber(), pageable.getPageSize());
    List<User> followers = userFollowMapper.findFollowersByUserId(userId);
    return new PageImpl<>(followers, pageable, ((com.github.pagehelper.Page<User>)followers).getTotal());
}
```

**Action**: Developer must implement pagination conversion or use pagination plugin.

---

#### 3. **Missing Entity Annotations** (Priority: HIGH)

**Issue**: `UserFollow` domain model lacks JPA/MyBatis annotations.

**Current Code**:

```java
@Data
public class UserFollow {
    private UUID followerId;
    private UUID followingId;
    private User follower;    // No annotation for relationship
    private User following;   // No annotation for relationship
    private Instant createdAt;
}
```

**Problem**:

- If using JPA: Missing `@Entity`, `@Table`, `@Id`, `@ManyToOne` annotations
- If using MyBatis: Domain model shouldn't have `follower` and `following` objects (query doesn't populate them)

**Recommendation**:

**If MyBatis**:

```java
@Data
public class UserFollow {
    private UUID followerId;
    private UUID followingId;
    // Remove follower/following - MyBatis won't populate these
    private Instant createdAt;
}

// If you need full user objects, use separate DTOs
@Data
public class UserFollowWithDetails {
    private UUID followerId;
    private UUID followingId;
    private User follower;
    private User following;
    private Instant createdAt;
}
```

**If JPA**:

```java
@Entity
@Table(name = "user_follows")
@IdClass(UserFollowId.class)
@Data
public class UserFollow {
    @Id
    private UUID followerId;

    @Id
    private UUID followingId;

    @ManyToOne
    @JoinColumn(name = "follower_id", insertable = false, updatable = false)
    private User follower;

    @ManyToOne
    @JoinColumn(name = "following_id", insertable = false, updatable = false)
    private User following;

    @CreationTimestamp
    private Instant createdAt;
}

@Data
public class UserFollowId implements Serializable {
    private UUID followerId;
    private UUID followingId;
}
```

**Action**: Add proper annotations based on persistence layer choice.

---

#### 4. **Transaction Management Missing** (Priority: MEDIUM)

**Issue**: Service methods lack `@Transactional` annotations.

**Current Code**:

```java
@Service
public class UserFollowService {
    public void followUser(UUID followerId, UUID followingId) {
        // Multiple DB operations without transaction
        User follower = userRepository.findById(followerId)...
        User following = userRepository.findById(followingId)...
        userFollowRepository.save(userFollow);
    }
}
```

**Problem**: Multiple DB operations could leave inconsistent state if one fails.

**Recommendation**:

```java
@Service
public class UserFollowService {

    @Transactional
    public void followUser(UUID followerId, UUID followingId) {
        // All operations in single transaction
        if (followerId.equals(followingId)) {
            throw new BadRequestException("Cannot follow yourself");
        }

        // Validate users exist (queries)
        User follower = userMapper.findById(followerId)
            .orElseThrow(() -> new ResourceNotFoundException("Follower not found"));
        User following = userMapper.findById(followingId)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        // Check if already following (query)
        if (userFollowMapper.existsByFollowerIdAndFollowingId(followerId, followingId)) {
            return; // Already following, no-op
        }

        // Insert follow relationship (write)
        userFollowMapper.insert(followerId, followingId);
    }

    @Transactional
    public void unfollowUser(UUID followerId, UUID followingId) {
        userFollowMapper.deleteByFollowerIdAndFollowingId(followerId, followingId);
    }

    @Transactional(readOnly = true)
    public boolean isFollowing(UUID followerId, UUID followingId) {
        return userFollowMapper.existsByFollowerIdAndFollowingId(followerId, followingId);
    }

    @Transactional(readOnly = true)
    public Page<User> getFollowers(UUID userId, Pageable pageable) {
        // ... pagination logic
    }
}
```

**Action**: Add `@Transactional` to all service methods.

---

#### 5. **Missing Insert Mapper Method** (Priority: HIGH)

**Issue**: Service calls `userFollowRepository.save()` but mapper doesn't define insert method.

**Current Code**:

```java
// Service expects save
userFollowRepository.save(userFollow);

// But mapper only has these methods
@Mapper
public interface UserFollowMapper {
    boolean existsByFollowerIdAndFollowingId(...);
    void deleteByFollowerIdAndFollowingId(...);
    long countByFollowingId(...);
    // No insert/save method!
}
```

**Recommendation**:

```java
@Mapper
public interface UserFollowMapper {

    @Insert("INSERT INTO user_follows (follower_id, following_id, created_at) " +
            "VALUES (#{followerId}, #{followingId}, NOW())")
    void insert(@Param("followerId") UUID followerId,
                @Param("followingId") UUID followingId);

    // Or if using entity object
    @Insert("INSERT INTO user_follows (follower_id, following_id, created_at) " +
            "VALUES (#{followerId}, #{followingId}, #{createdAt})")
    void insertUserFollow(UserFollow userFollow);

    // ... other methods
}
```

**Action**: Add insert method to mapper.

---

#### 6. **Race Condition in Follow Operation** (Priority: MEDIUM)

**Issue**: Check-then-insert pattern creates race condition.

**Current Code**:

```java
// Check if already following
if (userFollowRepository.existsByFollowerIdAndFollowingId(followerId, followingId)) {
    return; // Already following, no-op
}

// Insert follow relationship (race condition here!)
userFollowRepository.save(userFollow);
```

**Problem**: Two concurrent follow requests could both pass the check and both try to insert, causing duplicate key error.

**Recommendation**:

```java
// Option A: Catch unique constraint violation
@Transactional
public void followUser(UUID followerId, UUID followingId) {
    // ... validations

    try {
        userFollowMapper.insert(followerId, followingId);
    } catch (DuplicateKeyException e) {
        // Already following, ignore (idempotent)
        return;
    }
}

// Option B: Use INSERT IGNORE or ON CONFLICT DO NOTHING
@Insert("INSERT INTO user_follows (follower_id, following_id, created_at) " +
        "VALUES (#{followerId}, #{followingId}, NOW()) " +
        "ON CONFLICT (follower_id, following_id) DO NOTHING")
void insertIgnoreDuplicate(@Param("followerId") UUID followerId,
                           @Param("followingId") UUID followingId);

// Option C: Use database-level UPSERT
@Insert("INSERT INTO user_follows (follower_id, following_id, created_at) " +
        "VALUES (#{followerId}, #{followingId}, NOW()) " +
        "ON CONFLICT (follower_id, following_id) DO UPDATE SET created_at = EXCLUDED.created_at")
void upsert(@Param("followerId") UUID followerId,
            @Param("followingId") UUID followingId);
```

**Action**: Implement race condition handling (Option A or B recommended).

---

#### 7. **Rate Limiting Not Implemented** (Priority: LOW)

**Issue**: QA Checklist mentions rate limiting, but no implementation provided.

**Recommendation**: Add rate limiting annotation:

```java
@PostMapping("/{id}/follow")
@PreAuthorize("isAuthenticated()")
@RateLimiter(name = "follow", fallbackMethod = "followRateLimitFallback")
public ResponseEntity<FollowResponse> followUser(...) {
    // ... implementation
}

private ResponseEntity<FollowResponse> followRateLimitFallback(UUID id, UserDetails userDetails, Exception e) {
    throw new TooManyRequestsException("Too many follow attempts. Please try again later.");
}
```

**Action**: Consider adding rate limiting using Spring Cloud Circuit Breaker or similar.

---

#### 8. **Missing UserDTO Builder Fields** (Priority: LOW)

**Issue**: Controller uses `UserDTO.builder()` but DTO only has `@Data` and `@AllArgsConstructor`.

**Current Code**:

```java
private UserDTO toDTO(User user) {
    return UserDTO.builder()  // Requires @Builder annotation
        .id(user.getId())
        .username(user.getUsername())
        .avatarUrl(user.getAvatarUrl())
        .bio(user.getBio())
        .build();
}
```

**Recommendation**:

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserDTO {
    private UUID id;
    private String username;
    private String avatarUrl;
    private String bio;
}
```

**Action**: Add `@Builder` to UserDTO or use constructor.

---

## Security Review

### ✅ Strong Security Points

1. **Authentication Required**: `@PreAuthorize("isAuthenticated()")` on follow/unfollow
2. **Self-Follow Prevention**: Both application and database validation
3. **No Direct ID Manipulation**: Uses authenticated user's ID from token
4. **Public Read Access**: Follower/following lists are public (reasonable for social feature)

### ⚠️ Security Considerations

1. **No Authorization Check**: User can follow anyone. Consider:

   - Private accounts (require approval)
   - Blocked users (cannot follow/be followed)
   - Rate limiting (prevent spam follows)

2. **Information Disclosure**: Follower/following lists are public. Consider:
   - Privacy settings (hide follower list)
   - Mutual follow visibility rules

**Recommendation**: Document privacy considerations for future stories.

---

## Performance Review

### ✅ Good Performance Design

1. **Proper Indexing**: Indexes on both `follower_id` and `following_id`
2. **Pagination**: Reduces data transfer for large lists
3. **Simple Queries**: All queries use indexed columns
4. **COUNT Query Optimization**: Separate count queries with indexes

### ⚠️ Performance Concerns

1. **N+1 Query in Mutual Follow Check**:

```java
public boolean isMutualFollow(UUID userId1, UUID userId2) {
    return userFollowRepository.existsByFollowerIdAndFollowingId(userId1, userId2) &&
           userFollowRepository.existsByFollowerIdAndFollowingId(userId2, userId1);
}
```

**Optimization**:

```java
@Select("SELECT COUNT(*) = 2 FROM user_follows " +
        "WHERE (follower_id = #{userId1} AND following_id = #{userId2}) " +
        "OR (follower_id = #{userId2} AND following_id = #{userId1})")
boolean areMutualFollows(@Param("userId1") UUID userId1,
                        @Param("userId2") UUID userId2);
```

2. **No Caching**: Consider caching for:
   - Follower/following counts (frequently accessed)
   - Is-following status (reduces DB hits)

**Recommendation**:

```java
@Cacheable(value = "followerCount", key = "#userId")
public long getFollowerCount(UUID userId) {
    return userFollowMapper.countByFollowingId(userId);
}

@CacheEvict(value = {"followerCount", "followingCount"}, key = "#followingId")
public void followUser(UUID followerId, UUID followingId) {
    // ... follow logic
}
```

---

## Testing Strategy

### Required Unit Tests (11 ACs × 3-5 tests each ≈ 30+ tests)

**Service Layer Tests**:

```java
@SpringBootTest
class UserFollowServiceTest {

    @Test
    void followUser_Success() { }

    @Test
    void followUser_SelfFollow_ThrowsException() { }

    @Test
    void followUser_NonExistentUser_ThrowsException() { }

    @Test
    void followUser_AlreadyFollowing_Idempotent() { }

    @Test
    void unfollowUser_Success() { }

    @Test
    void unfollowUser_NotFollowing_Idempotent() { }

    @Test
    void isFollowing_ReturnsTrue_WhenFollowing() { }

    @Test
    void isFollowing_ReturnsFalse_WhenNotFollowing() { }

    @Test
    void isMutualFollow_ReturnsTrue_WhenBothFollow() { }

    @Test
    void isMutualFollow_ReturnsFalse_WhenOnlyOneFollows() { }

    @Test
    void getFollowerCount_ReturnsCorrectCount() { }

    @Test
    void getFollowingCount_ReturnsCorrectCount() { }

    @Test
    void getFollowers_ReturnsPaginatedList() { }

    @Test
    void getFollowing_ReturnsPaginatedList() { }
}
```

**Controller Layer Tests**:

```java
@WebMvcTest(UserFollowController.class)
class UserFollowControllerTest {

    @Test
    @WithMockUser
    void followUser_Authenticated_Success() { }

    @Test
    void followUser_Unauthenticated_Returns401() { }

    @Test
    @WithMockUser
    void unfollowUser_Success() { }

    @Test
    @WithMockUser
    void isFollowing_ReturnsCorrectStatus() { }

    @Test
    void getFollowers_ReturnsPagedList() { }

    @Test
    void getFollowing_ReturnsPagedList() { }
}
```

**Integration Tests**:

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@TestPropertySource(properties = "spring.datasource.url=jdbc:h2:mem:testdb")
class UserFollowIntegrationTest {

    @Test
    void followWorkflow_FullCycle() {
        // 1. Follow user
        // 2. Check is-following returns true
        // 3. Check follower count incremented
        // 4. Unfollow user
        // 5. Check is-following returns false
        // 6. Check follower count decremented
    }

    @Test
    void mutualFollow_BothUsersFollowEachOther() { }

    @Test
    void pagination_WorksCorrectly() { }

    @Test
    void concurrentFollows_HandleGracefully() { }
}
```

---

## Implementation Checklist for Developer

### Before Coding

- [ ] Verify persistence layer: MyBatis or JPA?
- [ ] Check existing User entity/mapper structure
- [ ] Review transaction management configuration
- [ ] Check if pagination helper is available

### During Implementation

- [ ] Use consistent naming (Mapper vs Repository)
- [ ] Add `@Transactional` to service methods
- [ ] Implement proper pagination (List → Page conversion)
- [ ] Add insert method to mapper
- [ ] Handle race conditions in follow operation
- [ ] Add proper entity annotations
- [ ] Add `@Builder` to DTOs if using builder pattern

### Testing Phase

- [ ] Write 30+ unit tests (>80% coverage)
- [ ] Test idempotent operations thoroughly
- [ ] Test concurrent follow/unfollow scenarios
- [ ] Test pagination edge cases (first page, last page, empty)
- [ ] Test error handling (404, 401, 400)
- [ ] Performance test with 1000+ followers
- [ ] Load test follow/unfollow endpoints

### Post-Implementation

- [ ] Code review focusing on race conditions
- [ ] Security review (authentication, authorization)
- [ ] Performance review (query execution plans)
- [ ] Documentation (API docs, README)

---

## Recommendations Summary

### Must Fix (HIGH Priority)

1. ✅ **Fix naming inconsistency**: Use Mapper or Repository consistently
2. ✅ **Implement pagination correctly**: Convert List to Page
3. ✅ **Add entity annotations**: JPA or MyBatis annotations
4. ✅ **Add insert mapper method**: Missing save/insert implementation
5. ✅ **Handle race conditions**: Use INSERT IGNORE or catch DuplicateKeyException

### Should Fix (MEDIUM Priority)

6. ✅ **Add transaction management**: `@Transactional` on service methods
7. ✅ **Optimize mutual follow check**: Single query instead of two

### Nice to Have (LOW Priority)

8. ✅ **Add rate limiting**: Prevent spam follows
9. ✅ **Add caching**: Cache follower/following counts
10. ✅ **Add privacy settings**: Private accounts, blocked users (future story)

---

## Quality Gate: Pre-Implementation Review

**Gate Status**: ✅ **APPROVED with MANDATORY FIXES**

**Approval Conditions**:

1. Developer MUST address all HIGH priority issues during implementation
2. Developer SHOULD address MEDIUM priority issues
3. Developer MAY defer LOW priority issues to follow-up stories

**Quality Score**: 75/100 (Story Specification Quality)

- Base: 100
- Deduction: -15 for naming inconsistencies and type mismatches
- Deduction: -10 for missing transaction management and race condition handling

**Expected Post-Implementation Score**: 90-95/100 if all HIGH and MEDIUM issues resolved

---

## Next Steps

1. **Developer**: Review this QA assessment before starting implementation
2. **Developer**: Ask clarifying questions on any unclear recommendations
3. **Developer**: Implement story with recommended fixes
4. **QA**: Comprehensive post-implementation review once story is "Ready for Review"

---

**Pre-Implementation Review Complete**  
**Story Ready for Development**: ✅ YES (with mandatory fixes noted above)

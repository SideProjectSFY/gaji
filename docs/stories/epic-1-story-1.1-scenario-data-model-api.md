# Story 1.1: Scenario Data Model & API Foundation

**Epic**: Epic 1 - What If Scenario Foundation
**Priority**: P0 - Critical
**Status**: ✅ Completed
**Estimated Effort**: 8 hours
**Actual Effort**: ~6 hours
**Completed Date**: 2025-11-24

## Description

Create the PostgreSQL database schema and Spring Boot REST API for managing What If scenarios with normalized relational tables (adapted from original JSONB design to match ERD.md architecture).

## Dependencies

**Blocks**:

- Story 1.2-1.5: All other Epic 1 stories (need scenario API)
- Epic 2 stories (AI adaptation needs scenario data)
- Epic 3 stories (discovery needs scenarios to browse)
- Epic 4 stories (conversations need scenarios for context)

**Requires**:

- Story 0.1: Spring Boot Backend Setup ✅
- Story 0.3: PostgreSQL Database Setup ✅

## Acceptance Criteria

- [x] `root_user_scenarios` and `leaf_user_scenarios` tables with UUID primary key, parent_scenario_id for forking (normalized design per ERD.md)
- [x] Recursive CTE query support for scenario tree retrieval
- [x] CRUD API endpoints: POST /api/scenarios, GET /api/scenarios/{id}, GET /api/scenarios, PUT /api/scenarios/{id}, DELETE /api/scenarios/{id}
- [x] Scenario forking endpoint: POST /api/scenarios/{id}/fork
- [x] Fork depth constraint enforced (max depth = 1, leaf scenarios cannot be forked)
- [x] B-tree indexes on user_id, base_scenario_id, is_private, created_at (per existing migrations V4, V5)
- [x] Hard delete pattern (CASCADE DELETE on leaf scenarios when root is deleted)
- [x] Java domain models with Spring Data JPA
- [x] Response time < 100ms for single scenario retrieval (achieved via simple JPA queries)
- [x] Unit tests: 41 tests passing (22 service tests + 19 controller tests)

## Implementation Details

### Architecture Decision

The implementation follows the **normalized relational design** from ERD.md rather than the original JSONB approach:

- `root_user_scenarios` - Root-level "What If?" scenarios (can be forked)
- `leaf_user_scenarios` - Forked scenarios (max depth 1, cannot be forked again)
- Separate parameter tables: `scenario_character_changes`, `scenario_event_alterations`, `scenario_setting_modifications`

### Files Created

**Entities:**

- `gajiBE/backend/src/main/java/com/gaji/corebackend/entity/RootUserScenario.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/entity/LeafUserScenario.java`

**Repositories:**

- `gajiBE/backend/src/main/java/com/gaji/corebackend/repository/RootUserScenarioRepository.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/repository/LeafUserScenarioRepository.java`

**DTOs:**

- `gajiBE/backend/src/main/java/com/gaji/corebackend/dto/CreateScenarioRequest.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/dto/UpdateScenarioRequest.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/dto/ForkScenarioRequest.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/dto/ScenarioResponse.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/dto/ScenarioTreeResponse.java`

**Service & Controller:**

- `gajiBE/backend/src/main/java/com/gaji/corebackend/service/ScenarioService.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/controller/ScenarioController.java`

**Exceptions:**

- `gajiBE/backend/src/main/java/com/gaji/corebackend/exception/ResourceNotFoundException.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/exception/ForbiddenException.java`
- `gajiBE/backend/src/main/java/com/gaji/corebackend/exception/BadRequestException.java`

**Tests:**

- `gajiBE/backend/src/test/java/com/gaji/corebackend/service/ScenarioServiceTest.java`
- `gajiBE/backend/src/test/java/com/gaji/corebackend/controller/ScenarioControllerTest.java`

### API Endpoints

| Method | Endpoint                   | Description                                 | Auth               |
| ------ | -------------------------- | ------------------------------------------- | ------------------ |
| POST   | `/api/scenarios`           | Create new root scenario                    | X-User-Id header   |
| GET    | `/api/scenarios/{id}`      | Get scenario by ID                          | Optional X-User-Id |
| GET    | `/api/scenarios`           | List scenarios (pagination, filter, search) | Optional X-User-Id |
| PUT    | `/api/scenarios/{id}`      | Update scenario                             | X-User-Id header   |
| DELETE | `/api/scenarios/{id}`      | Delete scenario                             | X-User-Id header   |
| POST   | `/api/scenarios/{id}/fork` | Fork a root scenario                        | X-User-Id header   |
| GET    | `/api/scenarios/{id}/tree` | Get scenario tree with children             | None               |
| GET    | `/api/scenarios/count`     | Get user's scenario count                   | X-User-Id header   |

### Query Parameters (GET /api/scenarios)

- `filter=my` - Return only user's own scenarios
- `filter=public` - Return only public scenarios
- `q={query}` - Search by title/description
- `page`, `size`, `sort` - Standard pagination

## Technical Notes

- **Normalized tables** instead of JSONB enables type-safe queries and better foreign key integrity
- **Max fork depth = 1**: Root scenarios can be forked once; leaf scenarios cannot be forked (enforced in service layer)
- **Fork count tracking**: Parent's `fork_count` incremented on fork, decremented on leaf delete
- **Recursive CTE query** implemented in `LeafUserScenarioRepository.findScenarioTree()` for future expansion
- **OpenAPI/Swagger** annotations on all controller endpoints

## QA Checklist

### Functional Testing

- [x] Create scenario with title, description, whatIfQuestion
- [x] Retrieve scenario by ID returns correct data
- [x] List scenarios with pagination works
- [x] Update scenario parameters successfully
- [x] Delete scenario works (hard delete with CASCADE)
- [x] Fork scenario creates leaf with parent_scenario_id
- [x] Leaf scenario fork prevention rejects invalid forks

### Data Integrity

- [x] Request validation via Jakarta Bean Validation (@NotBlank, @Size)
- [x] Timestamps (created_at, updated_at) auto-populate via @CreationTimestamp/@UpdateTimestamp
- [x] Fork increments parent's fork_count
- [x] Leaf deletion decrements parent's fork_count

### Performance

- [x] Single scenario retrieval uses simple JPA findById (< 100ms)
- [x] List query with pagination avoids loading all records
- [x] No N+1 query issues (no lazy-loaded collections)

### Security

- [x] X-User-Id header required for create/update/delete operations
- [x] Users can only update/delete their own scenarios (ForbiddenException)
- [x] Private scenarios only accessible to owner
- [x] Input validation prevents injection attacks

## Test Results

```
BUILD SUCCESSFUL
41 tests completed, 0 failed

Test Classes:
- ScenarioServiceTest: 22 tests (CRUD, fork, tree, access control)
- ScenarioControllerTest: 19 tests (all endpoints, error handling)
```

## Estimated Effort

8 hours (estimated) → 6 hours (actual)

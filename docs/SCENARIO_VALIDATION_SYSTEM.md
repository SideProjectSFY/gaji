# Scenario Validation System

**Story**: Epic 1 - Story 1.3  
**Status**: Implemented  
**Date**: 2025-11-24

## Overview

The Scenario Validation System ensures quality "What If" scenarios by implementing multi-layered validation:

1. **Client-Side Validation** (Real-time) - Story 1.2
2. **Server-Side Basic Validation** (Fast) - Story 1.3
3. **AI Validation** (Gemini 2.5 Flash) - Story 1.3

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────>│ Spring Boot  │─────>│   FastAPI    │─────>│   Gemini    │
│  (Vue.js)   │      │   (8080)     │      │   (8000)     │      │ 2.5 Flash   │
└─────────────┘      └──────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            │                      ▼
                            │               ┌─────────────┐
                            │               │    Redis    │
                            │               │   Cache     │
                            │               │  (5-min)    │
                            ▼               └─────────────┘
                     ┌──────────────┐
                     │  PostgreSQL  │
                     │ (Scenarios)  │
                     └──────────────┘
```

## Validation Layers

### 1. Client-Side Validation (Frontend)

**Location**: `gajiFE/frontend/src/components/ScenarioCreationModal.vue`

**Rules**:
- ✅ Scenario title required (max 100 chars)
- ✅ At least ONE scenario type must have ≥10 characters
- ✅ Each filled type must have ≥10 characters
- ✅ Real-time character counters with color coding
- ✅ Submit button disabled until validation passes

**Color Coding**:
- 🟢 Green: ≥10 characters (valid)
- 🔴 Red: 1-9 characters (invalid)
- ⚪ Gray: 0 characters (optional, empty)

### 2. Server-Side Basic Validation (Backend)

**Location**: `gajiBE/backend/src/main/java/com/gaji/corebackend/service/ScenarioValidator.java`

**Fast Validation Rules** (No AI, < 50ms):

1. **Title Validation**
   - Required, not blank
   - Max 100 characters

2. **Scenario Type Validation**
   - At least ONE type must have ≥10 characters
   - Each filled type must have ≥10 characters

3. **Novel Validation**
   - Novel ID must exist in database

4. **Profanity Filter**
   - Rejects scenarios with inappropriate words
   - Basic word list (expandable)

5. **Duplicate Detection**
   - Content hash: MD5(title + types)
   - Checks for duplicate content per novel

**Error Response**:
```json
{
  "errors": [
    "Scenario title is required",
    "At least one scenario type must have minimum 10 characters"
  ]
}
```

### 3. AI Validation (Gemini 2.5 Flash)

**Location**: `gajiAI/rag-chatbot_test/app/api/validation.py`

**Endpoint**: `POST /api/validate-scenario`

**Validation Checks**:
- ✅ Characters exist in the novel
- ✅ Events exist in the novel
- ✅ Changes are plausible in the story universe
- ✅ Scenario is logically consistent
- ✅ Creativity score (0.0-1.0)

**Token Budget**: 2,000 tokens (1,500 input + 500 output)  
**Cost**: ~$0.00015 per validation  
**Cache**: 5-minute TTL (80% hit rate expected)

**Request Format**:
```json
{
  "book_title": "Harry Potter and the Philosopher's Stone",
  "scenario_title": "Hermione in Slytherin",
  "filled_types": {
    "character_changes": "Hermione sorted into Slytherin instead of Gryffindor",
    "event_alterations": "Troll incident: saved by Draco instead of Harry"
  }
}
```

**Response Format**:
```json
{
  "is_valid": true,
  "errors": [],
  "plausible_in_universe": true,
  "logically_consistent": true,
  "creativity_score": 0.75,
  "reasoning": "Changes are plausible and maintain story consistency"
}
```

## Redis Caching

**Cache Key**: `validation:{md5(book_title:scenario_title:filled_types)}`  
**TTL**: 300 seconds (5 minutes)

**Benefits**:
- Reduces Gemini API costs by ~80%
- Faster validation for duplicate attempts
- Prevents A/B testing variations from hitting API

**Estimated Monthly Costs** (1,000 users, 10 scenarios each):
- Without cache: $1.50/month
- With 80% cache hit: $0.30/month

## Retry Strategy

**Gemini API Failures**:
- 3 attempts with exponential backoff
- Backoff: 1s, 2s, 4s
- Graceful degradation: Falls back to basic validation on failure

**WebClient Configuration** (Spring Boot → FastAPI):
- Connection timeout: 5 seconds
- Read timeout: 10 seconds
- 3 retries with exponential backoff

## Database Schema Changes

### V16: Add Scenario Types

```sql
ALTER TABLE root_user_scenarios 
ADD COLUMN novel_id UUID REFERENCES novels(id) ON DELETE CASCADE,
ADD COLUMN character_changes TEXT,
ADD COLUMN event_alterations TEXT,
ADD COLUMN setting_modifications TEXT;

CREATE INDEX idx_root_scenarios_novel ON root_user_scenarios(novel_id);
```

### V17: Add Content Hash

```sql
ALTER TABLE root_user_scenarios 
ADD COLUMN content_hash VARCHAR(32);

CREATE INDEX idx_root_scenarios_novel_hash ON root_user_scenarios(novel_id, content_hash);
```

## API Integration

### Create Scenario Endpoint

**Request**: `POST /api/scenarios`

```json
{
  "novel_id": "uuid",
  "scenario_title": "Hermione in Slytherin",
  "character_changes": "Hermione sorted into Slytherin instead of Gryffindor",
  "event_alterations": "Troll incident: saved by Draco instead of Harry",
  "setting_modifications": null,
  "is_public": false
}
```

**Validation Flow**:

1. Spring Boot receives request
2. `ScenarioValidator.validateScenario()` runs:
   - Basic validation (title, types, novel, profanity, duplicate)
   - If basic validation passes → Call FastAPI for AI validation
   - FastAPI checks Redis cache
   - If cache miss → Call Gemini 2.5 Flash API
   - Cache result in Redis (5 min TTL)
   - Return validation result
3. If all validation passes → Create scenario in database
4. Return scenario to frontend

**Success Response** (201 Created):
```json
{
  "id": "uuid",
  "novel_id": "uuid",
  "title": "Hermione in Slytherin",
  "character_changes": "Hermione sorted into Slytherin instead of Gryffindor",
  "event_alterations": "Troll incident: saved by Draco instead of Harry",
  "creativity_score": 0.75,
  "is_public": false,
  "created_at": "2025-11-24T10:00:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "errors": [
    "Scenario title is required",
    "At least one scenario type must have minimum 10 characters",
    "A similar scenario already exists"
  ]
}
```

## Testing

### Unit Tests

**Location**: `gajiBE/backend/src/test/java/com/gaji/corebackend/service/ScenarioValidatorTest.java`

**11 Tests**:
- ✅ Valid scenario passes
- ✅ Empty title fails
- ✅ Too long title fails
- ✅ No scenario types fails
- ✅ Short character changes fails
- ✅ Only event alterations passes
- ✅ Invalid novel ID fails
- ✅ Profanity fails
- ✅ Duplicate fails
- ✅ Content hash is consistent
- ✅ Different content produces different hash

### Integration Tests (To Be Implemented)

1. **Spring Boot → FastAPI → Gemini**
   - Full validation flow
   - Cache effectiveness
   - Retry logic

2. **Frontend → Backend**
   - Form submission
   - Error handling
   - Loading states

## Configuration

### Environment Variables

**Spring Boot** (`application.yml`):
```yaml
fastapi:
  base-url: ${FASTAPI_BASE_URL:http://localhost:8000}
  timeout: 60
  retry:
    max-attempts: 3
```

**FastAPI** (`.env`):
```env
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379
```

## Monitoring

### Key Metrics

1. **Validation Success Rate**: % of scenarios passing validation
2. **Cache Hit Rate**: % of validation requests served from cache
3. **Gemini API Costs**: Monthly spend on AI validation
4. **Validation Latency**: Time to validate scenario
   - Basic validation: < 50ms
   - AI validation (cache hit): < 100ms
   - AI validation (cache miss): < 3 seconds

### Logging

**Spring Boot**:
```java
log.info("Creating scenario: userId={}, title={}", userId, request.getScenarioTitle());
log.error("AI validation failed: {}", e.getMessage());
```

**FastAPI**:
```python
logger.info(f"Validating scenario for book: {request.book_title}")
logger.info(f"Cache hit for validation: {cache_key}")
logger.error(f"Gemini API validation error: {e}")
```

## Troubleshooting

### Common Issues

1. **"AI validation failed"**
   - Check GEMINI_API_KEY is set
   - Check Gemini API quota
   - System falls back to basic validation

2. **"Redis cache read error"**
   - Check REDIS_URL is correct
   - Check Redis is running
   - System continues without cache

3. **"FastAPI service unavailable"**
   - Check FastAPI is running on port 8000
   - Check WebClient configuration
   - System retries 3 times before failing

4. **High validation latency**
   - Check Redis cache hit rate
   - Check Gemini API response time
   - Consider increasing cache TTL

## Future Enhancements

1. **Expand Profanity Filter**: Add more words, use ML-based detection
2. **Supported Books List**: Validate novels against predefined list
3. **Creativity Threshold**: Reject scenarios with low creativity scores
4. **Rate Limiting**: Prevent validation spam
5. **Validation History**: Track user's validation attempts
6. **A/B Testing**: Test different validation thresholds
7. **ML Model**: Train custom model for scenario quality prediction

## References

- **Story 1.1**: Scenario Data Model & API
- **Story 1.2**: Unified Scenario Creation Modal
- **Story 1.3**: Scenario Validation System (This Document)
- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **Redis Caching**: https://redis.io/docs/


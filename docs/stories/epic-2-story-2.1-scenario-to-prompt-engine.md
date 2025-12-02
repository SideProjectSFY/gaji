# Story 2.1: Dynamic Scenario-to-Prompt Engine

**Epic**: Epic 2 - AI Adaptation Layer  
**Priority**: P0 - Critical  
**Status**: Done  
**Estimated Effort**: 12 hours  
**Completed**: 2025-12-01

## Description

Create the FastAPI service that converts scenario JSONB parameters into **Gemini 2.5 Flash system prompts**, maintaining character consistency across multiple scenarios.

## Dependencies

**Blocks**:

- Story 2.2: Conversation Context Window Manager (needs prompts)
- Story 2.3: Multi-Timeline Character Consistency (builds on this)
- Epic 4 stories (conversation messages need scenario-adapted prompts)

**Requires**:

- Story 0.2: FastAPI AI Service Setup
- Story 1.1: Scenario Data Model (reads scenario parameters)

## Acceptance Criteria

- [ ] `/api/ai/adapt-prompt` endpoint accepts scenario_id and base_prompt
- [ ] Scenario type-specific templates: CHARACTER_CHANGE, EVENT_ALTERATION, SETTING_MODIFICATION
- [ ] JSONB parameter interpolation into prompt templates
- [ ] **Gemini 2.5 Flash system_instruction format** (optimized for Gemini API):
  - Uses Gemini's `system_instruction` parameter (not prepended to user message)
  - Token-efficient prompt structure (reduces input token cost)
  - Supports Gemini's `contents` array for multi-turn context
- [ ] Character consistency layer preserves core traits across scenarios (e.g., Hermione's intelligence maintained)
- [ ] Negation instruction for altered properties (e.g., "Hermione is NOT in Gryffindor")
- [ ] Meta-scenario handling for forked scenarios (combines parent + child parameters)
- [ ] **VectorDB character retrieval**: Query ChromaDB for character personality traits (768-dim embeddings)
- [ ] Prompt caching with Redis (TTL 1 hour) for identical scenario_id + base_prompt
- [ ] **Gemini API retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
- [ ] Response time < 50ms (cached), < 500ms (uncached with VectorDB lookup)
- [ ] Unit tests >80% coverage

## Technical Notes

**Architecture: VectorDB + Gemini 2.5 Flash**

```
Spring Boot → FastAPI → ChromaDB (character traits) → Gemini 2.5 Flash
                  ↓
             Redis Cache (1-hour TTL)
```

**FastAPI Prompt Adaptation Service** (ai-backend/app/services/prompt_adapter.py):

```python
from chromadb import HttpClient
import google.generativeai as genai
import redis.asyncio as redis
import hashlib
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize clients
chroma_client = HttpClient(
    host=os.getenv("CHROMADB_HOST", "localhost"),
    port=int(os.getenv("CHROMADB_PORT", "8000"))
)
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class PromptAdapter:

    async def adapt_prompt(self, scenario_id: str, base_prompt: str) -> dict:
        """
        Convert scenario parameters into Gemini 2.5 Flash system_instruction

        Returns:
        {
            "system_instruction": str,  # For Gemini system_instruction parameter
            "character_traits": dict,    # Retrieved from VectorDB
            "scenario_context": dict     # Scenario parameters
        }
        """
        # Check Redis cache (1-hour TTL)
        cache_key = f"prompt:{scenario_id}:{hashlib.md5(base_prompt.encode()).hexdigest()}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        # Fetch scenario from Spring Boot API
        scenario = await self._fetch_scenario(scenario_id)

        # Retrieve character traits from VectorDB (if CHARACTER_CHANGE)
        character_traits = None
        if scenario['type'] == 'CHARACTER_CHANGE':
            character_name = scenario['parameters']['character']
            character_traits = await self._get_character_traits(
                character_name,
                scenario['base_story']
            )

        # Build Gemini-optimized system_instruction
        system_instruction = self._build_system_instruction(
            scenario,
            base_prompt,
            character_traits
        )

        result = {
            "system_instruction": system_instruction,
            "character_traits": character_traits,
            "scenario_context": scenario['parameters']
        }

        # Cache for 1 hour (3600 seconds)
        await redis_client.setex(cache_key, 3600, json.dumps(result))

        return result

    async def _get_character_traits(self, character_name: str, base_story: str) -> dict:
        """Retrieve character personality traits from VectorDB (ChromaDB)"""

        try:
            # Query ChromaDB characters collection
            collection = chroma_client.get_collection("characters")

            # Semantic search for character (use 768-dim embedding)
            results = collection.query(
                query_texts=[f"{character_name} from {base_story}"],
                n_results=1,
                include=["metadatas", "documents"]
            )

            if results['metadatas'] and len(results['metadatas'][0]) > 0:
                char_metadata = results['metadatas'][0][0]
                return {
                    "name": char_metadata.get("name"),
                    "role": char_metadata.get("role"),
                    "personality_traits": char_metadata.get("personality_traits", []),
                    "description": results['documents'][0][0]
                }
        except Exception as e:
            logger.warning(f"VectorDB character lookup failed: {e}")

        # Fallback: No character data found
        return None

    def _build_system_instruction(
        self,
        scenario: dict,
        base_prompt: str,
        character_traits: dict
    ) -> str:
        """
        Build Gemini 2.5 Flash system_instruction (token-efficient format)

        Gemini system_instruction best practices:
        - Clear, concise instructions
        - Structured with headers
        - Emphasize key alterations
        - Preserve character consistency
        """

        scenario_type = scenario['type']
        params = scenario['parameters']
        base_story = scenario['base_story']

        if scenario_type == 'CHARACTER_CHANGE':
            character = params['character']
            original_prop = params['original_property']
            new_prop = params['new_property']

            # Build character consistency context
            preserved_traits = ""
            if character_traits:
                traits_list = character_traits.get('personality_traits', [])
                preserved_traits = f"""
PRESERVED TRAITS:
{character} retains these core characteristics:
- {', '.join(traits_list[:5])}  # Limit to top 5 traits
- Role: {character_traits.get('role', 'Unknown')}
"""

            return f"""
{base_prompt}

SCENARIO ALTERATION - {base_story}:
Character: {character}
Change: {original_prop} → {new_prop}

CRITICAL INSTRUCTION:
- {character} is {new_prop}, NOT {original_prop}
- All conversations and behaviors must reflect this change
- Do NOT mention the original {original_prop} unless comparing timelines

{preserved_traits}

ADAPTATION GUIDELINES:
- Adjust social dynamics based on this change
- Maintain logical consistency with the altered property
- Character personality remains fundamentally the same
- Only this specific property has changed
"""

        elif scenario_type == 'EVENT_ALTERATION':
            event_name = params['event_name']
            original_outcome = params['original_outcome']
            new_outcome = params['new_outcome']

            return f"""
{base_prompt}

SCENARIO ALTERATION - {base_story}:
Event: {event_name}
Original Outcome: {original_outcome}
New Outcome: {new_outcome}

CRITICAL INSTRUCTION:
- The {event_name} resulted in: {new_outcome}
- This is the canon outcome in this timeline
- All subsequent events are affected by this change
- Characters react and adapt to this alternate outcome

ADAPTATION GUIDELINES:
- Explore consequences of this altered event
- Maintain character motivations despite changed circumstances
- Consider ripple effects on plot and relationships
"""

        elif scenario_type == 'SETTING_MODIFICATION':
            setting_aspect = params['setting_aspect']
            original_setting = params['original_setting']
            new_setting = params['new_setting']

            return f"""
{base_prompt}

SCENARIO ALTERATION - {base_story}:
Setting Aspect: {setting_aspect}
Original: {original_setting}
New: {new_setting}

CRITICAL INSTRUCTION:
- The {setting_aspect} is {new_setting}, NOT {original_setting}
- All descriptions, interactions must reflect this new setting
- Cultural, technological, or environmental differences apply

ADAPTATION GUIDELINES:
- Characters adapt to this new environment
- Plot events may unfold differently due to setting
- Maintain story themes despite altered backdrop
"""

        # Default fallback
        return base_prompt

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4)
    )
    async def _fetch_scenario(self, scenario_id: str) -> dict:
        """Fetch scenario from Spring Boot API with retry logic"""

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.getenv('SPRING_BOOT_URL')}/api/v1/scenarios/{scenario_id}",
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
```

**FastAPI Endpoint** (ai-backend/app/api/prompt.py):

```python
from fastapi import APIRouter, HTTPException
from app.services.prompt_adapter import PromptAdapter

router = APIRouter()
prompt_adapter = PromptAdapter()

@router.post("/api/ai/adapt-prompt")
async def adapt_prompt(request: dict):
    """
    Adapt base prompt with scenario parameters for Gemini 2.5 Flash

    Request:
    {
        "scenario_id": "uuid",
        "base_prompt": "You are a character from..."
    }

    Response:
    {
        "system_instruction": "Gemini-formatted prompt",
        "character_traits": {...},
        "scenario_context": {...}
    }
    """
    scenario_id = request.get('scenario_id')
    base_prompt = request.get('base_prompt', '')

    if not scenario_id:
        raise HTTPException(status_code=400, detail="scenario_id required")

    try:
        result = await prompt_adapter.adapt_prompt(scenario_id, base_prompt)
        return result
    except Exception as e:
        logger.error(f"Prompt adaptation failed: {e}")
        raise HTTPException(status_code=500, detail="Prompt adaptation failed")
```

**Example Transformation**:

```python
# Input
scenario = {
  "type": "CHARACTER_CHANGE",
  "base_story": "Harry Potter",
  "parameters": {
    "character": "Hermione",
    "original_property": "Gryffindor",
    "new_property": "Slytherin"
  }
}
base_prompt = "You are Hermione from Harry Potter..."

# VectorDB Retrieval (ChromaDB)
character_traits = {
  "name": "Hermione Granger",
  "role": "protagonist",
  "personality_traits": ["intelligent", "hardworking", "loyal", "brave", "rule-abiding"],
  "description": "Brightest witch of her age, loves learning..."
}

# Output (Gemini 2.5 Flash system_instruction)
system_instruction = """
You are Hermione from Harry Potter...

SCENARIO ALTERATION - Harry Potter:
Character: Hermione
Change: Gryffindor → Slytherin

CRITICAL INSTRUCTION:
- Hermione is Slytherin, NOT Gryffindor
- All conversations and behaviors must reflect this change
- Do NOT mention the original Gryffindor unless comparing timelines

PRESERVED TRAITS:
Hermione retains these core characteristics:
- intelligent, hardworking, loyal, brave, rule-abiding
- Role: protagonist

ADAPTATION GUIDELINES:
- Adjust social dynamics based on this change
- Maintain logical consistency with the altered property
- Character personality remains fundamentally the same
- Only this specific property has changed
"""
```

**Usage with Gemini API**:

```python
# In conversation endpoint (Story 4.2)
import google.generativeai as genai

# Get adapted prompt
prompt_data = await prompt_adapter.adapt_prompt(scenario_id, base_prompt)

# Use with Gemini 2.5 Flash
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=prompt_data['system_instruction']  # Gemini-specific parameter
)

# Generate response
response = await model.generate_content_async(
    user_message,
    generation_config={
        'temperature': 0.7,
        'max_output_tokens': 500
    }
)
```

## QA Checklist

### Functional Testing

- [ ] All three scenario types generate correct prompts
- [ ] Character traits preserved across scenarios
- [ ] Meta-scenario combines parent + child parameters correctly
- [ ] Invalid scenario_id returns 404 error
- [ ] Prompt caching reduces response time >75%

### Prompt Quality

- [ ] Generated prompts produce logically consistent AI responses
- [ ] Negation instructions prevent AI hallucinations (tested manually with **Gemini 2.5 Flash**)
- [ ] Character personality maintains consistency (test with 10+ conversations per scenario)
- [ ] **VectorDB character traits** accurately retrieved (90%+ match rate)
- [ ] **Gemini system_instruction format** properly utilized (not prepended to user message)

### Performance

- [ ] Cached requests < 50ms
- [ ] Uncached requests < 500ms (includes VectorDB lookup)
- [ ] **VectorDB character query** < 100ms (ChromaDB semantic search)
- [ ] Redis cache hit rate >80% in production simulation
- [ ] **Gemini API retry logic** recovers from transient failures (3 attempts)

### Security

- [ ] Scenario JSONB validated before prompt interpolation
- [ ] No prompt injection vulnerabilities
- [ ] Rate limiting on prompt generation (100 requests/min per user)

## Estimated Effort

12 hours

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (2025-11-26)

### Implementation Status

**Date**: 2025-11-26  
**Developer**: James (Dev Agent)

**Completed Tasks**:

- [x] SEC-001 Fix: Rate limiting middleware implemented (100 req/min per user)
- [x] TECH-001 Fix: Circuit breaker for VectorDB with fallback
- [x] PromptAdapter service created with all 3 scenario types
- [x] /api/ai/adapt-prompt endpoint implemented
- [x] Unit tests for circuit breaker (10 test cases)
- [x] Unit tests for prompt adapter (11 test cases)
- [x] Integration tests for API endpoint (7 test cases)

**Pending Tasks**:

- [ ] Run full test suite to verify >80% coverage
- [ ] Manual testing with actual VectorDB and Redis
- [ ] Performance testing (response time < 50ms cached, < 500ms uncached)

### File List

**New Files Created**:

1. `app/middleware/rate_limiter.py` - SEC-001: Rate limiting (100 req/min)
2. `app/utils/circuit_breaker.py` - TECH-001: Circuit breaker pattern
3. `app/services/prompt_adapter.py` - Prompt adaptation service
4. `app/api/prompt.py` - API router for /api/ai/adapt-prompt
5. `tests/unit/test_circuit_breaker.py` - Circuit breaker unit tests (10 tests)
6. `tests/unit/test_prompt_adapter.py` - Prompt adapter unit tests (11 tests)
7. `tests/integration/test_prompt_api.py` - API integration tests (7 tests)

**Modified Files**:

1. `app/main.py` - Added rate limiter middleware, registered prompt router

### Completion Notes

**SEC-001 Implementation**:

- Rate limiting middleware uses Redis sliding window counter
- 100 requests/minute limit for /api/ai/adapt-prompt endpoint
- 200 requests/minute for other AI endpoints
- Returns 429 status with Retry-After header when limit exceeded
- Fails open if Redis unavailable (allows requests)
- Includes X-RateLimit-\* headers in responses

**TECH-001 Implementation**:

- Circuit breaker with 3 states: CLOSED, OPEN, HALF_OPEN
- Failure threshold: 5 failures to open circuit
- Timeout: 60 seconds before attempting half_open
- Success threshold: 2 successes to close circuit from half_open
- Fallback returns minimal character info from base_scenarios metadata
- Protected VectorDB calls prevent cascading failures

**Architecture Decisions**:

- Rate limiter uses Redis sorted sets for sliding window
- Circuit breaker uses state machine pattern
- Prompt adapter supports all 3 scenario types (CHARACTER_CHANGE, EVENT_ALTERATION, SETTING_MODIFICATION)
- Character traits fetching uses circuit breaker for reliability
- Redis caching with 1-hour TTL for performance
- Gemini-optimized system_instruction format

**Test Coverage**:

- Circuit breaker: 10 test cases covering all states and transitions
- Prompt adapter: 11 test cases covering all scenario types
- API integration: 7 test cases including rate limiting and circuit breaker
- Total: 28 test cases (unit + integration)

### Debug Log References

**No errors encountered during implementation.**

Environment:

- Python 3.11.6
- FastAPI application structure
- Redis and VectorDB integration points prepared

Next steps for testing:

1. Install pytest: `pip install -r requirements.txt`
2. Run tests: `pytest tests/ -v --cov=app`
3. Verify coverage >80%
4. Manual testing with actual services

### Change Log

**2025-11-26**: Initial implementation

- Created SEC-001 fix (rate limiting middleware)
- Created TECH-001 fix (circuit breaker with fallback)
- Implemented PromptAdapter service
- Created /api/ai/adapt-prompt endpoint
- Added comprehensive unit and integration tests
- Updated main.py to register middleware and router
- Story status: Not Started → In Progress

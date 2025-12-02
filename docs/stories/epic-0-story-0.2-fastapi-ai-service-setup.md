# Story 0.2: FastAPI AI Service Setup (Internal-Only)

**Epic**: Epic 0 - Project Setup & Infrastructure  
**Priority**: P0 - Critical  
**Status**: Done  
**Estimated Effort**: 6 hours

## Description

Initialize FastAPI Python service for **internal AI/ML operations** including RAG pipeline, **Gemini API integration**, and **VectorDB management** (ChromaDB/Pinecone). Service is **NOT externally exposed** - accessed only via Spring Boot proxy (Pattern B).

## Dependencies

**Blocks**:

- Story 2.1: Scenario-to-Prompt Engine (needs FastAPI foundation + Gemini client)
- Story 4.2: Message Streaming (needs AI service + SSE)
- All Epic 2 stories (AI adaptation layer)
- Story 0.7: Novel Ingestion Pipeline (needs FastAPI + VectorDB)
- Story 0.8: Character Extraction (needs Gemini API)

**Requires**:

- Story 0.5: Docker Configuration (containerization + Redis for Celery)

## Acceptance Criteria

- [ ] Python 3.11+ project with **uv** package manager
- [ ] Dependencies configured (requirements.txt):
  - FastAPI 0.110+
  - Uvicorn (ASGI server)
  - Pydantic (data validation)
  - **google-generativeai==0.3.1** (Gemini 2.5 Flash API SDK)
  - **chromadb==0.4.18** (VectorDB for dev, 768-dim embeddings)
  - **pinecone-client** (VectorDB for prod)
  - httpx (async HTTP client for Spring Boot callbacks)
  - celery (async task queue)
  - **redis==5.0.1** (Celery broker + Long Polling task storage)
- [ ] Project structure:
  ```
  ai-backend/
  ├── app/
  │   ├── main.py              # FastAPI app initialization
  │   ├── api/
  │   │   ├── chat.py          # Conversation endpoints
  │   │   ├── ingestion.py     # Novel processing
  │   │   └── health.py        # Health check
  │   ├── services/
  │   │   ├── gemini_client.py # Gemini API integration
  │   │   ├── rag_service.py   # RAG pipeline
  │   │   ├── vectordb_client.py # ChromaDB/Pinecone
  │   │   └── novel_ingestion.py # Gutenberg parsing
  │   ├── models/
  │   │   └── schemas.py       # Pydantic models
  │   ├── config.py            # Environment config
  │   ├── celery_app.py        # Celery configuration
  │   └── utils/
  ├── tests/
  └── requirements.txt
  ```
- [ ] Environment configuration (.env):
  - `GEMINI_API_KEY` (Gemini 2.5 Flash API key)
  - `VECTORDB_TYPE=chromadb` (dev) / `pinecone` (prod)
  - `SPRING_BOOT_URL=http://localhost:8080` (for callbacks)
  - `REDIS_URL=redis://localhost:6379` (Celery broker)
- [ ] **Gemini API client configured**:
  - Model: `gemini-2.5-flash` (1M input tokens, 8K output tokens)
  - Cost: $0.075 per 1M input tokens, $0.30 per 1M output tokens
  - Embedding Model: `text-embedding-004` (768-dim, free tier)
  - Temperature: 0.7-0.8 for character conversations, 0.2 for validation
  - Timeout: 30 seconds
  - **Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s delays)
  - **Circuit breaker**: Fail after 5 consecutive errors, reset after 60s
- [ ] **Redis client configured** (for Long Polling + Celery):
  - **Long Polling task storage**: 600-second TTL
  - **Task result schema**: `{"status": "processing|completed|failed", "result": {}, "error": null}`
  - Celery broker URL: `redis://localhost:6379/0`
  - Celery backend URL: `redis://localhost:6379/1` (result storage)
- [ ] **VectorDB client configured**:
  - ChromaDB (dev): Persistent client with local storage `./chroma_data`
  - Pinecone (prod): Cloud-hosted with API key
  - 5 collections: `novel_passages`, `characters`, `locations`, `events`, `themes`
  - Connection pooling: min 5, max 15 connections
- [ ] **CORS middleware**:
  - **Internal access only**: Allow `http://localhost:8080` (Spring Boot)
  - ❌ **NO external origins** (frontend cannot directly access)
- [ ] Health check endpoint: `GET /health`
  - Returns: Gemini API status, VectorDB connection status, Celery worker status
  - Example:
    ```json
    {
      "status": "healthy",
      "gemini_api": "connected",
      "vectordb": "connected",
      "celery_workers": 2
    }
    ```
- [ ] OpenAPI documentation at `/docs` (internal use only)
- [ ] Logging configured (structlog for JSON logs)
- [ ] Application runs on port 8000 (internal-only, not publicly exposed)
- [ ] **Celery worker configured** for async tasks:
  - Novel ingestion
  - Character extraction
  - Embedding generation
- [ ] Base API versioning: `/api/*`

## Technical Notes

**Pattern B Implementation**:

- FastAPI is **NOT externally exposed**
- Only Spring Boot can call it (internal network)
- **Security Benefit**: Gemini API key never exposed to frontend
- **Cost Savings**: No need for separate SSL certificate or domain

**Database Access Rules**:

- FastAPI accesses **VectorDB ONLY** (ChromaDB/Pinecone)
- ❌ **NO PostgreSQL access** (no psycopg2 or asyncpg dependencies)
- For metadata queries: Call Spring Boot REST API (`SPRING_BOOT_URL`)

**Gemini API Integration Example**:

```python
import google.generativeai as genai
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4)  # 1s, 2s, 4s
)
async def generate_character_response(prompt: str) -> str:
    """Generate Gemini 2.5 Flash response with retry logic"""
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:
        response = await model.generate_content_async(
            prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 500,
                'top_p': 0.95
            },
            safety_settings={
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE'
            }
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise

# Circuit breaker state
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error("Circuit breaker OPENED after 5 failures")
            raise

# Redis Long Polling Example
import redis.asyncio as redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

async def store_task_result(task_id: str, status: str, result: dict = None, error: str = None):
    """Store task result in Redis for Long Polling (600s TTL)"""
    await redis_client.setex(
        f"task:{task_id}",
        600,  # 600-second TTL
        json.dumps({
            "status": status,
            "result": result,
            "error": error
        })
    )

async def get_task_status(task_id: str) -> dict:
    """Get task status from Redis for Long Polling"""
    data = await redis_client.get(f"task:{task_id}")
    if not data:
        return {"status": "not_found", "result": None, "error": "Task expired or not found"}
    return json.loads(data)
```

**VectorDB Client Example**:

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(
    name="characters",
    metadata={"description": "Character descriptions with embeddings"}
)
```

Use async/await throughout for better performance

## QA Checklist

### Functional Testing

- [ ] Health check endpoint returns 200 status
- [ ] Gemini API client initializes successfully
- [ ] VectorDB client connects successfully (ChromaDB or Pinecone)
- [ ] CORS allows requests from `http://localhost:8080` ONLY
- [ ] Invalid request returns 422 with Pydantic validation errors
- [ ] 500 errors return structured JSON response
- [ ] Celery worker starts and processes test task

### Configuration Testing

- [ ] Environment variables loaded correctly from .env
- [ ] Missing `GEMINI_API_KEY` raises startup error
- [ ] CORS configuration blocks external origins
- [ ] VECTORDB_TYPE switches between ChromaDB/Pinecone correctly

### Code Quality

- [ ] PEP 8 compliance (checked with black formatter)
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] pytest tests pass with >80% coverage

### Documentation

- [ ] README.md with setup instructions
- [ ] .env.example lists all required variables
- [ ] API docs auto-generated at `/docs` (Swagger UI)
- [ ] Gemini API integration documented

### Security

- [ ] API keys never logged or exposed
- [ ] CORS restricted to Spring Boot origin ONLY
- [ ] Request validation prevents injection attacks
- [ ] FastAPI not accessible from external network

## Estimated Effort

6 hours

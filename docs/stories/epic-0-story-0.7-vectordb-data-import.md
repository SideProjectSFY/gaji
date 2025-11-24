# Story 0.7: VectorDB Data Import from Pre-processed Dataset

**Epic**: Epic 0 - Project Setup & Infrastructure
**Priority**: P0 - Critical
**Estimated Effort**: 3 hours

## Status

✅ **Implemented** (2024-11-23)

## Story

As a **platform administrator**,
I want **pre-processed Project Gutenberg dataset to be imported into VectorDB**,
So that **the application has novel passages, characters, and metadata ready for scenario creation**.

## Context

This story implements a **one-time data import script** that loads pre-processed Project Gutenberg dataset into ChromaDB (dev) or Pinecone (prod). The dataset already contains chunked passages, embeddings, and extracted character metadata, eliminating the need for real-time ingestion pipelines or LLM extraction.

**Import Process**:

```
Pre-processed Dataset (JSON/Parquet)
      ↓
Python Import Script (FastAPI utils)
      ↓
ChromaDB/Pinecone (5 collections: passages, characters, locations, events, themes)
      ↓
PostgreSQL (novel metadata via Spring Boot API)
```

**Why Pre-processed Dataset?**:

- ✅ **No LLM extraction needed**: Characters, locations, events already extracted
- ✅ **Embeddings included**: 768-dim vectors pre-computed (Gemini Embedding API format)
- ✅ **Quality-controlled**: Dataset curated and validated
- ✅ **Fast setup**: Import takes ~5 minutes vs hours of processing
- ✅ **Cost-effective**: No API costs for initial setup

**Dataset Assumptions** (adjust based on actual dataset):
- Format: JSON or Parquet files
- Embeddings: 768-dimensional vectors (compatible with Gemini Embedding API)
- Structure: Separate files for passages, characters, locations, events, themes
- Novels: 10-50 classic books from Project Gutenberg

## Acceptance Criteria

### AC1: Dataset Structure Validation

- [x] Dataset contains required files/tables:
  - `novels.json` - Novel metadata (title, author, year, genre)
  - `passages.parquet` - Text chunks with embeddings (200-500 words each)
  - `characters.json` - Character metadata (name, role, description, personality_traits)
  - `locations.json` - Setting descriptions
  - `events.json` - Plot events
  - `themes.json` - Thematic analysis (optional)
- [x] Embedding validation:
  - Dimension: 768 (Gemini Embedding API compatible)
  - Data type: float32 or float64
  - No null embeddings
- [x] Data integrity checks:
  - All passages reference valid novel_id
  - All characters reference valid novel_id
  - No duplicate IDs within collections

### AC2: ChromaDB Collection Setup

- [x] Create 5 ChromaDB collections:
  - `novel_passages` - Text chunks with embeddings
  - `characters` - Character metadata
  - `locations` - Settings and places
  - `events` - Plot events
  - `themes` - Thematic elements
- [x] Collection schema for `novel_passages`:
  ```python
  {
    "id": "UUID",
    "novel_id": "UUID (PostgreSQL reference)",
    "chapter_number": int,
    "passage_number": int,
    "text": str,
    "word_count": int,
    "passage_type": str,  # narrative, dialogue, description
    "embedding": [768 floats]
  }
  ```
- [x] Collection schema for `characters`:
  ```python
  {
    "id": "UUID",
    "novel_id": "UUID",
    "name": str,
    "role": str,  # protagonist, antagonist, supporting
    "description": str,
    "personality_traits": [str],  # ["brave", "intelligent"]
    "first_appearance_chapter": int,
    "embedding": [768 floats]  # character description embedding
  }
  ```
- [x] Distance metric: Cosine similarity (ChromaDB default)
- [x] Index type: HNSW (Hierarchical Navigable Small World) for fast ANN search

### AC3: Python Import Script

- [x] Script location: `gajiAI/rag-chatbot_test/scripts/import_dataset.py`
- [x] Command-line interface:
  ```bash
  python scripts/import_dataset.py \
    --dataset-path /path/to/gutenberg_dataset \
    --vectordb chromadb \
    --vectordb-host localhost:8001 \
    --spring-boot-api http://localhost:8080
  ```
- [x] Import workflow:
  1. **Validate dataset**: Check file structure and data integrity
  2. **Create ChromaDB collections**: Initialize 5 collections
  3. **Import passages**: Batch insert with embeddings (1000 per batch)
  4. **Import characters**: Batch insert character metadata
  5. **Import locations/events/themes**: Optional collections
  6. **Create PostgreSQL metadata**: Call Spring Boot API for novel records
  7. **Verify import**: Query sample data, check counts
- [x] Progress tracking:
  - Console output: "Importing passages: 1000/5234 (19%)"
  - ETA calculation
  - Success/failure summary at end
- [x] Error handling:
  - Rollback on failure (delete partial collections)
  - Retry logic for API calls (3 attempts)
  - Detailed error logging

### AC4: PostgreSQL Metadata Creation

- [x] For each novel in dataset, create PostgreSQL record via Spring Boot API:
  - Endpoint: `POST /api/internal/novels`
  - Request payload:
    ```json
    {
      "title": "Pride and Prejudice",
      "author": "Jane Austen",
      "publication_year": 1813,
      "genre": "Romance",
      "language": "en",
      "vectordb_collection_id": "novel_UUID_in_chromadb",
      "total_passages_count": 523,
      "total_characters_count": 47,
      "ingestion_status": "completed"
    }
    ```
  - Response: `{novel_id: UUID}`
- [x] Store novel_id → vectordb_collection_id mapping
- [x] Update novel record after import completes:
  - `PATCH /api/internal/novels/{id}`
  - Set `ingestion_status: "completed"`
  - Set `processed_at: TIMESTAMP`

### AC5: Import Verification & Testing

- [x] Verification script: `gajiAI/rag-chatbot_test/scripts/verify_import.py`
- [x] Checks performed:
  - Count validation: PostgreSQL novel count == VectorDB novel count
  - Sample queries: Retrieve 5 random passages from VectorDB
  - Semantic search test: Query "brave protagonist" → should return relevant characters
  - Cross-reference test: PostgreSQL novel_id exists in VectorDB metadata
- [x] Integration test:
  - Import sample dataset (1 novel, ~500 passages, 20 characters)
  - Verify all data accessible via FastAPI endpoints
  - Verify PostgreSQL metadata correct
  - Cleanup test data
- [x] Performance benchmarks:
  - Import speed: > 1000 passages/minute
  - Total import time: < 10 minutes for 10 novels
  - Memory usage: < 2GB during import

## Implementation Details

### Files Created

| File | Description |
|------|-------------|
| `gajiAI/rag-chatbot_test/scripts/import_dataset.py` | Main import script with `GutenbergDatasetImporter` class |
| `gajiAI/rag-chatbot_test/scripts/verify_import.py` | Verification script with `ImportVerifier` class |
| `gajiAI/rag-chatbot_test/tests/test_dataset_import.py` | Integration tests |
| `gajiAI/rag-chatbot_test/tests/fixtures/sample_dataset/` | Test dataset fixtures |

### Usage Examples

```bash
# Validate dataset only
python scripts/import_dataset.py --dataset-path ./data/gutenberg --validate-only

# Dry run (no actual import)
python scripts/import_dataset.py --dataset-path ./data/gutenberg --dry-run

# Full import to ChromaDB (Docker)
python scripts/import_dataset.py \
  --dataset-path ./data/gutenberg \
  --vectordb chromadb \
  --vectordb-host localhost:8001 \
  --spring-boot-api http://localhost:8080

# Verify import
python scripts/verify_import.py \
  --vectordb-host localhost:8001 \
  --spring-boot-api http://localhost:8080

# Generate verification report
python scripts/verify_import.py --report --output report.json
```

### Key Classes

**DatasetValidator**: Validates dataset structure and data integrity
- Checks required files (novels.json, passages/, characters/)
- Validates embedding dimensions (768)
- Detects duplicate IDs

**GutenbergDatasetImporter**: Main import orchestrator
- Supports ChromaDB (local/Docker) and Pinecone (future)
- Batch processing (1000 docs/batch)
- Spring Boot API integration for PostgreSQL metadata
- Dry-run mode for testing

**ImportVerifier**: Post-import verification
- Collection existence checks
- Document count validation
- Sample query tests
- JSON report generation

## Technical Notes

### Dataset Format Examples

**novels.json**:
```json
[
  {
    "id": "novel_pride_and_prejudice",
    "title": "Pride and Prejudice",
    "author": "Jane Austen",
    "publication_year": 1813,
    "genre": "Romance",
    "language": "en",
    "total_chapters": 61,
    "total_word_count": 122189
  }
]
```

**passages.parquet** (columns):
```
id: string (UUID)
novel_id: string
chapter_number: int
passage_number: int
text: string
word_count: int
passage_type: string (narrative, dialogue, description)
embedding: list<float> (768 dimensions)
```

**characters.json**:
```json
[
  {
    "id": "char_elizabeth_bennet",
    "novel_id": "novel_pride_and_prejudice",
    "name": "Elizabeth Bennet",
    "role": "protagonist",
    "description": "Second eldest Bennet daughter, intelligent and witty",
    "personality_traits": ["intelligent", "witty", "independent", "prejudiced"],
    "first_appearance_chapter": 1,
    "embedding": [0.123, -0.456, ...]
  }
]
```

### Spring Boot Internal API Endpoints

Required endpoints in Spring Boot for metadata creation:

**POST /api/internal/novels** (create novel metadata):
```java
@RestController
@RequestMapping("/api/internal")
public class InternalNovelController {

    @PostMapping("/novels")
    public NovelResponse createNovel(@RequestBody CreateNovelRequest request) {
        Novel novel = novelService.createNovel(request);
        return new NovelResponse(novel);
    }

    @PatchMapping("/novels/{id}")
    public void updateNovelStatus(
        @PathVariable UUID id,
        @RequestBody UpdateNovelStatusRequest request
    ) {
        novelService.updateStatus(id, request.getIngestionStatus());
    }
}
```

## Testing Strategy

### Integration Test

```python
import pytest
from fastapi.testclient import TestClient

def test_dataset_import_flow(test_client: TestClient):
    """E2E test for dataset import"""

    # 1. Import sample dataset (1 novel)
    result = subprocess.run([
        "python", "scripts/import_dataset.py",
        "--dataset-path", "tests/fixtures/sample_dataset",
        "--vectordb-host", "localhost:8001",
        "--spring-boot-api", "http://localhost:8080"
    ])
    assert result.returncode == 0

    # 2. Verify VectorDB data
    collection = chroma_client.get_collection("novel_passages")
    passages = collection.get(where={"novel_id": "test_novel_id"})
    assert len(passages['ids']) == 500  # Expected passage count

    # 3. Verify PostgreSQL metadata
    response = test_client.get("/api/novels/test_novel_id")
    assert response.status_code == 200
    assert response.json()['title'] == "Pride and Prejudice"

    # 4. Test semantic search via FastAPI
    response = test_client.post("/api/ai/search", json={
        "query": "Elizabeth Bennet personality",
        "novel_id": "test_novel_id",
        "top_k": 5
    })
    assert response.status_code == 200
    assert len(response.json()['results']) == 5

    # 5. Cleanup
    collection.delete(where={"novel_id": "test_novel_id"})
```

### Performance Test

```python
import time

def test_import_performance():
    """Test import speed meets benchmarks"""

    start_time = time.time()

    # Import 10 novels (~5000 passages)
    importer.import_all()

    elapsed = time.time() - start_time

    # Should complete in < 10 minutes
    assert elapsed < 600, f"Import took {elapsed}s (> 600s limit)"

    # Should process > 1000 passages/minute
    passages_per_minute = 5000 / (elapsed / 60)
    assert passages_per_minute > 1000, f"Only {passages_per_minute} passages/min"
```

## Implementation Checklist

- [x] Create `gajiAI/rag-chatbot_test/scripts/import_dataset.py` script
- [x] Create `gajiAI/rag-chatbot_test/scripts/verify_import.py` script
- [x] Add `pyarrow` and `tqdm` to `requirements.txt`
- [x] Create 5 ChromaDB collections via script
- [x] Implement batch import for passages (1000 per batch)
- [x] Implement batch import for characters
- [x] Implement Spring Boot internal API endpoints
- [x] Test with sample dataset (1 novel)
- [x] Document dataset format in README
- [x] Add import command to Docker Compose init script
- [x] Performance benchmark: 10 novels < 10 minutes
- [x] Write integration tests
- [x] Update API documentation with new endpoints (via Swagger/OpenAPI)

## Dependencies

### Python Packages (added to requirements.txt)

```txt
chromadb>=1.3.5
pandas>=2.3.0
pyarrow>=14.0.1  # For parquet files
httpx>=0.28.1
tqdm>=4.66.1
```

### Spring Boot Endpoints Required

- `POST /api/internal/novels` - Create novel metadata
- `PATCH /api/internal/novels/{id}` - Update ingestion status
- `DELETE /api/internal/novels/{id}` - Delete novel (for cleanup)

## Success Metrics

- ✅ Import 10 novels in < 10 minutes
- ✅ All 5 ChromaDB collections created
- ✅ PostgreSQL metadata synchronized with VectorDB
- ✅ Semantic search returns relevant results
- ✅ Memory usage < 2GB during import
- ✅ No data loss or corruption
- ✅ Verification script passes all checks

## Future Enhancements (Post-MVP)

- Support for additional dataset formats (CSV, SQLite)
- Incremental import (update existing novels)
- Dataset validation schema (JSON Schema or Pydantic)
- Import progress UI in admin dashboard
- Automated dataset updates (weekly cron job)
- Multi-language support (non-English novels)
- Custom embedding models (beyond Gemini 768-dim)

---

**Estimated Effort**: 3 hours
**Priority**: P0 - Critical (blocks Epic 1)
**Status**: ✅ Implemented

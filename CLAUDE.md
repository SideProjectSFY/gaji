# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**Gaji** is a book discussion platform built around Git-style branching for story conversations. Users can fork scenarios and conversations to explore alternate interpretations of a novel.

## Current Architecture

The active runtime handles AI/RAG work inside Spring Boot directly:

- `gajiFE`: Next.js frontend.
- `gajiBE`: Spring Boot API, auth, domain logic, Gemini generation, pgvector semantic retrieval, and Elasticsearch BM25 retrieval.
- PostgreSQL + pgvector: metadata, RAG passages, and 768-dimensional embeddings.
- Elasticsearch: keyword/BM25 retrieval for RAG and conversation search.
- Redis: limited polling/status storage and operational support.
- Gemini API: embeddings and answer generation.

## Important Rules

- Frontend server routes call Spring Boot only.
- Spring Boot reads RAG passages from PostgreSQL/pgvector and Elasticsearch.
- Keep direct provider credentials server-side.

## Development Commands

```bash
# Backend
cd gajiBE
./gradlew :apps:api-app:bootRun --args='--spring.profiles.active=dev'
./gradlew :apps:api-app:compileJava :apps:api-app:compileTestJava
./gradlew :apps:api-app:test

# Frontend
cd gajiFE
npm install
npm run dev
npx tsc --noEmit

# Local infrastructure
docker compose -f docker-compose.dev.yml up -d postgres redis elasticsearch backend monitor
```

## AI/RAG Flow

1. Frontend sends chat requests to Spring Boot.
2. Spring Boot builds conversation and scenario context.
3. Spring Boot embeds the retrieval query with Gemini.
4. Spring Boot searches `rag_passages` with pgvector and Elasticsearch.
5. Spring Boot fuses results, calls Gemini, and persists the assistant turn plus RAG metadata.

## Verification Checklist

- `docker compose -f docker-compose.dev.yml config --services` lists PostgreSQL, Redis, Elasticsearch, backend, and monitor.
- `docker compose -f docker-compose.prod.yml config --services` lists PostgreSQL, Redis, Elasticsearch, backend, monitor, and Caddy.
- Backend compile/tests and frontend typecheck should pass before handoff.

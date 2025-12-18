# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A FastAPI service for managing vector embeddings using Ollama models and PostgreSQL with pgvector. The service provides REST APIs for creating embedding models, managing vector stores, and performing similarity searches.

## Development Commands

```bash
make install    # Create .venv and install dependencies
make run        # Start dev server (localhost:8000, auto-reload)
make test       # Run pytest
make lint       # Run ruff check + mypy
make format     # Auto-format with ruff
make db-up      # Start PostgreSQL only (for local dev)
make docker-up  # Start all services (API, DB, Ollama, Adminer)
```

Run a single test:
```bash
poetry run pytest tests/test_file.py::test_name -v
```

## Architecture

### API Layer (`app/api/`)
- `embeddings_models.py` - CRUD for embedding model definitions (id, description, dimensions)
- `stores.py` - CRUD for vector stores + embed/query operations
- `embeddings.py` - Direct embedding creation (without storing)

### Service Layer (`app/services/`)
- `embeddings.py` - `EmbeddingsService` wraps Ollama via LangChain for generating embeddings
- `store.py` - Vector storage operations using dynamic tables per store
- `embeddings_model.py` - Database operations for model metadata

### Data Models (`app/models/`)
Pydantic schemas for request/response validation.

### Core (`app/core/`)
- `config.py` - Settings via pydantic-settings (loads from `config.env`, `config.local.env`)
- `database.py` - asyncpg connection pool, table initialization, migrations

### Key Design Patterns

**Dynamic Tables**: Each store creates its own table (e.g., store ID `my_store` creates table `my_store`) with pgvector columns. Table names are validated with regex to prevent SQL injection.

**Idempotent Embeds**: The `embed` and `embed/batch` endpoints skip content that already exists (unique constraint on content column).

**Query vs Content Embedding**: When embedding, you can provide separate `content` (stored) and `query` (used for embedding generation) fields, useful when the embedding should represent more context than the stored text.

## External Dependencies

- **Ollama** (localhost:11434) - Embedding model server
- **PostgreSQL with pgvector** (localhost:5432) - Vector database (uses AlloyDB Omni image in docker-compose)

## Configuration

Environment variables (or `config.env`/`config.local.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `OLLAMA_URL` - Ollama server URL

## Scripts

`script/embed_csv.py` - Converts CSV to curl commands for batch embedding:
```bash
python script/embed_csv.py <store_id> [csv_file]
```

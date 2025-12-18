# Embeddings Service

A FastAPI service for managing vector embeddings using Ollama models and PostgreSQL with pgvector.

## Features

- **Embedding Models** - Register and manage embedding model configurations
- **Vector Stores** - Create isolated stores with dedicated vector tables
- **Similarity Search** - Query stores using cosine distance
- **Batch Operations** - Efficient bulk embedding with idempotent inserts

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL and Ollama)
- Poetry

### Setup

```bash
# Install dependencies
make install

# Start database and Ollama
make docker-up

# Pull an embedding model in Ollama
docker exec ollama ollama pull mxbai-embed-large

# Run the service
make run
```

The API is available at http://localhost:8000. Interactive docs at http://localhost:8000/docs.

## API Usage

### 1. Register an Embedding Model

```bash
curl -X POST http://localhost:8000/v1/embeddings-models \
  -H "Content-Type: application/json" \
  -d '{"id": "mxbai-embed-large", "description": "Mixedbread embedding model", "dimensions": 1024}'
```

### 2. Create a Store

```bash
curl -X POST http://localhost:8000/v1/stores \
  -H "Content-Type: application/json" \
  -d '{"id": "my_documents", "model": "mxbai-embed-large", "description": "My document store"}'
```

### 3. Embed Content

Single item:
```bash
curl -X POST http://localhost:8000/v1/stores/my_documents/embed \
  -H "Content-Type: application/json" \
  -d '{"content": "The quick brown fox jumps over the lazy dog"}'
```

Batch:
```bash
curl -X POST http://localhost:8000/v1/stores/my_documents/embed/batch \
  -H "Content-Type: application/json" \
  -d '{"items": [{"content": "First document"}, {"content": "Second document"}]}'
```

### 4. Query for Similar Content

```bash
curl -X POST http://localhost:8000/v1/stores/my_documents/query \
  -H "Content-Type: application/json" \
  -d '{"query": "fox and dog", "limit": 5}'
```

## Configuration

Environment variables (or in `config.env` / `config.local.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/embeddings` | PostgreSQL connection |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |

## Development

```bash
make test      # Run tests
make lint      # Run ruff + mypy
make format    # Auto-format code
```

## Architecture

```
app/
├── api/           # FastAPI routers
├── core/          # Config and database
├── models/        # Pydantic schemas
└── services/      # Business logic
```

Each store creates a dedicated PostgreSQL table with pgvector for efficient similarity search.

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | FastAPI application |
| db | 5432 | PostgreSQL with pgvector (AlloyDB Omni) |
| ollama | 11434 | Embedding model server |
| adminer | 8080 | Database admin UI |

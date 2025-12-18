import re

import asyncpg

from app.models.store import (
    StoreBatchEmbedResponse,
    StoreCreate,
    StoreEmbedRequest,
    StoreEmbedResponse,
    StoreQueryResponse,
    StoreQueryResult,
    StoreResponse,
    StoreUpdate,
)
from app.services.embeddings import get_embeddings_service


def _validate_table_name(name: str) -> str:
    """Validate and sanitize table name to prevent SQL injection."""
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(f"Invalid table name: {name}")
    return name


async def create_store(
    conn: asyncpg.Connection, store: StoreCreate, dimensions: int
) -> StoreResponse:
    """Create a new store and its corresponding embeddings table."""
    # Insert into stores table
    await conn.execute(
        "INSERT INTO stores (id, model, description) VALUES ($1, $2, $3)",
        store.id,
        store.model,
        store.description,
    )

    # Create dynamic table for embeddings with unique constraint on content
    table_name = _validate_table_name(store.id)
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL UNIQUE,
            embedding vector({dimensions})
        )
    """)

    return StoreResponse(id=store.id, model=store.model, description=store.description)


async def get_store(
    conn: asyncpg.Connection, store_id: str
) -> StoreResponse | None:
    """Get a single store by ID."""
    row = await conn.fetchrow(
        "SELECT id, model, description FROM stores WHERE id = $1",
        store_id,
    )
    if row is None:
        return None
    return StoreResponse(id=row["id"], model=row["model"], description=row["description"])


async def get_all_stores(
    conn: asyncpg.Connection,
) -> list[StoreResponse]:
    """Get all stores."""
    rows = await conn.fetch("SELECT id, model, description FROM stores")
    return [
        StoreResponse(id=row["id"], model=row["model"], description=row["description"])
        for row in rows
    ]


async def update_store(
    conn: asyncpg.Connection, store_id: str, store: StoreUpdate
) -> StoreResponse | None:
    """Update an existing store."""
    # First get current values
    current = await get_store(conn, store_id)
    if current is None:
        return None

    # Use provided values or keep current ones
    new_model = store.model if store.model is not None else current.model
    new_description = store.description if store.description is not None else current.description

    await conn.execute(
        "UPDATE stores SET model = $1, description = $2 WHERE id = $3",
        new_model,
        new_description,
        store_id,
    )
    return StoreResponse(id=store_id, model=new_model, description=new_description)


async def delete_store(conn: asyncpg.Connection, store_id: str) -> bool:
    """Delete a store. Returns True if deleted, False if not found."""
    result = await conn.execute(
        "DELETE FROM stores WHERE id = $1",
        store_id,
    )
    return str(result) != "DELETE 0"


async def embed_content(
    conn: asyncpg.Connection,
    store_id: str,
    model_id: str,
    content: str,
    query: str | None = None,
) -> StoreEmbedResponse:
    """Embed content and store it in the store's table. Idempotent - skips duplicates."""
    table_name = _validate_table_name(store_id)

    # Check if content already exists
    existing = await conn.fetchrow(
        f"SELECT id FROM {table_name} WHERE content = $1",
        content,
    )

    if existing:
        # Content already exists, return existing record
        return StoreEmbedResponse(
            id=existing["id"],
            content=content,
            dimensions=0,  # We don't re-fetch the embedding
            created=False,
        )

    # Create embedding using query if provided, otherwise use content
    text_to_embed = query if query else content
    embeddings_service = get_embeddings_service()
    embedding_response = await embeddings_service.embed_query(model_id, text_to_embed)

    # Convert embedding list to PostgreSQL vector format
    embedding_str = "[" + ",".join(str(x) for x in embedding_response.embedding) + "]"

    # Insert into the store's table
    row = await conn.fetchrow(
        f"""
        INSERT INTO {table_name} (content, embedding)
        VALUES ($1, $2::vector)
        RETURNING id
        """,
        content,
        embedding_str,
    )

    return StoreEmbedResponse(
        id=row["id"],
        content=content,
        dimensions=embedding_response.dimensions,
        created=True,
    )


async def embed_content_batch(
    conn: asyncpg.Connection,
    store_id: str,
    model_id: str,
    items: list[StoreEmbedRequest],
) -> StoreBatchEmbedResponse:
    """Embed multiple items and store them in the store's table. Idempotent - skips duplicates."""
    table_name = _validate_table_name(store_id)
    results: list[StoreEmbedResponse] = []
    created_count = 0
    skipped_count = 0

    # Get existing content to skip duplicates
    contents = [item.content for item in items]
    existing_rows = await conn.fetch(
        f"SELECT id, content FROM {table_name} WHERE content = ANY($1)",
        contents,
    )
    existing_map = {row["content"]: row["id"] for row in existing_rows}

    # Separate new items from existing ones
    new_items: list[tuple[int, StoreEmbedRequest]] = []
    for idx, item in enumerate(items):
        if item.content in existing_map:
            results.append(
                StoreEmbedResponse(
                    id=existing_map[item.content],
                    content=item.content,
                    dimensions=0,
                    created=False,
                )
            )
            skipped_count += 1
        else:
            new_items.append((idx, item))

    if not new_items:
        return StoreBatchEmbedResponse(
            results=results,
            total=len(items),
            created=created_count,
            skipped=skipped_count,
        )

    # Create embeddings for new items in batch
    texts_to_embed = [
        item.query if item.query else item.content for _, item in new_items
    ]
    embeddings_service = get_embeddings_service()
    embeddings_response = await embeddings_service.embed_documents(model_id, texts_to_embed)

    dimensions = embeddings_response.dimensions

    # Insert new items
    for i, (original_idx, item) in enumerate(new_items):
        embedding = embeddings_response.embeddings[i].embedding
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        row = await conn.fetchrow(
            f"""
            INSERT INTO {table_name} (content, embedding)
            VALUES ($1, $2::vector)
            ON CONFLICT (content) DO NOTHING
            RETURNING id
            """,
            item.content,
            embedding_str,
        )

        if row:
            results.append(
                StoreEmbedResponse(
                    id=row["id"],
                    content=item.content,
                    dimensions=dimensions,
                    created=True,
                )
            )
            created_count += 1
        else:
            # Race condition - content was inserted by another request
            existing = await conn.fetchrow(
                f"SELECT id FROM {table_name} WHERE content = $1",
                item.content,
            )
            results.append(
                StoreEmbedResponse(
                    id=existing["id"] if existing else 0,
                    content=item.content,
                    dimensions=0,
                    created=False,
                )
            )
            skipped_count += 1

    return StoreBatchEmbedResponse(
        results=results,
        total=len(items),
        created=created_count,
        skipped=skipped_count,
    )


async def query_store(
    conn: asyncpg.Connection,
    store_id: str,
    model_id: str,
    query: str,
    limit: int = 10,
    max_distance: float | None = None,
) -> StoreQueryResponse:
    """Query the store for the most similar content to the query."""
    table_name = _validate_table_name(store_id)

    # Create embedding for the query
    embeddings_service = get_embeddings_service()
    embedding_response = await embeddings_service.embed_query(model_id, query)

    # Convert embedding list to PostgreSQL vector format
    embedding_str = "[" + ",".join(str(x) for x in embedding_response.embedding) + "]"

    # Query for top results using cosine distance
    if max_distance is not None:
        rows = await conn.fetch(
            f"""
            SELECT id, content, embedding <=> $1::vector AS distance
            FROM {table_name}
            WHERE embedding <=> $1::vector <= $2
            ORDER BY distance
            LIMIT $3
            """,
            embedding_str,
            max_distance,
            limit,
        )
    else:
        rows = await conn.fetch(
            f"""
            SELECT id, content, embedding <=> $1::vector AS distance
            FROM {table_name}
            ORDER BY distance
            LIMIT $2
            """,
            embedding_str,
            limit,
        )

    results = [
        StoreQueryResult(
            id=row["id"],
            content=row["content"],
            distance=float(row["distance"]),
        )
        for row in rows
    ]

    return StoreQueryResponse(
        query=query,
        results=results,
        count=len(results),
    )

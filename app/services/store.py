import re

import asyncpg

from app.models.store import (
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)


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

    # Create dynamic table for embeddings
    table_name = _validate_table_name(store.id)
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
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

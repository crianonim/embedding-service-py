import asyncpg

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.DATABASE_URL)
    return _pool


async def get_db() -> asyncpg.Connection:
    """Get a database connection from the pool."""
    pool = await get_pool()
    return await pool.acquire()


async def release_db(conn: asyncpg.Connection) -> None:
    """Release a database connection back to the pool."""
    pool = await get_pool()
    await pool.release(conn)


async def init_db() -> None:
    """Create database tables if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings_models (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                dimensions INTEGER NOT NULL DEFAULT 1024
            )
        """)
        # Add dimensions column to existing tables (migration)
        await conn.execute("""
            ALTER TABLE embeddings_models
            ADD COLUMN IF NOT EXISTS dimensions INTEGER NOT NULL DEFAULT 1024
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL REFERENCES embeddings_models(id),
                description TEXT
            )
        """)

        # Migration: Add unique constraint on content column for all existing store tables
        store_rows = await conn.fetch("SELECT id FROM stores")
        for row in store_rows:
            table_name = row["id"]
            # Check if table exists and add unique constraint if missing
            await conn.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = '{table_name}_content_key'
                    ) THEN
                        ALTER TABLE {table_name}
                        ADD CONSTRAINT {table_name}_content_key UNIQUE (content);
                    END IF;
                END $$;
            """)


async def close_db() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

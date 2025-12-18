import asyncpg

from app.models.embeddings_model import (
    EmbeddingsModelCreate,
    EmbeddingsModelResponse,
    EmbeddingsModelUpdate,
)


async def create_embeddings_model(
    conn: asyncpg.Connection, model: EmbeddingsModelCreate
) -> EmbeddingsModelResponse:
    """Create a new embeddings model."""
    await conn.execute(
        "INSERT INTO embeddings_models (id, description, dimensions) VALUES ($1, $2, $3)",
        model.id,
        model.description,
        model.dimensions,
    )
    return EmbeddingsModelResponse(id=model.id, description=model.description, dimensions=model.dimensions)


async def get_embeddings_model(
    conn: asyncpg.Connection, model_id: str
) -> EmbeddingsModelResponse | None:
    """Get a single embeddings model by ID."""
    row = await conn.fetchrow(
        "SELECT id, description, dimensions FROM embeddings_models WHERE id = $1",
        model_id,
    )
    if row is None:
        return None
    return EmbeddingsModelResponse(id=row["id"], description=row["description"], dimensions=row["dimensions"])


async def get_all_embeddings_models(
    conn: asyncpg.Connection,
) -> list[EmbeddingsModelResponse]:
    """Get all embeddings models."""
    rows = await conn.fetch("SELECT id, description, dimensions FROM embeddings_models")
    return [
        EmbeddingsModelResponse(id=row["id"], description=row["description"], dimensions=row["dimensions"])
        for row in rows
    ]


async def update_embeddings_model(
    conn: asyncpg.Connection, model_id: str, model: EmbeddingsModelUpdate
) -> EmbeddingsModelResponse | None:
    """Update an existing embeddings model."""
    # First get current values
    current = await get_embeddings_model(conn, model_id)
    if current is None:
        return None

    # Use provided values or keep current ones
    new_description = model.description if model.description is not None else current.description
    new_dimensions = model.dimensions if model.dimensions is not None else current.dimensions

    await conn.execute(
        "UPDATE embeddings_models SET description = $1, dimensions = $2 WHERE id = $3",
        new_description,
        new_dimensions,
        model_id,
    )
    return EmbeddingsModelResponse(id=model_id, description=new_description, dimensions=new_dimensions)


async def delete_embeddings_model(conn: asyncpg.Connection, model_id: str) -> bool:
    """Delete an embeddings model. Returns True if deleted, False if not found."""
    result = await conn.execute(
        "DELETE FROM embeddings_models WHERE id = $1",
        model_id,
    )
    return str(result) != "DELETE 0"


async def upsert_embeddings_model(
    conn: asyncpg.Connection, model: EmbeddingsModelCreate
) -> tuple[EmbeddingsModelResponse, bool]:
    """Create or update an embeddings model. Returns (model, created) tuple."""
    result = await conn.execute(
        """
        INSERT INTO embeddings_models (id, description, dimensions) VALUES ($1, $2, $3)
        ON CONFLICT (id) DO UPDATE SET description = $2, dimensions = $3
        """,
        model.id,
        model.description,
        model.dimensions,
    )
    created = result == "INSERT 0 1"
    return EmbeddingsModelResponse(id=model.id, description=model.description, dimensions=model.dimensions), created

from fastapi import APIRouter, HTTPException, Response

from app.core.database import get_pool
from app.models.embeddings_model import (
    EmbeddingsModelCreate,
    EmbeddingsModelResponse,
    EmbeddingsModelUpdate,
)
from app.services.embeddings_model import (
    create_embeddings_model,
    delete_embeddings_model,
    get_all_embeddings_models,
    get_embeddings_model,
    update_embeddings_model,
    upsert_embeddings_model,
)

router = APIRouter(prefix="/embeddings-models", tags=["embeddings-models"])


@router.post("", response_model=EmbeddingsModelResponse, status_code=201)
async def create_model(
    model: EmbeddingsModelCreate,
) -> EmbeddingsModelResponse:
    """Create a new embeddings model."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await get_embeddings_model(conn, model.id)
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Model with id '{model.id}' already exists"
            )
        return await create_embeddings_model(conn, model)


@router.put("", response_model=EmbeddingsModelResponse)
async def upsert_model(
    model: EmbeddingsModelCreate,
    response: Response,
) -> EmbeddingsModelResponse:
    """Create or update an embeddings model."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result, created = await upsert_embeddings_model(conn, model)
        if created:
            response.status_code = 201
        return result


@router.get("", response_model=list[EmbeddingsModelResponse])
async def list_models() -> list[EmbeddingsModelResponse]:
    """Get all embeddings models."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await get_all_embeddings_models(conn)


@router.get("/{model_id}", response_model=EmbeddingsModelResponse)
async def get_model(
    model_id: str,
) -> EmbeddingsModelResponse:
    """Get a single embeddings model by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await get_embeddings_model(conn, model_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Model with id '{model_id}' not found"
            )
        return result


@router.put("/{model_id}", response_model=EmbeddingsModelResponse)
async def update_model(
    model_id: str,
    model: EmbeddingsModelUpdate,
) -> EmbeddingsModelResponse:
    """Update an existing embeddings model."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await update_embeddings_model(conn, model_id, model)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Model with id '{model_id}' not found"
            )
        return result


@router.delete("/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
) -> None:
    """Delete an embeddings model."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        deleted = await delete_embeddings_model(conn, model_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Model with id '{model_id}' not found"
            )

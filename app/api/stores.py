from fastapi import APIRouter, HTTPException

from app.core.database import get_pool
from app.models.store import (
    StoreBatchEmbedRequest,
    StoreBatchEmbedResponse,
    StoreCreate,
    StoreEmbedRequest,
    StoreEmbedResponse,
    StoreQueryRequest,
    StoreQueryResponse,
    StoreResponse,
    StoreUpdate,
)
from app.models.embeddings_model import EmbeddingsModelResponse
from app.services.store import (
    create_store,
    delete_store,
    embed_content,
    embed_content_batch,
    get_all_stores,
    get_store,
    query_store,
    update_store,
)
from app.services.embeddings_model import get_embeddings_model

router = APIRouter(prefix="/stores", tags=["stores"])


async def _get_and_validate_model(conn: object, model_id: str) -> EmbeddingsModelResponse:
    """Get and validate that the referenced embeddings model exists."""
    model = await get_embeddings_model(conn, model_id)  # type: ignore
    if model is None:
        raise HTTPException(
            status_code=400,
            detail=f"Embeddings model with id '{model_id}' does not exist",
        )
    return model


@router.post("", response_model=StoreResponse, status_code=201)
async def create_store_endpoint(
    store: StoreCreate,
) -> StoreResponse:
    """Create a new store and its corresponding embeddings table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        model = await _get_and_validate_model(conn, store.model)
        existing = await get_store(conn, store.id)
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Store with id '{store.id}' already exists"
            )
        return await create_store(conn, store, model.dimensions)


@router.get("", response_model=list[StoreResponse])
async def list_stores() -> list[StoreResponse]:
    """Get all stores."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await get_all_stores(conn)


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store_endpoint(
    store_id: str,
) -> StoreResponse:
    """Get a single store by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await get_store(conn, store_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Store with id '{store_id}' not found"
            )
        return result


@router.put("/{store_id}", response_model=StoreResponse)
async def update_store_endpoint(
    store_id: str,
    store: StoreUpdate,
) -> StoreResponse:
    """Update an existing store."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if store.model is not None:
            await _get_and_validate_model(conn, store.model)
        result = await update_store(conn, store_id, store)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"Store with id '{store_id}' not found"
            )
        return result


@router.delete("/{store_id}", status_code=204)
async def delete_store_endpoint(
    store_id: str,
) -> None:
    """Delete a store."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        deleted = await delete_store(conn, store_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Store with id '{store_id}' not found"
            )


@router.post("/{store_id}/embed", response_model=StoreEmbedResponse)
async def embed_content_endpoint(
    store_id: str,
    request: StoreEmbedRequest,
) -> StoreEmbedResponse:
    """Embed content and store it in the store's table. Idempotent - no duplicates."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get the store to find the model
        store = await get_store(conn, store_id)
        if store is None:
            raise HTTPException(
                status_code=404, detail=f"Store with id '{store_id}' not found"
            )

        try:
            result = await embed_content(
                conn,
                store_id,
                store.model,
                request.content,
                request.query,
                request.metadata,
            )
            if result is None:
                raise HTTPException(
                    status_code=400,
                    detail="Content cannot be empty",
                )
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed content: {str(e)}",
            )


@router.post("/{store_id}/embed/batch", response_model=StoreBatchEmbedResponse)
async def embed_content_batch_endpoint(
    store_id: str,
    request: StoreBatchEmbedRequest,
) -> StoreBatchEmbedResponse:
    """Embed multiple items and store them in the store's table. Idempotent - no duplicates."""
    if not request.items:
        raise HTTPException(
            status_code=400,
            detail="Items list cannot be empty",
        )

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get the store to find the model
        store = await get_store(conn, store_id)
        if store is None:
            raise HTTPException(
                status_code=404, detail=f"Store with id '{store_id}' not found"
            )

        try:
            return await embed_content_batch(
                conn,
                store_id,
                store.model,
                request.items,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to embed content: {str(e)}",
            )


@router.post("/{store_id}/query", response_model=StoreQueryResponse)
async def query_store_endpoint(
    store_id: str,
    request: StoreQueryRequest,
) -> StoreQueryResponse:
    """Query the store for the most similar content using vector similarity search."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get the store to find the model
        store = await get_store(conn, store_id)
        if store is None:
            raise HTTPException(
                status_code=404, detail=f"Store with id '{store_id}' not found"
            )

        try:
            return await query_store(
                conn,
                store_id,
                store.model,
                request.query,
                limit=request.limit,
                max_distance=request.distance,
                metadata_filters=request.metadata,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to query store: {str(e)}",
            )

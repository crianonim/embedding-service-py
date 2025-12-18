from fastapi import APIRouter, HTTPException

from app.models.embedding import (
    DocumentsEmbeddingRequest,
    DocumentsEmbeddingResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.services.embeddings import get_embeddings_service

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post("/query", response_model=EmbeddingResponse)
async def create_query_embedding(
    request: EmbeddingRequest,
) -> EmbeddingResponse:
    """Create an embedding for a single query using the specified model."""
    try:
        service = get_embeddings_service()
        return await service.embed_query(request.model, request.query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create embedding: {str(e)}",
        )


@router.post("/documents", response_model=DocumentsEmbeddingResponse)
async def create_documents_embeddings(
    request: DocumentsEmbeddingRequest,
) -> DocumentsEmbeddingResponse:
    """Create embeddings for a list of documents using the specified model."""
    if not request.documents:
        raise HTTPException(
            status_code=400,
            detail="Documents list cannot be empty",
        )

    try:
        service = get_embeddings_service()
        return await service.embed_documents(request.model, request.documents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create embeddings: {str(e)}",
        )

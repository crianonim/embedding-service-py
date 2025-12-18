from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Schema for creating an embedding from a single query."""

    model: str = Field(..., description="Model ID to use for embedding (e.g., 'mxbai-embed-large')")
    query: str = Field(..., description="Text to embed")


class EmbeddingResponse(BaseModel):
    """Schema for embedding response."""

    model: str = Field(..., description="Model ID used for embedding")
    embedding: list[float] = Field(..., description="The embedding vector")
    dimensions: int = Field(..., description="Number of dimensions in the embedding")


class DocumentsEmbeddingRequest(BaseModel):
    """Schema for creating embeddings from a list of documents."""

    model: str = Field(..., description="Model ID to use for embedding (e.g., 'mxbai-embed-large')")
    documents: list[str] = Field(..., description="List of documents to embed")


class DocumentEmbedding(BaseModel):
    """Schema for a single document embedding."""

    index: int = Field(..., description="Index of the document in the input list")
    embedding: list[float] = Field(..., description="The embedding vector")


class DocumentsEmbeddingResponse(BaseModel):
    """Schema for documents embedding response."""

    model: str = Field(..., description="Model ID used for embedding")
    embeddings: list[DocumentEmbedding] = Field(..., description="List of document embeddings")
    dimensions: int = Field(..., description="Number of dimensions in each embedding")
    count: int = Field(..., description="Number of documents embedded")

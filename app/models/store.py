from pydantic import BaseModel, Field


class StoreCreate(BaseModel):
    """Schema for creating a store."""

    id: str = Field(..., description="Unique identifier for the store")
    model: str = Field(..., description="Reference to embeddings_models.id")
    description: str | None = Field(None, description="Optional description of the store")


class StoreUpdate(BaseModel):
    """Schema for updating a store."""

    model: str | None = Field(None, description="Reference to embeddings_models.id")
    description: str | None = Field(None, description="Optional description of the store")


class StoreResponse(BaseModel):
    """Schema for store response."""

    id: str = Field(..., description="Unique identifier for the store")
    model: str = Field(..., description="Reference to embeddings_models.id")
    description: str | None = Field(None, description="Optional description of the store")


class StoreEmbedRequest(BaseModel):
    """Schema for embedding content into a store."""

    content: str = Field(..., description="Content to store and embed")
    query: str | None = Field(None, description="Optional query text to use for embedding instead of content")


class StoreEmbedResponse(BaseModel):
    """Schema for store embed response."""

    id: int = Field(..., description="ID of the stored record")
    content: str = Field(..., description="The stored content")
    dimensions: int = Field(..., description="Number of dimensions in the embedding")
    created: bool = Field(..., description="True if newly created, False if already existed")


class StoreBatchEmbedRequest(BaseModel):
    """Schema for batch embedding content into a store."""

    items: list[StoreEmbedRequest] = Field(..., description="List of items to embed")


class StoreBatchEmbedResponse(BaseModel):
    """Schema for batch store embed response."""

    results: list[StoreEmbedResponse] = Field(..., description="List of embed results")
    total: int = Field(..., description="Total number of items processed")
    created: int = Field(..., description="Number of new items created")
    skipped: int = Field(..., description="Number of items skipped (already existed)")


class StoreQueryRequest(BaseModel):
    """Schema for querying a store."""

    query: str = Field(..., description="Query text to search for")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return")
    distance: float | None = Field(None, ge=0, le=2, description="Maximum cosine distance (filters out results above this value)")


class StoreQueryResult(BaseModel):
    """Schema for a single query result."""

    id: int = Field(..., description="ID of the record")
    content: str = Field(..., description="The stored content")
    distance: float = Field(..., description="Cosine distance from query (lower is more similar)")


class StoreQueryResponse(BaseModel):
    """Schema for store query response."""

    query: str = Field(..., description="The original query")
    results: list[StoreQueryResult] = Field(..., description="Top matching results")
    count: int = Field(..., description="Number of results returned")

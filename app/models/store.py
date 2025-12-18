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

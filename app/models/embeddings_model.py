from pydantic import BaseModel, Field


class EmbeddingsModelCreate(BaseModel):
    """Schema for creating an embeddings model."""

    id: str = Field(..., description="Unique identifier for the model")
    description: str = Field(..., description="Description of the model")
    dimensions: int = Field(..., description="Number of dimensions for the embedding")


class EmbeddingsModelUpdate(BaseModel):
    """Schema for updating an embeddings model."""

    description: str | None = Field(None, description="Description of the model")
    dimensions: int | None = Field(None, description="Number of dimensions for the embedding")


class EmbeddingsModelResponse(BaseModel):
    """Schema for embeddings model response."""

    id: str = Field(..., description="Unique identifier for the model")
    description: str = Field(..., description="Description of the model")
    dimensions: int = Field(..., description="Number of dimensions for the embedding")

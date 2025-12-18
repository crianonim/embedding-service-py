from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.models.embedding import (
    DocumentEmbedding,
    DocumentsEmbeddingResponse,
    EmbeddingResponse,
)


class EmbeddingsService:
    """Service for creating embeddings using Ollama models."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url
        self._models: dict[str, OllamaEmbeddings] = {}

    def _get_model(self, model_id: str) -> OllamaEmbeddings:
        """Get or create an OllamaEmbeddings instance for the given model."""
        if model_id not in self._models:
            self._models[model_id] = OllamaEmbeddings(
                model=model_id,
                base_url=self._base_url,
            )
        return self._models[model_id]

    async def embed_query(self, model_id: str, query: str) -> EmbeddingResponse:
        """Create an embedding for a single query."""
        model = self._get_model(model_id)
        embedding = await model.aembed_query(query)

        return EmbeddingResponse(
            model=model_id,
            embedding=embedding,
            dimensions=len(embedding),
        )

    async def embed_documents(
        self, model_id: str, documents: list[str]
    ) -> DocumentsEmbeddingResponse:
        """Create embeddings for a list of documents."""
        model = self._get_model(model_id)
        embeddings = await model.aembed_documents(documents)

        document_embeddings = [
            DocumentEmbedding(index=i, embedding=emb)
            for i, emb in enumerate(embeddings)
        ]

        dimensions = len(embeddings[0]) if embeddings else 0

        return DocumentsEmbeddingResponse(
            model=model_id,
            embeddings=document_embeddings,
            dimensions=dimensions,
            count=len(documents),
        )


# Global service instance
_embeddings_service: EmbeddingsService | None = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create the global embeddings service instance."""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService(base_url=settings.OLLAMA_URL)
    return _embeddings_service

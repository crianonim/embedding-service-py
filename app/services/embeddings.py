from langchain_ollama import OllamaEmbeddings
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from app.core.config import settings
from app.models.embedding import (
    DocumentEmbedding,
    DocumentsEmbeddingResponse,
    EmbeddingResponse,
)

# Known Vertex AI embedding models
VERTEX_AI_MODELS = {"text-embedding-005", "text-embedding-004", "text-multilingual-embedding-002"}


class EmbeddingsService:
    """Service for creating embeddings using Ollama or Vertex AI models."""

    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self._ollama_base_url = ollama_base_url
        self._ollama_models: dict[str, OllamaEmbeddings] = {}
        self._vertex_models: dict[str, TextEmbeddingModel] = {}

    def _is_vertex_model(self, model_id: str) -> bool:
        """Check if model_id is a Vertex AI model."""
        return model_id in VERTEX_AI_MODELS

    def _get_ollama_model(self, model_id: str) -> OllamaEmbeddings:
        """Get or create an Ollama embeddings instance."""
        if model_id not in self._ollama_models:
            self._ollama_models[model_id] = OllamaEmbeddings(
                model=model_id,
                base_url=self._ollama_base_url,
            )
        return self._ollama_models[model_id]

    def _get_vertex_model(self, model_id: str) -> TextEmbeddingModel:
        """Get or create a Vertex AI embeddings model."""
        if model_id not in self._vertex_models:
            self._vertex_models[model_id] = TextEmbeddingModel.from_pretrained(model_id)
        return self._vertex_models[model_id]

    async def embed_query(self, model_id: str, query: str) -> EmbeddingResponse:
        """Create an embedding for a single query."""
        if self._is_vertex_model(model_id):
            vertex_model = self._get_vertex_model(model_id)
            inputs: list[str | TextEmbeddingInput] = [
                TextEmbeddingInput(query, "RETRIEVAL_QUERY")
            ]
            result = vertex_model.get_embeddings(inputs)
            embedding = result[0].values
        else:
            ollama_model = self._get_ollama_model(model_id)
            embedding = await ollama_model.aembed_query(query)

        return EmbeddingResponse(
            model=model_id,
            embedding=embedding,
            dimensions=len(embedding),
        )

    async def embed_documents(
        self, model_id: str, documents: list[str]
    ) -> DocumentsEmbeddingResponse:
        """Create embeddings for a list of documents."""
        if self._is_vertex_model(model_id):
            vertex_model = self._get_vertex_model(model_id)
            inputs: list[str | TextEmbeddingInput] = [
                TextEmbeddingInput(doc, "RETRIEVAL_DOCUMENT") for doc in documents
            ]
            result = vertex_model.get_embeddings(inputs)
            embeddings = [r.values for r in result]
        else:
            ollama_model = self._get_ollama_model(model_id)
            embeddings = await ollama_model.aembed_documents(documents)

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
        _embeddings_service = EmbeddingsService(ollama_base_url=settings.OLLAMA_URL)
    return _embeddings_service

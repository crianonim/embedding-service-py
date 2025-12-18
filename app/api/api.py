from fastapi import APIRouter

from app.api.embeddings import router as embeddings_router
from app.api.embeddings_models import router as embeddings_models_router
from app.api.stores import router as stores_router

api_router = APIRouter()
api_router.include_router(embeddings_models_router, prefix="")
api_router.include_router(stores_router, prefix="")
api_router.include_router(embeddings_router, prefix="")

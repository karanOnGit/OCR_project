from fastapi import APIRouter

from app.api.routes.upload import router as upload_router
from app.api.routes.google_docs import router as google_docs_router

api_router = APIRouter(prefix="/api")
api_router.include_router(upload_router)
api_router.include_router(google_docs_router)

__all__ = ["api_router"]

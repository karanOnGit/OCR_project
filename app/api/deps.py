from typing import Optional
from fastapi import Depends
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.supabase import get_supabase_client
from app.services.storage_service import StorageService
from app.services.google_docs_service import BaseGoogleDocsService, get_google_docs_service
from app.services.easyocr_service import EasyOCRService, get_easyocr_service
from supabase import Client


def get_supabase(
    settings: Settings = Depends(get_settings),
) -> Optional[Client]:
    return get_supabase_client(settings=settings)


def get_storage_service(
    settings: Settings = Depends(get_settings),
) -> StorageService:
    return StorageService(settings=settings)


def get_google_docs_service_dep(
    settings: Settings = Depends(get_settings),
) -> BaseGoogleDocsService:
    return get_google_docs_service(settings=settings)


def get_easyocr_service_dep() -> EasyOCRService:
    return get_easyocr_service()

from datetime import datetime, timezone
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import get_google_docs_service_dep
from app.core.config import get_settings
from app.core.errors import AppException
from app.schemas.google_docs import GoogleDocsRequest, GoogleDocsResponse
from app.services.google_docs_service import BaseGoogleDocsService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Google Docs Integration"])


@router.post(
    "/update-google-doc",
    response_model=GoogleDocsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Google Document & Sync to Supabase",
    description="Receives extracted on-device OCR text, appends it to the Google Document, and automatically persists the record in Supabase.",
)
async def update_google_doc(
    request: GoogleDocsRequest,
    google_docs_service: BaseGoogleDocsService = Depends(get_google_docs_service_dep),
) -> GoogleDocsResponse:
    if not request.text or not request.text.strip():
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="EMPTY_TEXT",
            message="The 'text' field cannot be empty.",
        )

    settings = get_settings()
    doc_id = request.documentId or settings.DEFAULT_GOOGLE_DOC_ID

    # Format text with title header if provided
    text_body = request.text.strip()
    if request.title and request.title.strip():
        formatted_content = f"\n=== {request.title.strip()} ===\n{text_body}\n"
    else:
        formatted_content = f"\n{text_body}\n"

    logger.info(f"Appending text to Google Doc '{doc_id}' (title: '{request.title}')")
    result = await google_docs_service.update_document(
        document_id=doc_id,
        text=formatted_content,
    )

    resolved_id = result.get("documentId", doc_id)
    supabase_synced = False

    # Sync everything received to Supabase
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        if supabase:
            now_iso = datetime.now(timezone.utc).isoformat()
            job_record = {
                "id": str(uuid.uuid4()),
                "original_filename": request.title or "Mobile ML Kit Capture",
                "image_path": f"gdoc://{resolved_id}",
                "status": "completed",
                "extracted_text": request.text,
                "error": None,
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            supabase.table("jobs").upsert(job_record).execute()
            supabase_synced = True
            logger.info("Successfully synced capture record to Supabase")
    except Exception as err:
        logger.warning(f"Supabase sync warning: {err}")

    return GoogleDocsResponse(
        success=True,
        documentId=resolved_id,
        message="Document updated successfully",
        charactersAppended=len(formatted_content),
        supabaseSynced=supabase_synced,
    )

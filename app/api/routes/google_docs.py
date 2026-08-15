import logging
from datetime import datetime, timezone
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
    summary="Update Google Document with direct ML Kit text",
    description="Directly appends extracted OCR text from the Flutter ML Kit on-device scanner into the target Google Document.",
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
    content_to_append = request.text.strip()
    if request.title:
        content_to_append = f"### {request.title}\n{content_to_append}"

    logger.info(f"Appending {len(content_to_append)} chars to Google Doc '{doc_id}'")
    result = await google_docs_service.update_document(
        document_id=doc_id,
        text=content_to_append,
    )

    resolved_id = result.get("documentId", doc_id)

    # Optional: Sync to Supabase table
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        if supabase:
            supabase.table("jobs").upsert({
                "id": str(uuid.uuid4()),
                "original_filename": request.title or "mlkit_extracted_doc",
                "image_path": "on_device_mlkit",
                "status": "completed",
                "extracted_text": request.text,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            logger.info("Synced ML Kit text record to Supabase")
    except Exception as err:
        logger.warning(f"Supabase sync warning: {err}")

    return GoogleDocsResponse(
        success=True,
        documentId=resolved_id,
        message="Document updated successfully",
        charactersAppended=len(content_to_append),
    )

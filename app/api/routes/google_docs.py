import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_google_docs_service_dep
from app.core.database import get_db
from app.core.errors import AppException, JobNotFoundException
from app.models.job import Job, JobStatus
from app.schemas.google_docs import GoogleDocsRequest, GoogleDocsResponse
from app.services.google_docs_service import BaseGoogleDocsService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Google Docs Integration"])


@router.post(
    "/update-google-doc",
    response_model=GoogleDocsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Google Document with extracted text",
    description="Appends the extracted OCR text from a completed job into the specified Google Document.",
)
async def update_google_doc(
    request: GoogleDocsRequest,
    db: Session = Depends(get_db),
    google_docs_service: BaseGoogleDocsService = Depends(get_google_docs_service_dep),
) -> GoogleDocsResponse:
    # 1. Fetch the job
    job = db.query(Job).filter(Job.id == request.jobId).first()
    if not job:
        raise JobNotFoundException(request.jobId)

    # 2. Check if job has extracted text
    if job.status != JobStatus.COMPLETED or not job.extracted_text:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="JOB_NOT_READY",
            message=f"Job '{request.jobId}' is in status '{job.status.value}' without completed OCR text.",
        )

    # 3. Call Google Docs Service
    logger.info(f"Updating Google Doc '{request.documentId}' with text from job {job.id}")
    await google_docs_service.update_document(
        document_id=request.documentId,
        text=job.extracted_text,
    )

    return GoogleDocsResponse(
        success=True,
        jobId=job.id,
        documentId=request.documentId,
        message="Document updated successfully",
    )

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_ocr_service_dep, get_storage_service
from app.core.database import get_db
from app.core.errors import JobNotFoundException, OCRProcessingException
from app.models.job import Job, JobStatus
from app.schemas.process import ProcessRequest, ProcessResponse
from app.services.ocr_service import BaseOCRService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["OCR Processing"])


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process document with OCR",
    description="Extracts text from the image associated with the given jobId using OCR and updates the job record.",
)
async def process_document(
    request: ProcessRequest,
    db: Session = Depends(get_db),
    ocr_service: BaseOCRService = Depends(get_ocr_service_dep),
    storage_service: StorageService = Depends(get_storage_service),
) -> ProcessResponse:
    # 1. Look up the job
    job = db.query(Job).filter(Job.id == request.jobId).first()
    if not job:
        raise JobNotFoundException(request.jobId)

    # 2. Verify file exists on disk
    storage_service.get_file_path(job.image_path)

    # 3. Update status to processing
    job.status = JobStatus.PROCESSING
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)

    # 4. Perform OCR text extraction
    try:
        extracted_text = await ocr_service.extract_text(job.image_path)
        job.status = JobStatus.COMPLETED
        job.extracted_text = extracted_text
        job.error = None
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)

        logger.info(f"Successfully processed OCR for job {job.id} (Extracted {len(extracted_text)} chars)")

        return ProcessResponse(
            success=True,
            jobId=job.id,
            status=job.status.value,
            text=job.extracted_text,
        )

    except Exception as e:
        logger.error(f"OCR processing failed for job {job.id}: {e}")
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)

        raise OCRProcessingException(f"OCR processing failed: {str(e)}") from e

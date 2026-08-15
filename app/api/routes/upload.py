import logging
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_storage_service
from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.upload import UploadResponse
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Document Upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document image",
    description="Uploads a document photo (JPG, JPEG, PNG, WEBP), validates size, stores it locally, and initializes a document record.",
)
async def upload_image(
    file: UploadFile = File(..., description="Document image file"),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> UploadResponse:
    # Validate and save the uploaded image
    file_id, file_path, file_size = await storage_service.save_upload_file(file)

    # Create new job in database
    job = Job(
        id=file_id,
        original_filename=file.filename,
        image_path=file_path,
        file_size=file_size,
        status=JobStatus.UPLOADED,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Sync to Supabase if configured
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        if supabase:
            supabase.table("jobs").upsert({
                "id": job.id,
                "original_filename": job.original_filename,
                "image_path": job.image_path,
                "file_size": job.file_size,
                "status": job.status.value,
                "extracted_text": None,
                "error": None,
            }).execute()
            logger.info(f"Synced new document {job.id} to Supabase")
    except Exception as e:
        logger.warning(f"Failed to sync document {job.id} to Supabase: {e}")

    logger.info(f"Created document {job.id} for file {file.filename} ({file_size} bytes)")

    return UploadResponse(
        success=True,
        jobId=job.id,
        message="Image uploaded successfully",
    )

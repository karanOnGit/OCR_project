from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_storage_service,
    get_ocr_service_dep,
    get_google_docs_service_dep,
)
from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.upload import UploadResponse, BatchJobItem, BatchProcessResponse
from app.services.storage_service import StorageService
from app.services.ocr_service import BaseOCRService
from app.services.google_docs_service import BaseGoogleDocsService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Document Upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document image",
    description="Uploads a document photo (JPG, JPEG, PNG, WEBP), validates size, stores it locally, and initializes a processing job.",
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
            logger.info(f"Synced new job {job.id} to Supabase")
    except Exception as e:
        logger.warning(f"Failed to sync job {job.id} to Supabase: {e}")

    logger.info(f"Created job {job.id} for file {file.filename} ({file_size} bytes)")

    return UploadResponse(
        success=True,
        jobId=job.id,
        message="Image uploaded successfully",
    )


@router.post(
    "/upload-batch",
    response_model=BatchProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-file batch upload, OCR processing, and Google Docs sync",
    description="Accepts multiple images, performs OCR on each, syncs them to Supabase/SQLite database, and sequentially appends their extracted text to Google Docs if documentId is provided.",
)
async def upload_batch(
    files: List[UploadFile] = File(..., description="Multiple document images"),
    documentId: Optional[str] = Form(None, description="Optional Google Document ID to update sequentially"),
    auto_process: bool = Form(True, description="Whether to automatically run OCR processing"),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
    ocr_service: BaseOCRService = Depends(get_ocr_service_dep),
    google_docs_service: BaseGoogleDocsService = Depends(get_google_docs_service_dep),
) -> BatchProcessResponse:
    batch_jobs: List[BatchJobItem] = []
    completed_count = 0
    all_extracted_texts: List[str] = []

    for file in files:
        try:
            # 1. Save file
            file_id, file_path, file_size = await storage_service.save_upload_file(file)

            # 2. Record Job in SQLite
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

            # 3. Auto process OCR
            if auto_process:
                job.status = JobStatus.PROCESSING
                db.commit()
                db.refresh(job)

                try:
                    text = await ocr_service.extract_text(job.image_path)
                    job.status = JobStatus.COMPLETED
                    job.extracted_text = text
                    job.error = None
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    db.refresh(job)

                    completed_count += 1
                    all_extracted_texts.append(f"[{file.filename}]\n{text}")

                    # Sync to Supabase
                    try:
                        from app.core.supabase import get_supabase_client
                        supabase = get_supabase_client()
                        if supabase:
                            supabase.table("jobs").upsert({
                                "id": job.id,
                                "original_filename": job.original_filename,
                                "image_path": job.image_path,
                                "file_size": job.file_size,
                                "status": "completed",
                                "extracted_text": text,
                                "error": None,
                            }).execute()
                    except Exception as err:
                        logger.warning(f"Supabase sync warning for {job.id}: {err}")

                    batch_jobs.append(
                        BatchJobItem(
                            jobId=job.id,
                            filename=file.filename,
                            status="completed",
                            text=text,
                            error=None,
                        )
                    )
                except Exception as ocr_err:
                    job.status = JobStatus.FAILED
                    job.error = str(ocr_err)
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()

                    batch_jobs.append(
                        BatchJobItem(
                            jobId=job.id,
                            filename=file.filename,
                            status="failed",
                            text=None,
                            error=str(ocr_err),
                        )
                    )
            else:
                batch_jobs.append(
                    BatchJobItem(
                        jobId=job.id,
                        filename=file.filename,
                        status="uploaded",
                        text=None,
                        error=None,
                    )
                )

        except Exception as upload_err:
            logger.error(f"Failed to process file {file.filename}: {upload_err}")
            batch_jobs.append(
                BatchJobItem(
                    jobId="error",
                    filename=file.filename,
                    status="failed",
                    text=None,
                    error=str(upload_err),
                )
            )

    # 4. Sequentially append all texts to Google Docs
    from app.core.config import get_settings
    settings = get_settings()
    target_doc_id = documentId if documentId and documentId.strip() else settings.DEFAULT_GOOGLE_DOC_ID

    if target_doc_id and all_extracted_texts:
        try:
            combined_content = "\n\n".join(all_extracted_texts)
            await google_docs_service.update_document(
                document_id=target_doc_id,
                text=combined_content,
            )
            logger.info(f"Successfully appended batch text ({len(all_extracted_texts)} items) to Google Doc {target_doc_id}")
        except Exception as gdoc_err:
            logger.error(f"Failed to update Google Doc {target_doc_id}: {gdoc_err}")

    return BatchProcessResponse(
        success=True,
        total=len(files),
        completed=completed_count,
        documentId=target_doc_id,
        jobs=batch_jobs,
        message=f"{completed_count} of {len(files)} documents processed successfully",
    )

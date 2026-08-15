import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_easyocr_service_dep,
    get_google_docs_service_dep,
    get_storage_service,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppException
from app.models.job import Job, JobStatus
from app.schemas.ocr import BatchOCRResponse, SingleOCRResponse, OCRItemResult
from app.services.easyocr_service import EasyOCRService
from app.services.google_docs_service import BaseGoogleDocsService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["EasyOCR Processing"])


@router.post(
    "/batch",
    response_model=BatchOCRResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch OCR extraction with EasyOCR and Google Docs sync",
    description="Extracts Hindi and English text from multiple images in parallel using EasyOCR, saves records to database, and sequentially syncs all extracted content into Google Docs.",
)
async def process_batch_ocr(
    files: List[UploadFile] = File(..., description="List of document image files"),
    documentId: Optional[str] = Form(None, description="Target Google Document ID or URL (defaults to project document)"),
    update_google_doc: bool = Form(True, description="Whether to sequentially update the Google Document"),
    db: Session = Depends(get_db),
    easyocr_service: EasyOCRService = Depends(get_easyocr_service_dep),
    google_docs_service: BaseGoogleDocsService = Depends(get_google_docs_service_dep),
    storage_service: StorageService = Depends(get_storage_service),
) -> BatchOCRResponse:
    if not files:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="NO_FILES",
            message="No image files were uploaded.",
        )

    start_time = time.time()
    settings = get_settings()
    target_doc_id = documentId if documentId and documentId.strip() else settings.DEFAULT_GOOGLE_DOC_ID

    # 1. Read all file bytes and save to disk/storage
    images_payload = []
    jobs_created = []

    for file in files:
        file_bytes = await file.read()
        filename = file.filename or "image.png"
        
        # Save local record
        file_id = str(uuid.uuid4())
        ext = filename.split(".")[-1].lower() if "." in filename else "png"
        dest_path = settings.upload_path / f"{file_id}.{ext}"
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        job = Job(
            id=file_id,
            original_filename=filename,
            image_path=str(dest_path.resolve()),
            file_size=len(file_bytes),
            status=JobStatus.PROCESSING,
        )
        db.add(job)
        jobs_created.append(job)
        images_payload.append((filename, file_bytes, job))

    db.commit()

    # 2. Parallel EasyOCR Inference
    logger.info(f"Starting parallel EasyOCR processing for {len(files)} images...")
    tasks = [
        easyocr_service.extract_single_safe(item[0], item[1])
        for item in images_payload
    ]
    raw_results = await asyncio.gather(*tasks)

    # 3. Update database and collect output
    processed_count = 0
    results: List[OCRItemResult] = []
    combined_texts: List[str] = []

    for i, res in enumerate(raw_results):
        job = jobs_created[i]
        filename = res["filename"]
        success = res["success"]
        text = res["text"]
        lines = res["lines"]
        err = res["error"]

        if success and text:
            job.status = JobStatus.COMPLETED
            job.extracted_text = text
            job.error = None
            processed_count += 1
            combined_texts.append(f"[{filename}]\n{text}")
        else:
            job.status = JobStatus.FAILED
            job.error = err or "No text detected"

        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Sync to Supabase
        try:
            from app.core.supabase import get_supabase_client
            supabase = get_supabase_client()
            if supabase:
                supabase.table("jobs").upsert({
                    "id": job.id,
                    "original_filename": filename,
                    "image_path": job.image_path,
                    "file_size": job.file_size,
                    "status": job.status.value,
                    "extracted_text": text if success else None,
                    "error": err,
                    "updated_at": job.updated_at.isoformat(),
                }).execute()
        except Exception as sup_err:
            logger.warning(f"Supabase sync warning for {job.id}: {sup_err}")

        results.append(
            OCRItemResult(
                filename=filename,
                success=success,
                jobId=job.id,
                text=text,
                lines=lines,
                lineCount=res["lineCount"],
                charCount=res["charCount"],
                error=err,
            )
        )

    # 4. Sequentially Sync into Google Docs
    full_combined_text = "\n\n".join(combined_texts)
    gdoc_updated = False

    if update_google_doc and target_doc_id and full_combined_text.strip():
        try:
            logger.info(f"Syncing batch text ({len(combined_texts)} items) into Google Doc '{target_doc_id}'")
            await google_docs_service.update_document(
                document_id=target_doc_id,
                text=full_combined_text,
            )
            gdoc_updated = True
            logger.info("Google Doc updated successfully with batch OCR content")
        except Exception as gdoc_err:
            logger.error(f"Failed to update Google Doc '{target_doc_id}': {gdoc_err}")

    execution_duration = round(time.time() - start_time, 2)

    return BatchOCRResponse(
        success=True,
        total=len(files),
        processed=processed_count,
        documentId=target_doc_id if gdoc_updated else target_doc_id,
        googleDocUpdated=gdoc_updated,
        results=results,
        combinedText=full_combined_text,
        executionTimeSeconds=execution_duration,
        message=f"{processed_count} of {len(files)} images extracted in {execution_duration}s"
        + (" and synced to Google Docs" if gdoc_updated else ""),
    )


@router.post(
    "/extract",
    response_model=SingleOCRResponse,
    status_code=status.HTTP_200_OK,
    summary="Single image OCR extraction",
    description="Extracts Hindi and English text from a single image using EasyOCR.",
)
async def process_single_ocr(
    file: UploadFile = File(..., description="Image file"),
    documentId: Optional[str] = Form(None, description="Optional Google Document ID to update"),
    update_google_doc: bool = Form(False, description="Whether to update Google Docs"),
    easyocr_service: EasyOCRService = Depends(get_easyocr_service_dep),
    google_docs_service: BaseGoogleDocsService = Depends(get_google_docs_service_dep),
) -> SingleOCRResponse:
    file_bytes = await file.read()
    filename = file.filename or "image.png"
    job_id = str(uuid.uuid4())

    res = await easyocr_service.extract_text(file_bytes)
    text = res["text"]
    lines = res["lines"]

    gdoc_updated = False
    settings = get_settings()
    target_doc = documentId or settings.DEFAULT_GOOGLE_DOC_ID

    if update_google_doc and target_doc and text:
        try:
            await google_docs_service.update_document(
                document_id=target_doc,
                text=f"[{filename}]\n{text}",
            )
            gdoc_updated = True
        except Exception as e:
            logger.error(f"Failed to update Google Doc: {e}")

    return SingleOCRResponse(
        success=True,
        filename=filename,
        jobId=job_id,
        text=text,
        lines=lines,
        documentId=target_doc if gdoc_updated else None,
        googleDocUpdated=gdoc_updated,
    )

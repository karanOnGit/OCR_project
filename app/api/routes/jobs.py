from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import JobNotFoundException
from app.models.job import Job, JobStatus
from app.schemas.job import JobResponse

router = APIRouter(tags=["Job Status"])


@router.get(
    "/job/{job_id}",
    response_model=JobResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Get job status and result",
    description="Returns the current status (uploaded, processing, completed, failed) and extracted text for a given job ID.",
)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise JobNotFoundException(job_id)

    status_val = job.status.value if isinstance(job.status, JobStatus) else job.status

    return JobResponse(
        jobId=job.id,
        status=status_val,
        text=job.extracted_text if job.status == JobStatus.COMPLETED else None,
        error=job.error if job.status == JobStatus.FAILED else None,
    )

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class JobResponse(BaseModel):
    jobId: str = Field(..., description="Job UUID")
    status: str = Field(..., description="Job status: uploaded, processing, completed, failed")
    text: Optional[str] = Field(None, description="Extracted document text")
    error: Optional[str] = Field(None, description="Error message if processing failed")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "jobId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "completed",
                "text": "Extracted document text...",
            }
        },
    )

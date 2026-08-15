from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProcessRequest(BaseModel):
    jobId: str = Field(..., description="Unique UUID identifier of the uploaded job to process")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "jobId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            }
        },
    )


class ProcessResponse(BaseModel):
    success: bool = True
    jobId: str = Field(..., description="Job UUID")
    status: str = Field(..., description="Processing status: processing, completed, or failed")
    text: Optional[str] = Field(None, description="Extracted document text (when completed)")
    error: Optional[str] = Field(None, description="Error message if processing failed")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "jobId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "completed",
                "text": "INVOICE #1024\nDate: 2026-08-15\nTotal: $150.00",
            }
        },
    )

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    success: bool = True
    jobId: str = Field(..., description="Unique UUID identifier for the created processing job")
    message: str = Field("Image uploaded successfully", description="Status message")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "jobId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message": "Image uploaded successfully",
            }
        },
    )


class BatchJobItem(BaseModel):
    jobId: str = Field(..., description="Unique UUID identifier")
    filename: Optional[str] = Field(None, description="Original filename")
    status: str = Field(..., description="Job status: uploaded, completed, failed")
    text: Optional[str] = Field(None, description="Extracted OCR text")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchProcessResponse(BaseModel):
    success: bool = True
    total: int = Field(..., description="Total number of uploaded files")
    completed: int = Field(..., description="Number of successfully processed files")
    documentId: Optional[str] = Field(None, description="Updated Google Document ID if provided")
    jobs: List[BatchJobItem] = Field(..., description="List of processed job details")
    message: str = Field("Batch processed successfully", description="Status message")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "total": 2,
                "completed": 2,
                "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
                "jobs": [
                  {
                    "jobId": "1ad46764-42f3-4192-867c-3e34bb3a932e",
                    "filename": "page1.png",
                    "status": "completed",
                    "text": "Extracted text from page 1...",
                  },
                  {
                    "jobId": "2be57875-53g4-5203-978d-4f45cc4b043f",
                    "filename": "page2.png",
                    "status": "completed",
                    "text": "Extracted text from page 2...",
                  }
                ],
                "message": "2 documents processed and synced to Google Docs successfully"
            }
        },
    )

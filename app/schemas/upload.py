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

from pydantic import BaseModel, ConfigDict, Field


class GoogleDocsRequest(BaseModel):
    jobId: str = Field(..., description="Job UUID containing extracted OCR text")
    documentId: str = Field(..., description="Target Google Document ID")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "jobId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "documentId": "195P9TGajq50RnYWSmNV5004LJU50wb2Mg1IUR4WvTk4",
            }
        },
    )


class GoogleDocsResponse(BaseModel):
    success: bool = True
    jobId: str = Field(..., description="Job UUID")
    documentId: str = Field(..., description="Google Document ID")
    message: str = Field("Document updated successfully", description="Status message")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "jobId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "documentId": "195P9TGajq50RnYWSmNV5004LJU50wb2Mg1IUR4WvTk4",
                "message": "Document updated successfully",
            }
        },
    )

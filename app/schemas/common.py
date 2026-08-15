from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "JOB_NOT_FOUND",
                "message": "Processing job was not found",
                "details": None,
            }
        }
    )


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": "Processing job was not found",
                },
            }
        }
    )

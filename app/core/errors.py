from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


HTTP_413_TOO_LARGE = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
HTTP_422_UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class AppException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        message: str = "An error occurred",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(self.message)


class JobNotFoundException(AppException):
    def __init__(self, job_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="JOB_NOT_FOUND",
            message=f"Processing job '{job_id}' was not found",
        )


class ImageNotFoundException(AppException):
    def __init__(self, message: str = "Image file was not found on disk"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="IMAGE_NOT_FOUND",
            message=message,
        )


class FileTooLargeException(AppException):
    def __init__(self, max_size_mb: int):
        super().__init__(
            status_code=HTTP_413_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message=f"File exceeds maximum allowed size of {max_size_mb} MB",
        )


class InvalidFileTypeException(AppException):
    def __init__(self, message: str = "Invalid file type. Allowed formats: JPG, JPEG, PNG, WEBP"):
        super().__init__(
            status_code=HTTP_422_UNPROCESSABLE,
            code="INVALID_FILE_TYPE",
            message=message,
        )


class OCRProcessingException(AppException):
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="OCR_PROCESSING_ERROR",
            message=message,
        )


class GoogleDocsException(AppException):
    def __init__(self, message: str = "Failed to update Google Document", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, code: str = "GOOGLE_DOCS_ERROR"):
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    content: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
        },
    }
    if exc.details:
        content["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        413: "FILE_TOO_LARGE",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred"
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first_error = errors[0]["msg"] if errors else "Validation failed"
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": first_error,
                "details": errors,
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred",
            },
        },
    )

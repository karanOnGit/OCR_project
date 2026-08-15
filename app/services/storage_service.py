import os
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

from app.core.config import Settings, get_settings
from app.core.errors import FileTooLargeException, InvalidFileTypeException, ImageNotFoundException


class StorageService:
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()

    def validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Validates uploaded file extension and content type.
        Returns normalized extension and content type.
        """
        filename = file.filename or ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        if not ext or ext not in self.settings.ALLOWED_EXTENSIONS:
            raise InvalidFileTypeException(
                f"Invalid file extension '.{ext}'. Allowed: {', '.join(sorted(self.settings.ALLOWED_EXTENSIONS))}"
            )

        content_type = file.content_type or ""
        if content_type and content_type not in self.settings.ALLOWED_MIME_TYPES:
            # Check if extension is valid even if mime is generic octet-stream
            if content_type != "application/octet-stream":
                raise InvalidFileTypeException(
                    f"Invalid MIME type '{content_type}'. Allowed: {', '.join(sorted(self.settings.ALLOWED_MIME_TYPES))}"
                )

        return ext, content_type

    async def save_upload_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Validates and saves the uploaded file securely.
        Returns: (file_id, file_path, file_size)
        """
        ext, _ = self.validate_file(file)
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}.{ext}"
        destination_path = self.settings.upload_path / safe_filename

        total_bytes = 0
        chunk_size = 1024 * 64  # 64 KB

        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > self.settings.max_file_size_bytes:
                    # Clean up the partially written file
                    buffer.close()
                    if destination_path.exists():
                        destination_path.unlink()
                    raise FileTooLargeException(self.settings.MAX_FILE_SIZE_MB)
                buffer.write(chunk)

        return file_id, str(destination_path.resolve()), total_bytes

    def get_file_path(self, path_str: str) -> Path:
        """
        Validates and returns the file path, verifying it exists on disk.
        """
        path = Path(path_str)
        if path.exists() and path.is_file():
            return path.resolve()

        if not path.is_absolute():
            path = self.settings.upload_path / path_str
            
        if not path.exists() or not path.is_file():
            raise ImageNotFoundException(f"Image file '{path.name}' not found on server")
            
        return path.resolve()

    def delete_file(self, path_str: str) -> bool:
        """
        Safely deletes a file from disk if it exists.
        """
        try:
            path = Path(path_str)
            if path.exists() and path.is_file():
                path.unlink()
                return True
        except Exception:
            pass
        return False

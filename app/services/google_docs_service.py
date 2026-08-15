import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError

from app.core.config import Settings, get_settings
from app.core.errors import GoogleDocsException

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]


class BaseGoogleDocsService(ABC):
    @abstractmethod
    async def update_document(self, document_id: str, text: str) -> Dict[str, Any]:
        """Insert or append text into the target Google Document."""
        pass


class GoogleDocsService(BaseGoogleDocsService):
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def _get_credentials(self):
        """Load Google credentials from service account or OAuth configuration."""
        # Check for service account credentials (filepath, raw JSON string, or Base64 JSON)
        if self.settings.GOOGLE_APPLICATION_CREDENTIALS:
            cred_val = self.settings.GOOGLE_APPLICATION_CREDENTIALS.strip()
            
            # Check if Base64 encoded JSON string
            if not cred_val.startswith("{") and not cred_val.endswith(".json") and len(cred_val) > 100:
                try:
                    import base64
                    decoded = base64.b64decode(cred_val).decode("utf-8")
                    if decoded.startswith("{"):
                        cred_val = decoded
                except Exception:
                    pass

            # Check if JSON string directly
            if cred_val.startswith("{") and cred_val.endswith("}"):
                try:
                    import json
                    info = json.loads(cred_val)
                    return service_account.Credentials.from_service_account_info(
                        info,
                        scopes=SCOPES,
                    )
                except Exception as e:
                    logger.error(f"Failed to parse GOOGLE_APPLICATION_CREDENTIALS JSON string: {e}")
                    raise GoogleDocsException(
                        f"Failed to parse Google credentials JSON: {str(e)}",
                        code="GOOGLE_AUTH_ERROR",
                    ) from e

            # Check if file path
            cred_path = Path(cred_val)
            if not cred_path.is_absolute():
                cred_path = Path.cwd() / cred_val

            if cred_path.exists() and cred_path.is_file():
                try:
                    return service_account.Credentials.from_service_account_file(
                        str(cred_path),
                        scopes=SCOPES,
                    )
                except Exception as e:
                    logger.error(f"Failed to load service account credentials from {cred_path}: {e}")
                    raise GoogleDocsException(
                        f"Failed to load Google credentials file: {str(e)}",
                        code="GOOGLE_AUTH_ERROR",
                    ) from e
            else:
                logger.warning(f"Google credentials file not found at: {cred_path}")

        # If not provided, try default credentials
        try:
            import google.auth
            credentials, _ = google.auth.default(scopes=SCOPES)
            return credentials
        except (DefaultCredentialsError, Exception) as e:
            raise GoogleDocsException(
                "Google Docs credentials not configured. Please set GOOGLE_APPLICATION_CREDENTIALS in .env",
                code="GOOGLE_CREDENTIALS_MISSING",
                status_code=400,
            ) from e

    def _sync_insert_text(self, document_id: str, text: str) -> Dict[str, Any]:
        """Synchronous Google Docs API call to insert text at the end of a document."""
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
        except ImportError as e:
            raise GoogleDocsException("google-api-python-client is not installed") from e

        credentials = self._get_credentials()

        try:
            service = build("docs", "v1", credentials=credentials, cache_discovery=False)
            
            # First, fetch document metadata to get end index or verify existence
            doc = service.documents().get(documentId=document_id).execute()
            
            # Prepare text to append
            content_to_insert = f"\n\n--- Extracted Document Text ---\n{text}\n"
            
            # Find the end index of the document
            content = doc.get("body", {}).get("content", [])
            end_index = 1
            if content:
                end_index = max(1, content[-1].get("endIndex", 1) - 1)

            requests = [
                {
                    "insertText": {
                        "location": {
                            "index": end_index,
                        },
                        "text": content_to_insert,
                    }
                }
            ]

            result = (
                service.documents()
                .batchUpdate(documentId=document_id, body={"requests": requests})
                .execute()
            )

            return {
                "documentId": document_id,
                "title": doc.get("title", ""),
                "replies": result.get("replies", []),
            }

        except HttpError as error:
            logger.error(f"Google Docs API HTTP error: {error}")
            status_code = error.resp.status if hasattr(error, "resp") else 500
            error_message = error.reason if hasattr(error, "reason") else str(error)
            
            if status_code == 404:
                raise GoogleDocsException(
                    f"Google Document '{document_id}' not found or access denied.",
                    status_code=404,
                    code="DOCUMENT_NOT_FOUND",
                )
            elif status_code == 403:
                raise GoogleDocsException(
                    f"Permission denied for Google Document '{document_id}'. Share the doc with the service account email.",
                    status_code=403,
                    code="GOOGLE_PERMISSION_DENIED",
                )
            else:
                raise GoogleDocsException(
                    f"Google Docs API error ({status_code}): {error_message}",
                    status_code=status_code,
                    code="GOOGLE_API_ERROR",
                )
        except Exception as e:
            if isinstance(e, GoogleDocsException):
                raise
            logger.error(f"Unexpected error updating Google Doc: {e}")
            raise GoogleDocsException(f"Failed to update Google Document: {str(e)}") from e

    async def update_document(self, document_id: str, text: str) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_insert_text, document_id, text)


class MockGoogleDocsService(BaseGoogleDocsService):
    """Mock service for testing Google Docs integration without real API calls."""
    async def update_document(self, document_id: str, text: str) -> Dict[str, Any]:
        if document_id == "invalid-doc-id":
            raise GoogleDocsException(
                f"Google Document '{document_id}' not found",
                status_code=404,
                code="DOCUMENT_NOT_FOUND",
            )
        if document_id == "forbidden-doc-id":
            raise GoogleDocsException(
                f"Permission denied for Google Document '{document_id}'",
                status_code=403,
                code="GOOGLE_PERMISSION_DENIED",
            )
        return {
            "documentId": document_id,
            "title": "Mock Document Title",
            "text_appended_length": len(text),
            "status": "success",
        }


def get_google_docs_service(settings: Optional[Settings] = None) -> BaseGoogleDocsService:
    settings = settings or get_settings()
    if settings.APP_ENV == "test":
        return MockGoogleDocsService()
    return GoogleDocsService(settings=settings)

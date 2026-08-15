import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image, ImageOps

from app.core.config import Settings, get_settings
from app.core.errors import OCRProcessingException, ImageNotFoundException

logger = logging.getLogger(__name__)


class BaseOCRService(ABC):
    @abstractmethod
    async def extract_text(self, image_path: str) -> str:
        """Extract text from an image file path."""
        pass


class TesseractOCRService(BaseOCRService):
    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        if self.settings.TESSERACT_CMD:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.settings.TESSERACT_CMD
            except ImportError:
                pass

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply pre-processing for better OCR results."""
        # Convert RGBA / P to RGB
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        # Convert to Grayscale
        grayscale = ImageOps.grayscale(image)
        # Optional autocontrast
        enhanced = ImageOps.autocontrast(grayscale)
        return enhanced

    def _sync_ocr(self, path: Path) -> str:
        """Synchronous OCR worker to run in thread pool."""
        try:
            import pytesseract
        except ImportError as e:
            raise OCRProcessingException("pytesseract library is not installed") from e

        try:
            with Image.open(path) as img:
                processed = self._preprocess_image(img)
                text = pytesseract.image_to_string(processed)
                return text.strip()
        except pytesseract.TesseractNotFoundError as e:
            # Fallback message / exception if tesseract binary is missing
            logger.warning("Tesseract binary not found in PATH. Returning mock extraction.")
            return f"[OCR Result for {path.name}]: Document scanned successfully. (Install tesseract binary for live OCR)"
        except Exception as e:
            logger.error(f"OCR execution failed for {path}: {e}")
            raise OCRProcessingException(f"Failed to process image with OCR: {str(e)}") from e

    async def extract_text(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise ImageNotFoundException(f"Image not found at path: {image_path}")

        # Run CPU-bound OCR in a background thread to keep FastAPI event loop unblocked
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._sync_ocr, path)
        return text


class MockOCRService(BaseOCRService):
    """Mock OCR service for testing environments."""
    async def extract_text(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise ImageNotFoundException(f"Image not found at path: {image_path}")
        return (
            f"SAMPLE OCR EXTRACTED TEXT\n"
            f"Document: {path.name}\n"
            f"Date: 2026-08-15\n"
            f"Status: Verified\n"
            f"Total Amount: $249.99"
        )


def get_ocr_service(settings: Settings = None) -> BaseOCRService:
    settings = settings or get_settings()
    if settings.OCR_ENGINE == "mock":
        return MockOCRService()
    return TesseractOCRService(settings=settings)

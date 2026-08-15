import asyncio
from functools import lru_cache
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Global singleton reader instance
_easyocr_reader = None
_reader_lock = asyncio.Lock()


def get_easyocr_reader(languages: Optional[List[str]] = None):
    """
    Lazy loads and returns the singleton EasyOCR Reader.
    Supports Hindi ('hi') and English ('en') by default.
    """
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        langs = languages or ["hi", "en"]
        logger.info(f"Initializing EasyOCR Reader with languages: {langs}")
        _easyocr_reader = easyocr.Reader(langs, gpu=False)
        logger.info("EasyOCR Reader initialized successfully")
    return _easyocr_reader


class EasyOCRService:
    def __init__(self, languages: Optional[List[str]] = None):
        self.languages = languages or ["hi", "en"]

    def _sync_readtext_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Synchronous CPU inference function."""
        reader = get_easyocr_reader(self.languages)
        
        # Load image via PIL and convert to numpy array (RGB)
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        image_np = np.array(image)

        # Run EasyOCR extraction
        lines: List[str] = reader.readtext(image_np, detail=0)
        full_text = "\n".join(lines).strip()

        return {
            "text": full_text,
            "lines": lines,
            "lineCount": len(lines),
            "charCount": len(full_text),
        }

    async def extract_text(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract text asynchronously from image bytes in a worker thread."""
        return await asyncio.to_thread(self._sync_readtext_from_bytes, image_bytes)

    async def extract_batch(
        self,
        images: List[Tuple[str, bytes]],
    ) -> List[Dict[str, Any]]:
        """
        Extract text concurrently from multiple images.
        images: List of tuples (filename, image_bytes)
        """
        tasks = []
        for filename, b in images:
            task = self.extract_single_safe(filename, b)
            tasks.append(task)

        return await asyncio.gather(*tasks)

    async def extract_single_safe(self, filename: str, image_bytes: bytes) -> Dict[str, Any]:
        try:
            res = await self.extract_text(image_bytes)
            return {
                "filename": filename,
                "success": True,
                "text": res["text"],
                "lines": res["lines"],
                "lineCount": res["lineCount"],
                "charCount": res["charCount"],
                "error": None,
            }
        except Exception as e:
            logger.error(f"EasyOCR failed on {filename}: {e}")
            return {
                "filename": filename,
                "success": False,
                "text": "",
                "lines": [],
                "lineCount": 0,
                "charCount": 0,
                "error": str(e),
            }


@lru_cache()
def get_easyocr_service() -> EasyOCRService:
    return EasyOCRService()

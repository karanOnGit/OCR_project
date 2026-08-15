from unittest.mock import patch
from app.services.ocr_service import BaseOCRService
from app.core.errors import OCRProcessingException


def test_process_valid_job(client, sample_image_bytes):
    # 1. Upload an image
    upload_res = client.post(
        "/api/upload",
        files={"file": ("invoice.png", sample_image_bytes, "image/png")},
    )
    job_id = upload_res.json()["jobId"]

    # 2. Trigger processing
    process_res = client.post("/api/process", json={"jobId": job_id})
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["success"] is True
    assert data["jobId"] == job_id
    assert data["status"] == "completed"
    assert "SAMPLE OCR EXTRACTED TEXT" in data["text"]


def test_process_non_existent_job(client):
    response = client.post("/api/process", json={"jobId": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "JOB_NOT_FOUND"


def test_process_ocr_failure(client, sample_image_bytes):
    # Upload an image
    upload_res = client.post(
        "/api/upload",
        files={"file": ("receipt.png", sample_image_bytes, "image/png")},
    )
    job_id = upload_res.json()["jobId"]

    class FailingOCRService(BaseOCRService):
        async def extract_text(self, image_path: str) -> str:
            raise RuntimeError("OCR Engine crashed")

    from app.api.deps import get_ocr_service_dep
    from app.main import app
    app.dependency_overrides[get_ocr_service_dep] = lambda: FailingOCRService()

    try:
        response = client.post("/api/process", json={"jobId": job_id})
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "OCR_PROCESSING_ERROR"

        # Verify job status in DB is failed
        job_res = client.get(f"/api/job/{job_id}")
        assert job_res.status_code == 200
        job_data = job_res.json()
        assert job_data["status"] == "failed"
        assert "OCR Engine crashed" in job_data["error"]
    finally:
        from app.services.ocr_service import MockOCRService
        app.dependency_overrides[get_ocr_service_dep] = lambda: MockOCRService()

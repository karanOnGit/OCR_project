import io
import pytest


def test_upload_valid_image(client, sample_image_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("document.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "jobId" in data
    assert len(data["jobId"]) > 0
    assert data["message"] == "Image uploaded successfully"


def test_upload_invalid_file_extension(client):
    response = client.post(
        "/api/upload",
        files={"file": ("malicious.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_FILE_TYPE"
    assert "Invalid file extension" in data["error"]["message"]


def test_upload_file_too_large(client, test_settings):
    # test_settings has MAX_FILE_SIZE_MB=2, so 3MB should fail
    large_content = b"x" * (3 * 1024 * 1024)
    response = client.post(
        "/api/upload",
        files={"file": ("large_doc.png", large_content, "image/png")},
    )
    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_missing_file_payload(client):
    response = client.post("/api/upload")
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

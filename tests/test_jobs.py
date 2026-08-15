from app.models.job import Job, JobStatus


def test_get_job_uploaded_status(client, sample_image_bytes):
    # Upload an image
    upload_res = client.post(
        "/api/upload",
        files={"file": ("photo.jpg", sample_image_bytes, "image/jpeg")},
    )
    job_id = upload_res.json()["jobId"]

    # Query status
    response = client.get(f"/api/job/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["jobId"] == job_id
    assert data["status"] == "uploaded"
    assert data.get("text") is None


def test_get_job_completed_status(client, sample_image_bytes):
    # Upload & process
    upload_res = client.post(
        "/api/upload",
        files={"file": ("photo.jpg", sample_image_bytes, "image/jpeg")},
    )
    job_id = upload_res.json()["jobId"]
    client.post("/api/process", json={"jobId": job_id})

    # Query status
    response = client.get(f"/api/job/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["jobId"] == job_id
    assert data["status"] == "completed"
    assert "SAMPLE OCR EXTRACTED TEXT" in data["text"]


def test_get_non_existent_job(client):
    response = client.get("/api/job/non-existent-uuid")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "JOB_NOT_FOUND"

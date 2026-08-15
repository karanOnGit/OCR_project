def test_update_google_doc_success(client, sample_image_bytes):
    # Upload and process an image
    upload_res = client.post(
        "/api/upload",
        files={"file": ("contract.png", sample_image_bytes, "image/png")},
    )
    job_id = upload_res.json()["jobId"]
    client.post("/api/process", json={"jobId": job_id})

    # Update Google Doc
    doc_id = "1A2B3C4D5E6F7G8H9I0J"
    response = client.post(
        "/api/update-google-doc",
        json={"jobId": job_id, "documentId": doc_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["jobId"] == job_id
    assert data["documentId"] == doc_id
    assert data["message"] == "Document updated successfully"


def test_update_google_doc_job_not_processed_yet(client, sample_image_bytes):
    # Upload without processing
    upload_res = client.post(
        "/api/upload",
        files={"file": ("notes.png", sample_image_bytes, "image/png")},
    )
    job_id = upload_res.json()["jobId"]

    response = client.post(
        "/api/update-google-doc",
        json={"jobId": job_id, "documentId": "some-doc-id"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "JOB_NOT_READY"


def test_update_google_doc_missing_job(client):
    response = client.post(
        "/api/update-google-doc",
        json={"jobId": "invalid-job-id", "documentId": "some-doc-id"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "JOB_NOT_FOUND"


def test_update_google_doc_api_not_found_error(client, sample_image_bytes):
    # Upload and process
    upload_res = client.post(
        "/api/upload",
        files={"file": ("contract.png", sample_image_bytes, "image/png")},
    )
    job_id = upload_res.json()["jobId"]
    client.post("/api/process", json={"jobId": job_id})

    # Update with document ID that triggers 404 in mock
    response = client.post(
        "/api/update-google-doc",
        json={"jobId": job_id, "documentId": "invalid-doc-id"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_update_google_doc_permission_denied(client, sample_image_bytes):
    # Upload and process
    upload_res = client.post(
        "/api/upload",
        files={"file": ("contract.png", sample_image_bytes, "image/png")},
    )
    job_id = upload_res.json()["jobId"]
    client.post("/api/process", json={"jobId": job_id})

    # Update with document ID that triggers 403 in mock
    response = client.post(
        "/api/update-google-doc",
        json={"jobId": job_id, "documentId": "forbidden-doc-id"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "GOOGLE_PERMISSION_DENIED"

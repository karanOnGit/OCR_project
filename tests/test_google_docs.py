def test_update_google_doc_direct_text_success(client):
    doc_id = "1A2B3C4D5E6F7G8H9I0J"
    text_content = "Extracted OCR text directly from Flutter ML Kit."
    response = client.post(
        "/api/update-google-doc",
        json={
            "documentId": doc_id,
            "text": text_content,
            "title": "Page 1",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["documentId"] == doc_id
    assert data["message"] == "Document updated successfully"
    assert data["charactersAppended"] > 0


def test_update_google_doc_default_document_id(client):
    response = client.post(
        "/api/update-google-doc",
        json={
            "text": "Extracted text without documentId provided.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["documentId"] == "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk"


def test_update_google_doc_empty_text_error(client):
    response = client.post(
        "/api/update-google-doc",
        json={
            "text": "   ",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMPTY_TEXT"


def test_update_google_doc_api_not_found_error(client):
    response = client.post(
        "/api/update-google-doc",
        json={
            "documentId": "invalid-doc-id",
            "text": "Valid text payload",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_update_google_doc_permission_denied(client):
    response = client.post(
        "/api/update-google-doc",
        json={
            "documentId": "forbidden-doc-id",
            "text": "Valid text payload",
        },
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "GOOGLE_PERMISSION_DENIED"

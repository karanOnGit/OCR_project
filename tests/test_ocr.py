import os
import io
from PIL import Image, ImageDraw


def test_ocr_extract_single(client):
    # Create test image with text
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "HELLO EASYOCR", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/ocr/extract",
        files={"file": ("test_sample.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "text" in data
    assert "lines" in data


def test_ocr_batch_parallel(client):
    # Create 2 test images
    img1 = Image.new("RGB", (300, 80), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.text((10, 30), "DOCUMENT PAGE ONE", fill=(0, 0, 0))
    buf1 = io.BytesIO()
    img1.save(buf1, format="PNG")

    img2 = Image.new("RGB", (300, 80), color=(255, 255, 255))
    draw2 = ImageDraw.Draw(img2)
    draw2.text((10, 30), "DOCUMENT PAGE TWO", fill=(0, 0, 0))
    buf2 = io.BytesIO()
    img2.save(buf2, format="PNG")

    response = client.post(
        "/api/ocr/batch",
        files=[
            ("files", ("page1.png", buf1.getvalue(), "image/png")),
            ("files", ("page2.png", buf2.getvalue(), "image/png")),
        ],
        data={
            "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
            "update_google_doc": "true",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 2
    assert data["processed"] == 2
    assert len(data["results"]) == 2
    assert "combinedText" in data
    assert data["executionTimeSeconds"] >= 0

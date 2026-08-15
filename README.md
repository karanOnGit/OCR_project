# CaptureBackend - FastAPI EasyOCR & Google Docs Backend

A production-ready FastAPI backend in Python supporting **EasyOCR (Hindi `hi` + English `en`)**, parallel multi-image batch extraction, and real-time syncing to **Google Docs** and **Supabase**.

---

## 🏗️ Core Flow

```text
Flutter Mobile App / Client
       ↓
POST /api/ocr/batch (Multi-image upload)
       ↓
1. Concurrent / Parallel EasyOCR Inference (Hindi + English)
2. Sync records to SQLite & Supabase
3. Sequentially append all extracted text to Google Docs in order
       ↓
Google Docs API v1 & Supabase Jobs Table
```

---

## 📡 API Endpoints

### 1. Batch Multi-Image EasyOCR & Google Docs Sync
`POST /api/ocr/batch` (multipart/form-data)

**Parameters:**
- `files`: List of image files (`.jpg`, `.jpeg`, `.png`, `.webp`)
- `documentId`: (Optional) Target Google Document ID or full URL (defaults to `1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk`)
- `update_google_doc`: `true` (default) or `false`

**cURL Example:**
```bash
curl -X 'POST' \
  'https://capture-backend-ocr.onrender.com/api/ocr/batch' \
  -H 'accept: application/json' \
  -F 'files=@test_01.png;type=image/png' \
  -F 'files=@test_02.png;type=image/png' \
  -F 'update_google_doc=true'
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "total": 2,
  "processed": 2,
  "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
  "googleDocUpdated": true,
  "results": [
    {
      "filename": "test_01.png",
      "success": true,
      "jobId": "8a56e007-8d91-43c2-8a98-ccba8ac5204b",
      "text": "में गधा सबसे ज्यादा बुद्धिहीन समझता जाता है...",
      "lines": ["में गधा सबसे ज्यादा बुद्धिहीन समझता जाता है", "हम जब किसी"],
      "lineCount": 16,
      "charCount": 622,
      "error": null
    }
  ],
  "combinedText": "[test_01.png]\nमें गधा सबसे ज्यादा बुद्धिहीन समझता जाता है...\n\n[test_02.png]\n...",
  "executionTimeSeconds": 2.15,
  "message": "2 of 2 images extracted in 2.15s and synced to Google Docs"
}
```

---

### 2. Single Image EasyOCR Extraction
`POST /api/ocr/extract` (multipart/form-data)

**cURL Example:**
```bash
curl -X 'POST' \
  'https://capture-backend-ocr.onrender.com/api/ocr/extract' \
  -H 'accept: application/json' \
  -F 'file=@test_01.png;type=image/png'
```

---

### 3. Direct Text Sync to Google Docs
`POST /api/update-google-doc` (application/json)

```json
{
  "text": "Any extracted text...",
  "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
  "title": "Page 1"
}
```

---

## 📱 Flutter / Dart Integration Code

Add `http` to `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.2.0
```

`lib/services/api_service.dart`:
```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://capture-backend-ocr.onrender.com/api';
  static const String defaultDocId = '1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk';

  /// Parallel Batch OCR with EasyOCR (Hindi + English) & Google Docs Sync
  static Future<Map<String, dynamic>> processBatchImages({
    required List<File> imageFiles,
    String? documentId,
    bool updateGoogleDoc = true,
  }) async {
    final uri = Uri.parse('$baseUrl/ocr/batch');
    final request = http.MultipartRequest('POST', uri);

    for (final file in imageFiles) {
      request.files.add(await http.MultipartFile.fromPath('files', file.path));
    }

    request.fields['documentId'] = documentId ?? defaultDocId;
    request.fields['update_google_doc'] = updateGoogleDoc.toString();

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      final err = jsonDecode(response.body);
      throw Exception(err['error']?['message'] ?? 'Batch OCR failed');
    }
  }
}
```

---

## 🧪 Testing

```bash
pytest -v
```

# CaptureBackend - FastAPI Google Docs & Supabase Sync Backend

A clean, production-ready FastAPI backend in Python designed to sync document text extracted via on-device **Google ML Kit** in Flutter directly to **Google Docs** and **Supabase**.

---

## 🏗️ Core Flow

```text
Flutter App (Google ML Kit on-device OCR)
       ↓
POST /api/update-google-doc { text: "...", documentId: "..." }
       ↓
1. Append text to Google Document (Google Docs API v1)
2. Sync record to Supabase
```

---

## 📁 Project Structure

```text
CaptureBackend/
│
├── app/
│   ├── main.py                     # FastAPI application setup, CORS, lifespan, exception handlers
│   ├── api/
│   │   ├── deps.py                 # FastAPI dependency injection (DB session, services)
│   │   └── routes/
│   │       ├── __init__.py         # Aggregates /api router
│   │       ├── google_docs.py      # POST /api/update-google-doc (Direct ML Kit text sync)
│   │       └── upload.py           # POST /api/upload (Optional image storage)
│   │
│   ├── core/
│   │   ├── config.py               # Pydantic Settings & environment variables
│   │   ├── database.py             # SQLAlchemy database engine (PostgreSQL / SQLite)
│   │   ├── errors.py               # Custom exceptions & uniform JSON error handlers
│   │   └── supabase.py             # Supabase client integration
│   │
│   ├── models/
│   │   └── job.py                  # SQLAlchemy Document/Job model
│   │
│   ├── schemas/
│   │   ├── common.py               # Standard error models
│   │   ├── google_docs.py          # Google Docs direct text request & response schemas
│   │   └── upload.py               # Image upload schemas
│   │
│   └── services/
│       ├── storage_service.py      # Secure file storage
│       └── google_docs_service.py  # Google Docs API v1 integration & URL parser
│
├── tests/
│   ├── conftest.py                 # Test fixtures & test client
│   ├── test_google_docs.py         # Google Docs direct text sync tests
│   └── test_upload.py              # Upload validation tests
│
├── Dockerfile                      # Ultra-lightweight Python 3.11 container
├── render.yaml                     # Render Blueprint
├── requirements.txt                # Lean Python dependencies
├── .env.example                    # Configuration template
└── README.md                       # Documentation
```

---

## 📡 API Endpoints

### 1. Update Google Document directly with ML Kit Text
`POST /api/update-google-doc` (application/json)

**Request Body:**
```json
{
  "text": "INVOICE #1024\nDate: 2026-08-15\nTotal: $150.00",
  "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
  "title": "Document Scan 1"
}
```
*(Note: `documentId` and `title` are optional. If omitted, `documentId` defaults to your configured default Google Doc)*

**Response (`200 OK`):**
```json
{
  "success": true,
  "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
  "message": "Document updated successfully",
  "charactersAppended": 45
}
```

---

## 📱 Flutter / Dart Integration Code

Add `http` package to your `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.2.0
```

`lib/services/api_service.dart`:
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://capture-backend-ocr.onrender.com/api';
  static const String defaultDocId = '1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk';

  /// Send on-device ML Kit extracted text directly to Google Docs
  static Future<Map<String, dynamic>> syncToGoogleDoc({
    required String text,
    String? title,
    String? documentId,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/update-google-doc'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'text': text,
        'title': title,
        'documentId': documentId ?? defaultDocId,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      final err = jsonDecode(response.body);
      throw Exception(err['error']?['message'] ?? 'Failed to update Google Document');
    }
  }
}
```

---

## 🧪 Testing

```bash
pytest -v
```

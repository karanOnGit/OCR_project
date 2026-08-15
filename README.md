# CaptureBackend - Google Docs & Supabase Sync API

A high-performance, minimalist Python FastAPI backend that receives document text extracted on-device via **Google ML Kit** in Flutter, appends it into your **Google Document**, and automatically persists all received records into **Supabase**.

---

## 🌐 Production API Endpoint

- **Base URL**: `https://stage.karanbhardwaj.in/api`
- **Interactive Swagger Docs**: `https://stage.karanbhardwaj.in/docs`
- **Health Check**: `https://stage.karanbhardwaj.in/health`

---

## 📡 Active API: `POST /api/update-google-doc`

Receives the on-device extracted text and appends it to the target Google Document while automatically syncing the capture record to Supabase.

### Request Specification
- **Method**: `POST`
- **URL**: `https://stage.karanbhardwaj.in/api/update-google-doc`
- **Headers**: `Content-Type: application/json`
- **Payload**:
```json
{
  "text": "Extracted Hindi/English text...",
  "title": "Document Capture - 2026-08-15 16:00",
  "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk"
}
```
*(Note: `title` and `documentId` are optional. If omitted, `documentId` automatically defaults to `1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk`)*

### Response (`200 OK`)
```json
{
  "success": true,
  "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
  "message": "Document updated successfully",
  "charactersAppended": 45,
  "supabaseSynced": true
}
```

---

## 💾 Supabase Persistence

On every successful request, the backend automatically writes a record to your Supabase `jobs` table:
- `id`: Unique UUID
- `original_filename` / `title`: Title sent from Flutter app
- `extracted_text`: Raw extracted text
- `status`: `completed`
- `created_at` / `updated_at`: UTC timestamps

---

## 📱 Flutter / Dart Implementation (`CaptureApp`)

`lib/services/api_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://stage.karanbhardwaj.in/api';
  static const String defaultDocId = '1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk';

  /// Syncs on-device extracted text to Google Docs and Supabase
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
      throw Exception(err['error']?['message'] ?? 'Failed to sync to Google Document');
    }
  }
}
```

---

## 🧪 Testing

```bash
pytest -v
```

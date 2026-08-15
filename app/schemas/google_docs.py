from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GoogleDocsRequest(BaseModel):
    text: str = Field(..., description="Extracted text from on-device ML Kit")
    title: Optional[str] = Field(None, description="Optional title or header timestamp")
    documentId: Optional[str] = Field(
        "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
        description="Target Google Document ID or full URL (defaults to configured document)",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "text": "Extracted Hindi/English text...",
                "title": "Document Capture - 2026-08-15 16:00",
                "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
            }
        },
    )


class GoogleDocsResponse(BaseModel):
    success: bool = True
    documentId: str = Field(..., description="Target Google Document ID")
    message: str = Field("Document updated successfully", description="Status message")
    charactersAppended: Optional[int] = Field(None, description="Number of characters appended")
    supabaseSynced: bool = Field(False, description="Whether entry was synced to Supabase database")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
                "message": "Document updated successfully",
                "charactersAppended": 45,
                "supabaseSynced": True,
            }
        },
    )

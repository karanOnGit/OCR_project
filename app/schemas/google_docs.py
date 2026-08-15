from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GoogleDocsRequest(BaseModel):
    text: str = Field(..., description="Extracted text from on-device ML Kit")
    documentId: Optional[str] = Field(
        "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
        description="Target Google Document ID or full URL (defaults to configured document)",
    )
    title: Optional[str] = Field(None, description="Optional section header or filename")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "text": "INVOICE #1024\nDate: 2026-08-15\nTotal: $150.00",
                "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
                "title": "Invoice Photo 1",
            }
        },
    )


class GoogleDocsResponse(BaseModel):
    success: bool = True
    documentId: str = Field(..., description="Google Document ID")
    message: str = Field("Document updated successfully", description="Status message")
    charactersAppended: Optional[int] = Field(None, description="Number of characters appended")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "documentId": "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk",
                "message": "Document updated successfully",
                "charactersAppended": 45,
            }
        },
    )

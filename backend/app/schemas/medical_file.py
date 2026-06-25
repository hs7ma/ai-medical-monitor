from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MedicalFileOut(BaseModel):
    id: int
    patient_id: int
    file_name: str
    file_type: str
    category: str
    mime_type: Optional[str]
    file_size: Optional[int]
    has_extracted_text: bool
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractedText(BaseModel):
    file_id: int
    extracted_text: str
    text_length: int

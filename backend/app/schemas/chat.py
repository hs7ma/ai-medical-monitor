from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ChatSessionOut(BaseModel):
    id: int
    patient_id: int
    user_id: int
    title: str
    status: str
    diagnosis_result: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    has_files: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StartSessionRequest(BaseModel):
    patient_id: int
    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    message: str
    file_ids: Optional[List[int]] = None


class DiagnosisResult(BaseModel):
    primary_diagnosis: str
    differential_diagnoses: List[str] = []
    severity: str
    confidence: str
    findings: List[str] = []
    possible_causes: List[str] = []
    recommendations: List[str] = []
    additional_tests: List[str] = []
    red_flags: List[str] = []
    follow_up_questions: List[str] = []

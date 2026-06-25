from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PatientBase(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    room: Optional[str] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VitalReadingCreate(BaseModel):
    spo2: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    confidence: Optional[int] = 0
    source: Optional[str] = "manual"


class VitalReadingOut(BaseModel):
    id: int
    patient_id: int
    spo2: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    confidence: Optional[int] = 0
    source: Optional[str] = "manual"
    created_at: datetime

    class Config:
        from_attributes = True

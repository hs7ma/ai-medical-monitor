from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BedAssign(BaseModel):
    patient_id: Optional[int] = None


class BedCreate(BaseModel):
    id: str
    room: Optional[str] = None


class BedOut(BaseModel):
    id: str
    room: Optional[str]
    status: str
    patient_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class VitalReading(BaseModel):
    time: str
    bed_id: str
    patient_id: Optional[str]
    spo2: Optional[float]
    heart_rate: Optional[float]
    temperature: Optional[float]
    confidence: Optional[int]


class SensorVitalsCreate(BaseModel):
    spo2: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    confidence: Optional[int] = 0
    finger_detected: Optional[bool] = False
    wifi_rssi: Optional[int] = 0
    source: Optional[str] = "sensor"

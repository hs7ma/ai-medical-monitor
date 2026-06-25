from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertOut(BaseModel):
    id: int
    bed_id: str
    patient_id: Optional[int]
    type: str
    severity: str
    message: str
    status: str
    created_at: datetime
    acked_at: Optional[datetime]
    acked_by: Optional[int]

    class Config:
        from_attributes = True


class AlertAck(BaseModel):
    pass

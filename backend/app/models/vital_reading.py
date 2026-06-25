from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class VitalReading(Base):
    __tablename__ = "vital_readings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    spo2 = Column(Float, nullable=True)
    heart_rate = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    confidence = Column(Integer, default=0)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="vital_readings")

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    phone = Column(String(20))
    room = Column(String(30))
    diagnosis = Column(String(500))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bed = relationship("Bed", back_populates="patient", uselist=False)
    alerts = relationship("Alert", back_populates="patient")
    diagnoses = relationship("Diagnosis", back_populates="patient")
    medical_files = relationship("MedicalFile", back_populates="patient")
    vital_readings = relationship("VitalReading", back_populates="patient", order_by="VitalReading.created_at.desc()")

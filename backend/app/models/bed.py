from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Bed(Base):
    __tablename__ = "beds"

    id = Column(String(20), primary_key=True)
    room = Column(String(20))
    status = Column(String(20), default="available")
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="bed")
    alerts = relationship("Alert", back_populates="bed")

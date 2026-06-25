from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    bed_id = Column(String(20), ForeignKey("beds.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(String(500), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    acked_at = Column(DateTime, nullable=True)
    acked_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    bed = relationship("Bed", back_populates="alerts")
    patient = relationship("Patient", back_populates="alerts")
    acked_by_user = relationship("User", back_populates="alerts_acked")

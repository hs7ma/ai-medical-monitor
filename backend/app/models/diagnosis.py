from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    source_vitals = Column(Boolean, default=False)
    file_ids = Column(JSON, default=list)
    diagnosis_text = Column(Text, nullable=False)
    severity = Column(String(20))
    possible_causes = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    red_flags = Column(JSON, default=list)
    confidence = Column(String(20))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="diagnoses")
    created_by_user = relationship("User", back_populates="diagnoses_made")

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class MedicalFile(Base):
    __tablename__ = "medical_files"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    category = Column(String(30), nullable=False)
    storage_key = Column(String(500), nullable=False)
    mime_type = Column(String(100))
    file_size = Column(Integer)
    extracted_text = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_files")
    uploaded_by_user = relationship("User", back_populates="files_uploaded")

    @property
    def has_extracted_text(self) -> bool:
        return self.extracted_text is not None and len(self.extracted_text) > 0

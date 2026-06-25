from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserRole(PyEnum):
    doctor = "doctor"
    nurse = "nurse"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.nurse)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    alerts_acked = relationship("Alert", back_populates="acked_by_user")
    diagnoses_made = relationship("Diagnosis", back_populates="created_by_user")
    files_uploaded = relationship("MedicalFile", back_populates="uploaded_by_user")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.bed import Bed
from app.schemas.patient import PatientCreate, PatientOut

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=List[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    return db.query(Patient).filter(Patient.is_active == True).all()


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

"""Vital signs endpoints — readings tied to patient_id."""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.vital_reading import VitalReading
from app.schemas.patient import VitalReadingCreate, VitalReadingOut

router = APIRouter(prefix="/api/patients", tags=["vitals"])


@router.post("/{patient_id}/vitals", response_model=VitalReadingOut, status_code=201)
def submit_vitals(
    patient_id: int,
    payload: VitalReadingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_active == True).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    reading = VitalReading(
        patient_id=patient_id,
        spo2=payload.spo2,
        heart_rate=payload.heart_rate,
        temperature=payload.temperature,
        confidence=payload.confidence or 0,
        source=payload.source or "manual",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/{patient_id}/vitals", response_model=List[VitalReadingOut])
def get_vitals(
    patient_id: int,
    limit: int = 50,
    minutes: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    query = db.query(VitalReading).filter(VitalReading.patient_id == patient_id)

    if minutes > 0:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        query = query.filter(VitalReading.created_at >= cutoff)

    return query.order_by(VitalReading.created_at.desc()).limit(limit).all()


@router.get("/{patient_id}/vitals/latest", response_model=VitalReadingOut)
def get_latest_vitals(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    reading = (
        db.query(VitalReading)
        .filter(VitalReading.patient_id == patient_id)
        .order_by(VitalReading.created_at.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No vitals found for this patient")
    return reading

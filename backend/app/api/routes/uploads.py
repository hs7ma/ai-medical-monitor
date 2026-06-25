import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.medical_file import MedicalFile
from app.services.storage import storage_service
from app.services.file_processor import file_processor
from app.schemas.medical_file import MedicalFileOut, ExtractedText

router = APIRouter(prefix="/api", tags=["uploads"])

VALID_CATEGORIES = {"lab", "imaging", "report", "other"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("/patients/{patient_id}/uploads", response_model=MedicalFileOut, status_code=201)
def upload_file(
    patient_id: int,
    file: UploadFile = File(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
        )

    data = file.file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    mime_type = file.content_type or "application/octet-stream"
    is_image = file_processor.is_image(mime_type)
    is_pdf = file_processor.is_pdf(mime_type)
    if not is_image and not is_pdf:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Only PDF and images are allowed.",
        )

    file_type = "image" if is_image else "pdf"
    ext = os.path.splitext(file.filename or "")[1] or (".pdf" if is_pdf else ".png")
    storage_key = f"{patient_id}/{category}/{uuid.uuid4().hex}{ext}"

    storage_service.ensure_bucket()
    if not storage_service.upload_file(storage_key, data, mime_type):
        raise HTTPException(status_code=500, detail="Failed to store file")

    extracted_text = file_processor.extract_text(data, mime_type)

    record = MedicalFile(
        patient_id=patient_id,
        file_name=file.filename or storage_key,
        file_type=file_type,
        category=category,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size=len(data),
        extracted_text=extracted_text if extracted_text else None,
        uploaded_by=user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/patients/{patient_id}/uploads", response_model=List[MedicalFileOut])
def list_uploads(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db.query(MedicalFile).filter(MedicalFile.patient_id == patient_id).all()


@router.get("/uploads/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    from fastapi import Response

    record = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    data = storage_service.download_file(record.storage_key)
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve file")
    return Response(
        content=data,
        media_type=record.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{record.file_name}"'},
    )


@router.delete("/uploads/{file_id}", status_code=204)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    record = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    storage_service.delete_file(record.storage_key)
    db.delete(record)
    db.commit()


@router.post("/uploads/{file_id}/extract", response_model=ExtractedText)
def re_extract_text(
    file_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    record = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    data = storage_service.download_file(record.storage_key)
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve file")
    text = file_processor.extract_text(data, record.mime_type or "")
    record.extracted_text = text if text else None
    db.commit()
    db.refresh(record)
    return ExtractedText(
        file_id=record.id,
        extracted_text=text or "",
        text_length=len(text or ""),
    )

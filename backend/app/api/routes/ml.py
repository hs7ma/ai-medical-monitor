"""ML prediction endpoints for local heart-disease model."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.services.ml_service import heart_prediction_service

router = APIRouter(prefix="/api/ml", tags=["ml"])


class HeartFeatures(BaseModel):
    age: Optional[float] = None
    sex: Optional[float] = None
    cp: Optional[float] = None
    trestbps: Optional[float] = None
    chol: Optional[float] = None
    fbs: Optional[float] = None
    restecg: Optional[float] = None
    thalach: Optional[float] = None
    exang: Optional[float] = None
    oldpeak: Optional[float] = None
    slope: Optional[float] = None
    ca: Optional[float] = None
    thal: Optional[float] = None
    extracted_keys: Optional[List[str]] = None
    vital_keys: Optional[List[str]] = None


@router.get("/status")
def ml_status(
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    return {"available": heart_prediction_service.is_available()}


@router.post("/predict/heart")
def predict_heart(
    payload: HeartFeatures,
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    if not heart_prediction_service.is_available():
        return {"available": False, "detail": "ML model not loaded"}
    data = payload.model_dump()
    extracted_keys = set(data.pop("extracted_keys") or [])
    vital_keys = set(data.pop("vital_keys") or [])
    result = heart_prediction_service.predict(
        data, extracted_keys=extracted_keys, vital_keys=vital_keys
    )
    if result is None:
        return {"available": False, "detail": "Prediction failed"}
    return result

"""ML prediction endpoints for local heart-disease model."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.services.ml_service import heart_prediction_service

router = APIRouter(prefix="/api/ml", tags=["ml"])


class HeartFeatures(BaseModel):
    age: float
    sex: float = 1
    cp: float = 0
    trestbps: float = 120
    chol: float = 200
    fbs: float = 0
    restecg: float = 0
    thalach: float = 150
    exang: float = 0
    oldpeak: float = 0
    slope: float = 1
    ca: float = 0
    thal: float = 0


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
    result = heart_prediction_service.predict(payload.model_dump())
    if result is None:
        return {"available": False, "detail": "Prediction failed"}
    return result

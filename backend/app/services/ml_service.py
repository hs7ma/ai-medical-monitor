"""Local ML heart-disease prediction service — calibrated 4-level risk model.

Model: HistGradientBoostingClassifier + CalibratedClassifierCV
Data: 2,138 patients (1,219 local + 920 UCI)
Accuracy: 85.5% | AUC: 0.926
Risk levels derived from calibrated probability:
  normal (<20%), low (20-50%), moderate (50-75%), high (>75%)
"""

import logging
import os
from typing import Optional

import joblib
import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")

FEATURE_ORDER = [
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope",
    "ca", "thal",
]

FEATURE_LABELS = {
    "age": "العمر",
    "sex": "الجنس (1=ذكر, 0=أنثى)",
    "cp": "نوع ألم الصدر (0-3)",
    "trestbps": "ضغط الدم عند الراحة",
    "chol": "الكوليسترول (mg/dL)",
    "fbs": "سكر الصيام >120 (1=نعم, 0=لا)",
    "restecg": "تخطيط القلب عند الراحة (0-2)",
    "thalach": "أقصى معدل لضربات القلب",
    "exang": "ذبحة مجهدة (1=نعم, 0=لا)",
    "oldpeak": "انخفاض ST الناتج عن الرياضة",
    "slope": "ميل ذروة ST (0-2)",
    "ca": "عدد الأوعية الرئيسية (0-4)",
    "thal": "نوع الثلاسيميا (0-3)",
}

FEATURE_RANGES = {
    "age": (1, 120),
    "sex": (0, 1),
    "cp": (0, 3),
    "trestbps": (80, 250),
    "chol": (80, 600),
    "fbs": (0, 1),
    "restecg": (0, 2),
    "thalach": (60, 220),
    "exang": (0, 1),
    "oldpeak": (-3, 10),
    "slope": (0, 2),
    "ca": (0, 4),
    "thal": (0, 3),
}

RISK_THRESHOLDS = [0.20, 0.50, 0.75]
RISK_LEVEL_NAMES = {0: "normal", 1: "low", 2: "moderate", 3: "high"}
RISK_LEVEL_AR = {0: "طبيعي", 1: "منخفض", 2: "متوسط", 3: "عالي"}


class HeartPredictionService:
    def __init__(self):
        self._model = None
        self._scaler = None

    def _load(self):
        if self._model is not None:
            return
        model_path = os.path.join(MODEL_DIR, "heart_model.joblib")
        scaler_path = os.path.join(MODEL_DIR, "heart_scaler.joblib")
        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            logger.warning("Model files not found at %s", MODEL_DIR)
            return
        self._model = joblib.load(model_path)
        self._scaler = joblib.load(scaler_path)
        logger.info("Loaded heart disease model (calibrated, 4-level risk)")

    def _risk_level(self, proba_positive):
        if proba_positive < RISK_THRESHOLDS[0]:
            return 0
        if proba_positive < RISK_THRESHOLDS[1]:
            return 1
        if proba_positive < RISK_THRESHOLDS[2]:
            return 2
        return 3

    def predict(self, features: dict) -> Optional[dict]:
        self._load()
        if self._model is None or self._scaler is None:
            return None

        try:
            row = []
            for col in FEATURE_ORDER:
                val = features.get(col)
                if val is None:
                    val = 0
                val = float(val)
                lo, hi = FEATURE_RANGES.get(col, (0, 1e9))
                if val < lo:
                    val = lo
                if val > hi:
                    val = hi
                row.append(val)
        except (ValueError, TypeError) as e:
            logger.warning("Feature validation error: %s", e)
            return None

        X = np.array([row])
        X_scaled = self._scaler.transform(X)

        proba = self._model.predict_proba(X_scaled)[0]
        pred = int(self._model.predict(X_scaled)[0])
        risk_score = float(proba[1]) if len(proba) > 1 else float(proba[0])
        confidence = float(max(proba))

        risk_idx = self._risk_level(risk_score)
        risk_level = RISK_LEVEL_NAMES[risk_idx]
        risk_level_ar = RISK_LEVEL_AR[risk_idx]

        # Try to get feature importances from underlying estimator
        top_features = []
        try:
            underlying = getattr(self._model, "estimator", None)
            if underlying is not None and hasattr(underlying, "feature_importances_"):
                importances = underlying.feature_importances_
            elif hasattr(self._model, "feature_importances_"):
                importances = self._model.feature_importances_
            else:
                importances = None

            if importances is not None:
                contributions = sorted(
                    zip(FEATURE_ORDER, importances),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                top_features = [
                    {"feature": FEATURE_LABELS.get(f, f), "importance": round(float(imp), 4)}
                    for f, imp in contributions
                ]
        except Exception:
            pass

        return {
            "prediction": pred,
            "prediction_label": "مرض قلبي محتمل" if pred == 1 else "طبيعي",
            "risk_score": round(risk_score, 4),
            "risk_percentage": round(risk_score * 100, 1),
            "confidence": round(confidence, 4),
            "risk_level": risk_level,
            "risk_level_index": risk_idx,
            "risk_level_ar": risk_level_ar,
            "model_name": "HistGradientBoosting + Calibrated",
            "model_accuracy": 0.855,
            "model_auc": 0.926,
            "training_size": 2138,
            "top_features": top_features,
            "features_used": {FEATURE_LABELS.get(c, c): features.get(c, 0) for c in FEATURE_ORDER},
        }

    def is_available(self) -> bool:
        self._load()
        return self._model is not None


heart_prediction_service = HeartPredictionService()

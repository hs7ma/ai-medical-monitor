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

REQUIRED_FEATURES = [
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope",
    "ca", "thal",
]

FEATURE_SOURCE_AR = {
    "extracted": "مستخرج بالذكاء الاصطناعي",
    "vital": "علامة حيوية لحظية",
    "patient": "بيانات المريض",
    "missing": "غير متوفر",
}

FEATURE_SOURCE_EN = {
    "extracted": "AI Extracted",
    "vital": "Live Vital",
    "patient": "Patient Data",
    "missing": "Missing",
}

FEATURE_LABELS_EN = {
    "age": "Age",
    "sex": "Sex (1=M, 0=F)",
    "cp": "Chest Pain Type (0-3)",
    "trestbps": "Resting Blood Pressure",
    "chol": "Cholesterol (mg/dL)",
    "fbs": "Fasting BS >120 (1=Y, 0=N)",
    "restecg": "Resting ECG (0-2)",
    "thalach": "Max Heart Rate",
    "exang": "Exercise Angina (1=Y, 0=N)",
    "oldpeak": "ST Depression",
    "slope": "ST Slope (0-2)",
    "ca": "Major Vessels (0-4)",
    "thal": "Thalassemia (0-3)",
}

RELIABILITY_AR = {"high": "عالية", "medium": "متوسطة", "low": "منخفضة"}


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

    def predict(self, features: dict, extracted_keys: Optional[set] = None, vital_keys: Optional[set] = None) -> Optional[dict]:
        self._load()
        if self._model is None or self._scaler is None:
            return None

        if extracted_keys is None:
            extracted_keys = set()
        if vital_keys is None:
            vital_keys = set()

        used_sources: dict[str, str] = {}
        used_values: dict[str, Optional[float]] = {}
        missing_keys: list[str] = []

        for col in FEATURE_ORDER:
            val = features.get(col)
            if val is None or val == "":
                used_sources[col] = "missing"
                used_values[col] = None
                missing_keys.append(col)
                continue
            try:
                val = float(val)
            except (ValueError, TypeError):
                used_sources[col] = "missing"
                used_values[col] = None
                missing_keys.append(col)
                continue
            lo, hi = FEATURE_RANGES.get(col, (0, 1e9))
            if val < lo or val > hi:
                used_sources[col] = "missing"
                used_values[col] = None
                missing_keys.append(col)
                continue
            source = "extracted" if col in extracted_keys else ("vital" if col in vital_keys else "patient")
            used_sources[col] = source
            used_values[col] = val

        features_breakdown = []
        for col in FEATURE_ORDER:
            src = used_sources[col]
            features_breakdown.append({
                "key": col,
                "label": FEATURE_LABELS.get(col, col),
                "label_ar": FEATURE_LABELS.get(col, col),
                "label_en": FEATURE_LABELS_EN.get(col, col),
                "value": used_values[col],
                "source": src,
                "source_ar": FEATURE_SOURCE_AR.get(src, src),
                "source_en": FEATURE_SOURCE_EN.get(src, src),
                "is_missing": src == "missing",
            })

        source_counts = {"extracted": 0, "vital": 0, "patient": 0, "missing": 0}
        for s in used_sources.values():
            source_counts[s] = source_counts.get(s, 0) + 1

        missing_count = source_counts.get("missing", 0)
        provided_count = len(FEATURE_ORDER) - missing_count
        can_predict = missing_count == 0

        missing_labels_ar = "، ".join(FEATURE_LABELS.get(k, k) for k in missing_keys)
        missing_labels_en = ", ".join(FEATURE_LABELS_EN.get(k, k) for k in missing_keys)

        if not can_predict:
            return {
                "can_predict": False,
                "missing_count": missing_count,
                "provided_count": provided_count,
                "total_count": len(FEATURE_ORDER),
                "missing_keys": missing_keys,
                "missing_labels_ar": missing_labels_ar,
                "missing_labels_en": missing_labels_en,
                "features_breakdown": features_breakdown,
                "source_counts": source_counts,
                "message_ar": (
                    f"تعذّر إجراء التشخيص. تم توفير {provided_count} من {len(FEATURE_ORDER)} مؤشر. "
                    f"المؤشرات التالية مفقودة ويجب توفيرها: {missing_labels_ar}."
                ),
                "message_en": (
                    f"Diagnosis cannot proceed. {provided_count} of {len(FEATURE_ORDER)} indicators provided. "
                    f"The following indicators are missing and must be provided: {missing_labels_en}."
                ),
            }

        try:
            row = [used_values[col] for col in FEATURE_ORDER]
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
                    {
                        "feature": FEATURE_LABELS.get(f, f),
                        "feature_en": FEATURE_LABELS_EN.get(f, f),
                        "importance": round(float(imp), 4),
                    }
                    for f, imp in contributions
                ]
        except Exception:
            pass

        reliability = "high" if source_counts.get("extracted", 0) >= 10 else ("medium" if source_counts.get("extracted", 0) >= 7 else "low")

        return {
            "can_predict": True,
            "prediction": pred,
            "prediction_label": "مرض قلبي محتمل" if pred == 1 else "طبيعي",
            "prediction_label_en": "Possible Heart Disease" if pred == 1 else "Normal",
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
            "features_used": {FEATURE_LABELS.get(c, c): used_values[c] for c in FEATURE_ORDER},
            "features_breakdown": features_breakdown,
            "source_counts": source_counts,
            "extracted_count": source_counts.get("extracted", 0),
            "missing_count": 0,
            "provided_count": provided_count,
            "reliability": reliability,
            "reliability_ar": RELIABILITY_AR.get(reliability, reliability),
        }

    def is_available(self) -> bool:
        self._load()
        return self._model is not None


heart_prediction_service = HeartPredictionService()

import logging
from typing import Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.medical_file import MedicalFile
from app.services.storage import storage_service
from app.services.file_processor import file_processor

logger = logging.getLogger(__name__)


class DiagnosisEngine:
    def gather_context(self, patient_id: int, db: Session, session_id: Optional[int] = None) -> dict[str, Any]:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")

        files = db.query(MedicalFile).filter(MedicalFile.patient_id == patient_id).all()

        vitals_summary = self._get_vitals_summary(patient_id, db)
        files_context = self._build_files_context(files)
        file_images = self._load_file_images(files)

        session_indicators = None
        if session_id:
            from app.models.chat import ChatSession
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session and session.clinical_indicators:
                session_indicators = session.clinical_indicators

        ml_prediction = self._get_ml_prediction(patient, db, session_indicators)

        context = {
            "patient": {
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "diagnosis": patient.diagnosis,
            },
            "vitals_summary": vitals_summary,
            "files_context": files_context,
            "file_images": file_images,
            "file_count": len(files),
            "ml_prediction": ml_prediction,
        }
        return context

    def _get_vitals_summary(self, patient_id: int, db: Session) -> str:
        try:
            from app.models.vital_reading import VitalReading

            cutoff = datetime.utcnow() - timedelta(hours=1)
            readings = (
                db.query(VitalReading)
                .filter(VitalReading.patient_id == patient_id, VitalReading.created_at >= cutoff)
                .order_by(VitalReading.created_at.desc())
                .limit(60)
                .all()
            )

            if not readings:
                latest = (
                    db.query(VitalReading)
                    .filter(VitalReading.patient_id == patient_id)
                    .order_by(VitalReading.created_at.desc())
                    .first()
                )
                if latest:
                    return (
                        f"آخر قراءة (من {latest.created_at.strftime('%Y-%m-%d %H:%M')}): "
                        f"SpO2={latest.spo2 or 'N/A'}%, "
                        f"نبض={latest.heart_rate or 'N/A'} bpm, "
                        f"حرارة={latest.temperature or 'N/A'}°C\n"
                        f"المصدر: {latest.source}"
                    )
                return "لا توجد علامات حيوية متاحة لهذا المريض"

            latest = readings[0]

            spo2_vals = [r.spo2 for r in readings if r.spo2 is not None]
            hr_vals = [r.heart_rate for r in readings if r.heart_rate is not None]
            temp_vals = [r.temperature for r in readings if r.temperature is not None]

            def avg(vals):
                return round(sum(vals) / len(vals), 1) if vals else None

            def rng(vals):
                return f"{min(vals):.1f}-{max(vals):.1f}" if vals else "N/A"

            return (
                f"آخر قراءة: SpO2={latest.spo2 or 'N/A'}%, "
                f"نبض={latest.heart_rate or 'N/A'} bpm, "
                f"حرارة={latest.temperature or 'N/A'}°C\n"
                f"عدد القراءات في آخر ساعة: {len(readings)}\n"
                f"متوسط: SpO2={avg(spo2_vals) or 'N/A'}%, "
                f"نبض={avg(hr_vals) or 'N/A'} bpm, "
                f"حرارة={avg(temp_vals) or 'N/A'}°C\n"
                f"النطاق: SpO2={rng(spo2_vals)}, "
                f"نبض={rng(hr_vals)}, "
                f"حرارة={rng(temp_vals)}\n"
                f"المصدر: {latest.source}"
            )
        except Exception as e:
            logger.warning("Failed to get vitals: %s", e)
            return "لا توجد علامات حيوية متاحة"

    def _get_ml_prediction(self, patient: Patient, db: Session, session_indicators: Optional[dict] = None) -> Optional[dict]:
        try:
            from app.services.ml_service import heart_prediction_service
            if not heart_prediction_service.is_available():
                return None

            from app.models.vital_reading import VitalReading
            latest_vital = (
                db.query(VitalReading)
                .filter(VitalReading.patient_id == patient.id)
                .order_by(VitalReading.created_at.desc())
                .first()
            )

            features: dict = {}

            if patient.age is not None:
                features["age"] = float(patient.age)
            if patient.gender:
                features["sex"] = 1.0 if patient.gender.lower().startswith("m") else 0.0

            vital_keys: set = set()
            if latest_vital:
                if latest_vital.heart_rate:
                    features["thalach"] = float(latest_vital.heart_rate)
                    vital_keys.add("thalach")
                if latest_vital.temperature and latest_vital.temperature > 38:
                    features["exang"] = 1.0
                    vital_keys.add("exang")

            extracted_keys: set = set()
            files = db.query(MedicalFile).filter(MedicalFile.patient_id == patient.id).all()
            for f in files:
                if not f.extracted_indicators:
                    continue
                for key, val in f.extracted_indicators.items():
                    if val is None:
                        continue
                    try:
                        features[key] = float(val)
                        extracted_keys.add(key)
                    except (ValueError, TypeError):
                        pass

            if session_indicators:
                for key, val in session_indicators.items():
                    if val is None:
                        continue
                    try:
                        features[key] = float(val)
                        extracted_keys.add(key)
                    except (ValueError, TypeError):
                        pass

            extracted_keys -= vital_keys
            for k in ("age", "sex"):
                extracted_keys.discard(k)

            return heart_prediction_service.predict(
                features, extracted_keys=extracted_keys, vital_keys=vital_keys
            )
        except Exception as e:
            logger.warning("ML prediction failed: %s", e)
            return None

    def _build_files_context(self, files: list[MedicalFile]) -> str:
        if not files:
            return "لا توجد فحوصات أو تحاليل مرفوعة بعد."

        parts = []
        for f in files:
            category_map = {
                "lab": "تحاليل مخبرية",
                "imaging": "صور طبية/أشعة",
                "report": "تقرير طبي",
                "other": "أخرى",
            }
            category_name = category_map.get(f.category, f.category)
            section = f"--- ملف #{f.id}: {f.file_name} ({category_name}) ---\n"
            if f.extracted_text:
                section += f"المحتوى المستخرج:\n{f.extracted_text[:3000]}\n"
            else:
                section += "لم يتم استخراج نص من هذا الملف (قد يكون صورة طبية سيتم تحليلها بالرؤية).\n"
            parts.append(section)

        return "\n".join(parts)

    def _load_file_images(self, files: list[MedicalFile]) -> list[dict]:
        images = []
        for f in files:
            if f.file_type == "image":
                data = storage_service.download_file(f.storage_key)
                if data is None:
                    continue
                prepared = file_processor.prepare_image_for_vision(data)
                if prepared:
                    images.append({
                        "data": file_processor.encode_image_for_vision(prepared),
                        "mime_type": "image/png",
                        "file_name": f.file_name,
                    })
            elif f.file_type == "pdf":
                data = storage_service.download_file(f.storage_key)
                if data is None:
                    continue
                page_images = file_processor.pdf_to_images(data)
                for idx, page_img in enumerate(page_images):
                    images.append({
                        "data": file_processor.encode_image_for_vision(page_img),
                        "mime_type": "image/png",
                        "file_name": f"{f.file_name} (page {idx + 1})",
                    })
        return images

    def build_context_message(self, context: dict[str, Any]) -> str:
        from app.services.openai_service import build_context_message
        return build_context_message(
            context["patient"],
            context["vitals_summary"],
            context["files_context"],
            context.get("ml_prediction"),
        )


diagnosis_engine = DiagnosisEngine()

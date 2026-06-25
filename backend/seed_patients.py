import sys
import os

# Add the current directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.db.session import SessionLocal, Base, engine
from app.models.user import User
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.alert import Alert
from app.models.medical_file import MedicalFile
from app.models.diagnosis import Diagnosis
from app.models.audit_log import AuditLog
from app.models.chat import ChatSession, ChatMessage
from app.models.vital_reading import VitalReading

def seed_test_patients():
    db = SessionLocal()
    try:
        # Check if user "doctor" exists to assign uploaded_by
        doctor = db.query(User).filter(User.username == "doctor").first()
        if not doctor:
            print("Error: Default user 'doctor' not found. Please run the backend at least once first.")
            return

        print("Seeding test patients with clinical data...")

        # 1. Patient: Ahmed Mansour (Cardiovascular Profile)
        ahmed = db.query(Patient).filter(Patient.name == "أحمد منصور").first()
        if not ahmed:
            ahmed = Patient(
                name="أحمد منصور",
                age=62,
                gender="Male",
                phone="0501234567",
                room="Room 201",
                diagnosis="ارتفاع ضغط الدم الشرياني (Hypertension)",
                notes="يعاني المريض من ألم صدري عند بذل مجهود وتاريخ عائلي لأمراض القلب.",
                is_active=True
            )
            db.add(ahmed)
            db.commit()
            db.refresh(ahmed)
            
            # Add vitals
            vitals = VitalReading(
                patient_id=ahmed.id,
                spo2=94.0,
                heart_rate=92.0,
                temperature=36.9,
                confidence=95,
                source="sensor",
                created_at=datetime.utcnow()
            )
            db.add(vitals)

            # Add Medical File
            file1 = MedicalFile(
                patient_id=ahmed.id,
                file_name="Lab_Results_Lipid_Profile.pdf",
                file_type="pdf",
                category="lab",
                storage_key=f"{ahmed.id}/lab/lipid_profile.pdf",
                mime_type="application/pdf",
                file_size=10240,
                extracted_text="""LABORATORY REPORT — CARDIAC PROFILE
Patient Name: Ahmed Mansour
Age: 62 | Gender: Male
--------------------------------------------------
TEST                  RESULT      REFERENCE RANGE
Cholesterol Total     260 mg/dL   < 200 (HIGH)
Triglycerides        210 mg/dL   < 150 (HIGH)
HDL Cholesterol       35 mg/dL    > 40 (LOW)
LDL Cholesterol       183 mg/dL   < 100 (VERY HIGH)
Troponin I            0.04 ng/mL  < 0.03 (Borderline High)
Creatine Kinase (CK)  185 U/L     39 - 308 (Normal)
--------------------------------------------------
Clinical Interpretation: Lipids are severely elevated. Troponin levels are borderline high and require monitoring.""",
                uploaded_by=doctor.id,
                created_at=datetime.utcnow()
            )
            db.add(file1)
            print("- Seeded patient: Ahmed Mansour")

        # 2. Patient: Fatima Al-Zahra (Diabetic Profile)
        fatima = db.query(Patient).filter(Patient.name == "فاطمة الزهراء").first()
        if not fatima:
            fatima = Patient(
                name="فاطمة الزهراء",
                age=45,
                gender="Female",
                phone="0507654321",
                room="Room 202",
                diagnosis="السكري من النوع الأول (Diabetes Type 1)",
                notes="تاريخ طويل مع مرض السكري وتفاوت مستويات السكر في الدم بشكل حاد.",
                is_active=True
            )
            db.add(fatima)
            db.commit()
            db.refresh(fatima)
            
            # Add vitals
            vitals = VitalReading(
                patient_id=fatima.id,
                spo2=98.0,
                heart_rate=104.0,
                temperature=37.2,
                confidence=98,
                source="sensor",
                created_at=datetime.utcnow()
            )
            db.add(vitals)

            # Add Medical File
            file2 = MedicalFile(
                patient_id=fatima.id,
                file_name="Diabetic_Lab_Report.pdf",
                file_type="pdf",
                category="lab",
                storage_key=f"{fatima.id}/lab/diabetic_report.pdf",
                mime_type="application/pdf",
                file_size=12500,
                extracted_text="""METABOLIC & DIABETIC ASSESSMENT
Patient Name: Fatima Al-Zahra
Age: 45 | Gender: Female
--------------------------------------------------
TEST                  RESULT      REFERENCE RANGE
HbA1c                 9.5 %       4.0 - 5.6 (Uncontrolled Diabetes)
Fasting Glucose       315 mg/dL   70 - 100 (Critical High)
Urine Ketones         Positive ++ Negative
BUN                   22 mg/dL    7 - 20 (Slightly High)
Serum Creatinine      0.9 mg/dL   0.6 - 1.1 (Normal)
--------------------------------------------------
Clinical Interpretation: Critical hyperglycemia with ketonuria, indicating risk of early diabetic ketoacidosis (DKA). Immediate insulin management required.""",
                uploaded_by=doctor.id,
                created_at=datetime.utcnow()
            )
            db.add(file2)
            print("- Seeded patient: Fatima Al-Zahra")

        # 3. Patient: Khaled Abdullah (Pulmonary Profile)
        khaled = db.query(Patient).filter(Patient.name == "خالد عبد الله").first()
        if not khaled:
            khaled = Patient(
                name="خالد عبد الله",
                age=28,
                gender="Male",
                phone="0508889999",
                room="Room 203",
                diagnosis="الربو الشعبي المزمن (Chronic Asthma)",
                notes="يعاني المريض من سعال جاف مستمر وصعوبة في التنفس مع زفير صفيري.",
                is_active=True
            )
            db.add(khaled)
            db.commit()
            db.refresh(khaled)
            
            # Add vitals
            vitals = VitalReading(
                patient_id=khaled.id,
                spo2=91.0,
                heart_rate=85.0,
                temperature=38.8,
                confidence=94,
                source="sensor",
                created_at=datetime.utcnow()
            )
            db.add(vitals)

            # Add Medical File
            file3 = MedicalFile(
                patient_id=khaled.id,
                file_name="Chest_XRay_Report.pdf",
                file_type="pdf",
                category="imaging",
                storage_key=f"{khaled.id}/imaging/chest_xray.pdf",
                mime_type="application/pdf",
                file_size=9800,
                extracted_text="""RADIOLOGY DEPARTMENT — CHEST X-RAY
Patient Name: Khaled Abdullah
Age: 28 | Gender: Male
--------------------------------------------------
EXAMINATION: Chest PA View
FINDINGS:
- Lungs show bilateral lower lobe bronchial wall thickening and mild hyperinflation.
- Patchy consolidative infiltrates seen in the left lower zone.
- Cardiomegaly: None. Pleural effusion: None.
--------------------------------------------------
Clinical Interpretation: Findings are consistent with bronchial asthma exacerbation accompanied by early bronchopneumonia infection.""",
                uploaded_by=doctor.id,
                created_at=datetime.utcnow()
            )
            db.add(file3)
            print("- Seeded patient: Khaled Abdullah")

        # 4. Patient: Sarah Ahmed (Renal & Hypertensive Profile)
        sarah = db.query(Patient).filter(Patient.name == "سارة أحمد").first()
        if not sarah:
            sarah = Patient(
                name="سارة أحمد",
                age=55,
                gender="Female",
                phone="0504445555",
                room="Room 204",
                diagnosis="الفشل الكلوي المزمن (Chronic Kidney Disease)",
                notes="تعاني من تورم مستمر في القدمين وصداع شديد، مع تذبذب كبير في ضغط الدم.",
                is_active=True
            )
            db.add(sarah)
            db.commit()
            db.refresh(sarah)
            
            # Add vitals
            vitals = VitalReading(
                patient_id=sarah.id,
                spo2=96.0,
                heart_rate=88.0,
                temperature=36.5,
                confidence=97,
                source="sensor",
                created_at=datetime.utcnow()
            )
            db.add(vitals)

            # Add Medical File
            file4 = MedicalFile(
                patient_id=sarah.id,
                file_name="Renal_Function_Test.pdf",
                file_type="pdf",
                category="report",
                storage_key=f"{sarah.id}/report/renal_function.pdf",
                mime_type="application/pdf",
                file_size=11200,
                extracted_text="""CLINICAL MEDICAL REPORT — RENAL FUNCTION
Patient Name: Sarah Ahmed
Age: 55 | Gender: Female
--------------------------------------------------
TEST                  RESULT      REFERENCE RANGE
Urea                  95 mg/dL    15 - 45 (ELEVATED)
Creatinine            2.8 mg/dL   0.5 - 1.2 (CRITICAL)
Blood Pressure        190/115     mmHg (Severe Hypertensive Crisis)
Glomerular Filtration 18 mL/min   > 90 (Stage 4 Kidney Disease)
--------------------------------------------------
Clinical Interpretation: Severe renal impairment with extremely high blood pressure. Close inpatient monitoring and pharmacological intervention required.""",
                uploaded_by=doctor.id,
                created_at=datetime.utcnow()
            )
            db.add(file4)
            print("- Seeded patient: Sarah Ahmed")

        db.commit()
        print("\nAll test patients seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_patients()

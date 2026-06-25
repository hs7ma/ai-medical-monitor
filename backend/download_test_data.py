import os
import urllib.request
import sys

def download_and_generate_test_data():
    # Define destination folder
    dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_medical_data")
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Creating test medical data directory at: {dest_dir}")

    # URLs of public domain medical images on Wikimedia Commons
    files_to_download = {
        "normal_chest_xray.jpg": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Normal_posteroanterior_chest_radiograph.jpg",
        "pneumonia_chest_xray.jpg": "https://upload.wikimedia.org/wikipedia/commons/d/d4/Chest_X-ray_of_patient_with_pneumonia_01.jpg",
        "sample_ecg.jpg": "https://upload.wikimedia.org/wikipedia/commons/2/26/Normal_ECG.jpg"
    }

    # Download files
    for filename, url in files_to_download.items():
        filepath = os.path.join(dest_dir, filename)
        try:
            print(f"Downloading {filename} from Wikimedia Commons...")
            # Use a User-Agent header to avoid HTTP 403 Forbidden errors
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Successfully downloaded and saved: {filepath}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}", file=sys.stderr)

    # Generate custom sample PDF reports using a simple layout to ensure compatibility
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        print("reportlab found, generating custom clinical PDF reports...")

        # 1. Generate Lab Report PDF for Ahmed Mansour
        pdf_path_1 = os.path.join(dest_dir, "lab_report_ahmed_mansour.pdf")
        c = canvas.Canvas(pdf_path_1, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "METABOLIC & CLINICAL PATHOLOGY LABORATORY")
        c.setFont("Helvetica", 10)
        c.drawString(50, 730, "AI Medical Center, 2026")
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(50, 720, 560, 720)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 690, "Patient Name:")
        c.setFont("Helvetica", 12)
        c.drawString(140, 690, "Ahmed Mansour")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, 690, "Age / Gender:")
        c.setFont("Helvetica", 12)
        c.drawString(450, 690, "62 years / Male")

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, 650, "TEST")
        c.drawString(200, 650, "RESULT")
        c.drawString(320, 650, "REFERENCE RANGE")
        c.drawString(460, 650, "STATUS")
        c.line(50, 642, 560, 642)

        c.setFont("Helvetica", 10)
        tests = [
            ("Total Cholesterol", "260 mg/dL", "< 200 mg/dL", "HIGH"),
            ("Triglycerides", "210 mg/dL", "< 150 mg/dL", "HIGH"),
            ("HDL Cholesterol", "35 mg/dL", "> 40 mg/dL", "LOW"),
            ("LDL Cholesterol", "183 mg/dL", "< 100 mg/dL", "VERY HIGH"),
            ("Troponin I", "0.04 ng/mL", "< 0.03 ng/mL", "Borderline High"),
            ("Creatine Kinase", "185 U/L", "39 - 308 U/L", "Normal")
        ]
        
        y = 620
        for test, res, ref, status in tests:
            c.drawString(50, y, test)
            c.drawString(200, y, res)
            c.drawString(320, y, ref)
            if status != "Normal":
                c.setFont("Helvetica-Bold", 10)
                c.drawString(460, y, status)
                c.setFont("Helvetica", 10)
            else:
                c.drawString(460, y, status)
            y -= 25

        c.line(50, y - 5, 560, y - 5)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 25, "Clinical Diagnosis & Notes:")
        c.setFont("Helvetica", 10)
        c.drawString(50, y - 45, "Severe hyperlipidemia with borderline elevated Cardiac Troponin I levels.")
        c.drawString(50, y - 60, "Suggestive of early myocardial distress under exertion. Recommendation: Urgent ECG")
        c.drawString(50, y - 75, "evaluation, cardiac consult, and initiation of lipid-lowering pharmacological therapy.")
        
        c.save()
        print(f"Successfully generated: {pdf_path_1}")

        # 2. Generate Diabetic Assessment PDF for Fatima Al-Zahra
        pdf_path_2 = os.path.join(dest_dir, "diabetic_assessment_fatima.pdf")
        c = canvas.Canvas(pdf_path_2, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "DIABETIC MEDICINE & METABOLIC LABORATORY")
        c.setFont("Helvetica", 10)
        c.drawString(50, 730, "AI Medical Center, 2026")
        c.line(50, 720, 560, 720)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 690, "Patient Name:")
        c.setFont("Helvetica", 12)
        c.drawString(140, 690, "Fatima Al-Zahra")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, 690, "Age / Gender:")
        c.setFont("Helvetica", 12)
        c.drawString(450, 690, "45 years / Female")

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, 650, "TEST")
        c.drawString(200, 650, "RESULT")
        c.drawString(320, 650, "REFERENCE RANGE")
        c.drawString(460, 650, "STATUS")
        c.line(50, 642, 560, 642)

        c.setFont("Helvetica", 10)
        tests_diab = [
            ("HbA1c", "9.5 %", "4.0 - 5.6 %", "CRITICAL HIGH"),
            ("Fasting Blood Sugar", "315 mg/dL", "70 - 100 mg/dL", "CRITICAL HIGH"),
            ("Urine Ketones", "Positive ++", "Negative", "HIGH"),
            ("Urea (BUN)", "22 mg/dL", "7 - 20 mg/dL", "Slightly High"),
            ("Serum Creatinine", "0.9 mg/dL", "0.6 - 1.1 mg/dL", "Normal")
        ]
        
        y = 620
        for test, res, ref, status in tests_diab:
            c.drawString(50, y, test)
            c.drawString(200, y, res)
            c.drawString(320, y, ref)
            if "Normal" not in status:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(460, y, status)
                c.setFont("Helvetica", 10)
            else:
                c.drawString(460, y, status)
            y -= 25

        c.line(50, y - 5, 560, y - 5)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y - 25, "Clinical Assessment:")
        c.setFont("Helvetica", 10)
        c.drawString(50, y - 45, "Patient exhibits severe uncontrolled hyperglycemia combined with positive ketones.")
        c.drawString(50, y - 60, "Clinical signs are strongly indicative of early Diabetic Ketoacidosis (DKA) risk.")
        c.drawString(50, y - 75, "Recommendation: immediate insulin therapy titration and close fluid/electrolyte monitoring.")
        
        c.save()
        print(f"Successfully generated: {pdf_path_2}")

    except ImportError:
        print("reportlab not found. Generating basic text files instead of clinical PDFs...")
        # Write txt file for Ahmed Mansour
        report_txt1 = os.path.join(dest_dir, "lab_report_ahmed_mansour.txt")
        with open(report_txt1, "w", encoding="utf-8") as f:
            f.write("""METABOLIC & CLINICAL PATHOLOGY LABORATORY
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
Clinical Interpretation: Lipids are severely elevated. Troponin levels are borderline high and require monitoring.""")
        print(f"Successfully generated text report: {report_txt1}")

        # Write txt file for Fatima
        report_txt2 = os.path.join(dest_dir, "diabetic_assessment_fatima.txt")
        with open(report_txt2, "w", encoding="utf-8") as f:
            f.write("""METABOLIC & DIABETIC ASSESSMENT
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
Clinical Interpretation: Critical hyperglycemia with ketonuria, indicating risk of early diabetic ketoacidosis (DKA). Immediate insulin management required.""")
        print(f"Successfully generated text report: {report_txt2}")

    print("\nAll test files ready in test_medical_data/ directory!")

if __name__ == "__main__":
    download_and_generate_test_data()

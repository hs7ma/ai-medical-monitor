export const mockBeds = [
  { id: "BED-001", room: "ICU-1", status: "occupied", patient_id: 1, created_at: "2026-06-21T08:00:00Z" },
  { id: "BED-002", room: "ICU-1", status: "occupied", patient_id: 2, created_at: "2026-06-21T08:00:00Z" },
  { id: "BED-003", room: "ICU-2", status: "occupied", patient_id: 3, created_at: "2026-06-21T08:00:00Z" },
  { id: "BED-004", room: "ICU-2", status: "available", patient_id: null, created_at: "2026-06-21T08:00:00Z" },
  { id: "BED-005", room: "WARD-A", status: "occupied", patient_id: 4, created_at: "2026-06-21T08:00:00Z" },
  { id: "BED-006", room: "WARD-A", status: "available", patient_id: null, created_at: "2026-06-21T08:00:00Z" },
];

export const mockPatients = [
  { id: 1, name: "أحمد محمد علي", age: 54, gender: "male", diagnosis: "التهاب رئوي", is_active: true, created_at: "2026-06-21T08:00:00Z" },
  { id: 2, name: "فاطمة حسن", age: 47, gender: "female", diagnosis: "ما بعد جراحة قلب", is_active: true, created_at: "2026-06-21T08:00:00Z" },
  { id: 3, name: "خالد إبراهيم", age: 63, gender: "male", diagnosis: "فشل تنفسي", is_active: true, created_at: "2026-06-21T08:00:00Z" },
  { id: 4, name: "نور سالم", age: 35, gender: "female", diagnosis: "مراقبة بعد الولادة", is_active: true, created_at: "2026-06-21T08:00:00Z" },
];

export const mockPatient = mockPatients[0];

export const mockVitals = (() => {
  const data: any[] = [];
  const now = Date.now();
  for (let i = 60; i >= 0; i--) {
    const t = new Date(now - i * 60_000);
    data.push({
      time: t.toISOString(),
      bed_id: "BED-001",
      patient_id: "1",
      spo2: 94 + Math.random() * 4,
      heart_rate: 68 + Math.random() * 12,
      temperature: 36.5 + Math.random() * 0.8,
      confidence: 85,
    });
  }
  return data;
})();

export const mockFiles = [
  { id: 1, patient_id: 1, file_name: "blood_test_2026.pdf", file_type: "pdf", category: "lab", mime_type: "application/pdf", file_size: 245000, has_extracted_text: true, uploaded_by: 2, created_at: "2026-06-21T09:30:00Z" },
  { id: 2, patient_id: 1, file_name: "chest_xray.jpg", file_type: "image", category: "imaging", mime_type: "image/jpeg", file_size: 1850000, has_extracted_text: false, uploaded_by: 2, created_at: "2026-06-21T10:15:00Z" },
  { id: 3, patient_id: 1, file_name: "ecg_report.pdf", file_type: "pdf", category: "report", mime_type: "application/pdf", file_size: 520000, has_extracted_text: true, uploaded_by: 2, created_at: "2026-06-22T08:00:00Z" },
];

export const mockAlerts = [
  { id: 1, bed_id: "BED-001", patient_id: 1, type: "spo2_low", severity: "warning", message: "SpO2 انخفض إلى 91%", status: "active", created_at: "2026-06-22T11:30:00Z", acked_at: null, acked_by: null },
  { id: 2, bed_id: "BED-003", patient_id: 3, type: "hr_high", severity: "critical", message: "نبض القلب تجاوز 120 bpm", status: "active", created_at: "2026-06-22T11:45:00Z", acked_at: null, acked_by: null },
  { id: 3, bed_id: "BED-002", patient_id: 2, type: "temp_high", severity: "warning", message: "الحرارة 37.8°C", status: "acked", created_at: "2026-06-22T10:15:00Z", acked_at: "2026-06-22T10:20:00Z", acked_by: 3 },
];

export const mockLiveVitals: Record<string, { spo2: number; heart_rate: number; temperature: number }> = {
  "BED-001": { spo2: 96, heart_rate: 74, temperature: 36.7 },
  "BED-002": { spo2: 97, heart_rate: 88, temperature: 37.8 },
  "BED-003": { spo2: 91, heart_rate: 122, temperature: 38.5 },
  "BED-005": { spo2: 98, heart_rate: 65, temperature: 36.5 },
};

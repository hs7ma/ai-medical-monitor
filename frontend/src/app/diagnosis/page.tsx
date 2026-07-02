"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { clsx } from "clsx";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, Select, Label } from "@/components/ui/Input";
import { FileUploader } from "@/components/uploads/FileUploader";
import { DiagnosisCard } from "@/components/diagnosis/DiagnosisCard";
import { useToast } from "@/components/ui/Toast";
import { useModal } from "@/components/ui/Modal";

interface Message {
  id: number;
  session_id: number;
  role: string;
  content: string;
  has_files: boolean;
  created_at: string;
}

interface Session {
  id: number;
  patient_id: number;
  title: string;
  status: string;
  diagnosis_result: any | null;
}

const catIcon: Record<string, string> = {
  lab: "🧪",
  imaging: "🩻",
  report: "📋",
  other: "📎",
};

const COMMON_SYMPTOMS = [
  { id: "chest_pain", labelAr: "ألم في الصدر", labelEn: "Chest Pain" },
  { id: "shortness_of_breath", labelAr: "ضيق في التنفس", labelEn: "Shortness of Breath" },
  { id: "palpitations", labelAr: "خفقان في القلب", labelEn: "Palpitations" },
  { id: "arm_jaw_pain", labelAr: "ألم ممتد للذراع/الكتف/الفك", labelEn: "Pain Radiating to Arm/Shoulder/Jaw" },
  { id: "sweating", labelAr: "تعرق بارد غزير", labelEn: "Cold Sweating (Diaphoresis)" },
  { id: "dizziness", labelAr: "دوار / دوخة", labelEn: "Dizziness / Lightheadedness" },
  { id: "fatigue", labelAr: "تعب / إرهاق شديد", labelEn: "Severe Fatigue" },
  { id: "leg_swelling", labelAr: "تورم الساقين أو القدمين", labelEn: "Leg/Foot Swelling (Edema)" },
  { id: "orthopnea", labelAr: "ضيق تنفس عند الاستلقاء", labelEn: "Difficulty Breathing when Lying Down (Orthopnea)" },
  { id: "syncope", labelAr: "إغماء أو فقدان وعي مؤقت", labelEn: "Fainting / Syncope" },
  { id: "nausea_vomiting", labelAr: "غثيان / قيء", labelEn: "Nausea / Vomiting" },
  { id: "cough", labelAr: "سعال / كحة", labelEn: "Cough" },
  { id: "fever", labelAr: "حمى / ارتفاع الحرارة", labelEn: "Fever / High Temperature" },
  { id: "headache", labelAr: "صداع", labelEn: "Headache" },
];

const formatDiagnosis = (diag: string, currentLocale: string) => {
  if (!diag) return "";
  const match = diag.match(/^(.*?)\s*\((.*?)\)$/);
  if (match) {
    const [, arPart, enPart] = match;
    return currentLocale === "ar" ? arPart.trim() : enPart.trim();
  }
  return diag;
};

const translateGender = (g: string, currentLocale: string) => {
  if (!g) return "";
  const lower = g.toLowerCase();
  if (lower.startsWith("m")) {
    return currentLocale === "ar" ? "ذكر" : "Male";
  }
  if (lower.startsWith("f")) {
    return currentLocale === "ar" ? "أنثى" : "Female";
  }
  return g;
};

function DiagnosisStepper({ step, hasDiagnosis }: { step: number; hasDiagnosis: boolean }) {
  const { t } = useI18n();
  return (
    <div className="flex items-center justify-center w-full max-w-2xl mx-auto mb-6 text-[10px] sm:text-xs border-b border-slate-100 pb-4">
      {/* Step 1: Intake & Symptoms */}
      <div className={clsx("flex items-center", step >= 0 ? "text-accent font-semibold" : "text-slate-400")}>
        <span className={clsx(
          "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold border",
          step > 0 ? "bg-accent text-white border-accent" : "border-accent bg-accent-light text-accent"
        )}>
          {step > 0 ? "✓" : "1"}
        </span>
        <span className="mr-1.5 ml-1.5">{t("diagnosis.stepperStep1")}</span>
      </div>

      <div className="flex-1 mx-2 h-0.5 bg-slate-200 relative">
        <div className={clsx("absolute top-0 right-0 h-full bg-accent transition-all duration-300", step >= 1 ? "w-full" : "w-0")} />
      </div>

      {/* Step 2: Heart Risk (ML) */}
      <div className={clsx("flex items-center", step >= 1 ? "text-accent font-semibold" : "text-slate-400")}>
        <span className={clsx(
          "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold border",
          step > 1 ? "bg-accent text-white border-accent" : step === 1 ? "border-accent bg-accent-light text-accent animate-pulse-dot" : "border-slate-200 bg-white"
        )}>
          {step > 1 ? "✓" : "2"}
        </span>
        <span className="mr-1.5 ml-1.5">{t("diagnosis.stepperStep2")}</span>
      </div>

      <div className="flex-1 mx-2 h-0.5 bg-slate-200 relative">
        <div className={clsx("absolute top-0 right-0 h-full bg-accent transition-all duration-300", step >= 2 ? "w-full" : "w-0")} />
      </div>

      {/* Step 3: Clinical Interview */}
      <div className={clsx("flex items-center", step >= 2 ? "text-accent font-semibold" : "text-slate-400")}>
        <span className={clsx(
          "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold border",
          step > 2 || hasDiagnosis ? "bg-accent text-white border-accent" : step === 2 ? "border-accent bg-accent-light text-accent animate-pulse-dot" : "border-slate-200 bg-white"
        )}>
          {step > 2 || hasDiagnosis ? "✓" : "3"}
        </span>
        <span className="mr-1.5 ml-1.5">{t("diagnosis.stepperStep3")}</span>
      </div>

      <div className="flex-1 mx-2 h-0.5 bg-slate-200 relative">
        <div className={clsx("absolute top-0 right-0 h-full bg-accent transition-all duration-300", hasDiagnosis || step >= 3 ? "w-full" : "w-0")} />
      </div>

      {/* Step 4: Final Report */}
      <div className={clsx("flex items-center", hasDiagnosis || step >= 3 ? "text-accent font-semibold" : "text-slate-400")}>
        <span className={clsx(
          "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold border",
          hasDiagnosis || step >= 3 ? "bg-accent text-white border-accent shadow-sm shadow-accent/20" : "border-slate-200 bg-white"
        )}>
          4
        </span>
        <span className="mr-1.5 ml-1.5">{t("diagnosis.stepperStep4")}</span>
      </div>
    </div>
  );
}

const riskColors: Record<string, { ring: string; text: string; bg: string; border: string }> = {
  high: {
    ring: "#ef4444",
    text: "text-rose-700",
    bg: "bg-rose-50/50",
    border: "border-rose-200/60",
  },
  moderate: {
    ring: "#f59e0b",
    text: "text-amber-700",
    bg: "bg-amber-50/50",
    border: "border-amber-200/60",
  },
  low: {
    ring: "#3b82f6",
    text: "text-blue-700",
    bg: "bg-blue-50/50",
    border: "border-blue-200/60",
  },
  normal: {
    ring: "#10b981",
    text: "text-emerald-700",
    bg: "bg-emerald-50/50",
    border: "border-emerald-200/60",
  },
};

const ML_EMPTY: Record<string, number | ""> = {
  age: "",
  sex: "",
  cp: "",
  trestbps: "",
  chol: "",
  fbs: "",
  restecg: "",
  thalach: "",
  exang: "",
  oldpeak: "",
  slope: "",
  ca: "",
  thal: "",
};

export default function DiagnosisPage() {
  const { t, locale } = useI18n();
  const { showToast } = useToast();
  const { showAlert } = useModal();
  const mlFields = [
    { key: "age", label: t("diagnosis.ageLabel"), type: "number" },
    {
      key: "sex",
      label: t("diagnosis.sexLabel"),
      options: [
        { value: "1", label: locale === "ar" ? "ذكر / Male" : "Male" },
        { value: "0", label: locale === "ar" ? "أنثى / Female" : "Female" },
      ],
    },
    {
      key: "cp",
      label: t("diagnosis.chestPainTypeLabel"),
      options: [
        { value: "0", label: locale === "ar" ? "Typical Angina" : "Typical Angina" },
        { value: "1", label: locale === "ar" ? "Atypical Angina" : "Atypical Angina" },
        { value: "2", label: locale === "ar" ? "Non-anginal" : "Non-anginal" },
        { value: "3", label: locale === "ar" ? "Asymptomatic" : "Asymptomatic" },
      ],
    },
    { key: "trestbps", label: t("diagnosis.restingBPLabel"), type: "number" },
    { key: "chol", label: t("diagnosis.cholesterolLabel"), type: "number" },
    {
      key: "fbs",
      label: t("diagnosis.fastingBSLabel"),
      options: [
        { value: "0", label: locale === "ar" ? "لا / No" : "No" },
        { value: "1", label: locale === "ar" ? "نعم / Yes" : "Yes" },
      ],
    },
    {
      key: "restecg",
      label: t("diagnosis.restingECGLabel"),
      options: [
        { value: "0", label: locale === "ar" ? "طبيعي / Normal" : "Normal" },
        { value: "1", label: "ST abnormality" },
        { value: "2", label: "LVH" },
      ],
    },
    { key: "thalach", label: t("diagnosis.maxHRLabel"), type: "number" },
    {
      key: "exang",
      label: t("diagnosis.exerciseAnginaLabel"),
      options: [
        { value: "0", label: locale === "ar" ? "لا / No" : "No" },
        { value: "1", label: locale === "ar" ? "نعم / Yes" : "Yes" },
      ],
    },
    { key: "oldpeak", label: t("diagnosis.oldpeakLabel"), type: "number" },
    {
      key: "slope",
      label: t("diagnosis.slopeLabel"),
      options: [
        { value: "0", label: "Downsloping" },
        { value: "1", label: "Flat" },
        { value: "2", label: "Upsloping" },
      ],
    },
    { key: "ca", label: t("diagnosis.vesselsLabel"), type: "number" },
    {
      key: "thal",
      label: t("diagnosis.thalassemiaLabel"),
      options: [
        { value: "0", label: locale === "ar" ? "طبيعي / Normal" : "Normal" },
        { value: "1", label: locale === "ar" ? "عيب ثابت / Fixed defect" : "Fixed defect" },
        { value: "2", label: locale === "ar" ? "عيب قابل للشفاء / Reversible defect" : "Reversible defect" },
        { value: "3", label: "Reversible" },
      ],
    },
  ];
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [selectedFileIds, setSelectedFileIds] = useState<number[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0: Intake, 1: ML Screening, 2: Chat, 3: Report
  const [diagnosis, setDiagnosis] = useState<any | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ML Form states
  const [mlFeatures, setMlFeatures] = useState<any>(ML_EMPTY);
  const [mlResult, setMlResult] = useState<any>(null);
  const [mlLoading, setMlLoading] = useState(false);
  const [mlError, setMlError] = useState("");
  const [aiExtracting, setAiExtracting] = useState(false);
  const [extractReport, setExtractReport] = useState<any>(null);
  const [liveNotification, setLiveNotification] = useState("");

  // Intake Form states
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [duration, setDuration] = useState("");
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [historyAndMedications, setHistoryAndMedications] = useState("");

  const loadPatients = useCallback(async () => {
    try {
      setPatients(await api.listPatients());
    } catch {}
  }, []);

  const loadFiles = useCallback(async (patientId: number) => {
    try {
      const patientFiles = await api.listUploads(patientId);
      setFiles(patientFiles);
    } catch {}
  }, []);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const handleSelectPatient = async (patientId: number) => {
    const p = patients.find((p) => p.id === patientId);
    setSelectedPatient(p);
    setSelectedFileIds([]);
    if (p) {
      loadFiles(p.id);
      
      const isMale = (p.gender || "").toLowerCase().startsWith("m") ? 1 : 0;
      let latestHr = 72;
      try {
        const latestVitals = await api.getLatestVitals(p.id);
        if (latestVitals) {
          if (latestVitals.heart_rate) latestHr = latestVitals.heart_rate;
        }
      } catch {}
      
      setMlFeatures({
        ...ML_EMPTY,
        age: p.age || "",
        sex: isMale,
        thalach: latestHr !== 72 ? latestHr : "",
      });
      setMlResult(null);
      setMlError("");
    }
  };

  const toggleSymptom = (id: string) => {
    setSelectedSymptoms((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const sendMessageToAI = async (sessionId: number, text: string, fileIds: number[]) => {
    const userMsg: Message = {
      id: Date.now(),
      session_id: sessionId,
      role: "user",
      content: text,
      has_files: fileIds.length > 0,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setThinking(true);
    try {
      const res = await api.sendMessage(sessionId, text, fileIds);
      if (res.message) setMessages((prev) => [...prev, res.message]);
      if (res.diagnosis) {
        setDiagnosis(res.diagnosis);
        setCurrentStep(3); // Transition to Unified Report dashboard
      }
      
      // Update clinical indicators from Q&A dynamically
      if (res.extracted_indicators && Object.keys(res.extracted_indicators).length > 0) {
        const newKeys = Object.keys(res.extracted_indicators).filter(
          (k) => res.extracted_indicators[k] !== null && res.extracted_indicators[k] !== undefined
        );
        setMlFeatures((prev: any) => {
          const updated = { ...prev };
          Object.entries(res.extracted_indicators).forEach(([k, v]) => {
            if (v !== null && v !== undefined) {
              updated[k] = v;
            }
          });
          handleLiveMLPredict(updated, newKeys);
          return updated;
        });

        const listStr = Object.entries(res.extracted_indicators)
          .filter(([, v]) => v !== null && v !== undefined)
          .map(([k, v]) => `${mlFields.find((f) => f.key === k)?.label || k}: ${v}`)
          .join("، ");
        setLiveNotification(locale === "ar"
          ? `🤖 قام الذكاء الاصطناعي بتحديث المؤشرات: ${listStr}`
          : `🤖 AI updated clinical indicators: ${listStr}`
        );
        setTimeout(() => setLiveNotification(""), 6000);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          session_id: sessionId,
          role: "assistant",
          content: `Error: ${err?.message || "Unknown error"}`,
          has_files: false,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setThinking(false);
    }
  };

  const handleStartSession = async () => {
    if (!selectedPatient) return;
    setLoading(true);
    try {
      const s = await api.startSession(selectedPatient.id, `تشخيص - ${selectedPatient.name}`);
      setSession(s);
      setCurrentStep(2); // Go to AI Chat step
      setMessages([]);
      setDiagnosis(null);
      const fileIds = selectedFileIds;
      
      const symptomsList = selectedSymptoms
        .map((sId) => {
          const symObj = COMMON_SYMPTOMS.find((x) => x.id === sId);
          if (!symObj) return sId;
          return `${symObj.labelAr} (${symObj.labelEn})`;
        })
        .join("، ");

      const mlContext = mlResult 
        ? `[نتائج فحص التعلم الآلي - ML Heart Risk Assessment]
الاحتمالية الإحصائية للإصابة بمرض قلبي: ${mlResult.risk_percentage}% (${mlResult.risk_level_ar})
مستوى ثقة النموذج: ${(mlResult.confidence * 100).toFixed(1)}%
أهم العوامل المساهمة: ${mlResult.top_features?.map((tf: any) => `${tf.feature} (${(tf.importance * 100).toFixed(1)}%)`).join("، ")}
المؤشرات المدخلة:
${Object.entries(mlResult.features_used).map(([label, val]) => `- ${label}: ${val}`).join("\n")}`
        : "لم يتم تشغيل نموذج فحص التعلم الآلي الإحصائي المسبق لهذه الجلسة.";

      const initialMsg = `[تقرير استبيان الحالة الأولي للتشخيص - Clinical Intake Summary]
المريض: ${selectedPatient.name}
العمر: ${selectedPatient.age || "غير حدد"}
الجنس: ${selectedPatient.gender || "غير حدد"}

الشكوى الرئيسية (Chief Complaint):
${chiefComplaint.trim() || "لم تذكر شكوى رئيسية محددة"}

مدة الأعراض وبدايتها (Onset & Duration):
${duration.trim() || "غير محددة"}

الأعراض المصاحبة (Associated Symptoms):
${symptomsList || "لا توجد أعراض مصاحبة محددة"}

التاريخ الطبي والأدوية (Medical History & Medications):
${historyAndMedications.trim() || "لا يوجد تاريخ طبي مسجل"}

الملفات الطبية المرفقة للتحليل:
${fileIds.length > 0 ? `تم إرفاق ${fileIds.length} ملفات للفحص والتحليل.` : "لم يتم إرفاق ملفات."}

${mlContext}

يرجى مراجعة هذه البيانات ونتائج الفحص والبدء بطرح الأسئلة السريرية اللازمة لاستكشاف وتفصيل الحالة.`;

      await sendMessageToAI(s.id, initialMsg, fileIds);
    } catch (err: any) {
      showToast({ type: "error", title: "خطأ", message: err?.message || "Failed to start session" });
    } finally {
      setLoading(false);
    }
  };

  const toggleFile = (fileId: number) =>
    setSelectedFileIds((prev) =>
      prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
    );

  const handleSend = async () => {
    if (!input.trim() || !session) return;
    const sentInput = input;
    setInput("");
    await sendMessageToAI(session.id, sentInput, selectedFileIds);
  };

  const handleNewSession = () => {
    setSession(null);
    setMessages([]);
    setDiagnosis(null);
    setCurrentStep(0);
    setSelectedFileIds([]);
    setChiefComplaint("");
    setDuration("");
    setSelectedSymptoms([]);
    setHistoryAndMedications("");
    setMlResult(null);
    setMlError("");
  };

  const handleMLPredict = async () => {
    setMlLoading(true);
    setMlError("");
    setMlResult(null);
    try {
      const res = await api.predictHeart(mlFeatures);
      if (res.available === false) {
        setMlError(res.detail || "Model not available");
      } else if (res.can_predict === false) {
        setMlError(locale === "ar" ? res.message_ar : res.message_en);
      } else {
        setMlResult(res);
      }
    } catch (err: any) {
      setMlError(err?.message || "Prediction failed");
    } finally {
      setMlLoading(false);
    }
  };

  const handleLiveMLPredict = async (features: any, extractedKeys?: string[]) => {
    try {
      const res = await api.predictHeart({
        ...features,
        extracted_keys: extractedKeys || Object.keys(features),
      });
      if (res && res.available !== false) {
        if (res.can_predict === false) {
          setMlError(locale === "ar" ? res.message_ar : res.message_en);
          setMlResult(null);
        } else {
          setMlResult(res);
          setMlError("");
        }
      }
    } catch {}
  };

  const handleAIExtractIndicators = async () => {
    if (!selectedPatient || selectedFileIds.length === 0) return;
    setAiExtracting(true);
    setExtractReport(null);
    try {
      const report = await api.extractFileIndicators(selectedPatient.id, selectedFileIds);
      const indicators = report?.indicators || {};
      const summary = report?.summary || {};
      const messageAr = report?.message_ar || "";
      const messageEn = report?.message_en || "";

      setExtractReport(report);

      const extractedKeys = Object.keys(indicators);
      const hasExtracted = extractedKeys.length > 0;

      if (hasExtracted) {
        setMlFeatures((prev: any) => {
          const updated = { ...prev };
          Object.entries(indicators).forEach(([key, val]: any) => {
            if (val !== null && val !== undefined) updated[key] = val;
          });
          return updated;
        });

        const mergedFeatures = { ...mlFeatures };
        Object.entries(indicators).forEach(([key, val]: any) => {
          if (val !== null && val !== undefined) mergedFeatures[key] = val;
        });

        setMlLoading(true);
        setMlError("");
        try {
          const res = await api.predictHeart({
            ...mergedFeatures,
            extracted_keys: extractedKeys,
          });
          if (res.available === false) {
            setMlError(res.detail || "Model not available");
          } else if (res.can_predict === false) {
            setMlError(locale === "ar" ? res.message_ar : res.message_en);
            setMlResult(null);
          } else {
            setMlResult(res);
          }
        } catch (err: any) {
          setMlError(err?.message || "Prediction failed");
        } finally {
          setMlLoading(false);
        }
      }

      const listStr = extractedKeys
        .map((k) => {
          const field = mlFields.find((f) => f.key === k);
          const val = indicators[k];
          return field ? `${field.label}: ${val}` : `${k}: ${val}`;
        })
        .join("، ");

      const missingStr = (summary.missing_keys || [])
        .map((k: string) => mlFields.find((f) => f.key === k)?.label || k)
        .join("، ");

      const invalidStr = (summary.invalid_keys || [])
        .map((k: string) => mlFields.find((f) => f.key === k)?.label || k)
        .join("، ");

      let fullMsg = locale === "ar" ? messageAr : messageEn;
      if (hasExtracted && listStr) {
        fullMsg += `\n\n${locale === "ar" ? "✓ المؤشرات المستخرجة:" : "✓ Extracted:"} ${listStr}`;
      }
      if (missingStr) {
        fullMsg += `\n${locale === "ar" ? "✗ المؤشرات المفقودة (مطلوبة):" : "✗ Missing (required):"} ${missingStr}`;
      }
      if (invalidStr) {
        fullMsg += `\n⚠️ ${locale === "ar" ? "قيم خارج النطاق (مرفوضة):" : "Out of range (rejected):"} ${invalidStr}`;
      }

      await showAlert({ type: "info", title: locale === "ar" ? "نتائج الاستخراج" : "Extraction Results", message: fullMsg });
    } catch (err: any) {
      showToast({
        type: "error",
        title: locale === "ar" ? "خطأ" : "Error",
        message: locale === "ar"
          ? `خطأ أثناء استخراج المؤشرات: ${err?.message || "فشل الاتصال"}`
          : `Error extracting indicators: ${err?.message || "Connection failed"}`
      });
    } finally {
      setAiExtracting(false);
    }
  };

  // Step 3 (or 4): Unified Clinical Report Dashboard (AI Report + ML Heart Risk Gauge side-by-side)
  if (currentStep === 3 && diagnosis) {
    return (
      <div className="flex flex-col gap-6 p-6 bg-gradient-to-tr from-slate-50 to-white min-h-[calc(100vh-6.5rem)] overflow-y-auto w-full animate-fade-in">
        {/* Progress Stepper at top */}
        <div className="w-full max-w-[1400px] mx-auto bg-white rounded-2xl border border-slate-200/80 shadow-sm p-4">
          <DiagnosisStepper step={3} hasDiagnosis={true} />
          
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-2">
            <div>
              <h2 className="text-lg font-bold text-text font-outfit">
                {locale === "ar" ? "التقرير السريري الموحد والتشخيص النهائي" : "Unified Clinical Report & Final Diagnosis"}
              </h2>
              <p className="text-xs text-text-muted mt-0.5">
                {selectedPatient?.name} · {selectedPatient?.age} {locale === "ar" ? "سنة" : "years"} · {translateGender(selectedPatient?.gender, locale)}
              </p>
            </div>
            
            <div className="flex gap-2.5">
              <button
                onClick={() => setCurrentStep(2)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-text-secondary transition hover:bg-slate-50 hover:text-text active:scale-[0.98]"
              >
                {locale === "ar" ? "← عرض المحادثة السريرية" : "← View Chat History"}
              </button>
              <button
                onClick={handleNewSession}
                className="rounded-xl bg-gradient-to-r from-accent to-cyan-500 px-5 py-2.5 text-xs font-semibold text-white shadow-md shadow-accent/15 transition-all hover:from-accent-hover hover:to-cyan-600 active:scale-[0.98]"
              >
                + {locale === "ar" ? "بدء جلسة جديدة" : "Start New Session"}
              </button>
            </div>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-6 w-full max-w-[1400px] mx-auto">
          {/* Left Column: AI Diagnosis Card */}
          <div className="space-y-4">
            <DiagnosisCard result={diagnosis} />
          </div>

          {/* Right Column: ML Heart Risk Gauge & Factors */}
          <div className="space-y-6">
            {mlResult ? (
              <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 space-y-6">
                <div className="border-b border-slate-100 pb-3">
                  <h3 className="text-sm font-bold text-text flex items-center gap-1.5">
                    <span>📊</span> {t("diagnosis.mlRiskResultTitle")}
                  </h3>
                </div>
                
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                  <RadialProgress
                    value={mlResult.risk_score * 100}
                    color={riskColors[mlResult.risk_level]?.ring || "#94a3b8"}
                  />
                  <div className="space-y-1">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{locale === "ar" ? "الاستنتاج الإحصائي" : "Statistical Conclusion"}</p>
                    <p className="text-base font-bold text-text">{locale === "ar" ? (mlResult.prediction_label || mlResult.prediction_label_en) : (mlResult.prediction_label_en || mlResult.prediction_label)}</p>
                    <div className="mt-2.5">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                          riskColors[mlResult.risk_level]?.bg
                        } ${riskColors[mlResult.risk_level]?.text} ${
                          riskColors[mlResult.risk_level]?.border
                        }`}
                      >
                        {locale === "ar" ? "مستوى الخطر: " : "Risk Level: "} 
                        {locale === "ar" ? (mlResult.risk_level_ar || mlResult.risk_level) : (mlResult.risk_level || mlResult.risk_level_ar)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3 pt-4 border-t border-slate-100">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                    {t("diagnosis.topFactors")}
                  </p>
                  <div className="space-y-3">
                    {mlResult.top_features?.map((tf: any, i: number) => {
                      const pct = tf.importance * 100;
                      return (
                        <div key={i} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-text-secondary">{locale === "ar" ? (tf.feature || tf.feature_en) : (tf.feature_en || tf.feature)}</span>
                            <span className="font-bold text-accent">{pct.toFixed(1)}%</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-accent transition-all duration-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 border border-slate-100 p-3 text-[10px] text-text-muted space-y-1">
                  <div>{locale === "ar" ? "النموذج: " : "Model: "} {mlResult.model_name}</div>
                  <div className="font-semibold text-text-secondary">
                    {locale === "ar" ? "دقة الفحص: " : "Accuracy: "} {(mlResult.model_accuracy * 100).toFixed(1)}% | AUC: {(mlResult.model_auc * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 text-center italic text-text-muted">
                {locale === "ar" ? "لم يتم تشغيل نموذج فحص خطورة القلب لهذه الجلسة." : "Local ML heart risk model not calculated for this session."}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Step 0: Clinical Intake Questionnaire
  if (currentStep === 0) {
    return (
      <div className="flex h-[calc(100vh-6.5rem)] items-center justify-center p-6 bg-gradient-to-tr from-slate-50 to-white overflow-y-auto w-full animate-fade-in">
        <div className="w-full max-w-[1400px] bg-white rounded-2xl border border-slate-200/80 shadow-md p-6 lg:p-8 flex flex-col h-full overflow-hidden">
          <DiagnosisStepper step={0} hasDiagnosis={false} />
          
          <div className="mb-4 text-center">
            <h2 className="text-lg font-bold text-text font-outfit">{t("diagnosis.title")}</h2>
            <p className="mt-1 text-xs text-text-muted">{t("diagnosis.step1Sub")}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1 overflow-hidden min-h-0">
            {/* Column 1: Patient Select & File Manager */}
            <div className="space-y-4 overflow-y-auto pr-1">
              <div className="border-b border-slate-100 pb-2">
                <h3 className="text-sm font-bold text-text mb-0.5">{t("diagnosis.step1Title")}</h3>
                <p className="text-[11px] text-text-muted">{t("diagnosis.step1Sub")}</p>
              </div>

              <div>
                <Label required className="text-xs font-bold text-text-secondary">{t("diagnosis.selectPatient")}</Label>
                <Select
                  value={selectedPatient?.id || ""}
                  onChange={(e) => handleSelectPatient(Number(e.target.value))}
                  className="mt-1 py-1.5 text-xs"
                >
                  <option value="">-- {t("diagnosis.selectPatient")} --</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.age} {locale === "ar" ? "سنة" : "years"})
                    </option>
                  ))}
                </Select>
              </div>

              {selectedPatient && (
                <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-3.5 transition-all duration-200 animate-slide-up">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-light text-xs font-bold text-accent shadow-sm shadow-accent/5">
                      {selectedPatient.name?.charAt(0)}
                    </div>
                    <div>
                      <p className="text-xs font-bold text-text">{selectedPatient.name}</p>
                      <p className="text-[11px] text-text-secondary mt-0.5">
                        {selectedPatient.age} {locale === "ar" ? "سنة" : "years"} · {translateGender(selectedPatient.gender, locale)} · {formatDiagnosis(selectedPatient.diagnosis, locale) || (locale === "ar" ? "بدون تشخيص سابق" : "No prior diagnosis")}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {selectedPatient && (
                <div className="space-y-3 pt-1">
                  <Label className="text-xs font-bold text-text-secondary">{t("diagnosis.includeDocs")} ({selectedFileIds.length})</Label>
                  {files.length > 0 ? (
                    <div className="max-h-[140px] overflow-y-auto space-y-1.5 border border-slate-150 rounded-xl p-2 bg-slate-50/30">
                      {files.map((f) => {
                        const sel = selectedFileIds.includes(f.id);
                        return (
                          <label
                            key={f.id}
                            className={clsx(
                              "flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-1.5 transition-all text-xs",
                              sel
                                ? "border-accent bg-accent-light text-accent font-semibold"
                                : "border-slate-200/60 bg-white hover:bg-slate-50 text-text-secondary"
                            )}
                          >
                            <input
                              type="checkbox"
                              checked={sel}
                              onChange={() => toggleFile(f.id)}
                              className="rounded border-slate-300 text-accent focus:ring-accent"
                            />
                            <span className="text-xs">{catIcon[f.category]}</span>
                            <span className="truncate flex-1 font-medium">{f.file_name}</span>
                          </label>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-text-muted italic bg-slate-50 p-2.5 rounded-xl border border-dashed text-center">{t("diagnosis.noFilesUploaded")}</p>
                  )}

                  <div className="border-t border-slate-100 pt-2">
                    <Label className="text-xs font-bold text-text-secondary">{t("diagnosis.uploadNewFiles")}</Label>
                    <div className="mt-1">
                      <FileUploader
                        patientId={selectedPatient.id}
                        onUploaded={() => loadFiles(selectedPatient.id)}
                        compact
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Column 2: Symptoms Intake Questionnaire */}
            <div className="space-y-4 border-t md:border-t-0 md:border-r border-slate-200/80 md:pr-6 pt-4 md:pt-0 overflow-y-auto pr-1">
              <div className="border-b border-slate-100 pb-2">
                <h3 className="text-sm font-bold text-text mb-0.5">{locale === "ar" ? "الشكوى السريرية والأعراض" : "Clinical Complaint & Symptoms"}</h3>
                <p className="text-[11px] text-text-muted">{locale === "ar" ? "مجموعة تفاصيل تساعد الذكاء الاصطناعي على فهم الحالة" : "Intake details to guide the AI co-pilot"}</p>
              </div>

              {!selectedPatient ? (
                <div className="h-full flex items-center justify-center py-12 text-center">
                  <p className="text-xs text-text-muted italic">{t("diagnosis.selectPatientPrompt")}</p>
                </div>
              ) : (
                <div className="space-y-4 animate-slide-up pb-4">
                  <div>
                    <Label required className="text-xs font-bold text-text-secondary">{t("diagnosis.chiefComplaintLabel")}</Label>
                    <textarea
                      placeholder={t("diagnosis.chiefComplaintPlaceholder")}
                      value={chiefComplaint}
                      onChange={(e) => setChiefComplaint(e.target.value)}
                      className="input-base mt-1 min-h-[50px] py-1.5 resize-y text-xs"
                      required
                    />
                  </div>

                  <div>
                    <Label className="text-xs font-bold text-text-secondary">{t("diagnosis.onsetDurationLabel")}</Label>
                    <Input
                      type="text"
                      placeholder={t("diagnosis.onsetDurationPlaceholder")}
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      className="mt-1 text-xs py-1.5"
                    />
                  </div>

                  <div>
                    <Label className="text-xs font-bold text-text-secondary">{t("diagnosis.associatedSymptomsLabel")}</Label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {COMMON_SYMPTOMS.map((sym) => {
                        const active = selectedSymptoms.includes(sym.id);
                        return (
                          <button
                            key={sym.id}
                            type="button"
                            onClick={() => toggleSymptom(sym.id)}
                            className={clsx(
                              "rounded-lg px-2.5 py-1 text-[11px] transition-all font-medium border",
                              active
                                ? "bg-accent/15 border-accent text-accent font-semibold"
                                : "bg-slate-50 border-slate-200 text-text-secondary hover:bg-slate-100"
                            )}
                          >
                            {t("diagnosis.symptoms." + sym.id)}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <Label className="text-xs font-bold text-text-secondary">{t("diagnosis.historyMedicationsLabel")}</Label>
                    <textarea
                      placeholder={t("diagnosis.historyMedicationsPlaceholder")}
                      value={historyAndMedications}
                      onChange={(e) => setHistoryAndMedications(e.target.value)}
                      className="input-base mt-1 min-h-[50px] py-1.5 resize-y text-xs"
                    />
                  </div>

                  <div className="pt-2 border-t border-slate-100">
                    <button
                      onClick={() => setCurrentStep(1)}
                      disabled={!chiefComplaint.trim()}
                      className="w-full rounded-xl bg-gradient-to-r from-accent to-cyan-500 py-2.5 text-xs font-semibold text-white shadow-md shadow-accent/15 transition-all hover:from-accent-hover hover:to-cyan-600 active:scale-[0.98] disabled:opacity-50"
                    >
                      {t("nextToMLBtn")}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Step 1: ML Heart Risk Assessment
  if (currentStep === 1) {
    return (
      <div className="flex h-[calc(100vh-6.5rem)] items-center justify-center p-6 bg-gradient-to-tr from-slate-50 to-white overflow-y-auto w-full animate-fade-in">
        <div className="w-full max-w-[1400px] bg-white rounded-2xl border border-slate-200/80 shadow-md p-6 lg:p-8 flex flex-col h-full overflow-auto">
          {/* Stepper progress */}
          <DiagnosisStepper step={1} hasDiagnosis={false} />
          
          <div className="mb-4 text-center">
            <h2 className="text-lg font-bold text-text font-outfit">{t("diagnosis.step2Title")}</h2>
            <p className="mt-1 text-xs text-text-muted">{t("diagnosis.step2Sub")}</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-6 flex-1 overflow-hidden min-h-0">
            {/* Column 1: Parameter inputs Form */}
            <div className="border border-slate-200 rounded-xl p-4 overflow-y-auto bg-slate-50/20 max-h-[460px] lg:max-h-full">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100">
                <h3 className="text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-1.5">
                  <span>🧬</span> {locale === "ar" ? "المؤشرات وعوامل الخطر (13 متغيراً)" : "Parameters & Risk Factors (13 Variables)"}
                </h3>
                {selectedFileIds.length > 0 && (
                  <button
                    type="button"
                    onClick={handleAIExtractIndicators}
                    disabled={aiExtracting}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-accent-light border border-accent/20 px-3 py-1.5 text-xs font-bold text-accent transition hover:bg-accent/20 active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none"
                  >
                    {aiExtracting ? (
                      <>
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                        {locale === "ar" ? "جاري الاستخراج..." : "Extracting..."}
                      </>
                    ) : (
                      <>
                        <span>🪄</span>
                        {locale === "ar" ? "تعبئة تلقائية بالذكاء الاصطناعي" : "AI Auto-populate"}
                      </>
                    )}
                  </button>
                )}
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {mlFields.map((f) => {
                  const detail = extractReport?.details?.find((d: any) => d.key === f.key);
                  const isExtracted = detail?.status === "extracted";
                  const isInvalid = detail?.status === "invalid";
                  const isMissing = detail?.status === "missing";
                  const sourceTooltip = detail ? (locale === "ar" ? detail.source_ar : detail.source_en) : "";
                  return (
                    <div key={f.key} className="space-y-1">
                      <Label className="text-[11px] font-bold text-text-secondary flex items-center gap-1">
                        {f.label}
                        {isExtracted && <span title={sourceTooltip} className="text-emerald-600">✓</span>}
                        {isInvalid && <span title={locale === "ar" ? "قيمة خارج النطاق" : "Out of range"} className="text-red-500">⚠</span>}
                        {isMissing && extractReport && <span title={locale === "ar" ? "مفقود - مطلوب" : "Missing - required"} className="text-amber-500">✗</span>}
                      </Label>
                      {f.options ? (
                        <Select
                          value={String(mlFeatures[f.key] === "" || mlFeatures[f.key] === undefined ? "" : mlFeatures[f.key])}
                          onChange={(e) => {
                            const val = e.target.value;
                            setMlFeatures((prev: any) => ({ ...prev, [f.key]: val === "" ? "" : parseFloat(val) }));
                          }}
                          className={`rounded-xl py-1 text-xs ${
                            isExtracted ? "border-emerald-300 bg-emerald-50/40"
                            : isInvalid ? "border-red-200 bg-red-50/30"
                            : (mlFeatures[f.key] === "" || mlFeatures[f.key] === undefined) ? "border-amber-300 bg-amber-50/30"
                            : "border-slate-200/80 bg-white"
                          }`}
                        >
                          <option value="">{locale === "ar" ? "-- اختر --" : "-- Select --"}</option>
                          {f.options.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </Select>
                      ) : (
                        <Input
                          type={f.type || "text"}
                          placeholder={locale === "ar" ? "أدخل القيمة" : "Enter value"}
                          value={mlFeatures[f.key] === undefined ? "" : mlFeatures[f.key]}
                          onChange={(e) => {
                            const val = e.target.value;
                            setMlFeatures((prev: any) => ({ ...prev, [f.key]: val === "" ? "" : parseFloat(val) }));
                          }}
                          className={`rounded-xl py-1 text-xs ${
                            isExtracted ? "border-emerald-300 bg-emerald-50/40"
                            : isInvalid ? "border-red-200 bg-red-50/30"
                            : (mlFeatures[f.key] === "" || mlFeatures[f.key] === undefined) ? "border-amber-300 bg-amber-50/30"
                            : "border-slate-200/80 bg-white"
                          }`}
                        />
                      )}
                    </div>
                  );
                })}
              </div>

              {extractReport && (
                <div className={`mt-4 rounded-xl border p-3 text-xs space-y-2 ${
                  extractReport.summary?.complete
                    ? "border-emerald-200 bg-emerald-50/40"
                    : "border-amber-200 bg-amber-50/40"
                }`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 font-bold text-text">
                      <span>{extractReport.summary?.complete ? "✅" : "⚠️"}</span>
                      <span>{locale === "ar" ? "تقرير استخراج البيانات" : "Data Extraction Report"}</span>
                    </div>
                    {extractReport.summary?.complete ? (
                      <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-emerald-800 font-bold text-[10px]">
                        {locale === "ar" ? "مكتمل" : "Complete"}
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-amber-800 font-bold text-[10px]">
                        {locale === "ar" ? "غير مكتمل" : "Incomplete"}
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700 font-bold border border-emerald-100">
                      ✓ {locale === "ar" ? "مستخرج:" : "Extracted:"} {extractReport.summary?.extracted_count ?? 0}/{extractReport.summary?.total_count ?? 13}
                    </span>
                    {(extractReport.summary?.missing_count ?? 0) > 0 && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700 font-bold border border-amber-100">
                        ✗ {locale === "ar" ? "مفقود (مطلوب):" : "Missing (required):"} {extractReport.summary?.missing_count}
                      </span>
                    )}
                    {(extractReport.summary?.invalid_count ?? 0) > 0 && (
                      <span className="rounded-full bg-red-50 px-2 py-0.5 text-red-700 font-bold border border-red-100">
                        ⚠ {locale === "ar" ? "خارج النطاق:" : "Invalid:"} {extractReport.summary?.invalid_count}
                      </span>
                    )}
                    {mlResult?.reliability && (
                      <span className={`rounded-full px-2 py-0.5 font-bold ${mlResult.reliability === "high" ? "bg-emerald-50 text-emerald-700" : mlResult.reliability === "medium" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>
                        {locale === "ar" ? "موثوقية:" : "Reliability:"} {locale === "ar" ? (mlResult.reliability_ar || mlResult.reliability) : mlResult.reliability}
                      </span>
                    )}
                  </div>
                  <p className="text-text-muted leading-relaxed whitespace-pre-line">{locale === "ar" ? (extractReport.message_ar || extractReport.message_en) : (extractReport.message_en || extractReport.message_ar)}</p>
                  {extractReport.summary?.had_error && (
                    <p className="text-red-600 text-[11px]">
                      {locale === "ar" ? "حدث خطأ مؤقت أثناء الاستخراج (تمت إعادة المحاولة)." : "Transient error occurred (retried)."}: {extractReport.summary.error}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Column 2: Radial Gauge & Results */}
            <div className="border border-slate-200 rounded-xl p-4 flex flex-col justify-between bg-slate-50/10 overflow-y-auto">
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-text-secondary pb-2 border-b border-slate-100 flex items-center gap-1.5">
                  <span>📊</span> {t("diagnosis.mlRiskResultTitle")}
                </h3>
                
                {mlResult ? (
                  <div className="space-y-6 animate-slide-up">
                    <div className="flex flex-col sm:flex-row items-center justify-around gap-4">
                      <RadialProgress
                        value={mlResult.risk_score * 100}
                        color={riskColors[mlResult.risk_level]?.ring || "#94a3b8"}
                      />
                      <div className="text-center sm:text-right space-y-1">
                        <p className="text-[9px] font-bold uppercase tracking-wider text-text-muted">{locale === "ar" ? "الاستنتاج" : "Conclusion"}</p>
                        <p className="text-sm font-bold text-text">{locale === "ar" ? (mlResult.prediction_label || mlResult.prediction_label_en) : (mlResult.prediction_label_en || mlResult.prediction_label)}</p>
                        <div className="mt-1.5">
                          <span
                            className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider ${
                              riskColors[mlResult.risk_level]?.bg
                            } ${riskColors[mlResult.risk_level]?.text} ${
                              riskColors[mlResult.risk_level]?.border
                            }`}
                          >
                            {locale === "ar" ? "مستوى الخطر: " : "Risk: "}
                            {locale === "ar" ? (mlResult.risk_level_ar || mlResult.risk_level) : (mlResult.risk_level || mlResult.risk_level_ar)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2 pt-3 border-t border-slate-100">
                      <p className="text-[9px] font-bold uppercase tracking-wider text-text-muted">
                        {t("diagnosis.topFactors")}
                      </p>
                      <div className="space-y-2">
                        {mlResult.top_features?.map((tf: any, i: number) => {
                          const pct = tf.importance * 100;
                          return (
                            <div key={i} className="space-y-0.5">
                              <div className="flex items-center justify-between text-[11px]">
                                <span className="font-semibold text-text-secondary">{locale === "ar" ? (tf.feature || tf.feature_en) : (tf.feature_en || tf.feature)}</span>
                                <span className="font-bold text-accent">{pct.toFixed(1)}%</span>
                              </div>
                              <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-accent transition-all duration-500"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-[200px] border border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center p-6 text-center bg-slate-50/50">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-400 mb-2 text-base">
                      ⚙️
                    </div>
                    <p className="text-xs font-semibold text-text-secondary">{t("diagnosis.mlNotCalculated")}</p>
                  </div>
                )}
                
                {mlError && (
                  <div className="rounded-xl bg-danger/10 border border-danger/20 px-3 py-2 text-[11px] text-danger space-y-2">
                    <div className="flex items-center gap-2">
                      <span>⚠️</span>
                      <p className="font-semibold">{mlError}</p>
                    </div>
                    <button
                      onClick={() => {
                        setMlError("");
                        handleMLPredict();
                      }}
                      disabled={mlLoading}
                      className="w-full rounded-lg bg-accent hover:bg-accent-hover py-2 text-xs font-semibold text-white shadow-sm transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {mlLoading
                        ? (locale === "ar" ? "جاري التحليل..." : "Analyzing...")
                        : (locale === "ar" ? "🔄 إعادة التشخيص" : "🔄 Re-diagnose")}
                    </button>
                  </div>
                )}
              </div>

              <div className="space-y-2.5 pt-4 border-t border-slate-100">
                {(() => {
                  const filledCount = mlFields.filter((f) => mlFeatures[f.key] !== "" && mlFeatures[f.key] !== undefined && mlFeatures[f.key] !== null).length;
                  const totalCount = mlFields.length;
                  const isComplete = filledCount === totalCount;
                  return (
                    <>
                      <div className={`text-center text-[11px] font-bold ${isComplete ? "text-emerald-600" : "text-amber-600"}`}>
                        {isComplete
                          ? (locale === "ar" ? `✓ جميع المؤشرات مكتملة (${totalCount}/${totalCount})` : `✓ All indicators complete (${totalCount}/${totalCount})`)
                          : (locale === "ar" ? `تم توفير ${filledCount} من ${totalCount} مؤشر — أكمل الباقي للتشخيص` : `${filledCount} of ${totalCount} indicators provided — complete the rest to diagnose`)}
                      </div>
                      <button
                        onClick={handleMLPredict}
                        disabled={mlLoading || !isComplete}
                        className={`w-full rounded-xl py-2.5 text-xs font-semibold text-white shadow-sm transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${
                          isComplete ? "bg-accent hover:bg-accent-hover shadow-accent/10" : "bg-slate-400"
                        }`}
                      >
                        {mlLoading ? t("diagnosis.mlPredicting") : isComplete ? t("diagnosis.mlPredictBtn") : (locale === "ar" ? "أكمل المؤشرات أولاً" : "Complete indicators first")}
                      </button>
                    </>
                  );
                })()}
                
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentStep(0)}
                    className="flex-1 rounded-xl border border-slate-200 bg-white py-2.5 text-xs font-semibold text-text-secondary transition hover:bg-slate-50 active:scale-[0.98]"
                  >
                    {t("backToIntakeBtn")}
                  </button>
                  <button
                    onClick={handleStartSession}
                    disabled={mlLoading}
                    className="flex-1 rounded-xl bg-gradient-to-r from-accent to-cyan-500 py-2.5 text-xs font-semibold text-white shadow-md shadow-accent/15 transition-all hover:from-accent-hover hover:to-cyan-600 active:scale-[0.98]"
                  >
                    {t("proceedToChatBtn")}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Step 2: Active Chat Session Layout (Sidebar + Chat Area)
  return (
    <div className="grid h-[calc(100vh-6.5rem)] grid-cols-1 gap-5 lg:grid-cols-[300px_1fr]">
      {/* Sidebar Panel */}
      <aside className="space-y-4 overflow-y-auto pr-1">
        {session && (
          <div className="card-base border-slate-200/60 p-4 bg-white/70 backdrop-blur-md">
            <div className="flex items-center gap-2 mb-2">
              <span className="h-2 w-2 rounded-full bg-success animate-pulse-dot" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-success">{t("diagnosis.sessionActive")}</span>
            </div>
            <p className="text-sm font-semibold text-text">{session.title}</p>
            <p className="text-xs text-text-secondary mt-0.5">{selectedPatient?.name} · {files.length} {t("uploads.title")}</p>
            <button
              onClick={handleNewSession}
              className="mt-3.5 w-full rounded-xl border border-slate-200 bg-slate-50 py-2 text-xs font-semibold text-text-secondary transition hover:bg-slate-100 hover:text-text active:scale-[0.98]"
            >
              + {t("diagnosis.newSession")}
            </button>
          </div>
        )}

        {(currentStep === 2) && mlResult && (
          <div className="card-base border-slate-200/60 p-4 bg-white/70 backdrop-blur-md space-y-3 animate-slide-up">
            <p className="text-[10px] font-bold uppercase tracking-wider text-text-secondary pb-1 border-b border-slate-100 flex items-center gap-1.5">
              <span>📊</span> {locale === "ar" ? "نسبة خطورة القلب (محلي)" : "Heart Risk Screening (Local)"}
            </p>
            <div className="flex items-center gap-3">
              <div className="scale-75 origin-center -ml-3 -mr-3">
                <RadialProgress
                  value={mlResult.risk_score * 100}
                  color={riskColors[mlResult.risk_level]?.ring || "#94a3b8"}
                />
              </div>
              <div className="flex-1 space-y-1 min-w-0">
                <p className="text-xs font-bold text-text truncate">{locale === "ar" ? (mlResult.prediction_label || mlResult.prediction_label_en) : (mlResult.prediction_label_en || mlResult.prediction_label)}</p>
                <div>
                  <span
                    className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[9px] font-bold ${
                      riskColors[mlResult.risk_level]?.bg
                    } ${riskColors[mlResult.risk_level]?.text} ${
                      riskColors[mlResult.risk_level]?.border
                    }`}
                  >
                    {locale === "ar" ? (mlResult.risk_level_ar || mlResult.risk_level) : (mlResult.risk_level || mlResult.risk_level_ar)}
                  </span>
                </div>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary space-y-1 bg-slate-50 p-2 rounded-xl border border-slate-100/80">
              <p className="font-bold text-text-muted mb-1">{locale === "ar" ? "المؤشرات النشطة:" : "Active Indicators:"}</p>
              <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
                <div>{locale === "ar" ? "العمر: " : "Age: "} {mlFeatures.age}</div>
                <div>{locale === "ar" ? "الضغط: " : "BP: "} {mlFeatures.trestbps}</div>
                <div>{locale === "ar" ? "الكوليسترول: " : "Chol: "} {mlFeatures.chol}</div>
                <div>{locale === "ar" ? "النبض: " : "Pulse: "} {mlFeatures.thalach}</div>
              </div>
            </div>
          </div>
        )}

        {(currentStep === 2) && selectedPatient && files.length > 0 && (
          <div className="card-base border-slate-200/60 p-4 bg-white/70 backdrop-blur-md">
            <p className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-3">{t("diagnosis.patientFiles")}</p>
            <div className="space-y-2">
              {files.map((f) => {
                const sel = selectedFileIds.includes(f.id);
                return (
                  <label
                    key={f.id}
                    className={clsx(
                      "flex cursor-pointer items-center gap-2.5 rounded-xl border px-3 py-2.5 transition-all text-xs",
                      sel
                        ? "border-accent bg-accent-light text-accent font-semibold"
                        : "border-slate-200/60 hover:bg-slate-50 text-text-secondary"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={sel}
                      onChange={() => toggleFile(f.id)}
                      className="rounded border-slate-300 text-accent focus:ring-accent"
                    />
                    <span className="text-base">{catIcon[f.category]}</span>
                    <span className="truncate flex-1 font-medium">{f.file_name}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        {(currentStep === 2) && selectedPatient && (
          <div className="card-base border-slate-200/60 p-4 bg-white/70 backdrop-blur-md">
            <p className="text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-3">{t("uploads.upload")}</p>
            <FileUploader
              patientId={selectedPatient.id}
              onUploaded={() => loadFiles(selectedPatient.id)}
              compact
            />
          </div>
        )}
      </aside>

      {/* Main Chat Workspace */}
      <section className="flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-100/50">
        {/* Chat Workspace Header */}
        <div className="border-b border-slate-200/80 bg-slate-50/50 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-xs font-bold text-accent">
              {selectedPatient?.name?.charAt(0)}
            </div>
            <div>
              <p className="text-xs font-bold text-text leading-tight">{selectedPatient?.name}</p>
              <p className="text-[10px] text-text-muted mt-0.5">{locale === "ar" ? "عمر" : "Age"} {selectedPatient?.age} · {selectedPatient?.gender}</p>
            </div>
          </div>
          <button
            onClick={handleNewSession}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-text-secondary transition hover:bg-slate-50 hover:text-text active:scale-95"
          >
            {t("diagnosis.endSession")}
          </button>
        </div>

        {/* Diagnostic Progress Stepper */}
        <div className="bg-white border-b border-slate-100 px-4 py-2 flex items-center justify-center w-full">
          <DiagnosisStepper step={2} hasDiagnosis={!!diagnosis} />
        </div>

        {liveNotification && (
          <div className="bg-accent/10 border-b border-accent/20 px-4 py-2 text-xs font-semibold text-accent flex items-center gap-2 animate-slide-up">
            <span>✨</span>
            <span className="flex-1">{liveNotification}</span>
            <button onClick={() => setLiveNotification("")} className="font-bold text-accent/65 hover:text-accent ml-2 text-sm">×</button>
          </div>
        )}

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto bg-slate-50/30 p-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center max-w-sm">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-light text-accent">
                  <svg className="h-5 w-5 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-text">{t("diagnosis.aiThinking")}</p>
                <p className="mt-1 text-xs text-text-muted">{t("diagnosis.aiThinkingIntro")}</p>
              </div>
            </div>
          ) : (
            <div className="mx-auto w-full max-w-[1300px] space-y-4">
              <div className="mx-auto max-w-4xl w-full space-y-4">
                {messages.map((msg) => (
                  <MsgBubble key={msg.id} msg={msg} />
                ))}
                {thinking && <TypingDot />}
              </div>
              {diagnosis && (
                <div className="pt-4 pb-2 animate-fade-in w-full">
                  <DiagnosisCard result={diagnosis} />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Panel */}
        <div className="border-t border-slate-200/80 bg-white p-4">
          <div className="mx-auto max-w-4xl">
            {selectedFileIds.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-1.5 animate-slide-up">
                {selectedFileIds.map((id) => {
                  const f = files.find((f) => f.id === id);
                  if (!f) return null;
                  return (
                    <span
                      key={id}
                      className="inline-flex items-center gap-1 rounded-lg bg-accent-light border border-accent/15 px-2.5 py-1 text-[11px] font-semibold text-accent"
                    >
                      {catIcon[f.category]} {f.file_name}
                      <button
                        onClick={() => toggleFile(id)}
                        className="ml-1 text-accent/50 hover:text-accent font-bold"
                      >
                        ×
                      </button>
                    </span>
                  );
                })}
              </div>
            )}

            <div className="flex gap-2 relative">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={t("diagnosis.chatPlaceholder")}
                disabled={thinking}
                className="input-base pr-4 flex-1 shadow-sm border-slate-200 focus:ring-accent/10 py-3 rounded-xl"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || thinking}
                className="rounded-xl bg-accent px-5 py-3 text-xs font-semibold text-white shadow-sm shadow-accent/10 transition-all hover:bg-accent-hover active:scale-95 disabled:pointer-events-none disabled:opacity-40"
              >
                {t("diagnosis.send")}
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function MsgBubble({ msg }: { msg: Message }) {
  const { t } = useI18n();
  const isUser = msg.role === "user";
  
  // Custom visual representation for the clinical intake report in chat bubbles
  const displayContent = msg.content.startsWith("[تقرير استبيان الحالة الأولي للتشخيص")
    ? t("diagnosis.intakeSent")
    : msg.content.startsWith("قم بتحليل حالة المريض")
      ? "بدء تشخيص المريض وتحليل الملفات الطبية المرفقة..."
      : msg.content;

  return (
    <div className={clsx("flex animate-slide-up", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm",
          isUser
            ? "bg-text text-white rounded-br-none"
            : "border border-slate-200/80 bg-white text-text rounded-bl-none"
        )}
      >
        <p className="whitespace-pre-wrap">{displayContent}</p>
      </div>
    </div>
  );
}

function TypingDot() {
  return (
    <div className="flex animate-slide-up justify-start">
      <div className="rounded-2xl border border-slate-200/80 bg-white px-4 py-3 shadow-sm rounded-bl-none">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-accent/40 [animation-delay:-0.3s]" />
          <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-accent/60 [animation-delay:-0.15s]" />
          <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-accent" />
        </div>
      </div>
    </div>
  );
}

function RadialProgress({ value, color }: { value: number; color: string }) {
  const radius = 60;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg height={radius * 2} width={radius * 2} className="transform -rotate-90">
        <circle
          stroke="#f1f5f9"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={color}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={circumference + " " + circumference}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-bold text-text font-outfit">{value.toFixed(1)}%</span>
        <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider mt-0.5">نسبة الخطر</span>
      </div>
    </div>
  );
}
